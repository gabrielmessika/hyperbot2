"""Fixed native-capital diagnostic; the prior statistical gate remains failed."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
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
from hyperbot2.research.volatility_spread import volatility_baskets

D = Decimal
REPORT = Path("reports/volatility_capital_2026-09-07")
PREVIOUS = Path("reports/volatility_long_2024_2026-09-07")
PREVIOUS_DATA = Path("data/volatility_long_2024_2026-09-07")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--panel",
        required=True,
        choices=("native_2026", "transfer_2025", "transfer_2024"),
    )
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    checked_input(REPORT / "registration.json")
    reg = json.loads((REPORT / "registration.json").read_text())
    version, script_sha = source_version(Path.cwd())[0], file_sha256(Path(__file__))
    if (
        reg["protocol_sha256"] != file_sha256(REPORT / "PROTOCOL.md")
        or reg["code_version"] != version
        or reg["script_sha256"] != script_sha
    ):
        raise ValueError("registered capital diagnostic changed")
    for filename, sha in reg["inputs"].items():
        if checked_input(Path(filename)) != sha:
            raise ValueError("registered input changed")
    coins = [
        r["coin"]
        for r in json.loads((PREVIOUS / "qualification.json").read_text())[
            "selected_by_metadata"
        ]
    ]
    if args.panel == "transfer_2024":
        bars, payments, quality = load_archives(
            PREVIOUS_DATA / "archives",
            coins,
            year=2024,
            october_2024_rest=PREVIOUS_DATA / "october_api_audit",
        )
    elif args.panel == "transfer_2025":
        q = Path("reports/prior_transfer_2026-09-07/qualification.json")
        full = [r["coin"] for r in json.loads(q.read_text())["selected_by_metadata"]]
        bars, payments, quality = load_archives(
            Path("data/prior_transfer_2026-09-07/archives"), full
        )
        bars, payments = ({c: rows[c] for c in coins} for rows in (bars, payments))
        quality["loaded_full_cohort"], quality["evaluated_cohort"] = full, coins
    else:
        folders = (
            [DATA / "history"]
            + [TRANSFER / "history" / f"batch-{b}" for b in range(2)]
            + [ROOT / "history", ROOT / "replication_history", OLD / "history"]
        )
        bars, payments, _, quality = load(folders, coins, START, END)
        quality["source_venue"] = "Hyperliquid"
    previous = PREVIOUS_DATA / f"{args.panel}_v2_run1"
    if quality != json.loads((previous / "quality.json").read_text()):
        raise ValueError("event-screen input quality changed")
    times = [b.time for b in bars[coins[0]]]
    records = volatility_baskets(
        {c: [b.close for b in rows] for c, rows in bars.items()}, times
    )
    normalized = json.loads(json.dumps([asdict(r) for r in records], default=str))
    if normalized != json.loads((previous / "selections.json").read_text()):
        raise ValueError("registered selections changed")
    signals = {
        rule: {c: [0] * len(times) for c in coins}
        for rule in ("volatility_extremes", "all_assets_control")
    }
    active = [r for r in records if r.sides]
    for basket in active:
        for c, _ in basket.sides:
            signals["volatility_extremes"][c][basket.index] = 1
        for c in coins:
            signals["all_assets_control"][c][basket.index] = 1
    if sum(map(sum, signals["volatility_extremes"].values())) != 6 * len(active):
        raise ValueError("six long entries per basket required")
    if sum(map(sum, signals["all_assets_control"].values())) != 11 * len(active):
        raise ValueError("eleven benchmark entries per basket required")
    meta_path = OLD / "meta.json"
    meta = {
        r["name"]: r
        for r in json.loads(meta_path.read_text())["response"][0]["universe"]
        if r["name"] in coins
    }
    if set(meta) != set(coins) or any(
        r.get("onlyIsolated", False)
        or r.get("isDelisted", False)
        or r["maxLeverage"] < 3
        for r in meta.values()
    ):
        raise ValueError("reference native margin assumptions fail")
    quality["sources"][str(meta_path)] = checked_input(meta_path)
    quality["native_reference_metadata"] = meta
    decimals = {c: r["szDecimals"] for c, r in meta.items()}
    names = dict.fromkeys(coins, "weekly")
    sleeves = {"weekly": AllocationSleeve(D(1), 168)}
    args.output.mkdir(parents=True, exist_ok=False)
    write_json(args.output / "quality.json", quality)
    write_json(args.output / "selections.json", normalized)
    write_json(
        args.output / "signal_checks.json",
        {
            "historical_quality_identical": True,
            "historical_selections_identical": True,
            "baskets": len(active),
            "intended_entries": {
                rule: sum(map(sum, entries.values()))
                for rule, entries in signals.items()
            },
        },
    )
    results = []
    for rule, entries in signals.items():
        for cap in (D("0.5"), D("1.5")):
            for limit in (D("0.2"), D("0.3")):
                for scenario in SCENARIOS:
                    for infra in (D(0), D(20)):
                        result = simulate_native_portfolio(
                            bars,
                            payments,
                            entries,
                            decimals,
                            {c: c for c in coins},
                            names,
                            sleeves,
                            scenario=scenario,
                            monthly_infra=infra,
                            drawdown_limit=limit,
                            gross_cap=cap,
                        )
                        name = (
                            f"{rule}-cap-{cap}-dd-{limit}-{scenario}-infra-{infra}.json"
                        )
                        sha = write_json(args.output / name, result)
                        s = result["summary"]
                        results.append(
                            {"rule": rule, "artifact": name, "sha256": sha, **s}
                        )
                        if infra == 0:
                            print(
                                args.panel,
                                rule,
                                cap,
                                limit,
                                scenario,
                                "net",
                                round(s["net_total_usd"], 2),
                                "bound %",
                                round(s["max_ohlc_drawdown_envelope"] * 100, 2),
                                "halt",
                                s["halted"],
                                flush=True,
                            )
    if (
        source_version(Path.cwd())[0] != version
        or file_sha256(Path(__file__)) != script_sha
    ):
        raise ValueError("code changed during diagnostic")
    write_json(
        args.output / "summary.json",
        {
            "run_id": f"volatility-capital-20260907-v1-{args.panel}",
            "panel": args.panel,
            "protocol_sha256": reg["protocol_sha256"],
            "code_version": version,
            "script_sha256": script_sha,
            "results": results,
            "coins": coins,
            "historical_venue": quality["source_venue"],
            "basket_dates": len(active),
            "previous_statistical_gate_failed": True,
            "promotion_authorized": False,
            "live_enabled": False,
            "network_data_calls": 0,
            "decision": "CAPITAL_RISK_DIAGNOSTIC_REVIEW_REQUIRED",
        },
    )


if __name__ == "__main__":
    main()
