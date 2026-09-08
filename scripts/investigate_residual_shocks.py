"""Registered beta-hedged residual-shock event study from local native data."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path

from investigate_funding_normalization import END, OLD, ROOT, SCENARIOS, load, summarize
from investigate_funding_transfer import DATA as TRANSFER
from investigate_funding_transfer import START
from investigate_pairs import bootstrap_ratio

from hyperbot2.research.artifacts import (
    checked_input,
    file_sha256,
    source_version,
    write_json,
)
from hyperbot2.research.funding_normalization import event_return
from hyperbot2.research.residual_shocks import residual_shock
from hyperbot2.research.rotation import HOUR

D = Decimal
DAY = 24 * HOUR
REPORT = Path("reports/residual_shocks_2026-09-07")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    checked_input(REPORT / "registration.json")
    registration = json.loads((REPORT / "registration.json").read_text())
    protocol = file_sha256(REPORT / "PROTOCOL.md")
    selection = Path("reports/funding_transfer_2026-09-07/selection.json")
    if registration["protocol_sha256"] != protocol or registration[
        "universe_sha256"
    ] != checked_input(selection):
        raise ValueError("registered residual study changed")
    coins = json.loads(selection.read_text())["eligible"]
    if len(coins) != 18 or "CASHCAT" in coins or "BTC" in coins:
        raise ValueError("registered universe mismatch")
    folders = [TRANSFER / "history" / f"batch-{b}" for b in range(2)] + [
        ROOT / "history",
        ROOT / "replication_history",
        OLD / "history",
    ]
    bars, payments, _, quality = load(folders, coins, START, END)
    hedge, hedge_payments, _, hedge_quality = load(
        [Path("data/search_2026-09-06/history")], ["BTC"], START, END
    )
    bars.update(hedge)
    payments.update(hedge_payments)
    quality["sources"].update(hedge_quality["sources"])
    quality["assets"].update(hedge_quality["assets"])
    quality["sources"][str(selection)] = checked_input(selection)
    logs = {c: [b.close.ln() for b in rows] for c, rows in bars.items()}
    opens = {c: [b.open for b in rows] for c, rows in bars.items()}
    events, counts = [], {}
    for c in coins:
        next_allowed, previous = 0, False
        count = {"model_filtered": 0, "outside_shock_range": 0, "events": 0}
        for i in range(175, len(bars[c]) - 25):
            frame = residual_shock(logs[c], logs["BTC"], i)
            if (
                frame is None
                or not D("0.25") <= frame[0].beta <= 4
                or frame[0].correlation < D("0.3")
                or frame[0].sigma < D("0.005")
            ):
                previous = False
                count["model_filtered"] += 1
                continue
            model, z = frame
            qualifies = 3 <= abs(z) < 6
            candidate = qualifies and not previous and i >= next_allowed
            previous = qualifies
            if not qualifies:
                count["outside_shock_range"] += 1
            if not candidate:
                continue
            next_allowed = i + 25
            side = -1 if z > 0 else 1
            weight = 1 / (1 + model.beta)
            returns, legs = {}, {}
            for h in (6, 24):
                returns[str(h)], legs[str(h)] = {}, {}
                for scenario, (fee, slip, delay, mode) in SCENARIOS.items():
                    asset = event_return(
                        opens[c],
                        START,
                        payments[c],
                        i + delay,
                        h,
                        side,
                        fee,
                        slip,
                        mode,
                    )
                    btc = event_return(
                        opens["BTC"],
                        START,
                        payments["BTC"],
                        i + delay,
                        h,
                        -side,
                        fee,
                        slip,
                        mode,
                    )
                    returns[str(h)][scenario] = {
                        key: weight * asset[key] + (1 - weight) * btc[key]
                        for key in asset
                    }
                    legs[str(h)][scenario] = {c: asset, "BTC": btc}
            events.append(
                {
                    "coin": c,
                    "side": side,
                    "entry_ms": START + i * HOUR + 60_000,
                    "last_signal_close_ms": START + i * HOUR - 1,
                    "last_training_close_ms": START + (i - 6) * HOUR - 1,
                    "model": asdict(model),
                    "z": z,
                    "asset_weight": weight,
                    "btc_weight": 1 - weight,
                    "returns": returns,
                    "legs": legs,
                }
            )
            count["events"] += 1
        counts[c] = count
        print(c, "events", count["events"], flush=True)
    events.sort(key=lambda e: (e["entry_ms"], e["coin"]))
    quality["model_counts"] = counts
    write_json(args.output / "quality.json", quality)
    write_json(args.output / "events.json", events)
    stats = {
        str(h): {
            scenario: summarize(events, str(h), scenario, START, 30)
            for scenario in SCENARIOS
        }
        for h in (6, 24)
    }
    distinct_days = len({e["entry_ms"] // DAY for e in events})
    interval = None
    if len(events) >= 30 and distinct_days >= 20:
        daily = {day: [0.0, 0] for day in range(START // DAY, END // DAY)}
        for e in events:
            daily[e["entry_ms"] // DAY][0] += float(
                e["returns"]["6"]["base"]["net_bps"]
            )
            daily[e["entry_ms"] // DAY][1] += 1
        interval = bootstrap_ratio(list(daily.values()))
    base = stats["6"]["base"]
    criteria = {
        "all_paid_scenarios_positive": all(
            stats["6"][s]["sum_net_bps"] > 0 for s in SCENARIOS if s != "zero_cost"
        ),
        "profit_factor_above_1_2": (base["profit_factor"] or 0) > D("1.2"),
        "positive_without_best": (base["sum_without_best_bps"] or 0) > 0,
    }
    write_json(
        args.output / "summary.json",
        {
            "run_id": "residual-shocks-20260907-v1",
            "protocol_sha256": protocol,
            "code_version": source_version(Path.cwd())[0],
            "scripts": {
                str(p): file_sha256(p)
                for p in (
                    Path(__file__),
                    Path("scripts/investigate_funding_normalization.py"),
                    Path("scripts/investigate_pairs.py"),
                )
            },
            "start_ms": START,
            "end_ms_exclusive": END,
            "primary_horizon_hours": 6,
            "statistics": stats,
            "distinct_entry_days": distinct_days,
            "primary_descriptive_interval": interval,
            "criteria": criteria,
            "decision": "PORTFOLIO_RESEARCH_REQUIRED"
            if all(criteria.values())
            else "HYPOTHESIS_NOT_CONFIRMED",
            "live_enabled": False,
            "promotion_authorized": False,
            "network_calls": 0,
            "limits": [
                "selected universe and previously consulted period",
                "beta hedge is approximate and fixed during holding",
                "event notional returns, no risk-sized account or depth validation",
                "descriptive interval not corrected for all prior searches",
            ],
        },
    )
    print(
        "primary",
        base["events"],
        "mean bps",
        base["mean_net_bps"],
        "criteria",
        criteria,
        flush=True,
    )


if __name__ == "__main__":
    main()
