"""Prior-period replication of the exploratory 72-hour funding continuation."""

from __future__ import annotations

import argparse
import json
import time
from decimal import Decimal
from pathlib import Path

from fetch_research_history import PublicResearchClient
from investigate_funding_normalization import (
    OLD,
    REPORT,
    ROOT,
    SCENARIOS,
    load,
    registered,
    study,
    summarize,
)

from hyperbot2.research.artifacts import (
    checked_input,
    file_sha256,
    source_version,
    write_json,
)
from hyperbot2.research.funding_normalization import event_return
from hyperbot2.research.rotation import HOUR

D = Decimal
START, END = 1784160000000, 1786060800000


def fetch(output: Path, coins: list[str], protocol: str) -> None:
    output.mkdir(parents=True, exist_ok=False)
    client = PublicResearchClient(output)

    def request(query: dict) -> list:
        if len(client.records) >= 54 or client.total_bytes >= 10_000_000:
            raise ValueError("registered public data budget exhausted")
        rows = client.info(query)
        time.sleep(2.5)
        return rows

    try:
        for c in coins:
            if c == "CASHCAT":
                continue
            bars = request(
                {
                    "type": "candleSnapshot",
                    "req": {
                        "coin": c,
                        "interval": "1h",
                        "startTime": START,
                        "endTime": END - 1,
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
                        "endTime": END - 1,
                    }
                )
                if not rows:
                    break
                times = [int(r["time"]) for r in rows]
                if min(times) < cursor or max(times) >= END:
                    raise ValueError("funding page outside requested interval")
                count += len(rows)
                cursor = max(times) + 1
                if cursor >= END - HOUR:
                    break
            print(c, "candles", len(bars), "funding", count, flush=True)
    finally:
        write_json(
            output / "manifest.json",
            {
                "requests": client.records,
                "response_bytes": client.total_bytes,
                "coins": coins,
                "start_ms": START,
                "end_ms_exclusive": END,
                "protocol_sha256": protocol,
                "code_sha256": file_sha256(Path(__file__)),
                "data_cost_usd": 0,
            },
        )


def controls(events: list[dict], bars: dict, payments: dict) -> dict:
    opens = {c: [b.open for b in rows] for c, rows in bars.items()}

    def net(c: str, i: int, side: int) -> Decimal:
        return event_return(
            opens[c],
            START,
            payments[c],
            i,
            72,
            side,
            D("0.00045"),
            D("0.0002"),
            "signed",
        )["net_bps"]

    grids = {}
    for c in opens:
        for side in (-1, 1):
            values = [net(c, i, side) for i in range(12, len(opens[c]) - 73, 73)]
            grids[c, side] = sum(values, D(0)) / len(values)
    rows = []
    for e in events:
        c, side = e["coin"], e["side"]
        i = (e["entry_ms"] - START - 60_000) // HOUR
        actual = net(c, i, side)
        if actual != e["returns"]["72"]["base"]["net_bps"]:
            raise ValueError("event/control accounting mismatch")
        market = sum((net(other, i, side) for other in opens if other != c), D(0)) / (
            len(opens) - 1
        )
        rows.append(
            {
                "coin": c,
                "entry_ms": e["entry_ms"],
                "actual_bps": actual,
                "market_bps": market,
                "grid_bps": grids[c, side],
            }
        )
    return {
        "rows": rows,
        "means_bps": {
            k: sum((r[k] for r in rows), D(0)) / len(rows) if rows else None
            for k in ("actual_bps", "market_bps", "grid_bps")
        },
        "descriptive_only": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fetch", action="store_true")
    args = parser.parse_args()
    _, coins = registered()
    path = REPORT / "replication_registration.json"
    checked_input(path)
    protocol = file_sha256(REPORT / "REPLICATION_PROTOCOL.md")
    registration = json.loads(path.read_text())
    if registration["protocol_sha256"] != protocol or registration[
        "discovery_summary_sha256"
    ] != checked_input(REPORT / "summary.json"):
        raise ValueError("replication registration changed")
    if args.fetch:
        fetch(args.output, coins, protocol)
        return
    args.output.mkdir(parents=True, exist_ok=False)
    bars, payments, rates, quality = load(
        [OLD / "cashcat_hedge", ROOT / "replication_history"], coins, START, END
    )
    selected = study(bars, payments, rates, START, END)["continuation"]
    selected.sort(key=lambda e: (e["entry_ms"], e["coin"]))
    stats = {s: summarize(selected, "72", s, START, 10) for s in SCENARIOS}
    base = stats["base"]
    criteria = {
        "all_paid_scenarios_positive": all(
            stats[s]["sum_net_bps"] > 0 for s in SCENARIOS if s != "zero_cost"
        ),
        "profit_factor_above_1_2": (base["profit_factor"] or 0) > D("1.2"),
        "positive_without_best": (base["sum_without_best_bps"] or 0) > 0,
    }
    write_json(args.output / "events.json", selected)
    write_json(args.output / "quality.json", quality)
    write_json(args.output / "controls.json", controls(selected, bars, payments))
    write_json(
        args.output / "summary.json",
        {
            "run_id": "funding-normalization-prior-20260907-v1",
            "protocol_sha256": protocol,
            "code_version": source_version(Path.cwd())[0],
            "scripts": {
                str(p): file_sha256(p)
                for p in (
                    Path(__file__),
                    Path("scripts/investigate_funding_normalization.py"),
                )
            },
            "start_ms": START,
            "end_ms_exclusive": END,
            "primary_horizon_hours": 72,
            "statistics": stats,
            "criteria": criteria,
            "decision": "PORTFOLIO_RESEARCH_REQUIRED"
            if all(criteria.values())
            else "REPLICATION_NOT_CONFIRMED",
            "distinct_entry_days": len(
                {e["entry_ms"] // (24 * HOUR) for e in selected}
            ),
            "live_enabled": False,
            "promotion_authorized": False,
            "limitations": [
                "short prior period, not independent of all previous work",
                "event returns, not portfolio returns or drawdown",
                "hourly open execution and funding oracle proxies",
            ],
        },
    )
    print(
        "events",
        base["events"],
        "mean bps",
        base["mean_net_bps"],
        "criteria",
        criteria,
        flush=True,
    )


if __name__ == "__main__":
    main()
