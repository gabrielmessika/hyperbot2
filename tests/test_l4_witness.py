"""Read-only witnesses stop on feed gaps and never persist echoed credentials."""

import asyncio
import json
import runpy
from pathlib import Path

import pytest


@pytest.mark.parametrize("credential_echo", [False, True])
def test_witness_stops_on_gap_or_credential_echo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, credential_echo: bool
) -> None:
    module = runpy.run_path(
        str(Path(__file__).resolve().parents[1] / "scripts/witness_archive_l4.py")
    )
    witness = module["witness"]
    key = "unit-test-secret"
    messages = iter(
        [json.dumps({"type": "gap", "reason": key if credential_echo else "upstream"})]
    )
    subscriptions = []

    class Socket:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def send(self, value):
            subscriptions.append(json.loads(value))

        async def recv(self):
            return next(messages)

    def connect(url, **kwargs):
        assert url == "wss://api.0xarchive.io/ws"
        assert kwargs["additional_headers"] == {"Authorization": "Bearer " + key}
        return Socket()

    monkeypatch.setitem(witness.__globals__, "connect", connect)
    output = tmp_path / "witness"
    asyncio.run(witness(output, 1715, key, 30, "hip4_l4_diffs"))
    report = json.loads((output / "report.json").read_text())
    assert report["stop_reason"] == (
        "exception:ValueError" if credential_echo else "gap"
    )
    assert not report["promotion_authorized"]
    assert not report["queue_qualified"]
    assert [s["symbol"] for s in subscriptions] == ["#17150", "#17151"]
    assert all(s["op"] == "subscribe" for s in subscriptions)
    assert all(key not in p.read_text() for p in output.rglob("*") if p.is_file())
    assert (output / "raw/archive-l4.jsonl").exists() != credential_echo
