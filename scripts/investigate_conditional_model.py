"""Fixed chronological ridge event screen, using existing checked panels only."""

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
from hyperbot2.research.conditional_model import (
    DAY,
    Observation,
    chronological_predictions,
    features_at,
)
from hyperbot2.research.funding_normalization import event_return
from hyperbot2.research.rotation import HOUR

D = Decimal
REPORT = Path("reports/conditional_model_2026-09-07")


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
    if (
        reg["protocol_sha256"] != file_sha256(REPORT / "PROTOCOL.md")
        or reg["qualification_sha256"] != checked_input(selection)
        or reg["native_selection_sha256"] != checked_input(original)
    ):
        raise ValueError("registered study changed")
    code_version = source_version(Path.cwd())[0]
    script_sha = file_sha256(Path(__file__))
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
    if any([b.time for b in rows] != times for rows in bars.values()) or any(
        b - a != HOUR for a, b in zip(times, times[1:], strict=False)
    ):
        raise ValueError("unaligned hourly panels")
    opens = {c: [b.open for b in bars[c]] for c in coins}
    buckets = {c: {} for c in coins}
    for c in coins:
        for at, rate in payments[c].items():
            buckets[c].setdefault(at // HOUR * HOUR, {})[at] = rate
        if set(buckets[c]) != set(times):
            raise ValueError("unqualified funding coverage")
    rates = {
        c: [float(sum(buckets[c][t].values(), D(0))) for t in times] for c in coins
    }
    observations = []
    for i in range(169, len(times) - 7):
        if times[i] % (6 * HOUR):
            continue
        for c, (features, scale) in features_at(bars, rates, i).items():
            observations.append(
                Observation(
                    c,
                    i,
                    times[i],
                    times[i + 6] + 60_000,
                    features,
                    scale,
                    float(opens[c][i + 6] / opens[c][i] - 1) / scale,
                )
            )
    predictions, fits = chronological_predictions(observations, start)
    evaluation_start = fits[0].time_ms if fits else end
    events = []
    for p in predictions:
        o = p.observation
        # The label is recorded for audit, but never selects an event.
        for rule, forecast in (
            ("ridge", p.predicted),
            ("intercept_control", p.intercept_only),
        ):
            raw_forecast = forecast * o.scale
            if abs(raw_forecast) < 0.004:
                continue
            side = 1 if raw_forecast > 0 else -1
            i, c = o.index, o.coin
            nearby = {
                at: rate
                for j in range(i, i + 8)
                for at, rate in buckets[c][times[j]].items()
            }
            results = {
                name: event_return(
                    opens[c], start, nearby, i + delay, 6, side, fee, slip, mode
                )
                for name, (fee, slip, delay, mode) in SCENARIOS.items()
            }
            events.append(
                {
                    "coin": c,
                    "time_ms": o.time_ms,
                    "rule": rule,
                    "side": side,
                    "trained_ms": p.trained_ms,
                    "forecast_raw_return": raw_forecast,
                    "returns": results,
                }
            )
    results = {}
    for rule in ("ridge", "intercept_control"):
        selected = [e for e in events if e["rule"] == rule]
        scenario_results = {}
        for scenario in SCENARIOS:
            daily = {d: [0.0, 0] for d in range(evaluation_start // DAY, end // DAY)}
            contributions: dict[str, Decimal] = {}
            months: dict[str, dict] = {}
            returns = []
            for e in selected:
                value = e["returns"][scenario]["net_bps"]
                returns.append(value)
                contributions[e["coin"]] = contributions.get(e["coin"], D(0)) + value
                day = e["time_ms"] // DAY
                daily[day][0] += float(value)
                daily[day][1] += 1
                month = datetime.fromtimestamp(e["time_ms"] / 1000, UTC).strftime(
                    "%Y-%m"
                )
                group = months.setdefault(month, {"n": 0, "sum_event_net_bps": D(0)})
                group["n"] += 1
                group["sum_event_net_bps"] += value
            gains = sum((max(v, D(0)) for v in returns), D(0))
            losses = -sum((min(v, D(0)) for v in returns), D(0))
            scenario_results[scenario] = {
                "mean_net_bps": sum(returns, D(0)) / len(returns) if returns else None,
                "worst_net_bps": min(returns) if returns else None,
                "profit_factor": gains / losses if losses else None,
                "contribution_sum_event_bps": contributions,
                "monthly_event_sums_not_portfolio_returns": months,
                "mean_bootstrap": bootstrap_ratio(list(daily.values()))
                if daily
                else None,
            }
        n_days = len({e["time_ms"] // DAY for e in selected})
        ci = scenario_results["base"]["mean_bootstrap"]
        criteria = {
            "thirty_events_and_days": len(selected) >= 30 and n_days >= 30,
            "positive_paid_scenarios": all(
                scenario_results[s]["mean_net_bps"] is not None
                and scenario_results[s]["mean_net_bps"] > 0
                for s in ("base", "cost_stress", "delay", "funding_adverse")
            ),
            "positive_central_lower_bound": bool(ci and (ci["lower_95"] or 0) > 0),
        }
        results[rule] = {
            "events": len(selected),
            "distinct_days": n_days,
            "by_coin": dict(Counter(e["coin"] for e in selected)),
            "by_side": dict(Counter(e["side"] for e in selected)),
            "scenarios": scenario_results,
            "criteria": criteria,
            "panel_filter_pass": all(criteria.values()),
        }
    mse = {
        name: sum((getattr(p, field) - p.observation.label) ** 2 for p in predictions)
        / len(predictions)
        if predictions
        else None
        for name, field in (
            ("ridge", "predicted"),
            ("intercept_control", "intercept_only"),
        )
    }
    if (
        source_version(Path.cwd())[0] != code_version
        or file_sha256(Path(__file__)) != script_sha
    ):
        raise ValueError("code changed during calculation")
    args.output.mkdir(parents=True, exist_ok=False)
    write_json(args.output / "quality.json", quality)
    write_json(args.output / "models.json", [asdict(f) for f in fits])
    write_json(args.output / "predictions.json", [asdict(p) for p in predictions])
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
            "run_id": f"conditional-model-20260907-v1-{args.panel}",
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
            "training_and_evaluation_rows": len(observations),
            "evaluated_rows": len(predictions),
            "monthly_fits": len(fits),
            "normalized_mse_all_predictions": mse,
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
            {
                "panel": args.panel,
                "fits": len(fits),
                "predictions": len(predictions),
                "mse": mse,
                "results": results,
            },
            default=str,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
