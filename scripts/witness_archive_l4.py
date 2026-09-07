"""Bounded raw L4 WebSocket witness with receipt clocks and no trading actions."""

from __future__ import annotations

import argparse
import asyncio
import json
import runpy
import time
from collections import Counter
from pathlib import Path
from typing import Any

from websockets.asyncio.client import connect

from hyperbot2.event_store import JsonlEventStore
from hyperbot2.models import EventContext, PublicMarketDataEvent
from hyperbot2.research.artifacts import file_sha256, write_json


async def witness(
    output: Path, outcome: int, key: str, seconds: int, channel: str
) -> None:
    if channel not in ("hip4_l4_diffs", "hip4_l4_orders") or not 1 <= seconds <= 120:
        raise ValueError("bounded HIP-4 L4 witness required")
    output.mkdir(parents=True, exist_ok=False)
    store = JsonlEventStore(output / "raw")
    context = EventContext(
        run_id=f"archive-witness-{time.time_ns()}",
        code_version="script-sha256:" + file_sha256(Path(__file__)),
        config_hash=__import__("hashlib")
        .sha256(
            json.dumps(
                {"outcome": outcome, "seconds": seconds, "channel": channel},
                sort_keys=True,
            ).encode()
        )
        .hexdigest(),
        time_source="exchange",
    )
    counts: Counter[str] = Counter()
    ages: list[int] = []
    snapshots: list[int] = []
    fields: set[str] = set()
    per_coin: dict[str, list[int]] = {}
    active = set()
    total = sequence = 0
    stopped = "duration"
    started = time.monotonic()
    try:
        async with connect(
            "wss://api.0xarchive.io/ws",
            additional_headers={"Authorization": "Bearer " + key},
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
                            "op": "subscribe",
                            "channel": channel,
                            "symbol": f"#{outcome * 10 + side}",
                        }
                    )
                )
            while time.monotonic() - started < seconds:
                remaining = seconds - (time.monotonic() - started)
                try:
                    raw = await asyncio.wait_for(ws.recv(), max(0.01, remaining))
                except TimeoutError:
                    break
                received, monotonic = time.time_ns() // 1_000_000, time.monotonic_ns()
                if isinstance(raw, bytes):
                    raw = raw.decode()
                if key in raw:
                    raise ValueError("credential echo rejected")
                total += len(raw.encode())
                if total > 20_000_000 or sequence >= 100_000:
                    stopped = "data_budget"
                    break
                message = json.loads(raw)
                kind = str(message.get("type", "unknown"))
                counts[kind] += 1
                coin = str(message.get("coin", message.get("symbol", "control")))
                event_times = []
                if kind == "l4_batch":
                    for event in message["data"]:
                        fields.update(event)
                        timestamp = event.get("ts", event.get("timestamp"))
                        if type(timestamp) is int:
                            event_times.append(timestamp)
                            age = received - timestamp
                            ages.append(age)
                            per_coin.setdefault(coin, []).append(age)
                elif kind == "l4_snapshot" and type(message.get("timestamp")) is int:
                    event_times.append(message["timestamp"])
                    snapshots.append(received - message["timestamp"])
                if kind == "subscribed":
                    active.add(coin)
                store.append(
                    "archive-l4",
                    PublicMarketDataEvent(
                        context,
                        channel,
                        coin,
                        max(event_times) if event_times else None,
                        received,
                        monotonic,
                        sequence,
                        raw,
                    ),
                )
                sequence += 1
                if kind in ("error", "gap_detected", "replay_gap", "gap"):
                    stopped = kind
                    break
            # Closing ends this bounded subscription; there is no reconnect loop.
    except Exception as exc:
        stopped = "exception:" + type(exc).__name__
    summarize = runpy.run_path(
        str(Path(__file__).with_name("diagnose_feasibility.py"))
    )["distribution"]
    raw_path = output / "raw/archive-l4.jsonl"
    report: dict[str, Any] = {
        "run_id": context.run_id,
        "script_sha256": file_sha256(Path(__file__)),
        "channel": channel,
        "outcome_id": outcome,
        "seconds_requested": seconds,
        "seconds_elapsed": time.monotonic() - started,
        "counts": dict(counts),
        "active_subscriptions": sorted(active),
        "received_bytes": total,
        "stop_reason": stopped,
        "snapshot_envelope_age_ms": summarize(snapshots),
        "diff_event_age_ms": summarize(ages),
        "per_coin_diff_age_ms": {c: summarize(a) for c, a in per_coin.items()},
        "diff_fields": sorted(fields),
        "diff_events": len(ages),
        "diff_events_with_age_0_to_500_ms": sum(0 <= a <= 500 for a in ages),
        "diff_events_with_age_0_to_100_ms": sum(0 <= a <= 100 for a in ages),
        "raw_path": str(raw_path),
        "raw_sha256": file_sha256(raw_path) if raw_path.exists() else None,
        "queue_qualified": False,
        "promotion_authorized": False,
        "limits": [
            "event ages, not time coverage or order placement latency",
            "snapshot envelope time is not a chain completeness watermark",
            "no sequence or continuity qualification from a quiet subscription",
            "local clock and provider timestamps may have offsets",
        ],
    }
    write_json(output / "report.json", report)
    print(output / "report.json")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--key-file", type=Path, required=True)
    parser.add_argument("--outcome-id", type=int, required=True)
    parser.add_argument("--seconds", type=int, default=30)
    parser.add_argument("--channel", default="hip4_l4_diffs")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    key = runpy.run_path(str(Path(__file__).with_name("probe_l4_archive.py")))[
        "read_key"
    ](args.key_file)
    asyncio.run(witness(args.output, args.outcome_id, key, args.seconds, args.channel))


if __name__ == "__main__":
    main()
