"""Bounded, credential-free USDC futures market history; no account routes."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path
from urllib.parse import urlencode

from hyperbot2.research.artifacts import file_sha256, write_json

START, END = 1773100800000, 1788652800000
HOUR = 3600000


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    records, total_bytes = [], 0
    try:
        for coin in ("BTC", "ETH", "SOL"):
            for route in ("klines", "fundingRate"):
                cursor, count = START, 0
                while cursor < END:
                    if len(records) >= 40 or total_bytes >= 20_000_000:
                        raise ValueError("public acquisition budget exhausted")
                    query = {
                        "symbol": coin + "USDC",
                        "startTime": cursor,
                        "endTime": END - 1,
                        "limit": 1000,
                    }
                    if route == "klines":
                        query["interval"] = "1h"
                    url = (
                        "https://fapi.binance.com/fapi/v1/"
                        + route
                        + "?"
                        + urlencode(query)
                    )
                    sent = time.time_ns() // 1_000_000
                    response = subprocess.run(
                        [
                            "curl",
                            "--fail-with-body",
                            "--max-time",
                            "20",
                            "--max-filesize",
                            "2000000",
                            "-sS",
                            url,
                        ],
                        capture_output=True,
                        timeout=25,
                        check=False,
                    )
                    total_bytes += len(response.stdout)
                    payload = {
                        "url": url,
                        "route": route,
                        "coin": coin,
                        "query": query,
                        "sent_ms": sent,
                        "received_ms": time.time_ns() // 1_000_000,
                        "returncode": response.returncode,
                    }
                    try:
                        payload["response"] = json.loads(response.stdout)
                    except ValueError:
                        payload["response"] = response.stdout.decode(errors="replace")[
                            :1000
                        ]
                    path = args.output / f"request-{len(records):03d}.json"
                    checksum = write_json(path, payload)
                    records.append({"path": str(path), "sha256": checksum})
                    write_json(args.output / f"index-{len(records):03d}.json", records)
                    if response.returncode or not isinstance(payload["response"], list):
                        raise ValueError(f"public request failed: {coin}/{route}")
                    rows = payload["response"]
                    if not rows:
                        break
                    times = [
                        int(r[0] if route == "klines" else r["fundingTime"])
                        for r in rows
                    ]
                    if (
                        times != sorted(set(times))
                        or min(times) < cursor
                        or max(times) >= END
                    ):
                        raise ValueError("invalid page timestamps")
                    count += len(rows)
                    cursor = max(times) + (HOUR if route == "klines" else 1)
                    time.sleep(0.5)
                print(coin, route, count, flush=True)
    finally:
        write_json(
            args.output / "manifest.json",
            {
                "start_ms": START,
                "end_ms_exclusive": END,
                "requests": records,
                "response_bytes": total_bytes,
                "script_sha256": file_sha256(Path(__file__)),
                "data_cost_usd": 0,
            },
        )


if __name__ == "__main__":
    main()
