"""Bounded public hedge data acquisition, never account or trading endpoints."""

from __future__ import annotations

import argparse
import json
import runpy
import subprocess
import time
from pathlib import Path

from hyperbot2.research.artifacts import checked_input, file_sha256, write_json

START, OLD_END, END = 1784073600000, 1786060800000, 1788652800000


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--boundaries", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    protocol = Path("reports/wide_funding_2026-09-07/CASHCAT_PROTOCOL.md")
    checked_input(protocol.parent / "cashcat_registration.json")
    if json.loads((protocol.parent / "cashcat_registration.json").read_text())[
        "protocol_sha256"
    ] != file_sha256(protocol):
        raise ValueError("modified hedge protocol")
    client_path = Path(__file__).with_name("fetch_research_history.py")
    client = runpy.run_path(str(client_path))["PublicResearchClient"](
        args.output / "hl"
    )
    records, total = [], 0
    begin = END - 3600000 if args.boundaries else START
    finish = END + 25 * 3600000 if args.boundaries else END
    funding_start = END if args.boundaries else START
    funding_end = finish if args.boundaries else OLD_END
    urls = {
        "spot_symbol": "https://api.kucoin.com/api/v2/symbols/CASHCAT-USDT",
        "spot_currency": "https://api.kucoin.com/api/v3/currencies/CASHCAT",
        "spot_book": "https://api.kucoin.com/api/v1/market/orderbook/level2_20?symbol=CASHCAT-USDT",
        "spot_klines": (
            "https://api.kucoin.com/api/ua/v1/market/kline?tradeType=SPOT"
            "&symbol=CASHCAT-USDT&interval=1hour"
            f"&startAt={begin // 1000}&endAt={finish // 1000}"
        ),
        "fx_klines_1": (
            "https://api.binance.com/api/v3/klines?symbol=USDCUSDT&interval=1h"
            f"&startTime={begin}&endTime={finish}&limit=1000"
        ),
        "fx_klines_2": (
            "https://api.binance.com/api/v3/klines?symbol=USDCUSDT&interval=1h"
            f"&startTime={START + 1000 * 3600000}&endTime={END}&limit=1000"
        ),
    }
    if args.boundaries:
        urls = {k: v for k, v in urls.items() if k in ("spot_klines", "fx_klines_1")}
    try:
        for label, url in urls.items():
            if len(records) >= 10 or total >= 20_000_000:
                raise ValueError("public GET budget exhausted")
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
            total += len(response.stdout)
            payload = {
                "url": url,
                "sent_ms": sent,
                "received_ms": time.time_ns() // 1_000_000,
                "returncode": response.returncode,
            }
            try:
                payload["response"] = json.loads(response.stdout)
            except ValueError:
                payload["response"] = response.stdout.decode(errors="replace")[:1000]
            path = args.output / f"{label}.json"
            checksum = write_json(path, payload)
            records.append(
                {
                    "path": str(path),
                    "sha256": checksum,
                    "returncode": response.returncode,
                }
            )
            print(
                label,
                "rc",
                response.returncode,
                "bytes",
                len(response.stdout),
                flush=True,
            )
        client.info(
            {
                "type": "candleSnapshot",
                "req": {
                    "coin": "CASHCAT",
                    "interval": "1h",
                    "startTime": begin,
                    "endTime": finish,
                },
            }
        )
        cursor = funding_start
        for _ in range(3):
            rows = client.info(
                {
                    "type": "fundingHistory",
                    "coin": "CASHCAT",
                    "startTime": cursor,
                    "endTime": funding_end - 1,
                }
            )
            if not rows:
                break
            times = [int(r["time"]) for r in rows]
            if min(times) < cursor or max(times) >= funding_end:
                raise ValueError("invalid funding page")
            cursor = max(times) + 1
            time.sleep(2.5)
            if cursor >= funding_end - 3600000:
                break
        if not args.boundaries:
            client.info({"type": "l2Book", "coin": "CASHCAT"})
    finally:
        write_json(
            args.output / "manifest.json",
            {
                "external_requests": records,
                "native_requests": client.records,
                "response_bytes": total + client.total_bytes,
                "data_cost_usd": 0,
                "start_ms": START,
                "end_ms": END,
                "code_hashes": {
                    str(p): file_sha256(p) for p in (Path(__file__), client_path)
                },
            },
        )


if __name__ == "__main__":
    main()
