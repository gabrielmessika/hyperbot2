"""Free prior-window extension of the fixed volume-breakout control."""

from __future__ import annotations

import argparse
import json
import time
from decimal import Decimal
from pathlib import Path

from fetch_research_history import PublicResearchClient
from investigate_funding_normalization import END, OLD, ROOT, load
from investigate_funding_transfer import DATA as TRANSFER
from investigate_funding_transfer import START as SPLIT

from hyperbot2.research.artifacts import (
    checked_input,
    file_sha256,
    source_version,
    write_json,
)
from hyperbot2.research.compression_breakout import compression_entries
from hyperbot2.research.funding_portfolio import simulate_portfolio
from hyperbot2.research.rotation import HOUR

D = Decimal
START = SPLIT - 24 * 24 * HOUR
REPORT = Path("reports/breakout_extension_2026-09-07")
DATA = Path("data/breakout_extension_2026-09-07")


def fetch(output: Path, coins: list[str], protocol: str) -> None:
    output.mkdir(parents=True, exist_ok=False)
    client = PublicResearchClient(output)

    def request(query: dict) -> list:
        if len(client.records) >= 54 or client.total_bytes >= 5_000_000:
            raise ValueError("registered acquisition budget exhausted")
        rows = client.info(query)
        time.sleep(3)
        if not isinstance(rows, list):
            raise ValueError("native list required")
        return rows

    try:
        for c in coins:
            bars = request(
                {
                    "type": "candleSnapshot",
                    "req": {
                        "coin": c,
                        "interval": "1h",
                        "startTime": START,
                        "endTime": SPLIT - 1,
                    },
                }
            )
            cursor, count = START, 0
            for _ in range(2):
                rows = request(
                    {
                        "type": "fundingHistory",
                        "coin": c,
                        "startTime": cursor,
                        "endTime": SPLIT - 1,
                    }
                )
                if not rows:
                    break
                times = [int(r["time"]) for r in rows]
                if min(times) < cursor or max(times) >= SPLIT:
                    raise ValueError("funding page outside requested period")
                count += len(rows)
                cursor = max(times) + 1
                if cursor >= SPLIT - HOUR:
                    break
            else:
                raise ValueError("funding pagination incomplete within budget")
            print(c, "candles", len(bars), "funding", count, flush=True)
    finally:
        write_json(
            output / "manifest.json",
            {
                "requests": client.records,
                "response_bytes": client.total_bytes,
                "coins": coins,
                "start_ms": START,
                "end_ms_exclusive": SPLIT,
                "protocol_sha256": protocol,
                "script_sha256": file_sha256(Path(__file__)),
                "data_cost_usd": 0,
            },
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fetch", action="store_true")
    parser.add_argument("--drawdown-limit", choices=("0.2", "0.3"), default="0.2")
    args = parser.parse_args()
    limit = D(args.drawdown_limit)
    checked_input(REPORT / "registration.json")
    registration = json.loads((REPORT / "registration.json").read_text())
    protocol = file_sha256(REPORT / "PROTOCOL.md")
    selection = Path("reports/funding_transfer_2026-09-07/selection.json")
    if registration["protocol_sha256"] != protocol or registration[
        "universe_sha256"
    ] != checked_input(selection):
        raise ValueError("registered extension changed")
    coins = json.loads(selection.read_text())["eligible"]
    if len(coins) != 18:
        raise ValueError("registered universe changed")
    if args.fetch:
        fetch(args.output, coins, protocol)
        return
    args.output.mkdir(parents=True, exist_ok=False)
    quality, results = {}, []
    folders = (
        [DATA / "history"]
        + [TRANSFER / "history" / f"batch-{b}" for b in range(2)]
        + [ROOT / "history", ROOT / "replication_history", OLD / "history"]
    )
    meta_path = OLD / "meta.json"
    checked_input(meta_path)
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
    for fold, end in (("older", SPLIT), ("continuous", END)):
        bars, payments, _, quality[fold] = load(folders, coins, START, end)
        if any(q["zero_volume_hours"] for q in quality[fold]["assets"].values()):
            write_json(args.output / "quality_failure.json", quality)
            raise ValueError("zero-volume candles: extension execution unqualified")
        entries = {
            c: compression_entries(bars[c], require_compression=False) for c in coins
        }
        quality[fold]["signal_counts"] = {
            c: sum(bool(s) for s in rows) for c, rows in entries.items()
        }
        quality[fold]["sources"][str(meta_path)] = checked_input(meta_path)
        write_json(
            args.output / f"{fold}-signals.json",
            {
                c: [
                    {"index": i, "entry_ms": bars[c][i].time + 60_000, "side": s}
                    for i, s in enumerate(rows)
                    if s
                ]
                for c, rows in entries.items()
            },
        )
        for scenario in (
            "base",
            "cost_stress",
            "delay",
            "funding_adverse",
            "zero_cost",
        ):
            for infra in (D(0), D(20)):
                result = simulate_portfolio(
                    bars,
                    payments,
                    entries,
                    decimals,
                    gross_cap=D("0.5"),
                    scenario=scenario,
                    monthly_infra=infra,
                    holding_hours=24,
                    drawdown_limit=limit,
                )
                result["summary"]["fold"] = fold
                name = f"{fold}-{scenario}-infra-{infra}.json"
                sha = write_json(args.output / name, result)
                results.append({"artifact": name, "sha256": sha, **result["summary"]})
                if infra == 0:
                    s = result["summary"]
                    print(
                        fold,
                        scenario,
                        "net",
                        round(s["net_total_usd"], 2),
                        "monthly %",
                        round(s["equivalent_monthly_compound"] * 100, 2),
                        "bound %",
                        round(s["max_ohlc_drawdown_envelope"] * 100, 2),
                        "trades",
                        s["round_trips"],
                        flush=True,
                    )
    write_json(args.output / "quality.json", quality)
    candidates = []
    for infra in (D(0), D(20)):
        required = [
            r
            for r in results
            if r["fold"] == "continuous"
            and r["monthly_infra"] == infra
            and r["scenario"] != "zero_cost"
        ]
        if len(required) == 4 and all(
            r["net_total_usd"] > 0
            and r["max_ohlc_drawdown_envelope"] <= limit
            and not r["margin_observed_breach"]
            and r["minimum_margin_envelope_buffer_usd"] >= 0
            for r in required
        ):
            candidates.append({"monthly_infra": infra})
    write_json(
        args.output / "summary.json",
        {
            "run_id": "breakout-extension-20260907-v1",
            "drawdown_limit": limit,
            "protocol_sha256": protocol,
            "code_version": source_version(Path.cwd())[0],
            "script_sha256": file_sha256(Path(__file__)),
            "results": results,
            "candidates": candidates,
            "decision": "EXTENSION_SCREEN_PASSED_UNQUALIFIED"
            if candidates
            else "EXTENSION_SCREEN_NOT_PASSED",
            "live_enabled": False,
            "promotion_authorized": False,
            "data_cost_usd": 0,
        },
    )


if __name__ == "__main__":
    main()
