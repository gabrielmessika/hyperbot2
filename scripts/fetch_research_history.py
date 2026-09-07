"""Fetch a bounded public research dataset without credentials or trading routes."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from hyperbot2.research.artifacts import file_sha256, write_json

COINS = ("BTC", "ETH", "SOL", "HYPE")
END = int(datetime(2026, 9, 6, tzinfo=UTC).timestamp() * 1000)
START = END - int(timedelta(days=180).total_seconds() * 1000)


class PublicResearchClient:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.records: list[dict[str, Any]] = []
        self.total_bytes = 0

    def info(self, payload: dict[str, Any]) -> Any:
        if payload.get("type") not in {
            "candleSnapshot",
            "fundingHistory",
            "outcomeMeta",
            "l2Book",
            "spotMeta",
        }:
            raise ValueError("public research request type required")
        if len(self.records) >= 100 or self.total_bytes >= 50_000_000:
            raise ValueError("research request/data budget exhausted")
        started = time.time_ns() // 1_000_000
        response = subprocess.run(
            [
                "curl",
                "--fail-with-body",
                "--max-time",
                "20",
                "--max-filesize",
                "5000000",
                "-sS",
                "https://api.hyperliquid.xyz/info",
                "-H",
                "Content-Type: application/json",
                "--data-binary",
                json.dumps(payload),
            ],
            capture_output=True,
            timeout=25,
            check=False,
        )
        received = time.time_ns() // 1_000_000
        self.total_bytes += len(response.stdout)
        item: dict[str, Any] = {
            "request": payload,
            "sent_ms": started,
            "received_ms": received,
            "returncode": response.returncode,
            "response_bytes": len(response.stdout),
        }
        try:
            item["response"] = json.loads(response.stdout)
        except ValueError:
            item["error"] = response.stdout.decode(errors="replace")[:1000]
        path = self.root / f"request-{len(self.records):03d}.json"
        checksum = write_json(path, item)
        self.records.append(
            {
                "path": str(path),
                "sha256": checksum,
                "request": payload,
                "returncode": response.returncode,
            }
        )
        write_json(self.root / f"index-{len(self.records):03d}.json", self.records)
        if response.returncode:
            raise ValueError(f"public API failed: {response.returncode}")
        return item["response"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    client = PublicResearchClient(args.output)
    for coin in COINS:
        candles = client.info(
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
        print(coin, "candles", len(candles), flush=True)
        cursor = START
        count = 0
        for _ in range(12):
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
                raise ValueError("funding page outside requested interval")
            count += len(rows)
            cursor = max(times) + 1
            if cursor >= END:
                break
        else:
            raise ValueError("funding pagination budget exhausted")
        print(coin, "funding", count, flush=True)
    metadata = client.info({"type": "outcomeMeta"})
    client.info({"type": "spotMeta"})
    write_json(
        args.output / "manifest.json",
        {
            "start_ms": START,
            "end_ms_exclusive": END,
            "requests": client.records,
            "response_bytes": client.total_bytes,
            "script_sha256": file_sha256(Path(__file__)),
            "metadata_keys": list(metadata) if isinstance(metadata, dict) else None,
            "classification": "public historical research; not receipt-causal A books",
        },
    )


if __name__ == "__main__":
    main()
