"""Bounded prior-history acquisition and fixed-rule transferability comparison."""

from __future__ import annotations

import argparse
import json
import time
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from fetch_research_history import PublicResearchClient
from investigate_funding_normalization import END, OLD, ROOT, load, registered
from replicate_funding_normalization import START as SPLIT

from hyperbot2.research.artifacts import (
    checked_input,
    file_sha256,
    source_version,
    write_json,
)
from hyperbot2.research.funding_portfolio import funding_entries, simulate_portfolio
from hyperbot2.research.rotation import HOUR

D = Decimal
START = int(datetime(2026, 3, 10, tzinfo=UTC).timestamp() * 1000)
REPORT = Path("reports/funding_transfer_2026-09-07")
DATA = Path("data/funding_transfer_2026-09-07")


def fetch(output: Path, coins: list[str], protocol: str) -> None:
    output.mkdir(parents=True, exist_ok=False)
    for batch in range(2):
        folder = output / f"batch-{batch}"
        folder.mkdir(exist_ok=False)
        client = PublicResearchClient(folder)

        def request(query: dict, batch_client: PublicResearchClient = client) -> list:
            if (
                len(batch_client.records) >= 72
                or batch_client.total_bytes >= 10_000_000
            ):
                raise ValueError("registered public data budget exhausted")
            rows = batch_client.info(query)
            time.sleep(3)
            return rows

        selected = coins[9 * batch : 9 * (batch + 1)]
        try:
            for c in selected:
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
                for _ in range(7):
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
                        raise ValueError("funding page outside requested interval")
                    count += len(rows)
                    cursor = max(times) + 1
                    if cursor >= SPLIT - HOUR:
                        break
                print(c, "candles", len(bars), "funding", count, flush=True)
        finally:
            write_json(
                folder / "manifest.json",
                {
                    "requests": client.records,
                    "response_bytes": client.total_bytes,
                    "coins": selected,
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
    args = parser.parse_args()
    checked_input(REPORT / "registration.json")
    protocol = file_sha256(REPORT / "PROTOCOL.md")
    registration = json.loads((REPORT / "registration.json").read_text())
    if registration["protocol_sha256"] != protocol or registration[
        "candidate_review_sha256"
    ] != checked_input(Path("reports/funding_portfolio_2026-09-07/review.json")):
        raise ValueError("registered transfer test changed")
    _, original = registered()
    coins = [c for c in original if c != "CASHCAT"]
    if len(coins) != 18:
        raise ValueError("registered universe changed")
    if args.fetch:
        fetch(args.output, coins, protocol)
        return
    args.output.mkdir(parents=True, exist_ok=False)
    older = [DATA / "history" / f"batch-{b}" for b in range(2)]
    eligible, excluded = [], {}
    for c in coins:
        try:
            load(older, [c], START, SPLIT)
        except ValueError as exc:
            if not str(exc).startswith(
                ("candle coverage failure:", "funding coverage failure:")
            ):
                raise
            excluded[c] = str(exc)
        else:
            eligible.append(c)
    selection = {
        "eligible": eligible,
        "excluded": excluded,
        "basis": "complete prior prices and funding, before PnL",
        "cashcat_excluded": "insufficient prior native history; transferability only",
    }
    write_json(args.output / "selection.json", selection)
    if len(eligible) < 5:
        raise ValueError("insufficient complete assets for registered transfer test")
    meta_path = OLD / "meta.json"
    checked_input(meta_path)
    meta = {
        m["name"]: m
        for m in json.loads(meta_path.read_text())["response"][0]["universe"]
        if m["name"] in eligible
    }
    if len(meta) != len(eligible) or any(
        m.get("onlyIsolated", False)
        or m.get("isDelisted", False)
        or m["maxLeverage"] < 3
        for m in meta.values()
    ):
        raise ValueError("registered margin assumptions fail")
    decimals = {c: m["szDecimals"] for c, m in meta.items()}
    folders = older + [ROOT / "history", ROOT / "replication_history", OLD / "history"]
    results, quality = [], {}
    for fold, start, end in (
        ("older", START, SPLIT),
        ("recent", SPLIT, END),
        ("continuous", START, END),
    ):
        bars, payments, rates, quality[fold] = load(folders, eligible, start, end)
        signals = {c: funding_entries(rates[c]) for c in eligible}
        quality[fold]["signal_counts"] = {
            c: sum(bool(s) for s in signals[c]) for c in eligible
        }
        for strategy in ("funding72", "hold_equal", "grid_long"):
            entries = {}
            for c in eligible:
                if strategy == "funding72":
                    entries[c] = signals[c]
                    continue
                rows = [0] * len(bars[c])
                if strategy == "hold_equal":
                    rows[12] = 1
                else:
                    for i in range(12, len(rows) - 73, 73):
                        rows[i] = 1
                entries[c] = tuple(rows)
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
                        gross_cap=D("0.4"),
                        scenario=scenario,
                        monthly_infra=infra,
                        holding_hours=None if strategy == "hold_equal" else 72,
                    )
                    result["summary"].update({"fold": fold, "strategy": strategy})
                    name = f"{fold}-{strategy}-{scenario}-infra-{infra}.json"
                    sha = write_json(args.output / name, result)
                    results.append(
                        {"artifact": name, "sha256": sha, **result["summary"]}
                    )
                    if scenario == "base" and infra == 0:
                        s = result["summary"]
                        print(
                            fold,
                            strategy,
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
            and r["strategy"] == "funding72"
            and r["monthly_infra"] == infra
            and r["scenario"] != "zero_cost"
        ]
        if len(required) == 4 and all(
            r["net_total_usd"] > 0
            and r["max_ohlc_drawdown_envelope"] <= D("0.2")
            and not r["margin_observed_breach"]
            and r["minimum_margin_envelope_buffer_usd"] >= 0
            for r in required
        ):
            candidates.append(
                {
                    "monthly_infra": infra,
                    "base_monthly_compound": next(
                        r["equivalent_monthly_compound"]
                        for r in required
                        if r["scenario"] == "base"
                    ),
                }
            )
    write_json(
        args.output / "summary.json",
        {
            "run_id": "funding-transfer-20260907-v1",
            "protocol_sha256": protocol,
            "code_version": source_version(Path.cwd())[0],
            "scripts": {
                str(p): file_sha256(p)
                for p in (
                    Path(__file__),
                    Path("scripts/investigate_funding_normalization.py"),
                )
            },
            "meta_sha256": checked_input(meta_path),
            "selection": selection,
            "results": results,
            "candidates": candidates,
            "decision": "TRANSFER_SCREEN_PASSED_UNQUALIFIED"
            if candidates
            else "TRANSFER_SCREEN_NOT_PASSED",
            "live_enabled": False,
            "promotion_authorized": False,
            "data_cost_usd": 0,
            "limits": [
                "selected current universe and historical coverage filter",
                "CASHCAT excluded: not a full replication of its recent strategy",
                "open execution/funding oracle and liquidation marks are proxies",
                "red segments descriptive; primary evaluation is continuous 180d",
            ],
        },
    )


if __name__ == "__main__":
    main()
