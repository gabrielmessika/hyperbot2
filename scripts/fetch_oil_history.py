"""Bounded public Brent backfill; WTI history is already available locally."""

from __future__ import annotations

import argparse
import json
import time
from datetime import UTC, datetime
from pathlib import Path

from fetch_research_history import PublicResearchClient

from hyperbot2.research.artifacts import checked_input, file_sha256, write_json

START = int(datetime(2026, 3, 31, tzinfo=UTC).timestamp() * 1000)
END = int(datetime(2026, 9, 6, tzinfo=UTC).timestamp() * 1000)
COIN = "xyz:BRENTOIL"
REPORT = Path("reports/oil_ratio_2026-09-07")


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
        bars = client.info(
            {
                "type": "candleSnapshot",
                "req": {
                    "coin": COIN,
                    "interval": "1h",
                    "startTime": START,
                    "endTime": END - 1,
                },
            }
        )
        print(COIN, "candles", len(bars), flush=True)
        cursor, count = START, 0
        for _ in range(9):
            if len(client.records) >= 10 or client.total_bytes >= 10_000_000:
                raise ValueError("registered public data budget exhausted")
            rows = client.info(
                {
                    "type": "fundingHistory",
                    "coin": COIN,
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
            if cursor >= END - 3_600_000:
                break
        print(COIN, "funding", count, flush=True)
    finally:
        write_json(
            args.output / "manifest.json",
            {
                "start_ms": START,
                "end_ms_exclusive": END,
                "coins": [COIN],
                "requests": client.records,
                "response_bytes": client.total_bytes,
                "protocol_sha256": protocol,
                "data_cost_usd": 0,
                "code_hashes": {
                    str(p): file_sha256(p)
                    for p in (Path(__file__), Path("scripts/fetch_research_history.py"))
                },
            },
        )


if __name__ == "__main__":
    main()
