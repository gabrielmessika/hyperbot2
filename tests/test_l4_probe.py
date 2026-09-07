"""Authentication stays off argv; bounded probes cannot authorize trading."""

import json
import runpy
import subprocess
from pathlib import Path

import pytest

module = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "scripts/probe_l4_archive.py")
)


def test_credential_only_sent_over_stdin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sentinel = "fake-unit-test-secret"
    observed = {}

    def fake_run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        observed.update({"argv": argv, **kwargs})
        body = json.dumps(
            {"success": True, "data": {}, "meta": {"request_id": "fixture"}}
        )
        return subprocess.CompletedProcess(argv, 0, (body + "\n200").encode(), b"")

    monkeypatch.setattr(subprocess, "run", fake_run)
    probe = module["ArchiveProbe"](tmp_path, sentinel)
    probe.get("#10", "", {"timestamp": 1000})
    assert sentinel not in str(observed["argv"])
    assert sentinel.encode() in observed["input"]
    assert sentinel not in json.dumps(probe.requests)
    assert all(sentinel not in p.read_text() for p in tmp_path.iterdir())


def test_arbitrary_routes_and_header_injection_fail(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="key"):
        module["ArchiveProbe"](tmp_path, "fake\nInjected: header")
    probe = module["ArchiveProbe"](tmp_path, "fake")
    with pytest.raises(ValueError, match="route"):
        probe.get("../exchange", "", {})


def test_auth_failure_retains_status_without_error_body(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        return subprocess.CompletedProcess(
            argv, 0, b"secret echoed by bad upstream\n401", b""
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    probe = module["ArchiveProbe"](tmp_path, "fake")
    with pytest.raises(ValueError, match="401"):
        probe.get("#10", "", {})
    assert probe.requests[0]["http_status"] == "401"
    assert not list(tmp_path.iterdir())
