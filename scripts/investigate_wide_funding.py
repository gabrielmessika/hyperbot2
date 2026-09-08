"""Public funding economic feasibility screen; no synthetic portfolio claim."""

from __future__ import annotations

import argparse
import json
import runpy
import time
from decimal import Decimal
from pathlib import Path

from hyperbot2.research.artifacts import checked_input, file_sha256, write_json

D = Decimal
HOUR, START, END = 3600000, 1786060800000, 1788652800000


def universe() -> list[str]:
    path = Path("data/wide_funding_2026-09-07/meta.json")
    checked_input(path)
    meta, ctx = json.loads(path.read_text())["response"]
    eligible = [
        (a["name"], D(b["dayNtlVlm"]))
        for a, b in zip(meta["universe"], ctx, strict=True)
        if not a.get("isDelisted", False)
        and a["name"] not in ("BTC", "ETH", "SOL", "HYPE")
        and D(b["dayNtlVlm"]) >= D(10_000_000)
    ]
    return [c for c, _ in sorted(eligible, key=lambda r: (-r[1], r[0]))[:20]]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--fetch", action="store_true")
    args = parser.parse_args()
    protocol = Path("reports/wide_funding_2026-09-07/PROTOCOL.md")
    checked_input(protocol.parent / "registration.json")
    if json.loads((protocol.parent / "registration.json").read_text())[
        "protocol_sha256"
    ] != file_sha256(protocol):
        raise ValueError("modified protocol")
    coins = universe()
    if args.fetch:
        args.raw.mkdir(parents=True, exist_ok=False)
        client = runpy.run_path(
            str(Path(__file__).with_name("fetch_research_history.py"))
        )["PublicResearchClient"](args.raw)
        try:
            for coin in coins:
                cursor, count = START, 0
                for _ in range(3):
                    if len(client.records) >= 60:
                        raise ValueError("funding screen request budget exhausted")
                    rows = client.info(
                        {
                            "type": "fundingHistory",
                            "coin": coin,
                            "startTime": cursor,
                            "endTime": END - 1,
                        }
                    )
                    if not rows:
                        break
                    times = [int(r["time"]) for r in rows]
                    if min(times) < cursor or max(times) >= END:
                        raise ValueError("invalid funding page")
                    count += len(rows)
                    cursor = max(times) + 1
                    time.sleep(2.5)
                    if cursor >= END - HOUR:
                        break
                print(coin, count, flush=True)
        finally:
            write_json(
                args.raw / "manifest.json",
                {
                    "coins": coins,
                    "requests": client.records,
                    "start_ms": START,
                    "end_ms_exclusive": END,
                    "response_bytes": client.total_bytes,
                    "code_sha256": file_sha256(Path(__file__)),
                    "data_cost_usd": 0,
                },
            )
        return
    if args.output is None:
        parser.error("--output required for offline analysis")
    args.output.mkdir(parents=True, exist_ok=False)
    checked_input(args.raw / "manifest.json")
    manifest = json.loads((args.raw / "manifest.json").read_text())
    if manifest["coins"] != coins:
        raise ValueError("universe changed")
    rates, sources = {c: {} for c in coins}, {}
    for record in manifest["requests"]:
        path = Path(record["path"])
        sources[str(path)] = checked_input(path)
        if sources[str(path)] != record["sha256"]:
            raise ValueError("manifest mismatch")
        raw = json.loads(path.read_text())
        if raw["returncode"]:
            raise ValueError("failed request")
        coin = raw["request"]["coin"]
        for row in raw["response"]:
            at = int(row["time"]) // HOUR * HOUR
            rate = D(row["fundingRate"])
            if (
                row["coin"] != coin
                or at in rates[coin]
                or not START <= at < END
                or not rate.is_finite()
            ):
                raise ValueError("invalid funding row")
            rates[coin][at] = rate
    results = {}
    for coin, rows in rates.items():
        missing = sorted(set(range(START, END, HOUR)) - rows.keys())
        total = sum(rows.values(), D(0))
        blocks = [
            sum(
                (
                    v
                    for t, v in rows.items()
                    if START + j * 168 * HOUR <= t < START + (j + 1) * 168 * HOUR
                ),
                D(0),
            )
            for j in range(5)
        ]
        without_best = total - sum(
            sorted((max(v, D(0)) for v in rows.values()), reverse=True)[:5], D(0)
        )
        criteria = {
            "complete_720_hours": not missing,
            "revenue_proxy_at_least_30_usd": 500 * total >= 30,
            "three_positive_full_weeks": sum(v > 0 for v in blocks[:4]) >= 3,
            "positive_without_top_five": without_best > 0,
        }
        results[coin] = {
            "hours": len(rows),
            "missing_hours_ms": missing,
            "sum_funding_rate": total,
            "constant_500_usd_short_revenue_proxy": 500 * total,
            "blocks_7d_rates": blocks,
            "min_hourly_rate": min(rows.values()) if rows else None,
            "max_hourly_rate": max(rows.values()) if rows else None,
            "positive_hour_fraction": sum(v > 0 for v in rows.values()) / len(rows)
            if rows
            else None,
            "rate_without_top_five": without_best,
            "criteria": criteria,
            "decision": "HEDGE_DATA_INVESTIGATION"
            if all(criteria.values())
            else "ECONOMIC_SCREEN_NOT_PASSED",
        }
    write_json(
        args.output / "summary.json",
        {
            "run_id": "wide-funding-2026-09-07",
            "assets": results,
            "universe": coins,
            "source_hashes": sources,
            "meta_sha256": checked_input(
                Path("data/wide_funding_2026-09-07/meta.json")
            ),
            "protocol_sha256": file_sha256(protocol),
            "code_sha256": file_sha256(Path(__file__)),
            "start_ms": START,
            "end_ms_exclusive": END,
            "promotion_authorized": False,
            "data_cost_usd": 0,
            "limits": [
                "current universe survivorship; retrospective feasibility only",
                "fixed-notional proxy with free rebalancing, not actual hedge PnL",
                "no spot borrow qualified for receiving negative funding",
                "prices, execution, margin, fees and rate persistence unvalidated",
            ],
        },
    )
    print(args.output / "summary.json")


if __name__ == "__main__":
    main()
