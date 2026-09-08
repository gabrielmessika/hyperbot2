"""Registered weekly long/short portfolio using the existing native panel."""

from __future__ import annotations

import argparse
import json
from decimal import Decimal
from pathlib import Path

from investigate_funding_normalization import END, OLD, ROOT, load
from investigate_funding_transfer import DATA as TRANSFER
from investigate_funding_transfer import START

from hyperbot2.research.artifacts import (
    checked_input,
    file_sha256,
    source_version,
    write_json,
)
from hyperbot2.research.funding_portfolio import simulate_portfolio
from hyperbot2.research.weekly_relative import weekly_entries

D = Decimal
REPORT = Path("reports/weekly_relative_2026-09-07")


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
        raise ValueError("registered weekly study changed")
    coins = json.loads(selection.read_text())["eligible"]
    if len(coins) != 18:
        raise ValueError("registered universe changed")
    folders = [TRANSFER / "history" / f"batch-{b}" for b in range(2)] + [
        ROOT / "history",
        ROOT / "replication_history",
        OLD / "history",
    ]
    bars, payments, _, quality = load(folders, coins, START, END)
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
        raise ValueError("registered margin assumptions fail")
    decimals = {c: m["szDecimals"] for c, m in meta.items()}
    times = [b.time for b in bars[coins[0]]]
    entries, selections = weekly_entries(
        {c: [b.close for b in rows] for c, rows in bars.items()}, times
    )
    if not selections:
        raise ValueError("no eligible weekly dates")
    quality["native_metadata"] = meta
    quality["weekly_dates"] = len(selections)
    quality["sources"][str(selection)] = checked_input(selection)
    write_json(args.output / "quality.json", quality)
    write_json(args.output / "selections.json", selections)
    held = {
        c: tuple(int(i == selections[0]["index"]) for i in range(len(times)))
        for c in coins
    }
    results = []
    for strategy, signals, horizon in (
        ("weekly_relative", entries, 168),
        ("hold_equal", held, None),
    ):
        for cap in (D("0.5"), D(1), D("1.5")):
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
                        signals,
                        decimals,
                        gross_cap=cap,
                        scenario=scenario,
                        monthly_infra=infra,
                        holding_hours=horizon,
                    )
                    result["summary"]["strategy"] = strategy
                    name = f"{strategy}-cap-{cap}-{scenario}-infra-{infra}.json"
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
    for cap in (D("0.5"), D(1), D("1.5")):
        for infra in (D(0), D(20)):
            required = [
                r
                for r in results
                if r["strategy"] == "weekly_relative"
                and r["gross_cap_at_entry"] == cap
                and r["monthly_infra"] == infra
                and r["scenario"] != "zero_cost"
            ]
            if len(required) == 4 and all(
                r["net_total_usd"] > 0
                and r["max_ohlc_drawdown_envelope"] <= D("0.2")
                and not r["margin_observed_breach"]
                and r["minimum_margin_envelope_buffer_usd"] >= 0
                for r in required
            ):
                candidates.append(
                    {
                        "gross_cap": cap,
                        "monthly_infra": infra,
                        "base_monthly_compound": next(
                            r["equivalent_monthly_compound"]
                            for r in required
                            if r["scenario"] == "base"
                        ),
                    }
                )
    write_json(
        args.output / "summary.json",
        {
            "run_id": "weekly-relative-20260907-v1",
            "protocol_sha256": protocol,
            "code_version": source_version(Path.cwd())[0],
            "scripts": {
                str(p): file_sha256(p)
                for p in (
                    Path(__file__),
                    Path("scripts/investigate_funding_normalization.py"),
                )
            },
            "results": results,
            "candidates": candidates,
            "decision": "WEEKLY_RESEARCH_CANDIDATE_UNQUALIFIED"
            if candidates
            else "HYPOTHESIS_NOT_CONFIRMED",
            "live_enabled": False,
            "promotion_authorized": False,
            "network_data_calls": 0,
            "limits": [
                "selected current universe and previously consulted period",
                "equal notionals do not imply beta neutrality",
                "full weekly close/reopen fees even for unchanged names",
                "hourly assumed fills and oracle/mark proxies",
                "180 days do not validate twelve months",
            ],
        },
    )


if __name__ == "__main__":
    main()
