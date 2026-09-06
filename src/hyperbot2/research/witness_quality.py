"""Receipt-based fast-feed diagnostics without equating snapshots with fills."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from hyperbot2.event_store import JsonlEventStore
from hyperbot2.outcomes.config import OutcomeConfig
from hyperbot2.research.artifacts import file_sha256


def witness_quality(root: Path, config: OutcomeConfig) -> dict[str, Any]:
    store = JsonlEventStore(root)
    counts: Counter[str] = Counter()
    levels: Counter[int] = Counter()
    prior: dict[str, int] = {}
    per_coin: dict[str, Counter[str]] = {}
    for record in store.iter_records("outcomes-fast-public"):
        event = record["payload"]
        assert isinstance(event, dict)
        if event["channel"] != "l2Book":
            continue
        payload = json.loads(str(event["payload_json"]))
        coin = str(event["coin"])
        exchange = int(str(event["exchange_ts_ms"]))
        received = int(str(event["receive_ts_ms"]))
        age = received - exchange
        local = per_coin.setdefault(coin, Counter())
        for target in (counts, local):
            target["books"] += 1
            target["fast_confirmed_in_payload"] += int(payload.get("fast") is True)
            target["distinct_exchange_updates"] += int(exchange != prior.get(coin))
            target["negative_age"] += int(age < 0)
            target["fresh_at_receipt"] += int(0 <= age <= config.stale_ms)
            target["fresh_at_activation_base"] += int(
                age >= 0
                and age + config.placement_ms + config.clock_uncertainty_ms
                <= config.stale_ms
            )
            target["fresh_at_activation_latency_x2"] += int(
                age >= 0
                and age + 2 * config.placement_ms + config.clock_uncertainty_ms
                <= config.stale_ms
            )
        prior[coin] = exchange
        for side in payload["levels"]:
            levels[len(side)] += 1
    return {
        "counts": dict(counts),
        "per_coin": per_coin,
        "levels_per_side": levels,
        "raw_sha256": file_sha256(root / "outcomes-fast-public.jsonl"),
        "raw_bytes": sum(p.stat().st_size for p in root.rglob("*") if p.is_file()),
        "queue_qualified": False,
        "interpretation": "event-weighted receipt observations; no time-coverage gate",
    }
