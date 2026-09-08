"""Registered OHLCV event study using existing free native archives."""

from __future__ import annotations

import argparse
import json
import random
import runpy
from decimal import Decimal
from pathlib import Path

from hyperbot2.research.artifacts import checked_input, file_sha256, write_json
from hyperbot2.research.rotation import COINS, HOUR, leg_return
from hyperbot2.research.volume import VolumeBar, classify

D = Decimal
DAY = 24 * HOUR
SCENARIOS = {
    "base": (D("0.00045"), D("0.0002"), 0, "signed"),
    "cost_stress": (D("0.0009"), D("0.0005"), 0, "signed"),
    "delay_stress": (D("0.00045"), D("0.0002"), 1, "signed"),
    "funding_adverse": (D("0.00045"), D("0.0002"), 0, "adverse"),
    "zero_cost": (D(0), D(0), 0, "zero"),
}


def interval(
    events: list[dict], start: int, end: int, horizon: str = "6"
) -> dict | None:
    days = {d: [0.0, 0] for d in range(start // DAY, end // DAY)}
    if len(events) < 30 or len({e["entry_ms"] // DAY for e in events}) < 20:
        return None
    for e in events:
        days[e["entry_ms"] // DAY][0] += float(e["returns"][horizon]["base"]["net_bps"])
        days[e["entry_ms"] // DAY][1] += 1
    daily = list(days.values())
    rng, values = random.Random(20260907), []
    for _ in range(5000):
        sample = []
        while len(sample) < len(daily):
            j = rng.randrange(len(daily) - 6)
            sample.extend(daily[j : j + 7])
        sample = sample[: len(daily)]
        count = sum(row[1] for row in sample)
        if count:
            values.append(sum(row[0] for row in sample) / count)
    values.sort()
    return {
        "confidence": 0.975,
        "lower": values[int(len(values) * 0.0125)],
        "upper": values[int(len(values) * 0.9875)],
        "replicates": len(values),
        "block_days": 7,
    }


def summarize(
    events: list[dict], horizon: str, scenario: str, start: int, end: int
) -> dict:
    vals = [e["returns"][horizon][scenario]["net_bps"] for e in events]
    gains = sum((max(v, D(0)) for v in vals), D(0))
    losses = -sum((min(v, D(0)) for v in vals), D(0))
    blocks = [D(0)] * ((end - start + 30 * DAY - 1) // (30 * DAY))
    coins = {c: {"n": 0, "sum_net_bps": D(0)} for c in COINS}
    sides = {s: {"n": 0, "sum_net_bps": D(0)} for s in (-1, 1)}
    for e, val in zip(events, vals, strict=True):
        blocks[(e["entry_ms"] - start) // (30 * DAY)] += val
        for target in (coins[e["coin"]], sides[e["side"]]):
            target["n"] += 1
            target["sum_net_bps"] += val
    return {
        "events": len(vals),
        "mean_net_bps": sum(vals, D(0)) / len(vals) if vals else None,
        "sum_net_bps": sum(vals, D(0)),
        "profit_factor": gains / losses if losses else None,
        "worst_event_bps": min(vals) if vals else None,
        "sum_without_best_bps": sum(vals, D(0)) - max(vals) if vals else None,
        "positive_fraction": sum(v > 0 for v in vals) / len(vals) if vals else None,
        "blocks_30d_sum_bps": blocks,
        "coins": coins,
        "sides": sides,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    protocol = Path("reports/volume_shocks_2026-09-07/PROTOCOL.md")
    registration = protocol.parent / "registration.json"
    checked_input(registration)
    if json.loads(registration.read_text())["protocol_sha256"] != file_sha256(protocol):
        raise ValueError("modified protocol")
    loader = Path(__file__).with_name("evaluate_alternatives.py")
    candles, funding, start, end, sources = runpy.run_path(str(loader))["load_history"](
        Path("data/search_2026-09-06/history")
    )
    bars = {}
    for source in sources:
        raw = json.loads(Path(source).read_text())
        if raw["request"]["type"] != "candleSnapshot":
            continue
        coin = raw["request"]["req"]["coin"]
        rows = [
            VolumeBar(int(b["t"]), *(D(b[k]) for k in ("o", "h", "l", "c", "v")))
            for b in raw["response"]
            if start <= b["t"] < end
        ]
        rows.sort(key=lambda b: b.time)
        if [b.time for b in rows] != [b.time for b in candles[coin]]:
            raise ValueError("OHLCV alignment failure")
        bars[coin] = rows
    events = {name: [] for name in ("continuation", "rejection")}
    for coin in COINS:
        rows = bars[coin]
        opens = [b.open for b in rows]
        rates = [funding[coin][b.time] for b in rows]
        next_allowed = dict.fromkeys(events, 0)
        for i in range(168, len(rows) - 26):
            for name, side in classify(rows, i).items():
                if i < next_allowed[name]:
                    continue
                next_allowed[name] = i + 25
                entry = i + 1
                event = {
                    "coin": coin,
                    "side": side,
                    "signal_ms": rows[i].time,
                    "entry_ms": rows[entry].time,
                    "returns": {},
                }
                for hold in (1, 6, 24):
                    event["returns"][str(hold)] = {
                        name: leg_return(
                            opens, rates, entry + delay, hold, side, fee, slip, mode
                        )
                        for name, (fee, slip, delay, mode) in SCENARIOS.items()
                    }
                events[name].append(event)
    results = {}
    for name, selected in events.items():
        selected.sort(key=lambda e: (e["entry_ms"], e["coin"]))
        ci = interval(selected, start + 7 * DAY, end)
        stats = {
            str(hold): {
                s: summarize(selected, str(hold), s, start + 7 * DAY, end)
                for s in SCENARIOS
            }
            for hold in (1, 6, 24)
        }
        base = stats["6"]["base"]
        criteria = {
            "all_cost_scenarios_positive": all(
                (stats["6"][s]["mean_net_bps"] or 0) > 0
                for s in SCENARIOS
                if s != "zero_cost"
            ),
            "profit_factor_above_1_2": (base["profit_factor"] or 0) > D("1.2"),
            "corrected_interval_lower_positive": ci is not None and ci["lower"] > 0,
            "four_positive_blocks": sum(v > 0 for v in base["blocks_30d_sum_bps"]) >= 4,
            "positive_without_best": (base["sum_without_best_bps"] or 0) > 0,
        }
        results[name] = {
            "horizons": stats,
            "primary_interval": ci,
            "criteria": criteria,
            "decision": "FURTHER_FREE_VALIDATION"
            if all(criteria.values())
            else "HYPOTHESIS_NOT_CONFIRMED",
        }
        write_json(args.output / f"{name}-events.json", selected)
    write_json(
        args.output / "summary.json",
        {
            "run_id": "volume-shocks-2026-09-07",
            "strategies": results,
            "start_ms": start,
            "end_ms_exclusive": end,
            "source_hashes": sources,
            "code_hashes": {
                str(p): file_sha256(p)
                for p in (
                    Path(__file__),
                    loader,
                    Path("src/hyperbot2/research/volume.py"),
                    Path("src/hyperbot2/research/rotation.py"),
                )
            },
            "protocol_sha256": file_sha256(protocol),
            "incremental_data_cost_usd": 0,
            "network_calls": 0,
            "independent_holdout": False,
            "promotion_authorized": False,
            "limits": [
                "historical traded opens do not guarantee executable quotes",
                "base-coin volume, not liquidations or order flow",
                "funding price uses hourly open proxy",
                "event bps, no risk-sized portfolio or intratrade drawdown",
                "local multiplicity correction cannot remove prior selection",
            ],
        },
    )
    print(args.output / "summary.json")


if __name__ == "__main__":
    main()
