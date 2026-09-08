"""Run the registered commodity trend portfolio with native data provenance."""

from __future__ import annotations

import argparse
import importlib.util
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path

from fetch_commodity_history import COINS, REPORT

from hyperbot2.research.artifacts import (
    checked_input,
    file_sha256,
    source_version,
    write_json,
)
from hyperbot2.research.commodity_trend import simulate_trend, trend_frames
from hyperbot2.research.hip3_fees import taker_fee

D = Decimal


def load(root: Path) -> tuple:
    path = Path("scripts/investigate_weekend_repricing.py")
    spec = importlib.util.spec_from_file_location("commodity_native_loader", path)
    if spec is None or spec.loader is None:
        raise ValueError("native loader unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.COINS = COINS
    return module.load(root)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--history", type=Path, default=Path("data/commodity_trend_2026-09-07/history")
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    checked_input(REPORT / "registration.json")
    protocol = file_sha256(REPORT / "PROTOCOL.md")
    if (
        json.loads((REPORT / "registration.json").read_text())["protocol_sha256"]
        != protocol
    ):
        raise ValueError("registered protocol changed")
    bars, funding, start, end, sources = load(args.history)
    meta_path = Path("data/weekend_repricing_2026-09-07/xyz_meta.json")
    sources[str(meta_path)] = checked_input(meta_path)
    meta = {
        r["name"]: r
        for r in json.loads(meta_path.read_text())["response"][0]["universe"]
        if r["name"] in COINS
    }
    fees = {
        c: taker_fee(
            deployer_fee_scale=D(m["deployerFeeScale"]), growth_mode=m.get("growthMode")
        )
        for c, m in meta.items()
    }
    if fees != {
        "xyz:GOLD": D("0.0009"),
        "xyz:SILVER": D("0.00009"),
        "xyz:CL": D("0.00009"),
    }:
        raise ValueError("fees differ from registered scenarios")
    decimals = {c: int(m["szDecimals"]) for c, m in meta.items()}
    frames = {c: trend_frames(bs) for c, bs in bars.items()}
    quality = {
        "start_ms": start,
        "end_ms_exclusive": end,
        "sources": sources,
        "fees": fees,
        "sz_decimals": decimals,
        "coins": {
            c: {
                "candles": len(bs),
                "funding": len(funding[c]),
                "zero_volume_hours": sum(b.volume <= 0 for b in bs),
                "signal_counts": dict(Counter(f.side for f in frames[c])),
            }
            for c, bs in bars.items()
        },
    }
    write_json(args.output / "quality.json", quality)
    summaries = []
    for cap in (D("0.5"), D(1), D("1.5")):
        for scenario in (
            "base",
            "cost_stress",
            "delay",
            "funding_adverse",
            "zero_cost",
        ):
            for infra in (D(0), D(20)):
                name = f"cap-{cap}-{scenario}-infra-{infra}"
                result = simulate_trend(
                    bars,
                    funding,
                    frames,
                    fees,
                    decimals,
                    gross_cap=cap,
                    scenario=scenario,
                    monthly_infra=infra,
                )
                checksum = write_json(args.output / f"{name}.json", result)
                summaries.append(
                    {
                        "artifact": name + ".json",
                        "sha256": checksum,
                        **result["summary"],
                    }
                )
                print(
                    name,
                    "net",
                    round(result["summary"]["net_total_usd"], 2),
                    "DD",
                    round(result["summary"]["max_hourly_drawdown"] * 100, 2),
                    "trades",
                    result["summary"]["round_trips"],
                    flush=True,
                )
    candidates = []
    for cap in (D("0.5"), D(1), D("1.5")):
        for infra in (D(0), D(20)):
            required = [
                r
                for r in summaries
                if r["gross_cap"] == cap
                and r["monthly_infra"] == infra
                and r["scenario"] in {"base", "cost_stress", "funding_adverse"}
            ]
            if all(
                r["net_total_usd"] > 0 and r["ohlc_envelope_le_20pct"] for r in required
            ):
                candidates.append({"gross_cap": cap, "monthly_infra": infra})
    summary = {
        "run_id": "commodity-trend-20260907-v1",
        "protocol_sha256": protocol,
        "code_version": source_version(Path.cwd())[0],
        "sources": sources,
        "scripts": {
            str(p): file_sha256(p)
            for p in (
                Path(__file__),
                Path("scripts/fetch_commodity_history.py"),
                Path("scripts/investigate_weekend_repricing.py"),
            )
        },
        "start_ms": start,
        "end_ms_exclusive": end,
        "results": summaries,
        "partial_calendar_months": ["2026-02", "2026-09"],
        "candidates_requiring_replication": candidates,
        "decision": "RESEARCH_CANDIDATE_UNQUALIFIED"
        if candidates
        else "HYPOTHESIS_NOT_CONFIRMED",
        "live_enabled": False,
        "promotion_authorized": False,
        "limitations": [
            "hourly OHLC and assumed fills, not native mark or queue history",
            "independent OHLC extremes are an adverse envelope, "
            "not an observed simultaneous path",
            "stops cannot guarantee loss caps in gaps",
            "historical fee timeline incomplete",
            "206 days do not validate 12 months",
        ],
    }
    write_json(args.output / "summary.json", summary)


if __name__ == "__main__":
    main()
