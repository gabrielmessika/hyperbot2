import json
import runpy
import subprocess
from pathlib import Path

import pytest


def test_archive_routes_and_credentials_stay_out_of_argv_and_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client_class = runpy.run_path("scripts/fetch_liquidation_study.py")[
        "LiquidationArchive"
    ]
    client = client_class(tmp_path / "raw", "fake-test-secret")
    with pytest.raises(ValueError, match="routes"):
        client.get("/exchange", {})
    with pytest.raises(ValueError, match="fields"):
        client.get("/v1/hyperliquid/liquidations/BTC", {"api_key": "x"})

    def response(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        assert "fake-test-secret" not in " ".join(argv)
        assert kwargs["input"] == b"X-API-Key: fake-test-secret\n"
        return subprocess.CompletedProcess(
            argv, 0, b'{"echo":"fake-test-secret"}\n200', b""
        )

    monkeypatch.setattr(subprocess, "run", response)
    with pytest.raises(ValueError, match="echo"):
        client.get("/v1/hyperliquid/liquidations/BTC", {})
    assert list((tmp_path / "raw").iterdir()) == []


def test_coverage_has_its_own_validated_envelope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client_class = runpy.run_path("scripts/fetch_liquidation_study.py")[
        "LiquidationArchive"
    ]
    client = client_class(tmp_path / "raw", "fake-test-secret")
    payload = {"exchange": "hyperliquid", "symbol": "BTC", "data_types": {}}
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda argv, **kwargs: subprocess.CompletedProcess(
            argv, 0, json.dumps(payload).encode() + b"\n200", b""
        ),
    )
    assert client.get("/v1/data-quality/coverage/hyperliquid/BTC", {}) == payload
    with pytest.raises(ValueError, match="unidentified"):
        client.get("/v1/hyperliquid/liquidations/BTC", {})
