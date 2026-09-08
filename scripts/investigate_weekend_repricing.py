"""Registered weekend repricing study using native equity perpetual data."""

from __future__ import annotations

import argparse
import json
import random
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from hyperbot2.research.artifacts import checked_input, file_sha256, write_json
from hyperbot2.research.equity_weekend import weekend_frame
from hyperbot2.research.rotation import HOUR, leg_return
from hyperbot2.research.volume import VolumeBar

D = Decimal
DAY = 24 * HOUR
COINS = ("xyz:TSLA", "xyz:NVDA", "xyz:HOOD", "xyz:META", "xyz:AMZN")
SCENARIOS = {
    "base": (D("0.0009"), D("0.0002"), 0, "signed"),
    "cost_stress": (D("0.0018"), D("0.0005"), 0, "signed"),
    "delay_stress": (D("0.0009"), D("0.0002"), 1, "signed"),
    "funding_adverse": (D("0.0009"), D("0.0002"), 0, "adverse"),
    "zero_cost": (D(0), D(0), 0, "zero"),
}


def load(root: Path) -> tuple[dict, dict, int, int, dict]:
    manifest = root / "manifest.json"
    checked_input(manifest)
    m = json.loads(manifest.read_text())
    start, end = m["start_ms"], m["end_ms_exclusive"]
    candles, funding, sources = (
        {},
        {c: {} for c in COINS},
        {str(manifest): checked_input(manifest)},
    )
    for record in m["requests"]:
        path = Path(record["path"])
        sources[str(path)] = checked_input(path)
        if sources[str(path)] != record["sha256"]:
            raise ValueError("manifest checksum mismatch")
        raw = json.loads(path.read_text())
        if raw["returncode"]:
            raise ValueError("failed native request")
        query, rows = raw["request"], raw["response"]
        if query["type"] == "candleSnapshot":
            coin = query["req"]["coin"]
            parsed = []
            for b in rows:
                if b["s"] != coin or b["i"] != "1h" or b["T"] != b["t"] + HOUR - 1:
                    raise ValueError("candle identity/interval")
                if start <= b["t"] < end:
                    parsed.append(
                        VolumeBar(b["t"], *(D(b[k]) for k in ("o", "h", "l", "c", "v")))
                    )
            candles[coin] = sorted(parsed, key=lambda b: b.time)
        elif query["type"] == "fundingHistory":
            coin = query["coin"]
            for f in rows:
                at = int(f["time"]) // HOUR * HOUR
                rate = D(f["fundingRate"])
                if f["coin"] != coin or at in funding[coin] or not rate.is_finite():
                    raise ValueError("funding identity/duplicate/nonfinite")
                funding[coin][at] = rate
        else:
            raise ValueError("unexpected history route")
    for coin in COINS:
        if [b.time for b in candles[coin]] != list(range(start, end, HOUR)):
            raise ValueError(f"candle gap/duplicate: {coin}")
        if sorted(funding[coin]) != list(range(start, end, HOUR)):
            raise ValueError(f"funding gap/duplicate: {coin}")
    return candles, funding, start, end, sources


def describe(events: list[dict], scenario: str, start: int, end: int) -> dict:
    values = [e["returns"][scenario]["net_bps"] for e in events]
    gains = sum((max(v, D(0)) for v in values), D(0))
    losses = -sum((min(v, D(0)) for v in values), D(0))
    blocks = [D(0)] * ((end - start + 30 * DAY - 1) // (30 * DAY))
    assets = {c: {"n": 0, "sum_net_bps": D(0)} for c in COINS}
    for e, v in zip(events, values, strict=True):
        blocks[(e["entry_ms"] - start) // (30 * DAY)] += v
        assets[e["coin"]]["n"] += 1
        assets[e["coin"]]["sum_net_bps"] += v
    return {
        "events": len(events),
        "active_weekends": len({e["entry_ms"] for e in events}),
        "mean_net_bps": sum(values, D(0)) / len(values) if values else None,
        "profit_factor": gains / losses if losses else None,
        "sum_net_bps": sum(values, D(0)),
        "worst_event_bps": min(values) if values else None,
        "sum_without_best_bps": sum(values, D(0)) - max(values) if values else None,
        "blocks_30d_sum_bps": blocks,
        "assets": assets,
    }


def interval(events: list[dict], frames: list[tuple]) -> dict | None:
    if len(events) < 30 or len({e["entry_ms"] for e in events}) < 20:
        return None
    weeks = {f[2]: [0.0, 0] for f in frames}
    for e in events:
        weeks[e["entry_ms"]][0] += float(e["returns"]["base"]["net_bps"])
        weeks[e["entry_ms"]][1] += 1
    data = list(weeks.values())
    rng, values = random.Random(20260907), []
    for _ in range(5000):
        sample = []
        while len(sample) < len(data):
            i = rng.randrange(len(data) - 2)
            sample.extend(data[i : i + 3])
        sample = sample[: len(data)]
        count = sum(v[1] for v in sample)
        if count:
            values.append(sum(v[0] for v in sample) / count)
    values.sort()
    return {
        "confidence": 0.975,
        "lower": values[int(len(values) * 0.0125)],
        "upper": values[int(len(values) * 0.9875)],
        "block_weekends": 3,
        "replicates": len(values),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    protocol = Path("reports/weekend_repricing_2026-09-07/PROTOCOL.md")
    checked_input(protocol.parent / "registration.json")
    if json.loads((protocol.parent / "registration.json").read_text())[
        "protocol_sha256"
    ] != file_sha256(protocol):
        raise ValueError("changed protocol")
    candles, funding, start, end, sources = load(
        Path("data/weekend_repricing_2026-09-07/history")
    )
    frames = []
    sunday = date(2026, 2, 15)
    while sunday <= date(2026, 9, 6):
        frame = weekend_frame(sunday)
        if frame and frame[0] >= start and frame[3] + HOUR < end:
            frames.append(frame)
        sunday += timedelta(days=7)
    events = {"weekend_fade": [], "weekend_follow": []}
    for coin in COINS:
        opens = [b.open for b in candles[coin]]
        rates = [funding[coin][b.time] for b in candles[coin]]
        for reference, signal, entry, exit_time in frames:
            i, j, k, stop = [
                (t - start) // HOUR for t in (reference, signal, entry, exit_time)
            ]
            change = candles[coin][j].close / candles[coin][i].close - 1
            if abs(change) < D("0.01"):
                continue
            for name, direction in (("weekend_fade", -1), ("weekend_follow", 1)):
                side = (1 if change > 0 else -1) * direction
                events[name].append(
                    {
                        "coin": coin,
                        "entry_ms": entry,
                        "exit_ms": exit_time,
                        "reference_ms": reference,
                        "signal_ms": signal,
                        "side": side,
                        "weekend_change_bps": change * 10000,
                        "returns": {
                            s: leg_return(
                                opens, rates, k + delay, stop - k, side, fee, slip, mode
                            )
                            for s, (fee, slip, delay, mode) in SCENARIOS.items()
                        },
                    }
                )
    results = {}
    for name, rows in events.items():
        rows.sort(key=lambda r: (r["entry_ms"], r["coin"]))
        summaries = {s: describe(rows, s, start, end) for s in SCENARIOS}
        ci = interval(rows, frames)
        base = summaries["base"]
        criteria = {
            "all_cost_scenarios_positive": all(
                (summaries[s]["mean_net_bps"] or 0) > 0
                for s in SCENARIOS
                if s != "zero_cost"
            ),
            "profit_factor_above_1_2": (base["profit_factor"] or 0) > D("1.2"),
            "corrected_interval_positive": ci is not None and ci["lower"] > 0,
            "five_positive_blocks": sum(v > 0 for v in base["blocks_30d_sum_bps"]) >= 5,
            "positive_without_best": (base["sum_without_best_bps"] or 0) > 0,
        }
        results[name] = {
            "scenarios": summaries,
            "interval": ci,
            "criteria": criteria,
            "decision": "FURTHER_FREE_VALIDATION"
            if all(criteria.values())
            else "HYPOTHESIS_NOT_CONFIRMED",
        }
        write_json(args.output / f"{name}-events.json", rows)
    write_json(
        args.output / "summary.json",
        {
            "run_id": "weekend-repricing-2026-09-07",
            "strategies": results,
            "eligible_weekends": len(frames),
            "frames_ms": frames,
            "source_hashes": sources,
            "start_ms": start,
            "end_ms_exclusive": end,
            "protocol_sha256": file_sha256(protocol),
            "code_hashes": {
                str(p): file_sha256(p)
                for p in (
                    Path(__file__),
                    Path("src/hyperbot2/research/equity_weekend.py"),
                    Path("src/hyperbot2/research/rotation.py"),
                    Path("src/hyperbot2/research/volume.py"),
                )
            },
            "data_cost_usd": 0,
            "promotion_authorized": False,
            "limits": [
                "native perpetual Friday price is not an external fair-value benchmark",
                "historical fee/deployer/oracle settings not qualified",
                "hourly opens hypothetical; no portfolio, margin or size simulation",
                "two-rule correction only; no broad research-selection correction",
            ],
        },
    )
    print(args.output / "summary.json")


if __name__ == "__main__":
    main()
