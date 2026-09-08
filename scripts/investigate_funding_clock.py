"""Offline paired event screen around ex-ante expected funding settlements."""

from __future__ import annotations

import argparse
import csv
import io
import json
import zipfile
from collections import Counter
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path

from investigate_pairs import bootstrap_ratio

from hyperbot2.research.artifacts import (
    checked_input,
    file_sha256,
    source_version,
    write_json,
)
from hyperbot2.research.binance_archives import END, START, load_archives
from hyperbot2.research.funding_clock import FundingObservation, next_clock_signal
from hyperbot2.research.funding_normalization import event_return
from hyperbot2.research.rotation import HOUR

D = Decimal
DAY = 24 * HOUR
REPORT = Path("reports/funding_clock_2026-09-07")
ARCHIVES = Path("data/prior_transfer_2026-09-07/archives")
SCENARIOS = {
    "base": (D("0.00045"), D("0.0002"), 0, "signed"),
    "cost_stress": (D("0.0009"), D("0.0005"), 0, "signed"),
    "delay": (D("0.00045"), D("0.0002"), 1, "signed"),
    "funding_adverse": (D("0.00045"), D("0.0002"), 0, "adverse"),
    "zero_cost": (D(0), D(0), 0, "zero"),
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    checked_input(REPORT / "registration.json")
    reg = json.loads((REPORT / "registration.json").read_text())
    q = Path("reports/prior_transfer_2026-09-07/qualification.json")
    if reg["protocol_sha256"] != file_sha256(REPORT / "PROTOCOL.md") or reg[
        "qualification_sha256"
    ] != checked_input(q):
        raise ValueError("registered study changed")
    coins = [r["coin"] for r in json.loads(q.read_text())["selected_by_metadata"]]
    bars, payments, quality = load_archives(ARCHIVES, coins)
    checked_input(ARCHIVES / "manifest.json")
    manifest = json.loads((ARCHIVES / "manifest.json").read_text())
    observed: dict[str, list[FundingObservation]] = {c: [] for c in coins}
    for row in sorted(
        manifest["archives"], key=lambda r: (r["coin"], r["month"], r["route"])
    ):
        if row["route"] != "fundingRate":
            continue
        p = Path(row["path"])
        if checked_input(p) != row["sha256"]:
            raise ValueError("funding source changed")
        with zipfile.ZipFile(p) as archive:
            records = csv.DictReader(
                io.StringIO(archive.read(p.with_suffix(".csv").name).decode())
            )
            observed[row["coin"]].extend(
                FundingObservation(
                    int(r["calc_time"]),
                    int(r["funding_interval_hours"]),
                    D(r["last_funding_rate"]),
                )
                for r in records
            )
    events = []
    for c in coins:
        prices = [b.open for b in bars[c]]
        actual_buckets = {p.time_ms // HOUR * HOUR for p in observed[c]}
        for previous in observed[c]:
            signal = next_clock_signal(previous, START, END)
            if signal is None:
                continue
            i = (signal.expected_payment_ms - START) // HOUR
            event = {
                "coin": c,
                **asdict(signal),
                "actual_payment_at_expected_hour": signal.expected_payment_ms
                in actual_buckets,
                "returns": {},
            }
            for name, (fee, slip, delay, mode) in SCENARIOS.items():
                # Keep the fixed +2h control even in the +1h primary stress.
                event["returns"][name] = {
                    "primary": event_return(
                        prices,
                        START,
                        payments[c],
                        i + delay,
                        1,
                        signal.side,
                        fee,
                        slip,
                        mode,
                    ),
                    "control": event_return(
                        prices,
                        START,
                        payments[c],
                        i + 2,
                        1,
                        signal.side,
                        fee,
                        slip,
                        mode,
                    ),
                }
            events.append(event)
    events.sort(key=lambda e: (e["expected_payment_ms"], e["coin"]))
    args.output.mkdir(parents=True, exist_ok=False)
    write_json(args.output / "events.json", events)
    write_json(args.output / "quality.json", quality)
    results = {}
    for name in SCENARIOS:
        daily_primary = {day: [0.0, 0] for day in range(START // DAY, END // DAY)}
        daily_difference = {day: [0.0, 0] for day in range(START // DAY, END // DAY)}
        main_returns = []
        control_returns = []
        contributions: dict[str, Decimal] = {}
        for e in events:
            main, control = (
                e["returns"][name][k]["net_bps"] for k in ("primary", "control")
            )
            main_returns.append(main)
            control_returns.append(control)
            contributions[e["coin"]] = contributions.get(e["coin"], D(0)) + main
            day = e["expected_payment_ms"] // DAY
            daily_primary[day][0] += float(main)
            daily_primary[day][1] += 1
            daily_difference[day][0] += float(main - control)
            daily_difference[day][1] += 1
        gains = sum((max(x, D(0)) for x in main_returns), D(0))
        losses = -sum((min(x, D(0)) for x in main_returns), D(0))
        results[name] = {
            "n": len(events),
            "mean_primary_net_bps": sum(main_returns, D(0)) / len(events)
            if events
            else None,
            "mean_control_net_bps": sum(control_returns, D(0)) / len(events)
            if events
            else None,
            "profit_factor": gains / losses if losses else None,
            "worst_event_bps": min(main_returns) if events else None,
            "contribution_sum_event_bps": contributions,
            "primary_mean_bootstrap": bootstrap_ratio(list(daily_primary.values())),
            "paired_advantage_bootstrap": bootstrap_ratio(
                list(daily_difference.values())
            ),
        }
    days = len({e["expected_payment_ms"] // DAY for e in events})
    criteria = {
        "thirty_events_and_days": len(events) >= 30 and days >= 30,
        "positive_required_cost_scenarios": all(
            results[s]["mean_primary_net_bps"] is not None
            and results[s]["mean_primary_net_bps"] > 0
            for s in ("base", "cost_stress", "delay", "funding_adverse")
        ),
        "positive_paired_lower_bound": (
            results["base"]["paired_advantage_bootstrap"]["lower_95"] or 0
        )
        > 0,
    }
    write_json(
        args.output / "summary.json",
        {
            "run_id": "funding-clock-20260907-v1",
            "protocol_sha256": reg["protocol_sha256"],
            "code_version": source_version(Path.cwd())[0],
            "script_sha256": file_sha256(Path(__file__)),
            "events": len(events),
            "distinct_days": days,
            "events_by_coin": dict(Counter(e["coin"] for e in events)),
            "events_by_side": dict(Counter(e["side"] for e in events)),
            "schedule_matches": sum(
                e["actual_payment_at_expected_hour"] for e in events
            ),
            "results": results,
            "criteria": criteria,
            "decision": "FUNDING_CLOCK_WORTH_PORTFOLIO_TEST"
            if all(criteria.values())
            else "FUNDING_CLOCK_HYPOTHESIS_NOT_CONFIRMED",
            "network_data_calls": 0,
            "portfolio_simulated": False,
            "native_fills_qualified": False,
            "live_enabled": False,
            "promotion_authorized": False,
        },
    )
    print(
        json.dumps(
            {
                "events": len(events),
                "days": days,
                "results": results,
                "criteria": criteria,
            },
            default=str,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
