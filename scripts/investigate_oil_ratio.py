"""Oil relative-value screen using the parameterized existing ratio engine."""

from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from investigate_commodity_trend import load as load_existing

from hyperbot2.research.artifacts import (
    checked_input,
    file_sha256,
    source_version,
    write_json,
)
from hyperbot2.research.hip3_fees import taker_fee
from hyperbot2.research.metals_ratio import ratio_frames, simulate_ratio
from hyperbot2.research.oil_calendar import oil_entry_allowed, oil_signal_window_allowed

D = Decimal
BRENT, WTI = "xyz:BRENTOIL", "xyz:CL"
REPORT = Path("reports/oil_ratio_2026-09-07")


def load_brent() -> tuple:
    path = Path("scripts/investigate_weekend_repricing.py")
    spec = importlib.util.spec_from_file_location("oil_native_loader", path)
    if spec is None or spec.loader is None:
        raise ValueError("native loader unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.COINS = (BRENT,)
    return module.load(Path("data/oil_ratio_2026-09-07/history"))


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
    old, old_funding, _, _, sources = load_existing(
        Path("data/commodity_trend_2026-09-07/history")
    )
    bars, funding, start, end, extra = load_brent()
    sources.update(extra)
    bars[WTI] = [b for b in old[WTI] if start <= b.time < end]
    funding[WTI] = old_funding[WTI]
    if [b.time for b in bars[BRENT]] != [b.time for b in bars[WTI]]:
        raise ValueError("native oil time alignment failed")
    meta_path = Path("data/weekend_repricing_2026-09-07/xyz_meta.json")
    sources[str(meta_path)] = checked_input(meta_path)
    meta = {
        r["name"]: r
        for r in json.loads(meta_path.read_text())["response"][0]["universe"]
        if r["name"] in (BRENT, WTI)
    }
    fees = {
        c: taker_fee(
            deployer_fee_scale=D(m["deployerFeeScale"]), growth_mode=m.get("growthMode")
        )
        for c, m in meta.items()
    }
    if fees != {BRENT: D("0.00009"), WTI: D("0.00009")}:
        raise ValueError("registered fee scenario mismatch")
    decimals = {c: int(m["szDecimals"]) for c, m in meta.items()}
    ratios = [
        (b.close / w.close).ln() for b, w in zip(bars[BRENT], bars[WTI], strict=True)
    ]
    unfiltered = ratio_frames(ratios, lookback=24)
    frames = tuple(
        f if oil_signal_window_allowed(b.time) else None
        for f, b in zip(unfiltered, bars[BRENT], strict=True)
    )
    evaluation_start = int(datetime(2026, 4, 1, tzinfo=UTC).timestamp() * 1000)
    first = next(i for i, b in enumerate(bars[BRENT]) if b.time == evaluation_start)
    bars = {c: bs[first:] for c, bs in bars.items()}
    frames = frames[first:]
    allowed = frozenset(b.time for b in bars[BRENT] if oil_entry_allowed(b.time))
    quality = {
        "data_start_ms": start,
        "evaluation_start_ms": evaluation_start,
        "end_ms_exclusive": end,
        "sources": sources,
        "fees": fees,
        "sz_decimals": decimals,
        "hours": len(frames),
        "calendar_entry_hours": len(allowed),
        "usable_frames_after_roll_filter": sum(f is not None for f in frames),
        "zero_volume_hours": {
            c: sum(b.volume <= 0 for b in bs) for c, bs in bars.items()
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
                result = simulate_ratio(
                    bars,
                    funding,
                    frames,
                    fees,
                    decimals,
                    gross_cap=cap,
                    scenario=scenario,
                    monthly_infra=infra,
                    assets=(BRENT, WTI),
                    max_holding_hours=2,
                    allowed_entries=allowed,
                )
                # Preserve the legacy engine contract; exported oil fields are explicit.
                result["cycles"] = [
                    {
                        k.replace("gold", "brent").replace("silver", "wti"): v
                        for k, v in cycle.items()
                    }
                    for cycle in result["cycles"]
                ]
                result["assets"] = {"first": BRENT, "second": WTI}
                name = f"cap-{cap}-{scenario}-infra-{infra}.json"
                sha = write_json(args.output / name, result)
                summaries.append({"artifact": name, "sha256": sha, **result["summary"]})
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
    write_json(
        args.output / "summary.json",
        {
            "run_id": "oil-ratio-20260907-v1",
            "protocol_sha256": protocol,
            "sources": sources,
            "code_version": source_version(Path.cwd())[0],
            "scripts": {
                str(p): file_sha256(p)
                for p in (
                    Path(__file__),
                    Path("scripts/fetch_oil_history.py"),
                    Path("scripts/investigate_commodity_trend.py"),
                    Path("scripts/investigate_weekend_repricing.py"),
                )
            },
            "results": summaries,
            "candidates_requiring_replication": candidates,
            "decision": "RESEARCH_CANDIDATE_UNQUALIFIED"
            if candidates
            else "HYPOTHESIS_NOT_CONFIRMED",
            "evaluation_start_ms": evaluation_start,
            "end_ms_exclusive": end,
            "partial_calendar_months": ["2026-09"],
            "live_enabled": False,
            "promotion_authorized": False,
            "limitations": [
                "different underlying futures contracts",
                "conservative roll blackout, historical oracle timeline unqualified",
                "hourly OHLC assumed fills, not native marks/depth",
                "independent extrema envelope is not an observed path",
                "158 days do not validate 12 months",
            ],
        },
    )


if __name__ == "__main__":
    main()
