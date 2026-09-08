"""Registered funding-event study using existing rates and free native prices."""

from __future__ import annotations

import argparse
import json
import random
import time
from decimal import Decimal
from pathlib import Path

from fetch_research_history import PublicResearchClient

from hyperbot2.research.artifacts import (
    checked_input,
    file_sha256,
    source_version,
    write_json,
)
from hyperbot2.research.funding_normalization import event_return, normalization
from hyperbot2.research.rotation import COINS, HOUR
from hyperbot2.research.volume import VolumeBar

D = Decimal
DAY = HOUR * 24
REPORT = Path("reports/funding_normalization_2026-09-07")
ROOT = Path("data/funding_normalization_2026-09-07")
OLD = Path("data/wide_funding_2026-09-07")
START, END = 1786060800000, 1788652800000
SCENARIOS = {
    "base": (D("0.00045"), D("0.0002"), 0, "signed"),
    "cost_stress": (D("0.0009"), D("0.0005"), 0, "signed"),
    "delay": (D("0.00045"), D("0.0002"), 1, "signed"),
    "funding_adverse": (D("0.00045"), D("0.0002"), 0, "adverse"),
    "zero_cost": (D(0), D(0), 0, "zero"),
}


def registered() -> tuple[str, list[str]]:
    checked_input(REPORT / "registration.json")
    sha = file_sha256(REPORT / "PROTOCOL.md")
    if json.loads((REPORT / "registration.json").read_text())["protocol_sha256"] != sha:
        raise ValueError("registered protocol changed")
    path = Path("reports/wide_funding_2026-09-07/summary.json")
    checked_input(path)
    assets = json.loads(path.read_text())["assets"]
    coins = sorted(c for c, a in assets.items() if a["hours"] == 720)
    if len(coins) != 19 or "PONS" in coins:
        raise ValueError("registered universe changed")
    return sha, coins


def fetch(output: Path, coins: list[str], protocol: str) -> None:
    output.mkdir(parents=True, exist_ok=False)
    client = PublicResearchClient(output)
    try:
        for coin in coins:
            if coin == "CASHCAT":
                continue  # Complete local native candle coverage already exists.
            if len(client.records) >= 19 or client.total_bytes >= 10_000_000:
                raise ValueError("public data budget exceeded")
            rows = client.info(
                {
                    "type": "candleSnapshot",
                    "req": {
                        "coin": coin,
                        "interval": "1h",
                        "startTime": START,
                        "endTime": END - 1,
                    },
                }
            )
            print(coin, "bars", len(rows), flush=True)
            time.sleep(2.5)
    finally:
        write_json(
            output / "manifest.json",
            {
                "requests": client.records,
                "response_bytes": client.total_bytes,
                "coins": coins,
                "start_ms": START,
                "end_ms_exclusive": END,
                "protocol_sha256": protocol,
                "code_sha256": file_sha256(Path(__file__)),
                "data_cost_usd": 0,
            },
        )


def load(
    folders: list[Path], coins: list[str], start: int, end: int
) -> tuple[dict, dict, dict, dict]:
    bars = {c: {} for c in coins}
    payments = {c: {} for c in coins}
    sources = {}
    for folder in folders:
        manifest = folder / "manifest.json"
        sources[str(manifest)] = checked_input(manifest)
        m = json.loads(manifest.read_text())
        for record in m.get("requests", []) + m.get("native_requests", []):
            path = Path(record["path"])
            sources[str(path)] = checked_input(path)
            if sources[str(path)] != record["sha256"]:
                raise ValueError("manifest checksum mismatch")
            raw = json.loads(path.read_text())
            if raw["returncode"]:
                raise ValueError("failed native request")
            q, response = raw["request"], raw["response"]
            if q["type"] == "candleSnapshot":
                c = q["req"]["coin"]
                if c not in coins:
                    continue
                for b in response:
                    if b["s"] != c or b["i"] != "1h" or b["T"] != b["t"] + HOUR - 1:
                        raise ValueError("candle identity/interval mismatch")
                    at = int(b["t"])
                    if not start <= at < end:
                        continue
                    bar = VolumeBar(at, *(D(b[k]) for k in ("o", "h", "l", "c", "v")))
                    if at in bars[c] and bars[c][at] != bar:
                        raise ValueError("conflicting native candle")
                    bars[c][at] = bar
            elif q["type"] == "fundingHistory":
                c = q["coin"]
                if c not in coins:
                    continue
                for f in response:
                    at, rate = int(f["time"]), D(f["fundingRate"])
                    if f["coin"] != c or not rate.is_finite():
                        raise ValueError("invalid funding identity/rate")
                    if not start <= at < end:
                        continue
                    if at in payments[c] and payments[c][at] != rate:
                        raise ValueError("conflicting native funding")
                    payments[c][at] = rate
    rates, quality = {}, {}
    expected = list(range(start, end, HOUR))
    for c in coins:
        if sorted(bars[c]) != expected:
            raise ValueError(f"candle coverage failure: {c}")
        hourly = {}
        for at, rate in sorted(payments[c].items()):
            bucket = at // HOUR * HOUR
            if bucket in hourly:
                raise ValueError(f"multiple funding payments per hour: {c}")
            hourly[bucket] = rate
        if sorted(hourly) != expected:
            raise ValueError(f"funding coverage failure: {c}")
        rates[c] = [hourly[t] for t in expected]
        bars[c] = [bars[c][t] for t in expected]
        quality[c] = {
            "hours": len(expected),
            "zero_volume_hours": sum(b.volume == 0 for b in bars[c]),
            "funding_offset_ms_min": min(t % HOUR for t in payments[c]),
            "funding_offset_ms_max": max(t % HOUR for t in payments[c]),
        }
    return bars, payments, rates, {"sources": sources, "assets": quality}


def interval(events: list[dict], start: int, end: int) -> dict | None:
    if len(events) < 30 or len({e["entry_ms"] // DAY for e in events}) < 20:
        return None
    daily = [[0.0, 0] for _ in range((end - start) // DAY)]
    for e in events:
        day = (e["entry_ms"] - start) // DAY
        daily[day][0] += float(e["returns"]["24"]["base"]["net_bps"])
        daily[day][1] += 1
    rng, samples = random.Random(20260907), []
    for _ in range(5000):
        sample = []
        while len(sample) < len(daily):
            i = rng.randrange(len(daily) - 6)
            sample.extend(daily[i : i + 7])
        sample = sample[: len(daily)]
        count = sum(row[1] for row in sample)
        if count:
            samples.append(sum(row[0] for row in sample) / count)
    samples.sort()
    return {
        "lower_bps": samples[int(len(samples) * 0.0125)],
        "upper_bps": samples[int(len(samples) * 0.9875)],
        "confidence": 0.975,
        "block_days": 7,
        "replicates": len(samples),
        "descriptive_only": True,
    }


def summarize(
    events: list[dict], horizon: str, scenario: str, start: int, days: int
) -> dict:
    values = [e["returns"][horizon][scenario]["net_bps"] for e in events]
    gains = sum((max(v, D(0)) for v in values), D(0))
    losses = -sum((min(v, D(0)) for v in values), D(0))
    ordered = sorted(values)
    n = len(values)
    by_coin, by_side, blocks = {}, {}, {}
    for e, v in zip(events, values, strict=True):
        for target, key in (
            (by_coin, e["coin"]),
            (by_side, str(e["side"])),
            (blocks, str((e["entry_ms"] - start) // (days * DAY))),
        ):
            row = target.setdefault(key, {"events": 0, "sum_net_bps": D(0)})
            row["events"] += 1
            row["sum_net_bps"] += v
    return {
        "events": n,
        "mean_net_bps": sum(values, D(0)) / n if n else None,
        "median_net_bps": (ordered[(n - 1) // 2] + ordered[n // 2]) / 2 if n else None,
        "sum_net_bps": sum(values, D(0)),
        "sum_without_best_bps": sum(values, D(0)) - max(values) if n else None,
        "worst_event_bps": min(values) if n else None,
        "profit_factor": gains / losses if losses else None,
        "positive_fraction": sum(v > 0 for v in values) / n if n else None,
        "by_coin": by_coin,
        "by_side": by_side,
        "blocks": blocks,
        "block_days": days,
    }


def study(bars: dict, payments: dict, rates: dict, start: int, end: int) -> dict:
    events = {name: [] for name in ("correction", "continuation")}
    for c, rows in bars.items():
        opens = [b.open for b in rows]
        next_allowed, previous = 0, 0
        for i in range(12, len(rows) - 73):
            signal = normalization(rates[c], i)
            candidate = signal and not previous and i >= next_allowed
            previous = signal
            if not candidate:
                continue
            next_allowed = i + 73
            for name, side in (("correction", -signal), ("continuation", signal)):
                events[name].append(
                    {
                        "coin": c,
                        "side": side,
                        "entry_ms": start + i * HOUR + 60_000,
                        "last_signal_payment_ms": max(
                            t for t in payments[c] if t < start + i * HOUR
                        ),
                        "returns": {
                            str(h): {
                                s: event_return(
                                    opens,
                                    start,
                                    payments[c],
                                    i + delay,
                                    h,
                                    side,
                                    fee,
                                    slip,
                                    mode,
                                )
                                for s, (fee, slip, delay, mode) in SCENARIOS.items()
                            }
                            for h in (6, 24, 72)
                        },
                    }
                )
    return events


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fetch", action="store_true")
    args = parser.parse_args()
    protocol, coins = registered()
    if args.fetch:
        fetch(args.output, coins, protocol)
        return
    args.output.mkdir(parents=True, exist_ok=False)
    major_root = Path("data/search_2026-09-06/history")
    checked_input(major_root / "manifest.json")
    major_start = json.loads((major_root / "manifest.json").read_text())["start_ms"]
    results, quality = {}, {}
    for cohort, assets, start, folders, block in (
        (
            "altcoins_30d",
            coins,
            START,
            [OLD / "history", OLD / "cashcat_hedge", ROOT / "history"],
            10,
        ),
        ("majors_180d", list(COINS), major_start, [major_root], 30),
    ):
        bars, payments, rates, quality[cohort] = load(folders, assets, start, END)
        events = study(bars, payments, rates, start, END)
        for name, selected in events.items():
            selected.sort(key=lambda e: (e["entry_ms"], e["coin"]))
            key = f"{cohort}-{name}"
            write_json(args.output / f"{key}-events.json", selected)
            stats = {
                str(h): {
                    s: summarize(selected, str(h), s, start, block) for s in SCENARIOS
                }
                for h in (6, 24, 72)
            }
            base = stats["24"]["base"]
            criteria = {
                "all_paid_scenarios_positive": all(
                    stats["24"][s]["sum_net_bps"] > 0
                    for s in SCENARIOS
                    if s != "zero_cost"
                ),
                "profit_factor_above_1_2": (base["profit_factor"] or 0) > D("1.2"),
                "positive_without_best": (base["sum_without_best_bps"] or 0) > 0,
            }
            results[key] = {
                "start_ms": start,
                "end_ms_exclusive": END,
                "statistics": stats,
                "primary_interval": interval(selected, start, END),
                "criteria": criteria,
                "decision": "FURTHER_FREE_VALIDATION"
                if all(criteria.values())
                else "HYPOTHESIS_NOT_CONFIRMED",
            }
            print(
                key,
                base["events"],
                "mean bps",
                base["mean_net_bps"],
                results[key]["decision"],
                flush=True,
            )
    write_json(args.output / "quality.json", quality)
    write_json(
        args.output / "summary.json",
        {
            "run_id": "funding-normalization-20260907-v1",
            "protocol_sha256": protocol,
            "code_version": source_version(Path.cwd())[0],
            "script_sha256": file_sha256(Path(__file__)),
            "results": results,
            "live_enabled": False,
            "promotion_authorized": False,
            "incremental_data_cost_usd": 0,
            "limitations": [
                "current altcoin universe survivorship; prior data exploration",
                "hourly open is hypothetical execution at +60 seconds",
                "funding uses hourly open instead of exact spot oracle",
                "event returns are not a sized portfolio or a drawdown validation",
                "no independent holdout; no full-family multiplicity correction",
            ],
        },
    )


if __name__ == "__main__":
    main()
