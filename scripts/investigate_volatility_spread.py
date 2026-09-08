"""Offline weekly low-volatility minus high-volatility basket screen."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from dataclasses import asdict
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
from hyperbot2.research.rotation import HOUR
from hyperbot2.research.volatility_spread import volatility_baskets

D = Decimal
DAY = 24 * HOUR
REPORT = Path("reports/volatility_spread_2026-09-07")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--panel",
        required=True,
        choices=("original_native", "matched_native", "prior_transfer"),
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    checked_input(REPORT / "registration.json")
    reg = json.loads((REPORT / "registration.json").read_text())
    selection = Path("reports/prior_transfer_2026-09-07/qualification.json")
    original = Path("reports/funding_transfer_2026-09-07/selection.json")
    code_version, script_sha = (
        source_version(Path.cwd())[0],
        file_sha256(Path(__file__)),
    )
    if (
        reg["protocol_sha256"] != file_sha256(REPORT / "PROTOCOL.md")
        or reg["qualification_sha256"] != checked_input(selection)
        or reg["native_selection_sha256"] != checked_input(original)
        or reg["code_version"] != code_version
        or reg["script_sha256"] != script_sha
    ):
        raise ValueError("registered study changed")
    coins = [
        r["coin"] for r in json.loads(selection.read_text())["selected_by_metadata"]
    ]
    if args.panel == "original_native":
        coins = json.loads(original.read_text())["eligible"]
    if args.panel == "prior_transfer":
        bars, payments, quality = load_archives(
            Path("data/prior_transfer_2026-09-07/archives"), coins
        )
    else:
        folders = (
            [DATA / "history"]
            + [TRANSFER / "history" / f"batch-{b}" for b in range(2)]
            + [ROOT / "history", ROOT / "replication_history", OLD / "history"]
        )
        bars, payments, _, quality = load(folders, coins, START, END)
        quality["source_venue"] = "Hyperliquid"
    if any(v["zero_volume_hours"] for v in quality["assets"].values()):
        raise ValueError("zero-volume panel")
    times = [b.time for b in bars[coins[0]]]
    start, end = times[0], times[-1] + HOUR
    if any([b.time for b in rows] != times for rows in bars.values()):
        raise ValueError("unaligned panels")
    opens = {c: [b.open for b in bars[c]] for c in coins}
    selections = volatility_baskets(
        {c: [b.close for b in bars[c]] for c in coins}, times
    )
    events = []
    for basket in selections:
        if not basket.sides:
            continue
        legs = []
        for c, side in basket.sides:
            nearby = {
                at: rate
                for at, rate in payments[c].items()
                if basket.time_ms <= at <= basket.time_ms + 169 * HOUR + 60_000
            }
            returns = {}
            for rule, direction in (("low_minus_high", side), ("long_control", 1)):
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
            for rule in ("low_minus_high", "long_control")
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
    for rule in ("low_minus_high", "long_control"):
        scenarios = {}
        for scenario in SCENARIOS:
            daily = {d: [0.0, 0] for d in range(evaluation_start // DAY, end // DAY)}
            returns = []
            contributions: dict[str, Decimal] = {}
            sides = {"low_volatility_longs": D(0), "high_volatility_group": D(0)}
            for e in events:
                value = e["basket_returns_net_bps"][rule][scenario]
                returns.append(value)
                daily[e["time_ms"] // DAY] = [float(value), 1]
                for leg in e["legs"]:
                    contribution = leg["returns"][rule][scenario]["net_bps"] / 6
                    c = leg["coin"]
                    contributions[c] = contributions.get(c, D(0)) + contribution
                    group = (
                        "low_volatility_longs"
                        if leg["side"] == 1
                        else "high_volatility_group"
                    )
                    sides[group] += contribution
            gains = sum((max(v, D(0)) for v in returns), D(0))
            losses = -sum((min(v, D(0)) for v in returns), D(0))
            scenarios[scenario] = {
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
                for s in ("base", "cost_stress", "delay", "funding_adverse")
            ),
            "positive_central_lower_bound": bool(ci and (ci["lower_95"] or 0) > 0),
        }
        results[rule] = {
            "scenarios": scenarios,
            "criteria": criteria,
            "panel_filter_pass": all(criteria.values()),
        }
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
            "run_id": f"volatility-spread-20260907-v1-{args.panel}",
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
            "eligible_weeks": len(selections),
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
