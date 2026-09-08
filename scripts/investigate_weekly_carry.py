"""Offline weekly carry basket screen with a fixed cost hurdle."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from investigate_breakout_extension import DATA, START
from investigate_funding_clock import SCENARIOS
from investigate_funding_normalization import END, OLD, ROOT, load
from investigate_funding_transfer import DATA as TRANSFER
from investigate_pairs import bootstrap_ratio

from hyperbot2.research.artifacts import (
    checked_input,
    file_sha256,
    source_version,
    write_json,
)
from hyperbot2.research.binance_archives import load_archives
from hyperbot2.research.funding_normalization import event_return
from hyperbot2.research.market_regime import join_panels
from hyperbot2.research.rotation import HOUR
from hyperbot2.research.weekly_carry import carry_baskets

D = Decimal
DAY = 24 * HOUR
REPORT = Path("reports/weekly_carry_2026-09-07")
PREVIOUS = Path("reports/volatility_long_2024_2026-09-07")
PREVIOUS_DATA = Path("data/volatility_long_2024_2026-09-07")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--panel",
        required=True,
        choices=("native_2026", "continuous_2024_2025"),
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    checked_input(REPORT / "registration_v2.json")
    reg = json.loads((REPORT / "registration_v2.json").read_text())
    code_version, script_sha = (
        source_version(Path.cwd())[0],
        file_sha256(Path(__file__)),
    )
    if (
        reg["protocol_sha256"] != file_sha256(REPORT / "PROTOCOL.md")
        or reg["code_version"] != code_version
        or reg["script_sha256"] != script_sha
    ):
        raise ValueError("registered carry study changed")
    for filename, sha in reg["inputs"].items():
        if checked_input(Path(filename)) != sha:
            raise ValueError("registered input changed")
    coins = [
        r["coin"]
        for r in json.loads((PREVIOUS / "qualification.json").read_text())[
            "selected_by_metadata"
        ]
    ]
    if args.panel == "continuous_2024_2025":
        left, left_payments, q4 = load_archives(
            PREVIOUS_DATA / "archives",
            coins,
            year=2024,
            october_2024_rest=PREVIOUS_DATA / "october_api_audit",
        )
        q = Path("reports/prior_transfer_2026-09-07/qualification.json")
        full = [r["coin"] for r in json.loads(q.read_text())["selected_by_metadata"]]
        right, right_payments, q5 = load_archives(
            Path("data/prior_transfer_2026-09-07/archives"), full
        )
        right, right_payments = (
            {c: rows[c] for c in coins} for rows in (right, right_payments)
        )
        bars, payments = join_panels(left, left_payments, right, right_payments)
        quality = {
            "source_venue": "Binance USDT perpetual futures",
            "sources": {**q4["sources"], **q5["sources"]},
            "segments": {"2024": q4, "2025": q5},
            "evaluated_cohort": coins,
            "data_class": "C",
            "continuous_hours": len(bars[coins[0]]),
            "annual_capital_or_warmup_reset": False,
        }
    else:
        folders = (
            [DATA / "history"]
            + [TRANSFER / "history" / f"batch-{b}" for b in range(2)]
            + [ROOT / "history", ROOT / "replication_history", OLD / "history"]
        )
        bars, payments, _, quality = load(folders, coins, START, END)
        quality["source_venue"] = "Hyperliquid"
    reference = (
        Path("reports/collective_trend_2026-09-07") / f"{args.panel}_quality.json"
    )
    expected_quality = json.loads(reference.read_text())
    expected_quality.pop("native_reference_metadata")
    expected_quality["sources"].pop(str(OLD / "meta.json"))
    if quality != expected_quality:
        raise ValueError("historical panel quality changed")
    times = [b.time for b in bars[coins[0]]]
    start, end = times[0], times[-1] + HOUR
    if any([b.time for b in rows] != times for rows in bars.values()):
        raise ValueError("unaligned panels")
    opens = {c: [b.open for b in bars[c]] for c in coins}
    selections = carry_baskets(payments, times)
    events = []
    for basket in selections:
        if not basket.eligible:
            continue
        legs = []
        for c, side in basket.sides:
            nearby = {
                at: rate
                for at, rate in payments[c].items()
                if basket.time_ms <= at <= basket.time_ms + 169 * HOUR + 60_000
            }
            returns = {}
            for rule, direction in (("carry", side), ("reverse_control", -side)):
                returns[rule] = {
                    scenario: event_return(
                        opens[c],
                        start,
                        nearby,
                        basket.index + delay,
                        168,
                        direction,
                        fee,
                        slip,
                        mode,
                    )
                    for scenario, (fee, slip, delay, mode) in SCENARIOS.items()
                }
            legs.append({"coin": c, "side": side, "returns": returns})
        returns = {
            rule: {
                s: sum((leg["returns"][rule][s]["net_bps"] for leg in legs), D(0)) / 6
                for s in SCENARIOS
            }
            for rule in ("carry", "reverse_control")
        }
        events.append(
            {
                "time_ms": basket.time_ms,
                "index": basket.index,
                "legs": legs,
                "basket_returns_net_bps": returns,
            }
        )
    evaluation_start = selections[0].time_ms if selections else end
    results = {}
    for rule in ("carry", "reverse_control"):
        scenarios = {}
        for scenario in SCENARIOS:
            daily = {d: [0.0, 0] for d in range(evaluation_start // DAY, end // DAY)}
            returns = []
            contributions: dict[str, Decimal] = {}
            sides = {"low_funding_group": D(0), "high_funding_group": D(0)}
            for e in events:
                value = e["basket_returns_net_bps"][rule][scenario]
                returns.append(value)
                daily[e["time_ms"] // DAY] = [float(value), 1]
                for leg in e["legs"]:
                    contribution = leg["returns"][rule][scenario]["net_bps"] / 6
                    c = leg["coin"]
                    contributions[c] = contributions.get(c, D(0)) + contribution
                    group = (
                        "low_funding_group"
                        if leg["side"] == 1
                        else "high_funding_group"
                    )
                    sides[group] += contribution
            components = {}
            for component in (
                "gross_bps",
                "slippage_bps",
                "fees_bps",
                "funding_cost_bps",
                "net_bps",
            ):
                values = [
                    sum(
                        (
                            leg["returns"][rule][scenario][component]
                            for leg in e["legs"]
                        ),
                        D(0),
                    )
                    / 6
                    for e in events
                ]
                components[component] = (
                    sum(values, D(0)) / len(values) if values else None
                )
            if events and abs(
                components["gross_bps"]
                - components["slippage_bps"]
                - components["fees_bps"]
                - components["funding_cost_bps"]
                - components["net_bps"]
            ) > D("1e-20"):
                raise ValueError("event component accounting mismatch")
            years = {}
            for e in events:
                year = str(datetime.fromtimestamp(e["time_ms"] / 1000, UTC).year)
                years.setdefault(year, []).append(
                    e["basket_returns_net_bps"][rule][scenario]
                )
            gains = sum((max(v, D(0)) for v in returns), D(0))
            losses = -sum((min(v, D(0)) for v in returns), D(0))
            scenarios[scenario] = {
                "mean_components_bps": components,
                "by_entry_year": {
                    y: {"baskets": len(v), "mean_net_bps": sum(v, D(0)) / len(v)}
                    for y, v in years.items()
                },
                "mean_basket_net_bps": sum(returns, D(0)) / len(returns)
                if returns
                else None,
                "worst_basket_net_bps": min(returns) if returns else None,
                "positive_baskets": sum(v > 0 for v in returns),
                "profit_factor": gains / losses if losses else None,
                "contribution_sum_basket_bps": contributions,
                "group_sum_basket_bps": sides,
                "mean_bootstrap": bootstrap_ratio(list(daily.values()))
                if daily
                else None,
            }
        ci = scenarios["base"]["mean_bootstrap"]
        criteria = {
            "twenty_baskets": len(events) >= 20,
            "positive_paid_scenarios": all(
                scenarios[s]["mean_basket_net_bps"] is not None
                and scenarios[s]["mean_basket_net_bps"] > 0
                for s in ("base", "cost_stress", "delay")
            ),
            "positive_central_lower_bound": bool(ci and (ci["lower_95"] or 0) > 0),
        }
        results[rule] = {
            "scenarios": scenarios,
            "criteria": criteria,
            "panel_filter_pass": all(criteria.values()),
        }
    paired = {d: [0.0, 0] for d in range(evaluation_start // DAY, end // DAY)}
    for e in events:
        r = e["basket_returns_net_bps"]
        paired[e["time_ms"] // DAY] = [
            float(r["carry"]["base"] - r["reverse_control"]["base"]),
            1,
        ]
    paired_ci = bootstrap_ratio(list(paired.values())) if paired else None
    if (
        source_version(Path.cwd())[0] != code_version
        or file_sha256(Path(__file__)) != script_sha
    ):
        raise ValueError("code changed during calculation")
    args.output.mkdir(parents=True, exist_ok=False)
    write_json(args.output / "quality.json", quality)
    write_json(args.output / "selections.json", [asdict(s) for s in selections])
    write_json(args.output / "events.json", events)
    config = {
        "protocol_sha256": reg["protocol_sha256"],
        "panel": args.panel,
        "scenarios": SCENARIOS,
        "fill_model": "hourly-open-proxy-at-plus-60s",
    }
    write_json(
        args.output / "summary.json",
        {
            "run_id": f"weekly-carry-20260907-v1-{args.panel}",
            "panel": args.panel,
            "code_version": code_version,
            "script_sha256": script_sha,
            "config": config,
            "config_sha256": hashlib.sha256(
                json.dumps(config, default=str, sort_keys=True).encode()
            ).hexdigest(),
            "start_ms": start,
            "end_ms": end,
            "evaluation_start_ms": evaluation_start,
            "historical_venue": quality["source_venue"],
            "coins": coins,
            "calendar_weeks": len(selections),
            "eligible_weeks": sum(s.eligible for s in selections),
            "paired_central_advantage_bootstrap": paired_ci,
            "baskets": len(events),
            "legs_by_coin": dict(
                Counter(leg["coin"] for e in events for leg in e["legs"])
            ),
            "results": results,
            "decision": "CROSS_PANEL_REVIEW_REQUIRED",
            "network_data_calls": 0,
            "portfolio_simulated": False,
            "native_fills_qualified": False,
            "live_enabled": False,
            "promotion_authorized": False,
        },
    )
    print(
        json.dumps(
            {"panel": args.panel, "baskets": len(events), "results": results},
            default=str,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
