"""Registered pre-open equity gap study on existing checksumed native archives."""

from __future__ import annotations

import argparse
import importlib.util
import json
import random
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path

from hyperbot2.research.artifacts import checked_input, file_sha256, write_json
from hyperbot2.research.equity_weekend import HOLIDAYS, NY
from hyperbot2.research.rotation import HOUR, leg_return

D = Decimal
DAY = 24 * HOUR
COINS = (
    "xyz:TSLA",
    "xyz:NVDA",
    "xyz:HOOD",
    "xyz:META",
    "xyz:AMZN",
    "xyz:COIN",
    "xyz:MSTR",
)
SPLIT = int(datetime(2026, 6, 1, tzinfo=UTC).timestamp() * 1000)


def frames(start: int, end: int) -> list[tuple[int, int, int, int]]:
    result = []
    day = date(2026, 2, 12)
    while day <= date(2026, 9, 5):
        previous = day - timedelta(days=1)
        if (
            day.weekday() in (1, 2, 3, 4)
            and day not in HOLIDAYS
            and previous not in HOLIDAYS
        ):
            ref = int(datetime.combine(previous, time(15), NY).timestamp() * 1000)
            entry = int(datetime.combine(day, time(8), NY).timestamp() * 1000)
            exit_time = int(datetime.combine(day, time(10), NY).timestamp() * 1000)
            if ref >= start and exit_time + HOUR < end:
                result.append((ref, entry - HOUR, entry, exit_time))
        day += timedelta(days=1)
    return result


def interval(events: list[dict], start: int, end: int) -> dict | None:
    if len(events) < 30 or len({e["entry_ms"] // DAY for e in events}) < 20:
        return None
    days = {d: [0.0, 0] for d in range(start // DAY, end // DAY)}
    for e in events:
        days[e["entry_ms"] // DAY][0] += float(e["returns"]["base"]["net_bps"])
        days[e["entry_ms"] // DAY][1] += 1
    data, rng, values = list(days.values()), random.Random(20260907), []
    for _ in range(5000):
        sample = []
        while len(sample) < len(data):
            j = rng.randrange(len(data) - 6)
            sample.extend(data[j : j + 7])
        sample = sample[: len(data)]
        count = sum(v[1] for v in sample)
        if count:
            values.append(sum(v[0] for v in sample) / count)
    values.sort()
    return {
        "confidence": 0.975,
        "lower": values[int(len(values) * 0.0125)],
        "upper": values[int(len(values) * 0.9875)],
        "block_days": 7,
        "replicates": len(values),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    protocol = Path("reports/overnight_repricing_2026-09-07/PROTOCOL.md")
    checked_input(protocol.parent / "registration.json")
    if json.loads((protocol.parent / "registration.json").read_text())[
        "protocol_sha256"
    ] != file_sha256(protocol):
        raise ValueError("modified protocol")
    helper_path = Path(__file__).with_name("investigate_weekend_repricing.py")
    spec = importlib.util.spec_from_file_location(
        "registered_equity_helper", helper_path
    )
    if spec is None or spec.loader is None:
        raise ValueError("unavailable helper")
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    candles, funding, start, end, sources = helper.load(
        Path("data/weekend_repricing_2026-09-07/history")
    )
    helper.COINS = COINS[-2:]
    extra, extra_funding, a, b, extra_sources = helper.load(
        Path("data/weekend_repricing_2026-09-07/replication_history")
    )
    if (a, b) != (start, end):
        raise ValueError("coverage mismatch")
    candles.update(extra)
    funding.update(extra_funding)
    sources.update(extra_sources)
    helper.COINS = COINS
    events = {"overnight_fade": [], "overnight_follow": []}
    slots = frames(start, end)
    for coin in COINS:
        opens = [b.open for b in candles[coin]]
        rates = [funding[coin][b.time] for b in candles[coin]]
        for reference, signal, entry, exit_time in slots:
            i, j, k, stop = [
                (t - start) // HOUR for t in (reference, signal, entry, exit_time)
            ]
            change = candles[coin][j].close / candles[coin][i].close - 1
            if abs(change) < D("0.01"):
                continue
            for name, direction in (("overnight_fade", -1), ("overnight_follow", 1)):
                side = (1 if change > 0 else -1) * direction
                returns = {
                    s: leg_return(
                        opens, rates, k + delay, stop - k, side, fee, slip, mode
                    )
                    for s, (fee, slip, delay, mode) in helper.SCENARIOS.items()
                }
                fee, slip, _, mode = helper.SCENARIOS["base"]
                returns["entry_delay_only"] = leg_return(
                    opens, rates, k + 1, 1, side, fee, slip, mode
                )
                returns["exit_delay_only"] = leg_return(
                    opens, rates, k, 3, side, fee, slip, mode
                )
                events[name].append(
                    {
                        "coin": coin,
                        "entry_ms": entry,
                        "exit_ms": exit_time,
                        "reference_ms": reference,
                        "signal_ms": signal,
                        "side": side,
                        "gap_bps": change * 10000,
                        "returns": returns,
                    }
                )
    results = {}
    for name, rows in events.items():
        rows.sort(key=lambda e: (e["entry_ms"], e["coin"]))
        segments = {}
        for segment, (a, b) in {
            "older": (start, SPLIT),
            "validation": (SPLIT, end),
        }.items():
            selected = [e for e in rows if a <= e["entry_ms"] < b]
            summaries = {
                s: helper.describe(selected, s, a, b)
                for s in (*helper.SCENARIOS, "entry_delay_only", "exit_delay_only")
            }
            for summary in summaries.values():
                summary["active_dates"] = summary.pop("active_weekends")
            ci, base = interval(selected, a, b), summaries["base"]
            criteria = {
                "all_cost_scenarios_positive": all(
                    (summaries[s]["mean_net_bps"] or 0) > 0
                    for s in helper.SCENARIOS
                    if s != "zero_cost"
                ),
                "profit_factor_above_1_2": (base["profit_factor"] or 0) > D("1.2"),
                "corrected_interval_positive": ci is not None and ci["lower"] > 0,
                "three_positive_blocks": sum(v > 0 for v in base["blocks_30d_sum_bps"])
                >= 3,
                "positive_without_best": (base["sum_without_best_bps"] or 0) > 0,
            }
            segments[segment] = {
                "scenarios": summaries,
                "interval": ci,
                "criteria": criteria,
            }
        passed = all(all(v["criteria"].values()) for v in segments.values())
        results[name] = {
            "segments": segments,
            "decision": "FURTHER_FREE_VALIDATION"
            if passed
            else "HYPOTHESIS_NOT_CONFIRMED",
        }
        write_json(args.output / f"{name}-events.json", rows)
    write_json(
        args.output / "summary.json",
        {
            "run_id": "overnight-repricing-2026-09-07",
            "strategies": results,
            "eligible_dates": len(slots),
            "source_hashes": sources,
            "start_ms": start,
            "split_ms": SPLIT,
            "end_ms_exclusive": end,
            "protocol_sha256": file_sha256(protocol),
            "code_hashes": {
                str(p): file_sha256(p)
                for p in (
                    Path(__file__),
                    helper_path,
                    Path("src/hyperbot2/research/equity_weekend.py"),
                    Path("src/hyperbot2/research/rotation.py"),
                    Path("src/hyperbot2/research/volume.py"),
                )
            },
            "promotion_authorized": False,
            "data_cost_usd": 0,
            "network_calls": 0,
            "limits": [
                "internally reserved windows, not a globally pristine holdout",
                "historical fees/oracles, corporate events and fills unqualified",
                "native previous-day reference, not an external fair value",
                "event bps, no portfolio or intraposition risk simulation",
            ],
        },
    )
    print(args.output / "summary.json")


if __name__ == "__main__":
    main()
