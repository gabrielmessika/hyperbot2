"""Fixed slow direction/inverse-volatility research across existing panels."""

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
from hyperbot2.research.funding_portfolio import AllocationSleeve
from hyperbot2.research.native_portfolio import simulate_native_portfolio
from hyperbot2.research.slow_trend import slow_entries

D = Decimal
REPORT = Path("reports/slow_trend_2026-09-07")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--panel",
        choices=("original_native", "matched_native", "prior_transfer"),
        required=True,
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    checked_input(REPORT / "registration.json")
    reg = json.loads((REPORT / "registration.json").read_text())
    if reg["protocol_sha256"] != file_sha256(REPORT / "PROTOCOL.md"):
        raise ValueError("registered protocol changed")
    selection = Path("reports/prior_transfer_2026-09-07/qualification.json")
    if reg["qualification_sha256"] != checked_input(selection):
        raise ValueError("registered cohort changed")
    q = json.loads(selection.read_text())
    coins = [r["coin"] for r in q["selected_by_metadata"]]
    if args.panel == "original_native":
        p = Path("reports/funding_transfer_2026-09-07/selection.json")
        checked_input(p)
        coins = json.loads(p.read_text())["eligible"]
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
    times = [b.time for b in bars[coins[0]]]
    signals, weights, records = slow_entries(
        {c: [b.close for b in rows] for c, rows in bars.items()}, times
    )
    names = dict.fromkeys(coins, "trend")
    sleeves = {"trend": AllocationSleeve(D(1), 168)}
    args.output.mkdir(parents=True, exist_ok=False)
    # Preserve old default allocation on an exact passive reference for all costs.
    old_folder = {
        "original_native": "original_final",
        "matched_native": "matched_run1",
        "prior_transfer": "prior_run1",
    }[args.panel]
    checks = []
    for scenario in SCENARIOS:
        for infra in (D(0), D(20)):
            p = (
                Path("data/prior_transfer_2026-09-07")
                / old_folder
                / f"passive_0.5-{scenario}-infra-{infra}.json"
            )
            sha = checked_input(p)
            passive = {
                c: tuple(int(i == 193) for i in range(len(times))) for c in coins
            }
            result = simulate_native_portfolio(
                bars,
                payments,
                passive,
                decimals,
                {c: c for c in coins},
                names,
                {
                    "trend": AllocationSleeve(
                        D(1), len(times) - 1 - 193 - int(scenario == "delay")
                    )
                },
                scenario=scenario,
                monthly_infra=infra,
                drawdown_limit=D("0.3"),
                gross_cap=D("0.5"),
            )
            if json.loads(json.dumps(result, default=str)) != json.loads(p.read_text()):
                raise ValueError("default native allocation regression")
            checks.append(
                {"source": str(p), "sha256": sha, "full_economic_match": True}
            )
    write_json(args.output / "baseline_checks.json", checks)
    write_json(args.output / "quality.json", quality)
    write_json(
        args.output / "signals.json",
        {
            "records": records,
            "counts": {c: sum(bool(x) for x in rows) for c, rows in signals.items()},
        },
    )
    results = []
    for weighting in ("inverse_volatility", "equal_control"):
        for cap in (D("0.5"), D("1.5")):
            for scenario in SCENARIOS:
                for infra in (D(0), D(20)):
                    result = simulate_native_portfolio(
                        bars,
                        payments,
                        signals,
                        decimals,
                        {c: c for c in coins},
                        names,
                        sleeves,
                        scenario=scenario,
                        monthly_infra=infra,
                        drawdown_limit=D("0.3"),
                        gross_cap=cap,
                        entry_weights=weights
                        if weighting == "inverse_volatility"
                        else None,
                    )
                    name = f"{weighting}-cap-{cap}-{scenario}-infra-{infra}.json"
                    sha = write_json(args.output / name, result)
                    results.append(
                        {
                            "weighting": weighting,
                            "artifact": name,
                            "sha256": sha,
                            **result["summary"],
                        }
                    )
                    if infra == 0:
                        s = result["summary"]
                        print(
                            args.panel,
                            weighting,
                            cap,
                            scenario,
                            "net",
                            round(s["net_total_usd"], 2),
                            "bound %",
                            round(s["max_ohlc_drawdown_envelope"] * 100, 2),
                            "halt",
                            s["halted"],
                            flush=True,
                        )
    write_json(
        args.output / "summary.json",
        {
            "run_id": f"slow-trend-20260907-v1-{args.panel}",
            "panel": args.panel,
            "protocol_sha256": reg["protocol_sha256"],
            "code_version": source_version(Path.cwd())[0],
            "script_sha256": file_sha256(Path(__file__)),
            "results": results,
            "coins": coins,
            "historical_venue": quality["source_venue"],
            "first_basket_ms": records[0]["time_ms"],
            "basket_dates": len(records),
            "network_data_calls": 0,
            "live_enabled": False,
            "promotion_authorized": False,
            "decision": "CROSS_PERIOD_REVIEW_REQUIRED",
        },
    )


if __name__ == "__main__":
    main()
