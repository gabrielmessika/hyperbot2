"""Fixed half-budget sleeves with one cash account and global risk shutdown."""

from __future__ import annotations

import argparse
import json
from decimal import Decimal
from pathlib import Path

from investigate_breakout_extension import DATA, START
from investigate_funding_normalization import END, OLD, ROOT, load
from investigate_funding_transfer import DATA as TRANSFER

from hyperbot2.research.artifacts import (
    checked_input,
    file_sha256,
    source_version,
    write_json,
)
from hyperbot2.research.compression_breakout import compression_entries
from hyperbot2.research.funding_portfolio import AllocationSleeve, simulate_portfolio
from hyperbot2.research.weekly_relative import weekly_entries

D = Decimal
REPORT = Path("reports/diversification_2026-09-07")
SCENARIOS = ("base", "cost_stress", "delay", "funding_adverse", "zero_cost")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    checked_input(REPORT / "portfolio_registration.json")
    reg = json.loads((REPORT / "portfolio_registration.json").read_text())
    protocol = file_sha256(REPORT / "PORTFOLIO_PROTOCOL.md")
    selection = Path("reports/funding_transfer_2026-09-07/selection.json")
    if reg["protocol_sha256"] != protocol or reg["universe_sha256"] != checked_input(
        selection
    ):
        raise ValueError("registered shared-account study changed")
    coins = json.loads(selection.read_text())["eligible"]
    if len(coins) != 18:
        raise ValueError("registered universe changed")
    folders = (
        [DATA / "history"]
        + [TRANSFER / "history" / f"batch-{b}" for b in range(2)]
        + [ROOT / "history", ROOT / "replication_history", OLD / "history"]
    )
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
    decimals = {c: m["szDecimals"] for c, m in meta.items()}
    breakout = {
        c: compression_entries(bars[c], require_compression=False) for c in coins
    }
    weekly, selections = weekly_entries(
        {c: [b.close for b in rows] for c, rows in bars.items()},
        [b.time for b in bars[coins[0]]],
    )
    args.output.mkdir(parents=True, exist_ok=False)
    baseline_checks = []
    for scenario in SCENARIOS:
        for infra in (D(0), D(20)):
            old = DATA / "dd30_run1" / f"continuous-{scenario}-infra-{infra}.json"
            sha = checked_input(old)
            expected = json.loads(old.read_text())
            del expected["summary"]["fold"]
            check = simulate_portfolio(
                bars,
                payments,
                breakout,
                decimals,
                gross_cap=D("0.5"),
                scenario=scenario,
                monthly_infra=infra,
                holding_hours=24,
                drawdown_limit=D("0.3"),
            )
            if json.loads(json.dumps(check, default=str)) != expected:
                raise ValueError(f"legacy default economic regression: {old}")
            baseline_checks.append(
                {"path": str(old), "sha256": sha, "economic_match": True}
            )
    write_json(args.output / "baseline_checks.json", baseline_checks)
    mappings = {f"{s}::{c}": (s, c) for s in ("breakout", "weekly") for c in coins}
    virtual_bars = {key: bars[c] for key, (_, c) in mappings.items()}
    virtual_payments = {key: payments[c] for key, (_, c) in mappings.items()}
    virtual_decimals = {key: decimals[c] for key, (_, c) in mappings.items()}
    entries = {
        key: (breakout if s == "breakout" else weekly)[c]
        for key, (s, c) in mappings.items()
    }
    asset_sleeves = {key: s for key, (s, _) in mappings.items()}
    sleeves = {
        "breakout": AllocationSleeve(D("0.5"), 24),
        "weekly": AllocationSleeve(D("0.5"), 168),
    }
    quality["virtual_to_native"] = mappings
    quality["weekly_dates"] = len(selections)
    quality["signals"] = {
        key: sum(bool(s) for s in rows) for key, rows in entries.items()
    }
    write_json(args.output / "quality.json", quality)
    results = []
    for cap in (D("0.5"), D(1), D("1.5"), D(2)):
        for scenario in SCENARIOS:
            for infra in (D(0), D(20)):
                result = simulate_portfolio(
                    virtual_bars,
                    virtual_payments,
                    entries,
                    virtual_decimals,
                    gross_cap=cap,
                    scenario=scenario,
                    monthly_infra=infra,
                    drawdown_limit=D("0.3"),
                    allocation_sleeves=sleeves,
                    asset_sleeves=asset_sleeves,
                )
                result["summary"]["sleeve_contributions_usd"] = {
                    s: sum(
                        (
                            c["net_pnl_usd"]
                            for c in result["cycles"]
                            if c["coin"].startswith(s + "::")
                        ),
                        D(0),
                    )
                    for s in sleeves
                }
                name = f"shared-cap-{cap}-{scenario}-infra-{infra}.json"
                sha = write_json(args.output / name, result)
                results.append({"artifact": name, "sha256": sha, **result["summary"]})
                if scenario == "base" and infra == 0:
                    s = result["summary"]
                    print(
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
    for cap in (D("0.5"), D(1), D("1.5"), D(2)):
        for infra in (D(0), D(20)):
            required = [
                r
                for r in results
                if r["gross_cap_at_entry"] == cap
                and r["monthly_infra"] == infra
                and r["scenario"] != "zero_cost"
            ]
            if len(required) == 4 and all(
                r["net_total_usd"] > 0
                and r["max_ohlc_drawdown_envelope"] <= D("0.3")
                and not r["margin_observed_breach"]
                and r["minimum_margin_envelope_buffer_usd"] >= 0
                for r in required
            ):
                candidates.append({"gross_cap": cap, "monthly_infra": infra})
    write_json(
        args.output / "summary.json",
        {
            "run_id": "shared-portfolio-20260907-v1",
            "protocol_sha256": protocol,
            "code_version": source_version(Path.cwd())[0],
            "script_sha256": file_sha256(Path(__file__)),
            "results": results,
            "candidates": candidates,
            "decision": "SHARED_PORTFOLIO_SCREEN_PASSED_UNQUALIFIED"
            if candidates
            else "SHARED_PORTFOLIO_SCREEN_FAILED",
            "live_enabled": False,
            "promotion_authorized": False,
            "network_data_calls": 0,
            "net_execution_qualified": False,
        },
    )


if __name__ == "__main__":
    main()
