from __future__ import annotations

import asyncio
import json
import time
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest
from websockets.asyncio.server import serve

from hyperbot2.models import EventContext, TimeSource
from hyperbot2.outcomes.catalog import discover_recurring
from hyperbot2.outcomes.config import OutcomeConfig
from hyperbot2.outcomes.pipeline import ReferenceJoin, WindowAssembler
from hyperbot2.research.artifacts import checked_input, file_sha256
from hyperbot2.services import runtime
from hyperbot2.services.public_collector import PublicWebSocketCollector


def metadata() -> dict:
    return {
        "outcomes": [
            {
                "name": "Recurring",
                "outcome": 1,
                "quoteToken": "USDC",
                "description": (
                    "class:priceBinary|underlying:BTC|expiry:20990101-0600|"
                    "targetPrice:80000|period:1d"
                ),
                "sideSpecs": [{"name": "Yes"}, {"name": "No"}],
            }
        ]
    }


def event(now: int, coin: str = "#10") -> dict:
    return {
        "receive_ts_ms": now,
        "local_sequence": now,
        "coin": coin,
        "channel": "l2Book",
        "payload_json": json.dumps(
            {
                "coin": coin,
                "time": now,
                "fast": True,
                "levels": [[{"px": ".4", "sz": "30"}], [{"px": ".6", "sz": "30"}]],
            }
        ),
    }


def test_assembler_preserves_gaps_and_unqualified_public_queue() -> None:
    definitions, _ = discover_recurring(metadata(), observed_ms=0)
    windows = []
    assembler = WindowAssembler(definitions, OutcomeConfig(), windows.append)
    assembler.consume(event(1000))
    assembler.consume(event(1200, "#11"))
    assembler.consume({"receive_ts_ms": 1300, "kind": "gap"})
    assembler.consume(event(2500))
    assembler.finish()
    assert len(windows) == 2
    assert all(not w.exposure_healthy for w in windows)
    assert all(not w.book.queue_qualified for w in windows)
    assert assembler.counts["no_book_representation_skipped"] == 1
    assert "public_queue_unqualified" in assembler.reasons


def test_assembler_skips_historical_trade_snapshot() -> None:
    definitions, _ = discover_recurring(metadata(), observed_ms=0)
    windows = []
    assembler = WindowAssembler(definitions, OutcomeConfig(), windows.append)
    assembler.consume(event(1000))
    trade = {
        "receive_ts_ms": 1200,
        "local_sequence": 1,
        "coin": "#10",
        "channel": "trades",
        "payload_json": json.dumps(
            {"coin": "#10", "time": 500, "tid": 1, "side": "A", "px": ".4", "sz": "10"}
        ),
    }
    assembler.consume(trade)
    assembler.finish()
    assert windows[0].trades == ()
    assert assembler.counts["historical_trade_snapshot_skipped"] == 1


def test_reference_join_is_causal_and_hash_checked(tmp_path: Path) -> None:
    path = tmp_path / "refs.jsonl"
    rows = [
        {
            "kind": "settlement_mark",
            "underlying": "BTC",
            "exchange_ms": t,
            "received_ms": t,
            "price": p,
            "source_sha256": "a" * 64,
        }
        for t, p in (
            (0, "80000"),
            (60000, "80001"),
            (120000, "79999"),
            (180000, "90000"),
        )
    ]
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    path.with_suffix(".jsonl.sha256").write_text(file_sha256(path))
    join = ReferenceJoin(path)
    definitions, _ = discover_recurring(metadata(), observed_ms=0)
    definition = replace(definitions[0], expiry_ms=86400000)
    assert join.predict(definition, 119999) is None
    value = join.predict(definition, 120000)
    assert value is not None and value.reference_ms == 120000
    assert join.models["BTC"].latest.price == Decimal("79999")
    path.write_text("modified")
    with pytest.raises(ValueError, match="changed"):
        join.verify()
    join.close()


def test_single_instance_and_stale_health(tmp_path: Path) -> None:
    with (
        runtime.instance_lock(tmp_path),
        pytest.raises(RuntimeError, match="another"),
        runtime.instance_lock(tmp_path),
    ):
        pass
    runtime.atomic_status(
        tmp_path / "status.json",
        {"state": "RUNNING", "updated_ms": 100, "operational_healthy": True},
    )
    assert runtime.read_health(tmp_path, now_ms=101)[1]
    assert not runtime.read_health(tmp_path, now_ms=16000)[1]


@pytest.mark.parametrize("operator_stop", [False, True])
def test_runtime_collects_finalizes_and_prepares_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, operator_stop: bool
) -> None:
    monkeypatch.setattr(runtime, "public_info", lambda _: metadata())

    async def scenario() -> dict:
        stop = asyncio.Event()
        if operator_stop:
            asyncio.get_running_loop().call_later(1.5, stop.set)

        async def handler(socket):
            requests = [json.loads(await socket.recv()) for _ in range(4)]
            for request in requests:
                await socket.send(
                    json.dumps({"channel": "subscriptionResponse", "data": request})
                )
            while not stop.is_set():
                now = time.time_ns() // 1_000_000
                for coin in ("#10", "#11"):
                    await socket.send(
                        json.dumps(
                            {
                                "channel": "l2Book",
                                "data": json.loads(event(now, coin)["payload_json"]),
                            }
                        )
                    )
                await asyncio.sleep(0.05)

        async with serve(handler, "127.0.0.1", 0) as server:
            port = server.sockets[0].getsockname()[1]

            def factory(**kwargs):
                kwargs["config"] = replace(
                    kwargs["config"], websocket_url=f"ws://127.0.0.1:{port}"
                )
                return PublicWebSocketCollector(**kwargs)

            monkeypatch.setattr(runtime, "PublicWebSocketCollector", factory)
            context = EventContext("test-run", "test", "a" * 64, TimeSource.EXCHANGE)
            result = await runtime.run_service(
                root=tmp_path / "service",
                config=OutcomeConfig(),
                context=context,
                source_files={},
                seconds=2,
                blocked_seconds=2,
                stop=stop,
            )
        return result

    result = asyncio.run(scenario())
    assert result["stop_reason"] == (
        "operator_stop" if operator_stop else "input_blockers_budget_complete"
    )
    assert result["counts"]["windows"] >= 1
    assert result["models"]["central"]["net_pnl_usd"] is None
    root = tmp_path / "service"
    assert runtime.read_health(root)[0]["state"] == "STOPPED"
    capture = root / "runs/test-run"
    checked_input(capture / "windows.jsonl")
    prepared = runtime.prepare_capture(
        capture=capture,
        output=tmp_path / "prepared",
        config=OutcomeConfig(),
        context=EventContext("prepared", "test", "a" * 64, TimeSource.REPLAY),
    )
    assert prepared["counts"]["windows"] == result["counts"]["windows"]


def test_discovery_failure_publishes_failed_health(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(runtime, "public_info", lambda _: {"outcomes": []})
    with pytest.raises(ValueError, match="no supported"):
        asyncio.run(
            runtime.run_service(
                root=tmp_path,
                config=OutcomeConfig(),
                context=EventContext("failed", "test", "a" * 64, TimeSource.EXCHANGE),
                source_files={},
                seconds=1,
                blocked_seconds=1,
            )
        )
    status, healthy = runtime.read_health(tmp_path)
    assert not healthy and status["state"] == "FAILED"
    assert (tmp_path / "runs/failed/failure.json").is_file()


def test_empty_pipeline_cannot_publish_an_economic_result(tmp_path: Path) -> None:
    definitions, _ = discover_recurring(metadata(), observed_ms=0)
    sink = runtime.PipelineStore(
        tmp_path,
        definitions,
        OutcomeConfig(),
        EventContext("empty", "test", "a" * 64, TimeSource.REPLAY),
    )
    result = sink.finish()
    assert result["verdict"] == "DATA_BLOCKED"
    assert result["models"]["central"]["net_pnl_usd"] is None


def test_writer_failure_stops_collector_without_hanging(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(runtime, "public_info", lambda _: metadata())

    def fail(*args, **kwargs):
        raise OSError("simulated disk failure")

    monkeypatch.setattr(runtime.PipelineStore, "append_many", fail)

    async def scenario() -> None:
        async def handler(socket):
            await socket.wait_closed()

        async with serve(handler, "127.0.0.1", 0) as server:
            port = server.sockets[0].getsockname()[1]

            def factory(**kwargs):
                kwargs["config"] = replace(
                    kwargs["config"], websocket_url=f"ws://127.0.0.1:{port}"
                )
                return PublicWebSocketCollector(**kwargs)

            monkeypatch.setattr(runtime, "PublicWebSocketCollector", factory)
            await asyncio.wait_for(
                runtime.run_service(
                    root=tmp_path,
                    config=OutcomeConfig(),
                    context=EventContext(
                        "disk-failure", "test", "a" * 64, TimeSource.EXCHANGE
                    ),
                    source_files={},
                    seconds=4,
                    blocked_seconds=4,
                ),
                timeout=5,
            )

    with pytest.raises(OSError, match="disk failure"):
        asyncio.run(scenario())
    assert runtime.read_health(tmp_path)[0]["state"] == "FAILED"
