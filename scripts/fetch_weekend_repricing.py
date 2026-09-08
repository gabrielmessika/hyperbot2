"""Bounded native history for a registered equity-weekend mechanism."""

from __future__ import annotations

import argparse
import json
import runpy
import time
from datetime import UTC, datetime
from pathlib import Path

from hyperbot2.research.artifacts import checked_input, file_sha256, write_json

COINS = ("xyz:TSLA", "xyz:NVDA", "xyz:HOOD", "xyz:META", "xyz:AMZN")
START = int(datetime(2026, 2, 12, tzinfo=UTC).timestamp() * 1000)
END = int(datetime(2026, 9, 6, tzinfo=UTC).timestamp() * 1000)
HOUR = 3600000


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    protocol = Path("reports/weekend_repricing_2026-09-07/PROTOCOL.md")
    checked_input(protocol.parent / "registration.json")
    if json.loads((protocol.parent / "registration.json").read_text())[
        "protocol_sha256"
    ] != file_sha256(protocol):
        raise ValueError("protocol changed")
    client_path = Path(__file__).with_name("fetch_research_history.py")
    client = runpy.run_path(str(client_path))["PublicResearchClient"](args.output)
    try:
        for coin in COINS:
            if len(client.records) >= 49:
                raise ValueError("insufficient remaining request budget for coin")
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
                if len(client.records) >= 60:
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
                    raise ValueError("invalid funding page range")
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
                "code_hashes": {
                    str(p): file_sha256(p) for p in (Path(__file__), client_path)
                },
                "data_cost_usd": 0,
            },
        )


if __name__ == "__main__":
    main()
