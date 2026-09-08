"""Explicit user-authorized 20/30 percent research drawdown comparison."""

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
REPORT = Path("reports/breakout_risk30_2026-09-07")
BASELINE = Path("data/compression_breakout_2026-09-07/run1")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    checked_input(REPORT / "registration.json")
    reg = json.loads((REPORT / "registration.json").read_text())
    protocol = file_sha256(REPORT / "PROTOCOL.md")
    selection = Path("reports/funding_transfer_2026-09-07/selection.json")
    if reg["protocol_sha256"] != protocol or reg["universe_sha256"] != checked_input(
        selection
    ):
        raise ValueError("registered drawdown comparison changed")
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
        raise ValueError("zero-volume input")
    meta_path = OLD / "meta.json"
    quality["sources"][str(meta_path)] = checked_input(meta_path)
    meta = {
        m["name"]: m
        for m in json.loads(meta_path.read_text())["response"][0]["universe"]
        if m["name"] in coins
    }
    if len(meta) != 18 or any(
        m.get("onlyIsolated", False)
        or m.get("isDelisted", False)
        or m["maxLeverage"] < 3
        for m in meta.values()
    ):
        raise ValueError("registered margin assumptions fail")
    entries = {
        c: compression_entries(bars[c], require_compression=False) for c in coins
    }
    decimals = {c: m["szDecimals"] for c, m in meta.items()}
    args.output.mkdir(parents=True, exist_ok=False)
    write_json(args.output / "quality.json", quality)
    results, baseline_checks = [], []
    for limit in (D("0.2"), D("0.3")):
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
                        drawdown_limit=limit,
                    )
                    if limit == D("0.2"):
                        suffix = f"cap-{cap}-{scenario}-infra-{infra}.json"
                        old = BASELINE / f"no_compression_control-{suffix}"
                        sha = checked_input(old)
                        expected = json.loads(old.read_text(), parse_float=D)
                        del expected["summary"]["strategy"]
                        # Artifacts encode Decimal as strings; normalize with the
                        # artifact serializer before comparing every economic field.
                        observed = json.loads(json.dumps(result, default=str))
                        del observed["summary"]["drawdown_limit"]
                        if observed != expected:
                            raise ValueError(f"20 percent baseline changed: {old}")
                        baseline_checks.append(
                            {"path": str(old), "sha256": sha, "economic_match": True}
                        )
                    name = f"dd-{limit}-cap-{cap}-{scenario}-infra-{infra}.json"
                    sha = write_json(args.output / name, result)
                    results.append(
                        {"artifact": name, "sha256": sha, **result["summary"]}
                    )
                    if scenario == "base" and infra == 0:
                        s = result["summary"]
                        print(
                            "DD limit",
                            limit,
                            "cap",
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
    for limit in (D("0.2"), D("0.3")):
        for cap in (D("0.5"), D(1), D("1.5")):
            for infra in (D(0), D(20)):
                required = [
                    r
                    for r in results
                    if r["drawdown_limit"] == limit
                    and r["gross_cap_at_entry"] == cap
                    and r["monthly_infra"] == infra
                    and r["scenario"] != "zero_cost"
                ]
                if len(required) == 4 and all(
                    r["net_total_usd"] > 0
                    and r["max_ohlc_drawdown_envelope"] <= limit
                    and not r["margin_observed_breach"]
                    and r["minimum_margin_envelope_buffer_usd"] >= 0
                    for r in required
                ):
                    candidates.append(
                        {
                            "drawdown_limit": limit,
                            "gross_cap": cap,
                            "monthly_infra": infra,
                        }
                    )
    write_json(args.output / "baseline_checks.json", baseline_checks)
    write_json(
        args.output / "summary.json",
        {
            "run_id": "breakout-risk30-20260907-v1",
            "protocol_sha256": protocol,
            "code_version": source_version(Path.cwd())[0],
            "script_sha256": file_sha256(Path(__file__)),
            "results": results,
            "candidates": candidates,
            "decision": "RISK_COMPARISON_UNQUALIFIED",
            "live_enabled": False,
            "promotion_authorized": False,
            "network_data_calls": 0,
        },
    )


if __name__ == "__main__":
    main()
