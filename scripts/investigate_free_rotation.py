"""Three preregistered free-data screens; never a portfolio/live qualification."""

from __future__ import annotations

import argparse
import itertools
import json
import random
import runpy
from decimal import Decimal
from pathlib import Path

from hyperbot2.research.artifacts import checked_input, file_sha256, write_json
from hyperbot2.research.rotation import COINS, HOUR, leg_return, signals

D = Decimal
DAY = 24 * HOUR
SCENARIOS = {
    "base": (D("0.00045"), D("0.0002"), 0, "signed"),
    "cost_stress": (D("0.0009"), D("0.0005"), 0, "signed"),
    "delay_stress": (D("0.00045"), D("0.0002"), 1, "signed"),
    "funding_adverse": (D("0.00045"), D("0.0002"), 0, "adverse"),
    "zero_cost": (D(0), D(0), 0, "zero"),
}


def bootstrap(daily: list[list[float | int]], n: int, days: int) -> dict | None:
    if n < 30 or days < 20:
        return None
    rng, values = random.Random(20260907), []
    for _ in range(5000):
        sample = []
        while len(sample) < len(daily):
            start = rng.randrange(len(daily) - 6)
            sample.extend(daily[start : start + 7])
        sample = sample[: len(daily)]
        count = sum(r[1] for r in sample)
        if count:
            values.append(sum(r[0] for r in sample) / count)
    values.sort()
    alpha = 0.05 / 3
    return {
        "confidence": 1 - alpha,
        "lower": values[int(len(values) * alpha / 2)],
        "upper": values[min(len(values) - 1, int(len(values) * (1 - alpha / 2)))],
        "replicates": len(values),
        "block_days": 7,
    }


def aggregate(legs: dict, sides: dict) -> dict:
    if not sides:
        raise ValueError("empty basket")
    keys = next(iter(legs.values())).keys()
    return {
        k: sum((legs[c, side][k] for c, side in sides.items()), D(0)) / len(sides)
        for k in keys
    }


def describe(events: list[dict], scenario: str, start: int, end: int) -> dict:
    values = [e["scenarios"][scenario]["net_bps"] for e in events]
    gains = sum((max(v, D(0)) for v in values), D(0))
    losses = -sum((min(v, D(0)) for v in values), D(0))
    daily = {d: [0.0, 0] for d in range(start // DAY, end // DAY)}
    block_count = (end - start + 30 * DAY - 1) // (30 * DAY)
    blocks, contributions = [D(0)] * block_count, {c: D(0) for c in COINS}
    peak = cumulative = drawdown = D(0)
    for event, value in zip(events, values, strict=True):
        daily[event["entry_ms"] // DAY][0] += float(value)
        daily[event["entry_ms"] // DAY][1] += 1
        blocks[(event["entry_ms"] - start) // (30 * DAY)] += value
        for c, v in event["legs"][scenario].items():
            contributions[c] += v["net_bps"] / len(event["sides"])
        cumulative += value
        peak = max(peak, cumulative)
        drawdown = max(drawdown, peak - cumulative)
    n = len(events)
    return {
        "baskets": n,
        "mean_net_bps": sum(values, D(0)) / n if n else None,
        "sum_net_bps": sum(values, D(0)),
        "mean_gross_bps": sum(
            (e["scenarios"][scenario]["gross_bps"] for e in events), D(0)
        )
        / n
        if n
        else None,
        "sum_fees_bps": sum(
            (e["scenarios"][scenario]["fees_bps"] for e in events), D(0)
        ),
        "sum_slippage_bps": sum(
            (e["scenarios"][scenario]["slippage_bps"] for e in events), D(0)
        ),
        "sum_funding_cost_bps": sum(
            (e["scenarios"][scenario]["funding_cost_bps"] for e in events), D(0)
        ),
        "positive_fraction": sum(v > 0 for v in values) / n if n else None,
        "profit_factor": gains / losses if losses else None,
        "worst_basket_bps": min(values) if values else None,
        "closed_basket_drawdown_bps": drawdown,
        "blocks_by_entry_date_bps": blocks,
        "asset_contributions_bps": contributions,
        "bootstrap_mean_bps": bootstrap(
            list(daily.values()), n, len({e["entry_ms"] // DAY for e in events})
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    protocol = Path("reports/free_rotation_2026-09-07/PROTOCOL.md")
    registration = protocol.parent / "registration.json"
    checked_input(registration)
    if json.loads(registration.read_text())["protocol_sha256"] != file_sha256(protocol):
        raise ValueError("protocol changed after registration")
    loader_path = Path(__file__).with_name("evaluate_alternatives.py")
    load_history = runpy.run_path(str(loader_path))["load_history"]
    candles, funding, start, end, source_hashes = load_history(
        Path("data/search_2026-09-06/history")
    )
    opens = {c: [b.open for b in candles[c]] for c in COINS}
    closes = {c: [b.close for b in candles[c]] for c in COINS}
    rates = {c: [funding[c][b.time] for b in candles[c]] for c in COINS}
    strategies = {}
    for strategy in ("momentum7d", "carry_relative", "trend30d"):
        hold = 168 if strategy == "trend30d" else 24
        events, null_options = [], []
        for index in range(720, len(candles["BTC"]) - hold - 1, hold):
            sides, scores = signals(closes, opens, rates, index, strategy)
            if not sides:
                continue
            event = {
                "entry_ms": candles["BTC"][index].time,
                "exit_ms": candles["BTC"][index + hold].time,
                "sides": sides,
                "scores": scores,
                "scenarios": {},
                "legs": {},
            }
            for scenario, (fee, slip, delay, mode) in SCENARIOS.items():
                economics = {
                    (c, side): leg_return(
                        opens[c], rates[c], index + delay, hold, side, fee, slip, mode
                    )
                    for c in COINS
                    for side in (-1, 1)
                }
                event["scenarios"][scenario] = aggregate(economics, sides)
                event["legs"][scenario] = {
                    c: economics[c, side] for c, side in sides.items()
                }
                if scenario == "base":
                    event["long_benchmark_bps"] = aggregate(
                        economics, {c: 1 for c in COINS}
                    )["net_bps"]
                    assignments = (
                        [
                            dict(zip(COINS, values, strict=True))
                            for values in itertools.product((-1, 1), repeat=4)
                        ]
                        if strategy == "trend30d"
                        else [
                            {a: 1, b: -1} for a, b in itertools.permutations(COINS, 2)
                        ]
                    )
                    null_options.append(
                        [float(aggregate(economics, a)["net_bps"]) for a in assignments]
                    )
            events.append(event)
        summaries = {s: describe(events, s, start + 30 * DAY, end) for s in SCENARIOS}
        observed = float(summaries["base"]["sum_net_bps"])
        rng = random.Random(20260907)
        null_totals = [
            sum(rng.choice(options) for options in null_options) for _ in range(2000)
        ]
        permutation_p = (1 + sum(v >= observed for v in null_totals)) / 2001
        base = summaries["base"]
        interval = base["bootstrap_mean_bps"]
        criteria = {
            "base_positive": (base["mean_net_bps"] or 0) > 0,
            "cost_stress_positive": (summaries["cost_stress"]["mean_net_bps"] or 0) > 0,
            "delay_stress_positive": (summaries["delay_stress"]["mean_net_bps"] or 0)
            > 0,
            "adverse_funding_positive": (
                summaries["funding_adverse"]["mean_net_bps"] or 0
            )
            > 0,
            "four_positive_blocks": sum(v > 0 for v in base["blocks_by_entry_date_bps"])
            >= 4,
            "profit_factor_above_1_2": (base["profit_factor"] or 0) > D("1.2"),
            "sufficient_sample": len(events) >= 30
            and len({e["entry_ms"] // DAY for e in events}) >= 20,
            "corrected_interval_lower_positive": interval is not None
            and interval["lower"] > 0,
            "permutation_family_threshold": permutation_p < 0.05 / 3,
        }
        write_json(args.output / f"{strategy}-events.json", events)
        strategies[strategy] = {
            "scenarios": summaries,
            "criteria": criteria,
            "permutation_p": permutation_p,
            "permutation_replicates": 2000,
            "long_benchmark_sum_bps": sum(
                (e["long_benchmark_bps"] for e in events), D(0)
            ),
            "decision": "FREE_LONGER_HISTORY_CANDIDATE"
            if all(criteria.values())
            else "INSUFFICIENT_SAMPLE"
            if not criteria["sufficient_sample"]
            else "HYPOTHESIS_NOT_CONFIRMED",
        }
    write_json(
        args.output / "summary.json",
        {
            "run_id": "free-rotation-2026-09-07",
            "strategies": strategies,
            "history_start_ms": start,
            "history_end_ms_exclusive": end,
            "source_hashes": source_hashes,
            "protocol_sha256": file_sha256(protocol),
            "code_hashes": {
                str(p): file_sha256(p)
                for p in (
                    Path(__file__),
                    loader_path,
                    Path("src/hyperbot2/research/rotation.py"),
                )
            },
            "incremental_data_cost_usd": 0,
            "network_calls": 0,
            "independent_holdout": False,
            "promotion_authorized": False,
            "limits": [
                "exploratory reused history and fixed four-coin universe",
                "label permutation is a heuristic, not causal identification",
                "no stops, size rounding, risk supervisor or portfolio simulation",
                "signed funding uses hourly price proxy, not exact oracle",
                "closed-basket drawdown omits intraposition risk",
                "three-test correction does not erase prior research selection",
                "hypothetical opens, unverified historical execution latency",
                "bps of gross notional, no capital or monthly return claim",
            ],
        },
    )
    print(args.output / "summary.json")


if __name__ == "__main__":
    main()
