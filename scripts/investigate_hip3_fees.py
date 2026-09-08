"""Reprice existing equity events at observed fees without changing signals."""

from __future__ import annotations

import argparse
import copy
import json
import runpy
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from typing import Any

import investigate_weekend_repricing as weekend

from hyperbot2.research.artifacts import checked_input, file_sha256, write_json
from hyperbot2.research.hip3_fees import reprice_fees, taker_fee
from hyperbot2.research.rotation import HOUR, leg_return

D = Decimal
REPORT = Path("reports/hip3_fee_review_2026-09-07")
ALL_COINS = weekend.COINS + ("xyz:COIN", "xyz:MSTR")
INPUTS = {
    "weekend_initial": Path("data/weekend_repricing_2026-09-07/run1"),
    "weekend_replication": Path("data/weekend_repricing_2026-09-07/replication_final"),
    "overnight": Path("data/overnight_repricing_2026-09-07/run1"),
}


def economic_proxy(events: list[dict], scenario: str, start: int, end: int) -> dict:
    dates: dict[int, list[Decimal]] = defaultdict(list)
    for e in events:
        dates[e["entry_ms"]].append(e["returns"][scenario]["net_bps"])
    days = D(end - start) / (24 * HOUR)
    small = sum((sum(v, D(0)) * D(50) / 10_000 for v in dates.values()), D(0))
    capped = sum(
        (sum(v, D(0)) / len(v) * D(1000) / 10_000 for v in dates.values()), D(0)
    )
    return {
        "period_days": days,
        "pnl_50_per_event_usd": small,
        "pnl_1000_total_per_date_usd": capped,
        "monthly_50_after_infra": small * 30 / days - 20,
        "monthly_1000_total_after_infra": capped * 30 / days - 20,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    checked_input(REPORT / "registration.json")
    protocol = file_sha256(REPORT / "PROTOCOL.md")
    if (
        json.loads((REPORT / "registration.json").read_text())["protocol_sha256"]
        != protocol
    ):
        raise ValueError("registered fee protocol changed")
    sources = {}

    def read(path: Path) -> Any:
        sources[str(path)] = checked_input(path)
        return json.loads(path.read_text())

    meta = read(Path("data/weekend_repricing_2026-09-07/xyz_meta.json"))
    universe = {m["name"]: m for m in meta["response"][0]["universe"]}
    fees = {}
    for coin in ALL_COINS:
        m = universe[coin]
        enabled = m.get("growthMode") == "enabled"
        if enabled != (coin != "xyz:MSTR"):
            raise ValueError("metadata differs from registered fee states")
        fees[coin] = taker_fee(
            deployer_fee_scale=D(m["deployerFeeScale"]), growth_mode=m.get("growthMode")
        )
    candles, funding, start, end, old_sources = weekend.load(
        Path("data/weekend_repricing_2026-09-07/history")
    )
    sources.update(old_sources)
    weekend.COINS = ALL_COINS[-2:]
    extra, extra_funding, a, b, extra_sources = weekend.load(
        Path("data/weekend_repricing_2026-09-07/replication_history")
    )
    if (a, b) != (start, end):
        raise ValueError("history coverage differs")
    candles.update(extra)
    funding.update(extra_funding)
    sources.update(extra_sources)
    overnight = runpy.run_path("scripts/investigate_overnight_repricing.py")
    groups, comparisons = {}, 0
    for group, root in INPUTS.items():
        original_summary = read(root / "summary.json")
        for direction in ("fade", "follow"):
            name = (
                ("overnight" if group == "overnight" else "weekend") + "_" + direction
            )
            original = read(root / f"{name}-events.json")
            adjusted = copy.deepcopy(original)
            for event, old in zip(adjusted, original, strict=True):
                coin = event["coin"]
                ratio = fees[coin] / D("0.0009")
                opens = [c.open for c in candles[coin]]
                rates = [funding[coin][c.time] for c in candles[coin]]
                index = (event["entry_ms"] - start) // HOUR
                horizon = (event["exit_ms"] - event["entry_ms"]) // HOUR
                for scenario, values in old["returns"].items():
                    original_values = {k: D(v) for k, v in values.items()}
                    new_values = reprice_fees(original_values, ratio)
                    event["returns"][scenario] = new_values
                    if scenario in weekend.SCENARIOS:
                        old_fee, slip, delay, mode = weekend.SCENARIOS[scenario]
                        k, duration = index + delay, horizon
                    else:
                        old_fee, slip, _, mode = weekend.SCENARIOS["base"]
                        k, duration = (
                            (index + 1, 1)
                            if scenario == "entry_delay_only"
                            else (index, 3)
                        )
                    expected = leg_return(
                        opens,
                        rates,
                        k,
                        duration,
                        event["side"],
                        old_fee * ratio,
                        slip,
                        mode,
                    )
                    if any(
                        abs(new_values[key] - expected[key]) > D("1e-18")
                        for key in expected
                    ):
                        raise ValueError(
                            "fee-only adjustment differs from raw repricing"
                        )
                    comparisons += 1
                if {k: v for k, v in event.items() if k != "returns"} != {
                    k: v for k, v in old.items() if k != "returns"
                }:
                    raise ValueError("signal changed during fee adjustment")
            weekend.COINS = (
                ALL_COINS
                if group == "overnight"
                else (
                    ALL_COINS[-2:] if group == "weekend_replication" else ALL_COINS[:5]
                )
            )
            windows = {"all": (start, end)}
            if group == "overnight":
                split = original_summary["split_ms"]
                windows = {"older": (start, split), "validation": (split, end)}
            segments = {}
            for segment, (a, b) in windows.items():
                selected = [e for e in adjusted if a <= e["entry_ms"] < b]
                scenarios = {
                    s: weekend.describe(selected, s, a, b)
                    for s in adjusted[0]["returns"]
                }
                ci = (
                    overnight["interval"](selected, a, b)
                    if group == "overnight"
                    else weekend.interval(selected, original_summary["frames_ms"])
                )
                base = scenarios["base"]
                criteria = {
                    "all_cost_scenarios_positive": all(
                        (scenarios[s]["mean_net_bps"] or 0) > 0
                        for s in weekend.SCENARIOS
                        if s != "zero_cost"
                    ),
                    "profit_factor_above_1_2": (base["profit_factor"] or 0) > D("1.2"),
                    "corrected_interval_positive": ci is not None and ci["lower"] > 0,
                    "positive_blocks": sum(v > 0 for v in base["blocks_30d_sum_bps"])
                    >= (3 if group == "overnight" else 5),
                    "positive_without_best": (base["sum_without_best_bps"] or 0) > 0,
                }
                profit_parts = [
                    max(D(0), v["sum_net_bps"]) for v in base["assets"].values()
                ]
                concentration = (
                    max(profit_parts) / sum(profit_parts) if sum(profit_parts) else None
                )
                economics = {s: economic_proxy(selected, s, a, b) for s in scenarios}
                segments[segment] = {
                    "scenarios": scenarios,
                    "interval": ci,
                    "criteria": criteria,
                    "economics": economics,
                    "positive_profit_concentration": concentration,
                    "research_gates_pass": all(criteria.values())
                    and economics["base"]["monthly_1000_total_after_infra"] >= 30,
                }
            key = group + "_" + direction
            write_json(args.output / f"{key}-events.json", adjusted)
            groups[key] = {
                "segments": segments,
                "decision": "FURTHER_FREE_VALIDATION"
                if all(s["research_gates_pass"] for s in segments.values())
                else "HYPOTHESIS_NOT_CONFIRMED",
            }
            print(
                key,
                json.dumps(
                    {
                        s: {
                            "mean": v["scenarios"]["base"]["mean_net_bps"],
                            "stress": v["scenarios"]["cost_stress"]["mean_net_bps"],
                            "delay": v["scenarios"]["delay_stress"]["mean_net_bps"],
                            "ci": v["interval"],
                            "criteria": v["criteria"],
                            "economics": v["economics"]["base"],
                        }
                        for s, v in segments.items()
                    },
                    default=str,
                ),
                flush=True,
            )
    write_json(
        args.output / "summary.json",
        {
            "run_id": "hip3-fee-sensitivity-20260907-v1",
            "protocol_sha256": protocol,
            "fees_per_side": fees,
            "groups": groups,
            "sources": sources,
            "raw_leg_comparisons": comparisons,
            "code_hashes": {
                str(p): file_sha256(p)
                for p in (
                    Path(__file__),
                    Path("scripts/investigate_weekend_repricing.py"),
                    Path("scripts/investigate_overnight_repricing.py"),
                    Path("src/hyperbot2/research/hip3_fees.py"),
                    Path("src/hyperbot2/research/rotation.py"),
                )
            },
            "fee_status": (
                "current public metadata and pre-period activation announcement; "
                "complete per-market fee history unqualified"
            ),
            "acceptable_user_target_monthly_usd": [150, 200],
            "live_enabled": False,
            "shadow_only": True,
            "public_data_only": True,
            "limits": [
                "existing events, not a new holdout",
                "hourly execution and oracle proxies",
                "economic proxies without margin/depth/size simulation",
                "no guaranteed monthly return",
            ],
        },
    )


if __name__ == "__main__":
    main()
