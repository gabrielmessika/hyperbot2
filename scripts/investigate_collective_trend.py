"""Fixed collective-trend condition with continuous two-year capital history."""

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
from hyperbot2.research.market_regime import collective_trend, join_panels
from hyperbot2.research.native_portfolio import simulate_native_portfolio
from hyperbot2.research.volatility_spread import volatility_baskets

D = Decimal
REPORT = Path("reports/collective_trend_2026-09-07")
PREVIOUS = Path("reports/volatility_long_2024_2026-09-07")
PREVIOUS_DATA = Path("data/volatility_long_2024_2026-09-07")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--panel",
        required=True,
        choices=("native_2026", "continuous_2024_2025"),
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
    if args.panel == "continuous_2024_2025":
        left, left_payments, q4 = load_archives(
            PREVIOUS_DATA / "archives",
            coins,
            year=2024,
            october_2024_rest=PREVIOUS_DATA / "october_api_audit",
        )
        q = Path("reports/prior_transfer_2026-09-07/qualification.json")
        full = [r["coin"] for r in json.loads(q.read_text())["selected_by_metadata"]]
        right, right_payments, q5 = load_archives(
            Path("data/prior_transfer_2026-09-07/archives"), full
        )
        right, right_payments = (
            {c: rows[c] for c in coins} for rows in (right, right_payments)
        )
        bars, payments = join_panels(left, left_payments, right, right_payments)
        quality = {
            "source_venue": "Binance USDT perpetual futures",
            "sources": {**q4["sources"], **q5["sources"]},
            "segments": {"2024": q4, "2025": q5},
            "evaluated_cohort": coins,
            "data_class": "C",
            "continuous_hours": len(bars[coins[0]]),
            "annual_capital_or_warmup_reset": False,
        }
    else:
        folders = (
            [DATA / "history"]
            + [TRANSFER / "history" / f"batch-{b}" for b in range(2)]
            + [ROOT / "history", ROOT / "replication_history", OLD / "history"]
        )
        bars, payments, _, quality = load(folders, coins, START, END)
        quality["source_venue"] = "Hyperliquid"
        if quality != json.loads(
            (PREVIOUS_DATA / "native_2026_v2_run1/quality.json").read_text()
        ):
            raise ValueError("native historical quality changed")
    times = [b.time for b in bars[coins[0]]]
    closes = {c: [b.close for b in rows] for c, rows in bars.items()}
    records = volatility_baskets(closes, times)
    normalized = json.loads(json.dumps([asdict(r) for r in records], default=str))
    by_time = {r["time_ms"]: r for r in normalized}
    references = (
        ("native_2026",)
        if args.panel == "native_2026"
        else ("transfer_2024", "transfer_2025")
    )
    old_weeks = 0
    for reference in references:
        path = PREVIOUS_DATA / f"{reference}_v2_run1/selections.json"
        for previous in json.loads(path.read_text()):
            current = by_time[previous["time_ms"]]
            if any(previous[k] != current[k] for k in ("time_ms", "scores", "sides")):
                raise ValueError("previous weekly ranking changed")
            old_weeks += 1
    signals = {
        rule: {c: [0] * len(times) for c in coins}
        for rule in ("collective_trend", "unconditional_control")
    }
    active = [r for r in records if r.sides]
    regimes = []
    for basket in active:
        trend = collective_trend(closes, basket.index)
        eligible = trend > 0
        regimes.append(
            {
                "time_ms": basket.time_ms,
                "index": basket.index,
                "median_return_30d": trend,
                "eligible": eligible,
            }
        )
        for c, _ in basket.sides:
            signals["unconditional_control"][c][basket.index] = 1
            signals["collective_trend"][c][basket.index] = int(eligible)
    if sum(map(sum, signals["collective_trend"].values())) != 6 * sum(
        r["eligible"] for r in regimes
    ):
        raise ValueError("six long entries per eligible basket required")
    if sum(map(sum, signals["unconditional_control"].values())) != 6 * len(active):
        raise ValueError("six benchmark entries per basket required")
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
    write_json(args.output / "regime_signals.json", regimes)
    write_json(
        args.output / "signal_checks.json",
        {
            "historical_sources_revalidated": True,
            "previous_weekly_rankings_identical": old_weeks,
            "newly_covered_weeks": len(active) - old_weeks,
            "baskets": len(active),
            "intended_entries": {
                rule: sum(map(sum, entries.values()))
                for rule, entries in signals.items()
            },
        },
    )
    results = []
    baseline_checks = []
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
                        if (
                            args.panel == "native_2026"
                            and rule == "unconditional_control"
                        ):
                            previous_name = (
                                f"volatility_extremes-cap-{cap}-dd-{limit}"
                                f"-{scenario}-infra-{infra}.json"
                            )
                            previous = (
                                Path(
                                    "data/volatility_capital_2026-09-07/native_2026_run1"
                                )
                                / previous_name
                            )
                            previous_sha = checked_input(previous)
                            if json.loads(
                                json.dumps(result, default=str)
                            ) != json.loads(previous.read_text()):
                                raise ValueError(
                                    "native unconditional economics changed"
                                )
                            baseline_checks.append(
                                {
                                    "source": str(previous),
                                    "sha256": previous_sha,
                                    "full_match": True,
                                }
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
    write_json(args.output / "baseline_checks.json", baseline_checks)
    write_json(
        args.output / "summary.json",
        {
            "run_id": f"collective-trend-20260907-v1-{args.panel}",
            "panel": args.panel,
            "protocol_sha256": reg["protocol_sha256"],
            "code_version": version,
            "script_sha256": script_sha,
            "results": results,
            "coins": coins,
            "historical_venue": quality["source_venue"],
            "basket_dates": len(active),
            "previous_strategy_statistical_gate_failed": True,
            "eligible_basket_dates": sum(r["eligible"] for r in regimes),
            "annual_capital_or_warmup_reset": False,
            "promotion_authorized": False,
            "live_enabled": False,
            "network_data_calls": 0,
            "decision": "COLLECTIVE_TREND_REVIEW_REQUIRED",
        },
    )


if __name__ == "__main__":
    main()
