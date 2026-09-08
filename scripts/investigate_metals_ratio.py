"""Frozen gold/silver ratio experiment using existing native history only."""

from __future__ import annotations

import argparse
import json
from decimal import Decimal
from pathlib import Path

from investigate_commodity_trend import load

from hyperbot2.research.artifacts import (
    checked_input,
    file_sha256,
    source_version,
    write_json,
)
from hyperbot2.research.hip3_fees import taker_fee
from hyperbot2.research.metals_ratio import GOLD, SILVER, ratio_frames, simulate_ratio

D = Decimal
REPORT = Path("reports/metals_ratio_2026-09-07")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
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
    bars, funding, start, end, sources = load(
        Path("data/commodity_trend_2026-09-07/history")
    )
    meta_path = Path("data/weekend_repricing_2026-09-07/xyz_meta.json")
    sources[str(meta_path)] = checked_input(meta_path)
    meta = {
        r["name"]: r
        for r in json.loads(meta_path.read_text())["response"][0]["universe"]
        if r["name"] in {GOLD, SILVER}
    }
    fees = {
        c: taker_fee(
            deployer_fee_scale=D(m["deployerFeeScale"]), growth_mode=m.get("growthMode")
        )
        for c, m in meta.items()
    }
    if fees != {GOLD: D("0.0009"), SILVER: D("0.00009")}:
        raise ValueError("registered fees differ from metadata")
    decimals = {c: int(m["szDecimals"]) for c, m in meta.items()}
    log_ratios = [
        (g.close / s.close).ln() for g, s in zip(bars[GOLD], bars[SILVER], strict=True)
    ]
    frames = ratio_frames(log_ratios)
    quality = {
        "start_ms": start,
        "end_ms_exclusive": end,
        "sources": sources,
        "fees": fees,
        "sz_decimals": decimals,
        "hours": len(log_ratios),
        "usable_frames": sum(f is not None for f in frames),
        "eligible_signal_hours": sum(
            f is not None and D(2) <= abs(f.z) < 4 for f in frames
        ),
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
                result = simulate_ratio(
                    bars,
                    funding,
                    frames,
                    fees,
                    decimals,
                    gross_cap=cap,
                    scenario=scenario,
                    monthly_infra=infra,
                )
                name = f"cap-{cap}-{scenario}-infra-{infra}.json"
                checksum = write_json(args.output / name, result)
                summaries.append(
                    {"artifact": name, "sha256": checksum, **result["summary"]}
                )
                s = result["summary"]
                print(
                    name,
                    "net",
                    round(s["net_total_usd"], 2),
                    "DD",
                    round(s["max_hourly_drawdown"] * 100, 2),
                    "trades",
                    s["round_trips"],
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
            if len(required) == 3 and all(
                r["net_total_usd"] > 0 and r["ohlc_envelope_le_20pct"] for r in required
            ):
                candidates.append({"gross_cap": cap, "monthly_infra": infra})
    summary = {
        "run_id": "metals-ratio-20260907-v1",
        "protocol_sha256": protocol,
        "sources": sources,
        "scripts": {
            str(p): file_sha256(p)
            for p in (
                Path(__file__),
                Path("scripts/investigate_commodity_trend.py"),
                Path("scripts/investigate_weekend_repricing.py"),
            )
        },
        "code_version": source_version(Path.cwd())[0],
        "start_ms": start,
        "end_ms_exclusive": end,
        "results": summaries,
        "candidates_requiring_replication": candidates,
        "decision": "RESEARCH_CANDIDATE_UNQUALIFIED"
        if candidates
        else "HYPOTHESIS_NOT_CONFIRMED",
        "partial_calendar_months": ["2026-02", "2026-09"],
        "live_enabled": False,
        "promotion_authorized": False,
        "limitations": [
            "period previously used for another hypothesis",
            "hourly OHLC and assumed fills, not native marks/depth",
            "independent extrema envelope, not an observed path",
            "no guaranteed exit at risk threshold",
            "fee timeline incomplete",
            "206 days do not validate 12 months",
        ],
    }
    write_json(args.output / "summary.json", summary)


if __name__ == "__main__":
    main()
