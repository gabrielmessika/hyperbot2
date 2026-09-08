"""Fetch registered commodity history through the existing public-only client."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from fetch_research_history import PublicResearchClient
from fetch_weekend_repricing import END, HOUR, START

from hyperbot2.research.artifacts import checked_input, file_sha256, write_json

COINS = ("xyz:GOLD", "xyz:SILVER", "xyz:CL")
REPORT = Path("reports/commodity_trend_2026-09-07")


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
    client = PublicResearchClient(args.output)
    try:
        for coin in COINS:
            bars = client.info(
                {
                    "type": "candleSnapshot",
                    "req": {
                        "coin": coin,
                        "interval": "1h",
                        "startTime": START,
                        "endTime": END - 1,
                    },
                }
            )
            print(coin, "candles", len(bars), flush=True)
            cursor, count = START, 0
            for _ in range(10):
                if len(client.records) >= 40:
                    raise ValueError("registered request budget exhausted")
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
                    raise ValueError("funding page range mismatch")
                cursor = max(times) + 1
                count += len(rows)
                time.sleep(2.5)
                if cursor >= END - HOUR:
                    break
            print(coin, "funding", count, flush=True)
    finally:
        write_json(
            args.output / "manifest.json",
            {
                "coins": COINS,
                "start_ms": START,
                "end_ms_exclusive": END,
                "requests": client.records,
                "response_bytes": client.total_bytes,
                "protocol_sha256": protocol,
                "data_cost_usd": 0,
                "code_hashes": {
                    str(p): file_sha256(p)
                    for p in (
                        Path(__file__),
                        Path("scripts/fetch_research_history.py"),
                        Path("scripts/fetch_weekend_repricing.py"),
                    )
                },
            },
        )


if __name__ == "__main__":
    main()
