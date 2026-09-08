"""Native inventory replay of the fixed shared strategy using existing data."""

from __future__ import annotations

import argparse
import json
from decimal import Decimal
from pathlib import Path

from investigate_breakout_extension import DATA, START
from investigate_funding_normalization import END, OLD, ROOT, load
from investigate_funding_transfer import DATA as TRANSFER
from investigate_shared_portfolio import SCENARIOS

from hyperbot2.research.artifacts import (
    checked_input,
    file_sha256,
    source_version,
    write_json,
)
from hyperbot2.research.compression_breakout import compression_entries
from hyperbot2.research.funding_portfolio import AllocationSleeve, simulate_portfolio
from hyperbot2.research.native_portfolio import simulate_native_portfolio
from hyperbot2.research.weekly_relative import weekly_entries

D = Decimal
REPORT = Path("reports/native_execution_2026-09-07")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    checked_input(REPORT / "registration.json")
    reg = json.loads((REPORT / "registration.json").read_text())
    selection = Path("reports/funding_transfer_2026-09-07/selection.json")
    if reg["protocol_sha256"] != file_sha256(REPORT / "PROTOCOL.md") or reg[
        "universe_sha256"
    ] != checked_input(selection):
        raise ValueError("registered study changed")
    coins = json.loads(selection.read_text())["eligible"]
    folders = (
        [DATA / "history"]
        + [TRANSFER / "history" / f"batch-{b}" for b in range(2)]
        + [ROOT / "history", ROOT / "replication_history", OLD / "history"]
    )
    bars, payments, _, quality = load(folders, coins, START, END)
    if len(coins) != 18 or any(
        q["zero_volume_hours"] for q in quality["assets"].values()
    ):
        raise ValueError("registered data quality failed")
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
    mapping = {f"{s}::{c}": c for s in ("breakout", "weekly") for c in coins}
    names = {v: v.split("::")[0] for v in mapping}
    entries = {
        v: (breakout if names[v] == "breakout" else weekly)[c]
        for v, c in mapping.items()
    }
    sleeves = {
        "breakout": AllocationSleeve(D("0.5"), 24),
        "weekly": AllocationSleeve(D("0.5"), 168),
    }
    args.output.mkdir(parents=True, exist_ok=False)
    checks = []
    for scenario in SCENARIOS:
        for infra in (D(0), D(20)):
            old_path = (
                Path("data/diversification_2026-09-07/portfolio_run1")
                / f"shared-cap-1.5-{scenario}-infra-{infra}.json"
            )
            sha = checked_input(old_path)
            old = json.loads(old_path.read_text())
            current = simulate_portfolio(
                {v: bars[c] for v, c in mapping.items()},
                {v: payments[c] for v, c in mapping.items()},
                entries,
                {v: decimals[c] for v, c in mapping.items()},
                gross_cap=D("1.5"),
                scenario=scenario,
                monthly_infra=infra,
                drawdown_limit=D("0.3"),
                allocation_sleeves=sleeves,
                asset_sleeves=names,
            )
            del old["summary"]["sleeve_contributions_usd"]
            if json.loads(json.dumps(current, default=str)) != old:
                raise ValueError(
                    f"shared allocation helper changed baseline: {old_path}"
                )
            checks.append(
                {"source": str(old_path), "sha256": sha, "economic_match": True}
            )
    write_json(args.output / "baseline_checks.json", checks)
    quality["virtual_to_native"] = mapping
    quality["weekly_dates"] = len(selections)
    write_json(args.output / "quality.json", quality)
    results = []
    for dd in (D("0.2"), D("0.3")):
        for scenario in SCENARIOS:
            for infra in (D(0), D(20)):
                result = simulate_native_portfolio(
                    bars,
                    payments,
                    entries,
                    decimals,
                    mapping,
                    names,
                    sleeves,
                    scenario=scenario,
                    monthly_infra=infra,
                    drawdown_limit=dd,
                )
                name = f"native-dd-{dd}-{scenario}-infra-{infra}.json"
                sha = write_json(args.output / name, result)
                results.append({"artifact": name, "sha256": sha, **result["summary"]})
                s = result["summary"]
                print(
                    dd,
                    scenario,
                    infra,
                    "net",
                    round(s["net_total_usd"], 2),
                    "bound %",
                    round(s["max_ohlc_drawdown_envelope"] * 100, 2),
                    "flat",
                    s["terminal_flat"],
                    "halt",
                    s["halted"],
                    flush=True,
                )
    candidates = []
    for dd in (D("0.2"), D("0.3")):
        for infra in (D(0), D(20)):
            required = [
                r
                for r in results
                if r["drawdown_limit"] == dd
                and r["monthly_infra"] == infra
                and r["scenario"] != "zero_cost"
            ]
            if len(required) == 4 and all(
                r["net_total_usd"] > 0
                and r["max_ohlc_drawdown_envelope"] <= dd
                and r["terminal_flat"]
                and not r["margin_observed_breach"]
                and r["minimum_margin_envelope_buffer_usd"] >= 0
                for r in required
            ):
                candidates.append({"drawdown_limit": dd, "monthly_infra": infra})
    write_json(
        args.output / "summary.json",
        {
            "run_id": "native-execution-20260907-v1",
            "protocol_sha256": reg["protocol_sha256"],
            "code_version": source_version(Path.cwd())[0],
            "script_sha256": file_sha256(Path(__file__)),
            "results": results,
            "candidates": candidates,
            "decision": "NATIVE_EXECUTION_RESEARCH_CANDIDATE_UNQUALIFIED"
            if candidates
            else "NATIVE_EXECUTION_SCREEN_FAILED",
            "network_data_calls": 0,
            "live_enabled": False,
            "promotion_authorized": False,
            "fill_liquidity_qualified": False,
            "independent_validation": False,
        },
    )


if __name__ == "__main__":
    main()
