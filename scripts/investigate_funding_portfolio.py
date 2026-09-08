"""Registered 52-day portfolio comparison, entirely from local native archives."""

from __future__ import annotations

import argparse
import json
from decimal import Decimal
from pathlib import Path

from investigate_funding_normalization import END, OLD, ROOT, load, registered
from replicate_funding_normalization import START

from hyperbot2.research.artifacts import (
    checked_input,
    file_sha256,
    source_version,
    write_json,
)
from hyperbot2.research.funding_portfolio import funding_entries, simulate_portfolio

D = Decimal
REPORT = Path("reports/funding_portfolio_2026-09-07")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reduced-risk", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    checked_input(REPORT / "registration.json")
    protocol = file_sha256(REPORT / "PROTOCOL.md")
    if (
        json.loads((REPORT / "registration.json").read_text())["protocol_sha256"]
        != protocol
    ):
        raise ValueError("registered protocol changed")
    adaptation = None
    caps = (D("0.5"), D(1), D("1.5"))
    if args.reduced_risk:
        checked_input(REPORT / "risk_registration.json")
        adaptation = json.loads((REPORT / "risk_registration.json").read_text())
        if adaptation["adaptation_sha256"] != file_sha256(
            REPORT / "RISK_ADAPTATION.md"
        ):
            raise ValueError("registered risk adaptation changed")
        initial = Path("data/funding_portfolio_2026-09-07/run1/summary.json")
        if adaptation["initial_summary_sha256"] != checked_input(initial):
            raise ValueError("initial evidence changed")
        caps = (D("0.4"),)
    _, coins = registered()
    bars, payments, rates, quality = load(
        [
            OLD / "cashcat_hedge",
            OLD / "history",
            ROOT / "history",
            ROOT / "replication_history",
        ],
        coins,
        START,
        END,
    )
    meta_path = OLD / "meta.json"
    quality["sources"][str(meta_path)] = checked_input(meta_path)
    meta = {
        m["name"]: m
        for m in json.loads(meta_path.read_text())["response"][0]["universe"]
        if m["name"] in coins
    }
    if len(meta) != len(coins) or any(
        m.get("onlyIsolated", False)
        or m.get("isDelisted", False)
        or m["maxLeverage"] < 3
        for m in meta.values()
    ):
        raise ValueError("cross-margin research assumptions do not match metadata")
    decimals = {c: m["szDecimals"] for c, m in meta.items()}
    signals = {c: funding_entries(rates[c]) for c in coins}
    quality["native_metadata"] = meta
    quality["signal_counts"] = {c: sum(bool(s) for s in signals[c]) for c in coins}
    quality["hours"] = len(bars[coins[0]])
    quality["start_ms"], quality["end_ms_exclusive"] = START, END
    write_json(args.output / "quality.json", quality)
    results = []
    for strategy in ("funding72", "grid_long", "hold_equal", "hold_cashcat"):
        entries = {}
        for c in coins:
            if strategy == "funding72":
                entries[c] = signals[c]
                continue
            rows = [0] * quality["hours"]
            if strategy == "grid_long":
                for i in range(12, len(rows) - 73, 73):
                    rows[i] = 1
            elif strategy == "hold_equal" or c == "CASHCAT":
                rows[12] = 1
            entries[c] = tuple(rows)
        for cap in caps:
            for scenario in (
                "base",
                "cost_stress",
                "delay",
                "funding_adverse",
                "zero_cost",
            ):
                for infra in (D(0), D(20)):
                    result = simulate_portfolio(
                        bars,
                        payments,
                        entries,
                        decimals,
                        gross_cap=cap,
                        scenario=scenario,
                        monthly_infra=infra,
                        holding_hours=None if strategy.startswith("hold_") else 72,
                    )
                    name = f"{strategy}-cap-{cap}-{scenario}-infra-{infra}.json"
                    result["summary"]["strategy"] = strategy
                    sha = write_json(args.output / name, result)
                    results.append(
                        {"artifact": name, "sha256": sha, **result["summary"]}
                    )
                    if scenario == "base" and infra == 0:
                        s = result["summary"]
                        print(
                            strategy,
                            cap,
                            "net",
                            round(s["net_total_usd"], 2),
                            "monthly %",
                            round(s["equivalent_monthly_compound"] * 100, 2),
                            "DD %",
                            round(s["max_hourly_drawdown"] * 100, 2),
                            "bound %",
                            round(s["max_ohlc_drawdown_envelope"] * 100, 2),
                            "trades",
                            s["round_trips"],
                            flush=True,
                        )
    candidates = []
    for cap in caps:
        for infra in (D(0), D(20)):
            required = [
                r
                for r in results
                if r["strategy"] == "funding72"
                and r["gross_cap_at_entry"] == cap
                and r["monthly_infra"] == infra
                and r["scenario"] != "zero_cost"
            ]
            passes = len(required) == 4 and all(
                r["net_total_usd"] > 0
                and r["max_ohlc_drawdown_envelope"] <= D("0.2")
                and not r["margin_observed_breach"]
                and r["minimum_margin_envelope_buffer_usd"] >= 0
                for r in required
            )
            if passes:
                base = next(r for r in required if r["scenario"] == "base")
                candidates.append(
                    {
                        "gross_cap": cap,
                        "monthly_infra": infra,
                        "base_monthly_compound": base["equivalent_monthly_compound"],
                        "target_15pct_reached_in_sample": base[
                            "equivalent_monthly_compound"
                        ]
                        >= D("0.15"),
                    }
                )
    write_json(
        args.output / "summary.json",
        {
            "run_id": "funding-portfolio-20260907-v1",
            "protocol_sha256": protocol,
            "risk_adaptation": adaptation,
            "code_version": source_version(Path.cwd())[0],
            "scripts": {
                str(p): file_sha256(p)
                for p in (
                    Path(__file__),
                    Path("scripts/investigate_funding_normalization.py"),
                    Path("scripts/replicate_funding_normalization.py"),
                )
            },
            "results": results,
            "candidates": candidates,
            "decision": "SHORT_SAMPLE_PORTFOLIO_UNQUALIFIED"
            if candidates
            else "PORTFOLIO_SCREEN_NOT_PASSED",
            "live_enabled": False,
            "promotion_authorized": False,
            "data_cost_usd": 0,
            "network_data_calls": 0,
            "limitations": [
                "52 days and selected universe, not independent holdout",
                "hourly opens assumed at +60s, no executed quotes",
                "funding oracle and liquidation marks unqualified",
                "current margin metadata only, conservative 20% stress",
                "OHLC envelope may overstate intrahour risk",
            ],
        },
    )


if __name__ == "__main__":
    main()
