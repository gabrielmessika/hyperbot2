"""Extend the fixed slow trend with free daily prices and hourly funding."""

from __future__ import annotations

import argparse
import itertools
import json
import random
import runpy
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from hyperbot2.research.artifacts import checked_input, file_sha256, write_json
from hyperbot2.research.rotation import COINS, HOUR, leg_return

D = Decimal
DAY = 24 * HOUR
START, OLD_END, END = 1733356800000, 1773100800000, 1788652800000


def daily_leg(
    opens: list[Decimal],
    funding: dict[int, Decimal],
    index: int,
    side: int,
    fee: Decimal,
    slip: Decimal,
    mode: str,
) -> dict:
    economics = leg_return(
        opens, [D(0)] * len(opens), index, 7, side, fee, slip, "zero"
    )
    entry_ms = START + index * DAY
    entry_price = opens[index] * (1 + side * slip)
    cost = D(0)
    if mode != "zero":
        for at in range(entry_ms + HOUR, entry_ms + 7 * DAY + HOUR, HOUR):
            rate = funding[at]
            cost += (
                opens[(at - START) // DAY]
                / entry_price
                * (side * rate if mode == "signed" else abs(rate))
            )
    economics["funding_cost_bps"] = cost * 10000
    economics["net_bps"] -= cost * 10000
    return economics


def daily_inputs(root: Path) -> tuple[dict, dict, dict]:
    sources, opens, closes = {}, {}, {}
    manifest = root / "manifest.json"
    sources[str(manifest)] = checked_input(manifest)
    for request in json.loads(manifest.read_text())["requests"]:
        path = Path(request["path"])
        sources[str(path)] = checked_input(path)
        if sources[str(path)] != request["sha256"]:
            raise ValueError("daily source mismatch")
        query = request["request"]
        if query["type"] != "candleSnapshot" or query["req"]["interval"] != "1d":
            raise ValueError("daily query expected")
        coin = query["req"]["coin"]
        if coin not in COINS or coin in opens:
            raise ValueError("unexpected or duplicate coin")
        raw = json.loads(path.read_text())["response"]
        rows = [b for b in raw if START <= b["t"] < END]
        if [b["t"] for b in rows] != list(range(START, END, DAY)):
            raise ValueError("daily price gap/duplicate")
        for b in rows:
            if b["s"] != coin or b["i"] != "1d" or b["T"] != b["t"] + DAY - 1:
                raise ValueError("daily candle identity")
            o, h, low, c = [D(b[k]) for k in ("o", "h", "l", "c")]
            if (
                not all(v.is_finite() and v > 0 for v in (o, h, low, c))
                or not low <= min(o, c) <= max(o, c) <= h
            ):
                raise ValueError("invalid OHLC")
        opens[coin] = [D(b["o"]) for b in rows]
        closes[coin] = [D(b["c"]) for b in rows]
    if set(opens) != set(COINS):
        raise ValueError("daily universe must remain BTC/ETH/SOL/HYPE")
    return opens, closes, sources


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    root = Path("data/free_rotation_2026-09-07")
    opens, closes, sources = daily_inputs(root / "daily")
    folder = Path("reports/free_rotation_2026-09-07")
    for reg, doc in (
        ("extension_registration.json", "EXTENSION.md"),
        ("coverage_registration.json", "COVERAGE_ADJUSTMENT.md"),
    ):
        sources[str(folder / reg)] = checked_input(folder / reg)
        sources[str(folder / doc)] = file_sha256(folder / doc)
        if (
            json.loads((folder / reg).read_text())["protocol_sha256"]
            != sources[str(folder / doc)]
        ):
            raise ValueError("extension protocol changed")
    loader_path = Path(__file__).with_name("evaluate_alternatives.py")
    hourly, funding, _, _, old_sources = runpy.run_path(str(loader_path))[
        "load_history"
    ](Path("data/search_2026-09-06/history"))
    sources.update(old_sources)
    comparisons = 0
    for coin in COINS:
        for b in hourly[coin]:
            if b.time % DAY == 0:
                if b.open != opens[coin][(b.time - START) // DAY]:
                    raise ValueError("daily/hourly open divergence")
                comparisons += 1
    manifest = root / "old_funding/manifest.json"
    sources[str(manifest)] = checked_input(manifest)
    for request in json.loads(manifest.read_text())["requests"]:
        path = Path(request["path"])
        sources[str(path)] = checked_input(path)
        if sources[str(path)] != request["sha256"]:
            raise ValueError("funding source mismatch")
        coin = request["request"]["coin"]
        for r in json.loads(path.read_text())["response"]:
            at = int(r["time"]) // HOUR * HOUR
            rate = D(r["fundingRate"])
            if r["coin"] != coin or at in funding[coin] or not rate.is_finite():
                raise ValueError("funding identity/duplicate/nonfinite")
            funding[coin][at] = rate
    funding_gaps = {}
    for coin in COINS:
        funding_gaps[coin] = sorted(set(range(START, END, HOUR)) - funding[coin].keys())
        # Trend training uses prices only. Unused pre-trade funding is not imputed.
        if any(at >= START + 30 * DAY for at in funding_gaps[coin]):
            raise ValueError("funding coverage incomplete in evaluation period")
    helper_path = Path(__file__).with_name("investigate_free_rotation.py")
    helper = runpy.run_path(str(helper_path))
    aggregate, describe, scenarios = (
        helper["aggregate"],
        helper["describe"],
        helper["SCENARIOS"],
    )
    events, nulls = [], []
    for i in range(30, len(opens["BTC"]) - 8):
        at = START + i * DAY
        if datetime.fromtimestamp(at / 1000, UTC).weekday() != 3:
            continue
        scores = {c: closes[c][i - 1] / opens[c][i - 30] - 1 for c in COINS}
        sides = {c: 1 if score > 0 else -1 for c, score in scores.items() if score}
        if not sides:
            continue
        e = {
            "entry_ms": at,
            "exit_ms": at + 7 * DAY,
            "sides": sides,
            "scores": scores,
            "scenarios": {},
            "legs": {},
        }
        for name, (fee, slip, delay, mode) in scenarios.items():
            # One day, not one hour, is the conservative observable delay here.
            results = {
                (c, s): daily_leg(opens[c], funding[c], i + delay, s, fee, slip, mode)
                for c in COINS
                for s in (-1, 1)
            }
            e["scenarios"][name] = aggregate(results, sides)
            e["legs"][name] = {c: results[c, s] for c, s in sides.items()}
            if name == "base":
                e["long_benchmark_bps"] = aggregate(results, {c: 1 for c in COINS})[
                    "net_bps"
                ]
                nulls.append(
                    [
                        float(
                            aggregate(results, dict(zip(COINS, values, strict=True)))[
                                "net_bps"
                            ]
                        )
                        for values in itertools.product((-1, 1), repeat=4)
                    ]
                )
        events.append(e)
    segments = {}
    for name, selected, a, b in (
        (
            "older_unseen_segment",
            [j for j, e in enumerate(events) if e["exit_ms"] + DAY <= OLD_END],
            START + 30 * DAY,
            OLD_END,
        ),
        (
            "previously_seen_period",
            [j for j, e in enumerate(events) if e["entry_ms"] >= OLD_END],
            OLD_END,
            END,
        ),
        ("full", list(range(len(events))), START + 30 * DAY, END),
    ):
        subset = [events[j] for j in selected]
        summaries = {s: describe(subset, s, a, b) for s in scenarios}
        rng = random.Random(20260907)
        observed = float(summaries["base"]["sum_net_bps"])
        null_sums = [sum(rng.choice(nulls[j]) for j in selected) for _ in range(2000)]
        p = (1 + sum(v >= observed for v in null_sums)) / 2001
        base = summaries["base"]
        ci = base["bootstrap_mean_bps"]
        criteria = {
            "positive_base_and_stresses": all(
                (summaries[s]["mean_net_bps"] or 0) > 0
                for s in ("base", "cost_stress", "delay_stress", "funding_adverse")
            ),
            "sufficient_sample": len(subset) >= 30,
            "profit_factor_above_1_2": (base["profit_factor"] or 0) > D("1.2"),
            "corrected_interval_positive": ci is not None and ci["lower"] > 0,
            "permutation_family_threshold": p < 0.05 / 3,
        }
        segments[name] = {
            "scenarios": summaries,
            "permutation_p": p,
            "criteria": criteria,
            "long_benchmark_sum_bps": sum(
                (e["long_benchmark_bps"] for e in subset), D(0)
            ),
        }
    write_json(args.output / "events.json", events)
    write_json(
        args.output / "summary.json",
        {
            "run_id": "free-long-trend-2026-09-07",
            "start_ms": START,
            "end_ms_exclusive": END,
            "daily_bars_per_coin": len(opens["BTC"]),
            "hourly_funding_per_coin": {c: len(funding[c]) for c in COINS},
            "unused_warmup_funding_gaps_ms": funding_gaps,
            "daily_hourly_opens_matched": comparisons,
            "segments": segments,
            "decision": "RISK_SIMULATION_CANDIDATE"
            if all(segments["older_unseen_segment"]["criteria"].values())
            else "HYPOTHESIS_NOT_CONFIRMED",
            "promotion_authorized": False,
            "additional_spend_usd": 0,
            "source_hashes": sources,
            "code_hashes": {
                str(p): file_sha256(p)
                for p in (
                    Path(__file__),
                    helper_path,
                    loader_path,
                    Path("src/hyperbot2/research/rotation.py"),
                )
            },
            "limits": [
                "older extension, not prospective OOS; selected after recent data",
                "daily-open funding proxy; no hourly price interpolation claimed",
                "one-day delay stress, opens remain hypothetical",
                "no portfolio sizing, stops, intrabar drawdown or infrastructure costs",
                "fixed four-surviving-coin universe limits generalization",
                "cross-boundary basket belongs only to full segment",
            ],
        },
    )
    print(args.output / "summary.json")


if __name__ == "__main__":
    main()
