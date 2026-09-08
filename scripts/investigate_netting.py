"""Audit native deltas of fixed historical shared portfolios, entirely offline."""

from __future__ import annotations

import argparse
import json
from collections import Counter
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
from hyperbot2.research.netting_audit import audit_net_positions

REPORT = Path("reports/netting_2026-09-07")
SOURCE = Path("data/diversification_2026-09-07/portfolio_run1")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    checked_input(REPORT / "registration.json")
    reg = json.loads((REPORT / "registration.json").read_text())
    if reg["protocol_sha256"] != file_sha256(REPORT / "PROTOCOL.md"):
        raise ValueError("registered protocol changed")
    selection = Path("reports/funding_transfer_2026-09-07/selection.json")
    checked_input(selection)
    coins = json.loads(selection.read_text())["eligible"]
    if len(coins) != 18:
        raise ValueError("unexpected universe")
    folders = (
        [DATA / "history"]
        + [TRANSFER / "history" / f"batch-{b}" for b in range(2)]
        + [ROOT / "history", ROOT / "replication_history", OLD / "history"]
    )
    bars, payments, _, quality = load(folders, coins, START, END)
    meta_path = OLD / "meta.json"
    quality["sources"][str(meta_path)] = checked_input(meta_path)
    decimals = {
        m["name"]: m["szDecimals"]
        for m in json.loads(meta_path.read_text())["response"][0]["universe"]
        if m["name"] in coins
    }
    original_quality = SOURCE / "quality.json"
    quality["sources"][str(original_quality)] = checked_input(original_quality)
    mapping = {
        key: value[1]
        for key, value in json.loads(original_quality.read_text())[
            "virtual_to_native"
        ].items()
    }
    args.output.mkdir(parents=True, exist_ok=False)
    results = []
    for cap in ("1.5", "2"):
        for scenario in SCENARIOS:
            for infra in (0, 20):
                name = f"shared-cap-{cap}-{scenario}-infra-{infra}.json"
                path = SOURCE / name
                sha = checked_input(path)
                source = json.loads(path.read_text())
                result = audit_net_positions(bars, payments, decimals, mapping, source)
                result["summary"].update(
                    {
                        "gross_cap": cap,
                        "scenario": scenario,
                        "monthly_infra": infra,
                        "source_sha256": sha,
                        "source_path": str(path),
                        "original_drawdown_envelope": source["summary"][
                            "max_ohlc_drawdown_envelope"
                        ],
                        "small_orders_by_kind": dict(
                            Counter(
                                o["kind"]
                                for o in result["orders"]
                                if o["below_minimum"]
                            )
                        ),
                    }
                )
                artifact_sha = write_json(args.output / name, result)
                results.append(
                    {"artifact": name, "sha256": artifact_sha, **result["summary"]}
                )
                print(
                    cap,
                    scenario,
                    infra,
                    "small",
                    result["summary"]["below_minimum_orders"],
                    "bound",
                    result["summary"]["net_exposure_drawdown_envelope"],
                    flush=True,
                )
    write_json(args.output / "quality.json", quality)
    write_json(
        args.output / "summary.json",
        {
            "run_id": "netting-20260907-v1",
            "protocol_sha256": reg["protocol_sha256"],
            "code_version": source_version(Path.cwd())[0],
            "script_sha256": file_sha256(Path(__file__)),
            "results": results,
            "network_data_calls": 0,
            "live_enabled": False,
            "promotion_authorized": False,
            "decision": "FIXED_NATIVE_DELTAS_REQUIRE_EXECUTION_PLANNER"
            if any(not r["direct_delta_minimums_passed"] for r in results)
            else "FIXED_NATIVE_DELTAS_MINIMUM_SCREEN_PASSED_UNQUALIFIED",
        },
    )


if __name__ == "__main__":
    main()
