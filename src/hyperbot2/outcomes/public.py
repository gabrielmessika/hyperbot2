"""Bounded public witness; no credentials, signing or trading endpoint."""

from __future__ import annotations

import asyncio
import json
import subprocess
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from hyperbot2.event_store import JsonlEventStore
from hyperbot2.models import EventContext
from hyperbot2.outcomes.catalog import discover_recurring
from hyperbot2.research.artifacts import CampaignBudget, write_json
from hyperbot2.research.witness_quality import witness_quality
from hyperbot2.services.public_collector import (
    CollectorConfig,
    PublicWebSocketCollector,
    Subscription,
)


def public_info(payload: dict[str, Any]) -> Any:
    if payload.get("type") not in {"outcomeMeta", "l2Book", "metaAndAssetCtxs"}:
        raise ValueError("not an allowed public discovery request")
    if set(payload) - {"type", "coin"}:
        raise ValueError("private or unexpected request fields")
    response = subprocess.run(
        [
            "curl",
            "--fail-with-body",
            "--max-time",
            "20",
            "-sS",
            "https://api.hyperliquid.xyz/info",
            "-H",
            "Content-Type: application/json",
            "--data-binary",
            json.dumps(payload),
        ],
        capture_output=True,
        check=True,
        timeout=25,
    )
    return json.loads(response.stdout)


async def witness(
    *,
    output: Path,
    context: EventContext,
    seconds: int,
    budget: CampaignBudget,
) -> dict[str, Any]:
    if not 1 <= seconds <= 3600:
        raise ValueError("witness duration must be within 1..3600 seconds")
    metadata = public_info({"type": "outcomeMeta"})
    observed_ms = time.time_ns() // 1_000_000
    write_json(output / "outcome_meta.json", metadata)
    definitions, issues = discover_recurring(metadata, observed_ms=observed_ms)
    if not definitions:
        raise ValueError("no supported recurring markets")
    subscriptions = tuple(
        Subscription(channel, coin, channel == "l2Book")
        for d in definitions
        for coin in (d.coin, f"#{d.outcome_id * 10 + 1}")
        for channel in ("l2Book", "trades")
    )
    store = JsonlEventStore(output / "raw")
    collector = PublicWebSocketCollector(
        config=CollectorConfig(
            subscriptions,
            data_stream="outcomes-fast-public",
            control_stream="outcomes-fast-control",
        ),
        context=context,
        store=store,
    )
    stop = asyncio.Event()
    task = asyncio.create_task(collector.run(stop))
    started = time.monotonic()
    try:
        while time.monotonic() - started < seconds:
            await asyncio.sleep(min(1, seconds - (time.monotonic() - started)))
            budget.check()
            if task.done():
                task.result()
                break
    finally:
        stop.set()
        metrics = await task
    report = {
        "run_id": context.run_id,
        "code_version": context.code_version,
        "config_sha256": context.config_hash,
        "observed_ms": observed_ms,
        "definitions": [asdict(d) for d in definitions],
        "catalog_issues": issues,
        "metrics": asdict(metrics),
        "quality": witness_quality(output / "raw", budget.config),
        "duration_seconds": time.monotonic() - started,
        "maximum_l2_levels_per_side": 5,
        "queue_qualified": False,
        "verdict": "DATA_BLOCKED",
        "promotion_authorized": False,
        "reasons": [
            "public witness only; fees, specification and execution need qualification"
        ],
    }
    write_json(output / "witness.json", report)
    return report
