"""Single-instance, bounded public shadow service with durable diagnostics."""

from __future__ import annotations

import asyncio
import fcntl
import hashlib
import json
import os
import signal
import threading
import time
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
from typing import Any

from hyperbot2.event_store import JsonlEventStore
from hyperbot2.models import DomainEvent, EventContext
from hyperbot2.outcomes.catalog import discover_recurring
from hyperbot2.outcomes.config import OutcomeConfig
from hyperbot2.outcomes.pipeline import ReferenceJoin, WindowAssembler, recorded_events
from hyperbot2.outcomes.public import public_info
from hyperbot2.outcomes.serialization import window_payload
from hyperbot2.outcomes.session import OutcomeSession, OutcomeWindow
from hyperbot2.replay.engine import FillModelKind
from hyperbot2.research.artifacts import (
    CampaignBudget,
    checked_input,
    file_sha256,
    write_json,
)
from hyperbot2.services.public_collector import (
    CollectorConfig,
    PublicWebSocketCollector,
    Subscription,
)


def atomic_status(path: Path, status: dict[str, Any]) -> None:
    raw = (json.dumps(status, default=str, sort_keys=True, indent=2) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    with temporary.open("wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


@contextmanager
def instance_lock(root: Path) -> Iterator[None]:
    root.mkdir(parents=True, exist_ok=True)
    with (root / ".runtime.lock").open("a") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError(
                "another HyperBot2 instance owns this data directory"
            ) from error
        yield


def read_health(root: Path, now_ms: int | None = None) -> tuple[dict[str, Any], bool]:
    try:
        value = json.loads((root / "status.json").read_text())
        age = (now_ms if now_ms is not None else time.time_ns() // 1_000_000) - value[
            "updated_ms"
        ]
        healthy = (
            value["state"] == "RUNNING"
            and 0 <= age <= 15_000
            and value.get("operational_healthy") is True
        )
        return {**value, "heartbeat_age_ms": age, "healthy": healthy}, healthy
    except (OSError, KeyError, ValueError, TypeError):
        return {"state": "UNAVAILABLE", "healthy": False}, False


class PipelineStore:
    """Persist raw before interpretation; serialize all derived writes under a lock."""

    def __init__(
        self,
        output: Path,
        definitions: tuple[Any, ...],
        config: OutcomeConfig,
        context: EventContext,
        references: ReferenceJoin | None = None,
    ) -> None:
        self.lock = threading.RLock()
        self.raw = JsonlEventStore(output / "raw")
        self.path = output / "windows.jsonl"
        self.stream = self.path.open("xb")
        self.sha256 = hashlib.sha256()
        self.sessions = {
            kind.value: OutcomeSession(config, context, kind, shadow=True)
            for kind in (FillModelKind.CENTRAL, FillModelKind.PESSIMISTIC)
        }
        self.pipeline = WindowAssembler(definitions, config, self.emit, references)
        self.closed = False

    def emit(self, window: OutcomeWindow) -> None:
        line = (
            json.dumps(window_payload(window), default=str, sort_keys=True) + "\n"
        ).encode()
        self.stream.write(line)
        self.stream.flush()
        os.fsync(self.stream.fileno())
        self.sha256.update(line)
        for session in self.sessions.values():
            session.process(window)

    def append(self, stream: str, event: DomainEvent) -> object:
        return self.append_many(stream, (event,))

    def append_many(self, stream: str, events: Sequence[DomainEvent]) -> object:
        with self.lock:
            result = tuple(self.raw.append(stream, event) for event in events)
            for event in events:
                self.pipeline.consume(asdict(event))
            return result

    def snapshot(self) -> dict[str, Any]:
        with self.lock:
            return {
                "counts": dict(self.pipeline.counts),
                "blockers": dict(self.pipeline.reasons),
                "verdict": "DATA_BLOCKED" if self.pipeline.reasons else "WARMING_UP",
            }

    def finish(self) -> dict[str, Any]:
        with self.lock:
            if self.closed:
                raise RuntimeError("pipeline already finalized")
            try:
                self.pipeline.finish()
                if not self.pipeline.counts["windows"]:
                    self.pipeline.reasons["no_completed_windows"] += 1
                results = {
                    name: session.finish() for name, session in self.sessions.items()
                }
                self.stream.flush()
                os.fsync(self.stream.fileno())
                self.path.with_suffix(".jsonl.sha256").write_text(
                    self.sha256.hexdigest() + "  windows.jsonl\n"
                )
                return {
                    **self.snapshot(),
                    "models": results,
                    "windows_sha256": self.sha256.hexdigest(),
                    "promotion_authorized": False,
                }
            finally:
                self.stream.close()
                self.closed = True


def prepare_capture(
    *,
    capture: Path,
    output: Path,
    config: OutcomeConfig,
    context: EventContext,
    attestations: Path | None = None,
    references: Path | None = None,
) -> dict[str, Any]:
    metadata_path = capture / "outcome_meta.json"
    metadata_hash = checked_input(metadata_path)
    witness_path = capture / "witness.json"
    runtime_manifest = capture / "manifest.json"
    clock_path = witness_path if witness_path.exists() else runtime_manifest
    checked_input(clock_path)
    observed_ms = json.loads(clock_path.read_text())["observed_ms"]
    att_hash = checked_input(attestations) if attestations else None
    att = json.loads(attestations.read_text()) if attestations else None
    definitions, issues = discover_recurring(
        json.loads(metadata_path.read_text()), observed_ms=observed_ms, attestations=att
    )
    output.mkdir(parents=True, exist_ok=False)
    sink = PipelineStore(
        output, definitions, config, context, ReferenceJoin(references)
    )
    sources = {str(p): file_sha256(p) for p in (capture / "raw").glob("*.jsonl")}
    budget = CampaignBudget(config, output)
    try:
        for index, event in enumerate(recorded_events(capture / "raw")):
            if index % 1000 == 0:
                budget.check()
            sink.pipeline.consume(event)
        result = sink.finish()
        if metadata_hash != file_sha256(metadata_path) or any(
            file_sha256(Path(p)) != h for p, h in sources.items()
        ):
            raise ValueError("capture changed during preparation")
        if attestations and att_hash != file_sha256(attestations):
            raise ValueError("attestations changed during preparation")
        report = {
            **result,
            "run_id": context.run_id,
            "sources": sources,
            "metadata_sha256": metadata_hash,
            "attestations_sha256": att_hash,
            "references_sha256": sink.pipeline.references.sha256,
            "catalog_issues": issues,
            "resources": budget.metrics(),
        }
        write_json(output / "prepare.json", report)
        return report
    finally:
        if not sink.closed:
            sink.stream.close()
        sink.pipeline.references.close()


async def run_service(
    *,
    root: Path,
    config: OutcomeConfig,
    context: EventContext,
    source_files: dict[str, str],
    seconds: int = 900,
    blocked_seconds: int = 300,
    stop: asyncio.Event | None = None,
    attestations: Path | None = None,
) -> dict[str, Any]:
    if (
        not 1 <= seconds <= min(86400, config.max_wall_seconds)
        or not 1 <= blocked_seconds <= seconds
    ):
        raise ValueError("invalid service duration/blocker budget")
    stop = stop or asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop.set)
    with instance_lock(root):
        output = root / "runs" / context.run_id
        output.mkdir(parents=True, exist_ok=False)
        budget = CampaignBudget(config, root)
        budget.check()
        previous_path = root / "status.json"
        if previous_path.exists():
            previous = json.loads(previous_path.read_text())
            if previous.get("state") in ("RUNNING", "STARTING", "STOPPING"):
                write_json(
                    output / "previous_interruption.json",
                    {
                        "previous_status": previous,
                        "economic_continuity": False,
                        "reason": "previous run unfinished; PnL invalid",
                    },
                )
        status: dict[str, Any] = {
            "state": "STARTING",
            "run_id": context.run_id,
            "code_version": context.code_version,
            "live_enabled": False,
            "shadow_only": True,
            "output": str(output),
            "updated_ms": time.time_ns() // 1_000_000,
            "operational_healthy": False,
            "mode": "public_shadow",
        }
        atomic_status(root / "status.json", status)
        sink: PipelineStore | None = None
        task: asyncio.Task[Any] | None = None
        started = time.monotonic()
        reason = "duration_complete"
        try:
            metadata = await asyncio.to_thread(public_info, {"type": "outcomeMeta"})
            observed_ms = time.time_ns() // 1_000_000
            att_hash = checked_input(attestations) if attestations else None
            att = json.loads(attestations.read_text()) if attestations else None
            definitions, issues = discover_recurring(
                metadata, observed_ms=observed_ms, attestations=att
            )
            if not definitions:
                raise ValueError("no supported recurring contracts")
            write_json(output / "outcome_meta.json", metadata)
            write_json(
                output / "manifest.json",
                {
                    "observed_ms": observed_ms,
                    "context": asdict(context),
                    "config": asdict(config),
                    "source_files": source_files,
                    "attestations_sha256": att_hash,
                    "catalog_issues": issues,
                    "duration_seconds": seconds,
                    "blocked_seconds": blocked_seconds,
                },
            )
            sink = PipelineStore(output, definitions, config, context)
            subscriptions = tuple(
                Subscription(channel, coin, channel == "l2Book")
                for d in definitions
                for coin in (d.coin, f"#{d.outcome_id * 10 + 1}")
                for channel in ("l2Book", "trades")
            )
            collector = PublicWebSocketCollector(
                config=CollectorConfig(
                    subscriptions,
                    heartbeat_interval_seconds=5,
                    stale_after_seconds=10,
                    data_stream="outcomes-fast-public",
                    control_stream="outcomes-fast-control",
                ),
                context=context,
                store=sink,
            )
            task = asyncio.create_task(collector.run(stop))
            while not stop.is_set() and time.monotonic() - started < seconds:
                await asyncio.sleep(1)
                budget.check()
                if task.done():
                    task.result()
                    if stop.is_set():
                        break
                    raise RuntimeError("collector exited unexpectedly")
                metrics = collector.metrics
                research = sink.snapshot()
                recent = metrics.last_message_receive_ms
                now = time.time_ns() // 1_000_000
                healthy = (
                    metrics.connected
                    and metrics.missing_subscription_count == 0
                    and metrics.dropped_events == 0
                    and metrics.clock_healthy
                    and recent is not None
                    and 0 <= now - recent < 10_000
                )
                status.update(
                    state="RUNNING",
                    updated_ms=now,
                    operational_healthy=healthy,
                    collector=asdict(metrics),
                    research=research,
                )
                atomic_status(root / "status.json", status)
                if (
                    research["blockers"]
                    and time.monotonic() - started >= blocked_seconds
                ):
                    reason = "input_blockers_budget_complete"
                    break
                if min(d.expiry_ms for d in definitions) <= now:
                    reason = "catalog_expired"
                    break
            if stop.is_set():
                reason = "operator_stop"
            status.update(
                state="STOPPING",
                updated_ms=time.time_ns() // 1_000_000,
                operational_healthy=False,
            )
            atomic_status(root / "status.json", status)
            stop.set()
            await asyncio.wait_for(task, timeout=25)
            result = sink.finish()
            result.update(
                run_id=context.run_id, stop_reason=reason, resources=budget.metrics()
            )
            write_json(output / "result.json", result)
            status.update(
                state="STOPPED",
                updated_ms=time.time_ns() // 1_000_000,
                stop_reason=reason,
                research=sink.snapshot(),
                operational_healthy=False,
            )
            atomic_status(root / "status.json", status)
            return result
        except BaseException as error:
            stop.set()
            if task and not task.done():
                try:
                    await asyncio.wait_for(task, 25)
                except BaseException:
                    task.cancel()
            if sink and not sink.closed:
                sink.stream.close()
            failure = {
                "exception": type(error).__name__,
                "reason": str(error),
                "run_id": context.run_id,
                "verdict": "DATA_BLOCKED",
                "promotion_authorized": False,
            }
            write_json(output / "failure.json", failure)
            status.update(
                state="FAILED",
                operational_healthy=False,
                updated_ms=time.time_ns() // 1_000_000,
                failure=failure,
            )
            atomic_status(root / "status.json", status)
            raise
        finally:
            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.remove_signal_handler(sig)
