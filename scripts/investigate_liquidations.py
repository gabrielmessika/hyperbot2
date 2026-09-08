"""Reproduce the registered liquidation pilot offline from checksummed inputs."""

from __future__ import annotations

import argparse
import json
import runpy
import statistics
from decimal import Decimal
from pathlib import Path

from hyperbot2.research.artifacts import checked_input, file_sha256, write_json
from hyperbot2.research.liquidations import (
    HOUR,
    long_return,
    quantile,
    reconcile_raw,
    selected_hours,
    timestamp,
    volume_hours,
)

D = Decimal
START, END = 1786233600000, 1788652800000
DAY = 24 * HOUR
SCENARIOS = {
    "base": (D("0.00045"), D("0.0002"), 0, True),
    "cost_stress": (D("0.0009"), D("0.0005"), 0, True),
    "delay_stress": (D("0.00045"), D("0.0002"), 1, True),
    "zero_cost_control": (D(0), D(0), 0, False),
}


def archive_requests(root: Path, sources: dict) -> list[tuple[dict, dict]]:
    manifest = root / "manifest.json"
    sources[str(manifest)] = checked_input(manifest)
    results = []
    for request in json.loads(manifest.read_text())["requests"]:
        path = Path(request["path"])
        sources[str(path)] = checked_input(path)
        if request["sha256"] != sources[str(path)] or request["http_status"] != "200":
            raise ValueError("archive manifest mismatch or unsuccessful request")
        payload = json.loads(path.read_text(), parse_float=D)
        if payload.get("success") is not True or not payload.get("meta", {}).get(
            "request_id"
        ):
            raise ValueError("unidentified response")
        if payload["meta"]["count"] != len(payload["data"]):
            raise ValueError("row count mismatch")
        results.append((request, payload))
    return results


def controls(at: int, volumes: dict, returns: dict, volatility: dict) -> list[int]:
    candidates = []
    for t, row in volumes.items():
        if not at - 168 * HOUR <= t or t + 25 * HOUR >= at:
            continue
        prior = [
            r.long_usd
            for k, r in volumes.items()
            if t - 168 * HOUR <= k < t and r.long_usd > 0
        ]
        if (
            not prior
            or not 0 < row.long_usd <= quantile(prior, 0.5)
            or abs(returns[t] - returns[at]) > D("0.0025")
            or not 0.5 * volatility[at] <= volatility[t] <= 2 * volatility[at]
        ):
            continue
        candidates.append(t)
    selected: list[int] = []
    for t in sorted(candidates, key=lambda t: (abs(returns[t] - returns[at]), t)):
        if all(abs(t - k) >= 25 * HOUR for k in selected):
            selected.append(t)
        if len(selected) == 3:
            break
    return selected


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--archive", type=Path, default=Path("data/liquidations_2026-09-07")
    )
    parser.add_argument(
        "--history", type=Path, default=Path("data/search_2026-09-06/history")
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    loader = runpy.run_path(str(Path(__file__).with_name("evaluate_alternatives.py")))[
        "load_history"
    ]
    candles, funding, _, _, sources = loader(args.history)
    registrations = Path("reports/liquidations_2026-09-07")
    for name, document in (
        ("study_registration.json", "PROTOCOL.md"),
        ("pilot_registration.json", "PILOT_PROTOCOL.md"),
    ):
        path = registrations / name
        sources[str(path)] = checked_input(path)
        sources[str(path.parent / document)] = file_sha256(path.parent / document)
        if (
            json.loads(path.read_text())["protocol_sha256"]
            != sources[str(path.parent / document)]
        ):
            raise ValueError("protocol changed after registration")
    raw_requests = archive_requests(args.archive / "event_raw", sources)
    raw_requests += archive_requests(args.archive / "event_raw_continued", sources)
    aggregate = archive_requests(args.archive / "pilot", sources)
    volume, interest = {}, {}
    for request, payload in aggregate:
        coin = request["route"].split("/")[-1]
        if payload["meta"].get("next_cursor"):
            raise ValueError("aggregate pagination incomplete")
        if request["parameters"] != {
            "start": START,
            "end": END,
            "limit": 1000,
            "interval": "1h",
        }:
            raise ValueError("unexpected pilot range")
        if request["route"].endswith("/volume"):
            coin = request["route"].split("/")[-2]
            if coin in volume:
                raise ValueError("duplicate volume series")
            volume[coin] = volume_hours(payload["data"], coin, START, END)
        else:
            if coin in interest:
                raise ValueError("duplicate OI series")
            interest[coin] = {}
            for r in payload["data"]:
                t = timestamp(r["timestamp"])
                if not START <= t < END:
                    continue
                oi = D(r["open_interest"])
                if (
                    r["coin"] != coin
                    or r["symbol"] != coin
                    or t in interest[coin]
                    or not oi.is_finite()
                    or oi <= 0
                ):
                    raise ValueError("invalid OI identity/value")
                interest[coin][t] = oi
            if sorted(interest[coin]) != list(range(START, END, HOUR)):
                raise ValueError("OI hours missing")

    events, quality = [], {}
    for coin in ("BTC", "ETH"):
        bars = {b.time: b for b in candles[coin]}
        opens = {t: b.open for t, b in bars.items()}
        returns = {t: b.close / b.open - 1 for t, b in bars.items()}
        volatility = {
            t: statistics.pstdev(
                float(returns[k]) for k in range(t - 24 * HOUR, t, HOUR)
            )
            for t in range(START, END, HOUR)
        }
        v = volume[coin]
        selected = selected_hours(v, returns, coin, START, END)
        observed = [
            sum(t - 168 * HOUR <= k < t and r.long_usd > 0 for k, r in v.items())
            for t in range(START + 168 * HOUR, END - 26 * HOUR, HOUR)
        ]
        quality[coin] = {
            "hours_in_range": (END - START) // HOUR,
            "published_volume_hours": len(v),
            "unpublished_volume_hours_not_imputed": (END - START) // HOUR - len(v),
            "positive_long_hours": sum(r.long_usd > 0 for r in v.values()),
            "max_prior_positive_hours": max(observed),
            "hours_with_60_prior_positive": sum(n >= 60 for n in observed),
            "complete_hourly_oi": len(interest[coin]),
        }
        for event in selected:
            at = event["hour_ms"]
            pages = [
                (r, p)
                for r, p in raw_requests
                if r["route"] == f"/v1/hyperliquid/liquidations/{coin}"
                and r["parameters"]["start"] == at
                and r["parameters"]["end"] == at + HOUR
            ]
            cursor, rows, seen = None, [], set()
            for i, (request, payload) in enumerate(pages):
                if request["parameters"].get("cursor") != cursor or (
                    i and cursor is None
                ):
                    raise ValueError("broken raw page chain")
                rows.extend(payload["data"])
                cursor = payload["meta"].get("next_cursor")
                if cursor is not None and cursor in seen:
                    raise ValueError("repeated raw cursor")
                seen.add(cursor)
            if not pages or cursor is not None:
                raise ValueError("incomplete event raw pagination")
            verification = reconcile_raw(rows, coin, v[at])
            matched = controls(at, v, returns, volatility)
            result = {
                **event,
                "signal_ms": at + HOUR,
                "entry_ms": at + HOUR,
                "oi_contracts_change_fraction": interest[coin][at]
                / interest[coin][at - HOUR]
                - 1,
                "raw_verification": verification,
                "raw_pages": len(pages),
                "control_hours": matched,
                "scenarios": {},
            }
            for scenario, (fee, slip, delay, charge) in SCENARIOS.items():
                horizons = {}
                for h in (1, 6, 24):
                    value = long_return(
                        opens,
                        funding[coin],
                        at + (1 + delay) * HOUR,
                        h,
                        fee,
                        slip,
                        charge,
                    )
                    reference = [
                        long_return(
                            opens,
                            funding[coin],
                            t + (1 + delay) * HOUR,
                            h,
                            fee,
                            slip,
                            charge,
                        )["net_bps"]
                        for t in matched
                    ]
                    value["matched_control_mean_net_bps"] = (
                        sum(reference, D(0)) / len(reference) if reference else None
                    )
                    value["matched_excess_bps"] = (
                        value["net_bps"] - sum(reference, D(0)) / len(reference)
                        if reference
                        else None
                    )
                    horizons[str(h)] = value
                result["scenarios"][scenario] = horizons
            events.append(result)
    n, days = len(events), len({e["entry_ms"] // DAY for e in events})
    summaries = {}
    bootstrap = runpy.run_path(str(Path(__file__).with_name("investigate_pairs.py")))[
        "bootstrap_ratio"
    ]
    for scenario in SCENARIOS:
        summaries[scenario] = {}
        for h in (1, 6, 24):
            values = [e["scenarios"][scenario][str(h)] for e in events]
            matched_values = [
                v["matched_excess_bps"]
                for v in values
                if v["matched_excess_bps"] is not None
            ]
            daily = {
                day: [0.0, 0] for day in range((START + 7 * DAY) // DAY, END // DAY)
            }
            paired_daily = {day: [0.0, 0] for day in daily}
            for e in events:
                value = e["scenarios"][scenario][str(h)]
                daily[e["entry_ms"] // DAY][0] += float(value["net_bps"])
                daily[e["entry_ms"] // DAY][1] += 1
                if value["matched_excess_bps"] is not None:
                    paired_daily[e["entry_ms"] // DAY][0] += float(
                        value["matched_excess_bps"]
                    )
                    paired_daily[e["entry_ms"] // DAY][1] += 1
            summaries[scenario][str(h)] = {
                "events": n,
                "mean_gross_bps": sum((v["gross_bps"] for v in values), D(0)) / n
                if n
                else None,
                "mean_net_bps": sum((v["net_bps"] for v in values), D(0)) / n
                if n
                else None,
                "positive_net_events": sum(v["net_bps"] > 0 for v in values),
                "paired_events": len(matched_values),
                "mean_matched_excess_bps": sum(matched_values, D(0))
                / len(matched_values)
                if matched_values
                else None,
                "bootstrap_net": bootstrap(list(daily.values()))
                if n >= 30 and days >= 20
                else None,
                "bootstrap_matched": bootstrap(list(paired_daily.values()))
                if n >= 30 and days >= 20 and len(matched_values) >= 20
                else None,
            }
    write_json(args.output / "events.json", events)
    write_json(
        args.output / "summary.json",
        {
            "run_id": "liquidation-rebound-pilot-2026-09-07",
            "start_ms": START,
            "end_ms_exclusive": END,
            "warmup_days": 7,
            "observation_days": 21,
            "events": n,
            "distinct_event_days": days,
            "quality": quality,
            "raw_events_verified": sum(e["raw_verification"]["valid"] for e in events),
            "primary_horizon_hours": 6,
            "scenarios": summaries,
            "source_hashes": sources,
            "code_hashes": {
                str(p): file_sha256(p)
                for p in (
                    Path(__file__),
                    Path(__file__).with_name("evaluate_alternatives.py"),
                    Path(__file__).with_name("investigate_pairs.py"),
                    Path(__file__).with_name("fetch_liquidation_study.py"),
                    Path("src/hyperbot2/research/liquidations.py"),
                )
            },
            "decision": "INSUFFICIENT_SAMPLE"
            if n < 30 or days < 20
            else "PILOT_REQUIRES_LONGER_VALIDATION",
            "promotion_authorized": False,
            "independent_holdout": False,
            "limits": [
                "180-day protocol blocked by provider history entitlement",
                "liquidation coverage uncertified; absent hours not zeros",
                "liquidator/liquidated identity fields suspicious and unused",
                "raw/aggregate consistency does not prove source completeness",
                "hourly open fills are hypothetical; publication delay unmeasured",
                "OI buckets treated as available only after hour end",
                "funding oracle approximated by hourly price",
                "bootstrap withheld below 30 events/20 days",
                "no portfolio, risk qualification or monthly return estimate",
            ],
        },
    )
    print(args.output / "summary.json")


if __name__ == "__main__":
    main()
