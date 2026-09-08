"""Older-period falsification of the post-selected long volatility-extremes rule."""

from __future__ import annotations

import argparse
import hashlib
import json
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
REPORT = Path("reports/volatility_long_2024_2026-09-07")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--panel",
        required=True,
        choices=("native_2026", "transfer_2025", "transfer_2024"),
    )
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    checked_input(REPORT / "economic_registration_v2.json")
    reg = json.loads((REPORT / "economic_registration_v2.json").read_text())
    correction_root = Path("data/volatility_long_2024_2026-09-07/october_api_audit")
    qpath = REPORT / "qualification.json"
    previous = Path("reports/prior_transfer_2026-09-07/qualification.json")
    version, script_sha = source_version(Path.cwd())[0], file_sha256(Path(__file__))
    if (
        reg["protocol_sha256"] != file_sha256(REPORT / "ECONOMIC_PROTOCOL.md")
        or reg["qualification_sha256"] != checked_input(qpath)
        or reg["previous_qualification_sha256"] != checked_input(previous)
        or reg["code_version"] != version
        or reg["script_sha256"] != script_sha
        or reg["amendment_sha256"] != file_sha256(REPORT / "SOURCE_AMENDMENT.md")
        or reg["rest_manifest_sha256"]
        != checked_input(correction_root / "manifest.json")
    ):
        raise ValueError("registered study changed")
    coins = [r["coin"] for r in json.loads(qpath.read_text())["selected_by_metadata"]]
    if len(coins) != 11:
        raise ValueError("registered cohort changed")
    if args.panel == "transfer_2024":
        bars, payments, quality = load_archives(
            Path("data/volatility_long_2024_2026-09-07/archives"),
            coins,
            year=2024,
            october_2024_rest=correction_root,
        )
    elif args.panel == "transfer_2025":
        full = [
            r["coin"] for r in json.loads(previous.read_text())["selected_by_metadata"]
        ]
        bars, payments, quality = load_archives(
            Path("data/prior_transfer_2026-09-07/archives"), full
        )
        bars, payments = ({c: rows[c] for c in coins} for rows in (bars, payments))
        quality["loaded_full_cohort"] = full
        quality["evaluated_cohort"] = coins
    else:
        folders = (
            [DATA / "history"]
            + [TRANSFER / "history" / f"batch-{b}" for b in range(2)]
            + [ROOT / "history", ROOT / "replication_history", OLD / "history"]
        )
        bars, payments, _, quality = load(folders, coins, START, END)
        quality["source_venue"] = "Hyperliquid"
    if any(quality["assets"][c]["zero_volume_hours"] for c in coins):
        raise ValueError("zero-volume cohort")
    times = [b.time for b in bars[coins[0]]]
    start, end = times[0], times[-1] + HOUR
    if any([b.time for b in rows] != times for rows in bars.values()):
        raise ValueError("unaligned price panels")
    selections = volatility_baskets(
        {c: [b.close for b in rows] for c, rows in bars.items()}, times
    )
    opens = {c: [b.open for b in rows] for c, rows in bars.items()}
    events = []
    for basket in selections:
        if not basket.sides:
            continue
        selected = set(dict(basket.sides))
        legs = []
        for c in coins:
            nearby = {
                at: rate
                for at, rate in payments[c].items()
                if basket.time_ms <= at <= basket.time_ms + 169 * HOUR + 60_000
            }
            returns = {
                s: event_return(
                    opens[c],
                    start,
                    nearby,
                    basket.index + delay,
                    168,
                    1,
                    fee,
                    slip,
                    mode,
                )
                for s, (fee, slip, delay, mode) in SCENARIOS.items()
            }
            legs.append({"coin": c, "selected": c in selected, "returns": returns})
        aggregate = {
            rule: {
                s: sum(
                    (
                        leg["returns"][s]["net_bps"]
                        for leg in legs
                        if rule == "all_assets_control" or leg["selected"]
                    ),
                    D(0),
                )
                / count
                for s in SCENARIOS
            }
            for rule, count in (("volatility_extremes", 6), ("all_assets_control", 11))
        }
        events.append(
            {
                "time_ms": basket.time_ms,
                "index": basket.index,
                "legs": legs,
                "basket_returns_net_bps": aggregate,
            }
        )
    evaluation_start = selections[0].time_ms if selections else end
    results = {}
    for rule in ("volatility_extremes", "all_assets_control"):
        scenarios = {}
        for s in SCENARIOS:
            daily = {
                day: [0.0, 0] for day in range(evaluation_start // DAY, end // DAY)
            }
            paired = {day: [0.0, 0] for day in daily}
            returns, differences = [], []
            contributions: dict[str, Decimal] = {}
            count = 6 if rule == "volatility_extremes" else 11
            for e in events:
                value = e["basket_returns_net_bps"][rule][s]
                difference = (
                    value - e["basket_returns_net_bps"]["all_assets_control"][s]
                )
                returns.append(value)
                differences.append(difference)
                daily[e["time_ms"] // DAY] = [float(value), 1]
                paired[e["time_ms"] // DAY] = [float(difference), 1]
                for leg in e["legs"]:
                    if rule == "all_assets_control" or leg["selected"]:
                        c = leg["coin"]
                        contributions[c] = (
                            contributions.get(c, D(0))
                            + leg["returns"][s]["net_bps"] / count
                        )
            gains = sum((max(v, D(0)) for v in returns), D(0))
            losses = -sum((min(v, D(0)) for v in returns), D(0))
            scenarios[s] = {
                "mean_basket_net_bps": sum(returns, D(0)) / len(returns)
                if returns
                else None,
                "mean_advantage_bps": sum(differences, D(0)) / len(differences)
                if differences
                else None,
                "worst_basket_net_bps": min(returns) if returns else None,
                "best_basket_net_bps": max(returns) if returns else None,
                "positive_baskets": sum(v > 0 for v in returns),
                "profit_factor": gains / losses if losses else None,
                "contribution_sum_basket_bps": contributions,
                "mean_bootstrap": bootstrap_ratio(list(daily.values()))
                if daily
                else None,
                "paired_advantage_bootstrap": bootstrap_ratio(list(paired.values()))
                if paired
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
            "older_period_positive_advantage": args.panel != "transfer_2024"
            or (scenarios["base"]["mean_advantage_bps"] or 0) > 0,
        }
        results[rule] = {
            "scenarios": scenarios,
            "criteria": criteria,
            "panel_filter_pass": all(criteria.values()),
        }
    if (
        source_version(Path.cwd())[0] != version
        or file_sha256(Path(__file__)) != script_sha
    ):
        raise ValueError("code changed during calculation")
    args.output.mkdir(parents=True, exist_ok=False)
    write_json(args.output / "quality.json", quality)
    write_json(args.output / "selections.json", [asdict(s) for s in selections])
    write_json(args.output / "events.json", events)
    config = {
        "protocol_sha256": reg["protocol_sha256"],
        "source_amendment_sha256": reg["amendment_sha256"],
        "panel": args.panel,
        "scenarios": SCENARIOS,
        "fill_model": "hourly-open-proxy-at-plus-60s",
    }
    write_json(
        args.output / "summary.json",
        {
            "run_id": f"volatility-long-2024-20260907-v2-{args.panel}",
            "panel": args.panel,
            "code_version": version,
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
            "results": results,
            "decision": "CROSS_PANEL_REVIEW_REQUIRED",
            "network_data_calls_this_simulation": 0,
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
