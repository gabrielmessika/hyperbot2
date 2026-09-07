"""Capture a bounded, simultaneous native/L4 witness without trading actions."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import runpy
import time
from pathlib import Path

from websockets.asyncio.client import connect

from hyperbot2.event_store import JsonlEventStore
from hyperbot2.models import EventContext, PublicMarketDataEvent
from hyperbot2.research.artifacts import file_sha256, write_json

SCRIPTS = Path(__file__).resolve().parent


async def native(output: Path, outcome: int, seconds: int) -> dict:
    store = JsonlEventStore(output / "raw")
    context = EventContext(
        run_id=f"paired-native-{time.time_ns()}",
        code_version="script-sha256:" + file_sha256(Path(__file__)),
        config_hash=hashlib.sha256(f"{outcome}:{seconds}:fast".encode()).hexdigest(),
        time_source="exchange",
    )
    started = time.monotonic()
    sequence = total = 0
    reason = "duration"
    try:
        async with connect(
            "wss://api.hyperliquid.xyz/ws",
            open_timeout=10,
            close_timeout=3,
            max_size=2_000_000,
            max_queue=32,
            ping_interval=10,
        ) as ws:
            for side in (0, 1):
                await ws.send(
                    json.dumps(
                        {
                            "method": "subscribe",
                            "subscription": {
                                "type": "l2Book",
                                "coin": f"#{outcome * 10 + side}",
                                "fast": True,
                            },
                        }
                    )
                )
            while time.monotonic() - started < seconds:
                try:
                    raw = await asyncio.wait_for(
                        ws.recv(), max(0.01, seconds - (time.monotonic() - started))
                    )
                except TimeoutError:
                    break
                received, mono = time.time_ns() // 1_000_000, time.monotonic_ns()
                if isinstance(raw, bytes):
                    raw = raw.decode()
                total += len(raw.encode())
                if total > 20_000_000 or sequence >= 100_000:
                    reason = "data_budget"
                    break
                message = json.loads(raw)
                data = message.get("data", {})
                kind = message.get("channel", "unknown")
                is_book = kind == "l2Book"
                store.append(
                    "native",
                    PublicMarketDataEvent(
                        context,
                        kind,
                        data["coin"] if is_book else "control",
                        data["time"] if is_book else None,
                        received,
                        mono,
                        sequence,
                        raw,
                    ),
                )
                sequence += 1
                if kind == "error":
                    reason = "error"
                    break
    except Exception as exc:
        reason = "exception:" + type(exc).__name__
    path = output / "raw/native.jsonl"
    return {
        "stop_reason": reason,
        "messages": sequence,
        "wire_bytes": total,
        "seconds_elapsed": time.monotonic() - started,
        "raw_sha256": file_sha256(path) if path.exists() else None,
    }


async def capture(output: Path, outcome: int, key: str, seconds: int) -> None:
    if outcome < 0 or not 1 <= seconds <= 120:
        raise ValueError("nonnegative outcome and 1..120 seconds required")
    if not key or any(c in key for c in "\r\n\x00"):
        raise ValueError("invalid key format")
    output.mkdir(parents=True, exist_ok=False)
    start = time.time_ns() // 1_000_000
    archive = runpy.run_path(str(SCRIPTS / "witness_archive_l4.py"))["witness"]
    native_report, _ = await asyncio.gather(
        native(output, outcome, seconds),
        archive(output / "archive", outcome, key, seconds, "hip4_l4_diffs"),
    )
    write_json(
        output / "capture.json",
        {
            "run_id": f"paired-{outcome}-{start}",
            "outcome_id": outcome,
            "started_ms": start,
            "ended_ms": time.time_ns() // 1_000_000,
            "seconds_requested": seconds,
            "native": native_report,
            "script_sha256": file_sha256(Path(__file__)),
            "archive_script_sha256": file_sha256(SCRIPTS / "witness_archive_l4.py"),
            "queue_qualified": False,
            "promotion_authorized": False,
        },
    )
    print(output / "capture.json")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--key-file", type=Path, required=True)
    parser.add_argument("--outcome-id", type=int, required=True)
    parser.add_argument("--seconds", type=int, default=60)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    key = runpy.run_path(str(SCRIPTS / "probe_l4_archive.py"))["read_key"](
        args.key_file
    )
    asyncio.run(capture(args.output, args.outcome_id, key, args.seconds))


if __name__ == "__main__":
    main()
