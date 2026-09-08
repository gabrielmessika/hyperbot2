"""Fixed prior-period transfer and passive controls, with explicit venue labels."""

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
from hyperbot2.research.binance_archives import load_archives
from hyperbot2.research.compression_breakout import compression_entries
from hyperbot2.research.funding_portfolio import AllocationSleeve
from hyperbot2.research.native_portfolio import simulate_native_portfolio
from hyperbot2.research.weekly_relative import weekly_entries

D = Decimal
REPORT = Path("reports/prior_transfer_2026-09-07")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--panel",
        choices=("original_native", "matched_native", "prior_transfer"),
        required=True,
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    checked_input(REPORT / "economic_registration.json")
    reg = json.loads((REPORT / "economic_registration.json").read_text())
    if reg["protocol_sha256"] != file_sha256(REPORT / "ECONOMIC_PROTOCOL.md") or reg[
        "qualification_sha256"
    ] != checked_input(REPORT / "qualification.json"):
        raise ValueError("registered study changed")
    q = json.loads((REPORT / "qualification.json").read_text())
    matched = [r["coin"] for r in q["selected_by_metadata"]]
    selection = Path("reports/funding_transfer_2026-09-07/selection.json")
    checked_input(selection)
    coins = (
        json.loads(selection.read_text())["eligible"]
        if args.panel == "original_native"
        else matched
    )
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
    meta_path = OLD / "meta.json"
    quality["sources"][str(meta_path)] = checked_input(meta_path)
    meta = {
        m["name"]: m
        for m in json.loads(meta_path.read_text())["response"][0]["universe"]
        if m["name"] in coins
    }
    if set(meta) != set(coins) or any(
        m.get("onlyIsolated", False)
        or m.get("isDelisted", False)
        or m["maxLeverage"] < 3
        for m in meta.values()
    ):
        raise ValueError("reference margin assumptions fail")
    decimals = {c: m["szDecimals"] for c, m in meta.items()}
    breakout = {
        c: compression_entries(bars[c], require_compression=False) for c in coins
    }
    times = [b.time for b in bars[coins[0]]]
    weekly, _ = weekly_entries(
        {c: [b.close for b in rows] for c, rows in bars.items()}, times
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
    baseline_checks = []
    cache = {}
    if args.panel == "original_native":
        for dd in (D("0.2"), D("0.3")):
            for scenario in SCENARIOS:
                for infra in (D(0), D(20)):
                    source = (
                        Path("data/native_execution_2026-09-07/run1")
                        / f"native-dd-{dd}-{scenario}-infra-{infra}.json"
                    )
                    sha = checked_input(source)
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
                    if json.loads(json.dumps(result, default=str)) != json.loads(
                        source.read_text()
                    ):
                        raise ValueError(
                            f"native default economic regression: {source}"
                        )
                    if dd == D("0.3"):
                        cache[scenario, infra] = result
                    baseline_checks.append(
                        {"source": str(source), "sha256": sha, "economic_match": True}
                    )
        write_json(args.output / "baseline_checks.json", baseline_checks)
    write_json(args.output / "quality.json", quality)
    results = []
    for strategy in ("candidate", "passive_0.5", "passive_1.5"):
        for scenario in SCENARIOS:
            for infra in (D(0), D(20)):
                if strategy == "candidate":
                    result = cache.get((scenario, infra)) or simulate_native_portfolio(
                        bars,
                        payments,
                        entries,
                        decimals,
                        mapping,
                        names,
                        sleeves,
                        scenario=scenario,
                        monthly_infra=infra,
                        drawdown_limit=D("0.3"),
                    )
                else:
                    passive = {
                        c: tuple(int(i == 193) for i in range(len(times)))
                        for c in coins
                    }
                    horizon = len(times) - 1 - 193 - int(scenario == "delay")
                    result = simulate_native_portfolio(
                        bars,
                        payments,
                        passive,
                        decimals,
                        {c: c for c in coins},
                        dict.fromkeys(coins, "passive"),
                        {"passive": AllocationSleeve(D(1), horizon)},
                        scenario=scenario,
                        monthly_infra=infra,
                        drawdown_limit=D("0.3"),
                        gross_cap=D(strategy.split("_")[1]),
                    )
                name = f"{strategy}-{scenario}-infra-{infra}.json"
                sha = write_json(args.output / name, result)
                results.append(
                    {
                        "strategy": strategy,
                        "artifact": name,
                        "sha256": sha,
                        **result["summary"],
                    }
                )
                if infra == 0:
                    s = result["summary"]
                    print(
                        args.panel,
                        strategy,
                        scenario,
                        "net",
                        round(s["net_total_usd"], 2),
                        "bound %",
                        round(s["max_ohlc_drawdown_envelope"] * 100, 2),
                        "halt",
                        s["halted"],
                        flush=True,
                    )
    candidates = []
    for strategy in ("candidate", "passive_0.5", "passive_1.5"):
        for infra in (D(0), D(20)):
            paid = [
                r
                for r in results
                if r["strategy"] == strategy
                and r["monthly_infra"] == infra
                and r["scenario"] != "zero_cost"
            ]
            if len(paid) == 4 and all(
                r["net_total_usd"] > 0
                and r["max_ohlc_drawdown_envelope"] <= D("0.3")
                and r["terminal_flat"]
                and not r["margin_observed_breach"]
                and r["minimum_margin_envelope_buffer_usd"] >= 0
                for r in paid
            ):
                candidates.append({"strategy": strategy, "monthly_infra": infra})
    write_json(
        args.output / "summary.json",
        {
            "run_id": f"prior-transfer-20260907-v1-{args.panel}",
            "panel": args.panel,
            "coins": coins,
            "code_version": source_version(Path.cwd())[0],
            "script_sha256": file_sha256(Path(__file__)),
            "protocol_sha256": reg["protocol_sha256"],
            "results": results,
            "exploratory_screen_passes": candidates,
            "historical_venue": quality["source_venue"],
            "hypothetical_execution_constraints": (
                "Hyperliquid reference lots/ticks/fees and fixed 2x margin"
            ),
            "native_fill_validation": False,
            "promotion_authorized": False,
            "live_enabled": False,
            "decision": "TRANSFER_AND_PASSIVE_REVIEW_REQUIRED",
        },
    )


if __name__ == "__main__":
    main()
