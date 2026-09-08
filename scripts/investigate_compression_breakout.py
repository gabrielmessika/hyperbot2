"""Registered compression portfolio and matched no-compression control."""

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
from hyperbot2.research.compression_breakout import compression_entries
from hyperbot2.research.funding_portfolio import simulate_portfolio

D = Decimal
REPORT = Path("reports/compression_breakout_2026-09-07")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    checked_input(REPORT / "registration.json")
    registration = json.loads((REPORT / "registration.json").read_text())
    protocol = file_sha256(REPORT / "PROTOCOL.md")
    selection = Path("reports/funding_transfer_2026-09-07/selection.json")
    if registration["protocol_sha256"] != protocol or registration[
        "universe_sha256"
    ] != checked_input(selection):
        raise ValueError("registered compression study changed")
    coins = json.loads(selection.read_text())["eligible"]
    if len(coins) != 18:
        raise ValueError("registered universe changed")
    folders = [TRANSFER / "history" / f"batch-{b}" for b in range(2)] + [
        ROOT / "history",
        ROOT / "replication_history",
        OLD / "history",
    ]
    bars, payments, _, quality = load(folders, coins, START, END)
    if any(q["zero_volume_hours"] for q in quality["assets"].values()):
        raise ValueError("zero-volume candle in registered complete universe")
    meta_path = OLD / "meta.json"
    quality["sources"][str(meta_path)] = checked_input(meta_path)
    quality["sources"][str(selection)] = checked_input(selection)
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
    quality["native_metadata"] = meta
    args.output.mkdir(parents=True, exist_ok=False)
    write_json(args.output / "quality.json", quality)
    results, counts = [], {}
    for strategy, required in (
        ("compression", True),
        ("no_compression_control", False),
    ):
        entries = {
            c: compression_entries(bars[c], require_compression=required) for c in coins
        }
        counts[strategy] = {c: sum(bool(s) for s in entries[c]) for c in coins}
        write_json(
            args.output / f"{strategy}-signals.json",
            {
                c: [
                    {"index": i, "entry_ms": bars[c][i].time + 60_000, "side": s}
                    for i, s in enumerate(rows)
                    if s
                ]
                for c, rows in entries.items()
            },
        )
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
                        entries,
                        decimals,
                        gross_cap=cap,
                        scenario=scenario,
                        monthly_infra=infra,
                        holding_hours=24,
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
            required_results = [
                r
                for r in results
                if r["strategy"] == "compression"
                and r["gross_cap_at_entry"] == cap
                and r["monthly_infra"] == infra
                and r["scenario"] != "zero_cost"
            ]
            if len(required_results) == 4 and all(
                r["net_total_usd"] > 0
                and r["max_ohlc_drawdown_envelope"] <= D("0.2")
                and not r["margin_observed_breach"]
                and r["minimum_margin_envelope_buffer_usd"] >= 0
                for r in required_results
            ):
                candidates.append({"gross_cap": cap, "monthly_infra": infra})
    write_json(
        args.output / "summary.json",
        {
            "run_id": "compression-breakout-20260907-v1",
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
            "signal_counts": counts,
            "candidates": candidates,
            "decision": "COMPRESSION_SCREEN_PASSED_UNQUALIFIED"
            if candidates
            else "HYPOTHESIS_NOT_CONFIRMED",
            "live_enabled": False,
            "promotion_authorized": False,
            "network_data_calls": 0,
            "limits": [
                "current universe and previously examined period",
                "hourly fill/oracle/mark proxies",
                "control is descriptive and cannot be promoted opportunistically",
                "180 days do not validate twelve months",
            ],
        },
    )


if __name__ == "__main__":
    main()
