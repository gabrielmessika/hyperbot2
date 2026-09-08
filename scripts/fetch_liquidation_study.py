"""Bounded, read-only BTC/ETH archive queries with credential-safe provenance."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
import time
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlencode

from hyperbot2.research.artifacts import write_json


class LiquidationArchive:
    def __init__(self, output: Path, key: str) -> None:
        if not key or any(c in key for c in "\r\n\x00"):
            raise ValueError("invalid key format")
        self.output, self.key = output, key
        self.requests: list[dict] = []
        self.total_bytes = 0
        self.started = time.monotonic()
        output.mkdir(parents=True, exist_ok=False)

    def get(self, route: str, parameters: dict) -> dict:
        if not re.fullmatch(
            r"/v1/(hyperliquid/(liquidations/(BTC|ETH)(/volume)?|"
            r"openinterest/(BTC|ETH)|candles/(BTC|ETH))|"
            r"data-quality/coverage/hyperliquid/(BTC|ETH))",
            route,
        ):
            raise ValueError("only registered public BTC/ETH data routes allowed")
        if (
            len(self.requests) >= 100
            or self.total_bytes >= 48_000_000
            or time.monotonic() - self.started > 1800
        ):
            raise ValueError("bounded acquisition budget exhausted")
        if set(parameters) - {"start", "end", "limit", "interval", "cursor"}:
            raise ValueError("unexpected query fields")
        if (
            "start" in parameters
            and not 0 < parameters["end"] - parameters["start"] <= 31 * 86_400_000
        ):
            raise ValueError("query window must be within 31 days")
        url = "https://api.0xarchive.io" + route + "?" + urlencode(parameters)
        sent = time.time_ns() // 1_000_000
        with tempfile.TemporaryDirectory(prefix="hb2-liq-") as temporary:
            headers = Path(temporary) / "headers"
            response = subprocess.run(
                [
                    "curl",
                    "-sS",
                    "--max-time",
                    "20",
                    "--max-filesize",
                    "2000000",
                    "--header",
                    "@-",
                    "--dump-header",
                    str(headers),
                    "-w",
                    "\n%{http_code}",
                    url,
                ],
                input=("X-API-Key: " + self.key + "\n").encode(),
                capture_output=True,
                timeout=25,
                check=False,
            )
            selected = {}
            if headers.exists():
                for line in headers.read_text().splitlines():
                    name, _, value = line.partition(":")
                    if (
                        name.lower()
                        in ("x-credits-used", "x-credits-remaining", "x-credits-limit")
                        and value.strip().isdigit()
                    ):
                        selected[name.lower()] = int(value.strip())
        raw, _, status = response.stdout.rpartition(b"\n")
        record = {
            "url": url,
            "route": route,
            "parameters": parameters,
            "sent_ms": sent,
            "received_ms": time.time_ns() // 1_000_000,
            "http_status": status.decode(),
            "curl_exit": response.returncode,
            "credits": selected,
        }
        self.requests.append(record)
        if self.key.encode() in raw:
            raise ValueError("credential echo rejected")
        if response.returncode:
            raise ValueError("archive transport failed")
        path = self.output / f"response-{len(self.requests) - 1:03d}.json"
        with path.open("xb") as stream:
            stream.write(raw)
        digest = hashlib.sha256(raw).hexdigest()
        path.with_suffix(".json.sha256").write_text(digest + "  " + path.name + "\n")
        self.total_bytes += len(raw)
        record.update({"path": str(path), "sha256": digest, "bytes": len(raw)})
        if status != b"200":
            raise ValueError("archive HTTP " + status.decode())
        result = json.loads(raw, parse_float=Decimal)
        if route.startswith("/v1/data-quality/coverage/"):
            if (
                result.get("exchange") != "hyperliquid"
                or result.get("symbol") != route.rsplit("/", 1)[1]
                or not isinstance(result.get("data_types"), dict)
            ):
                raise ValueError("invalid coverage response")
            return result
        if result.get("success") is not True or not result.get("meta", {}).get(
            "request_id"
        ):
            raise ValueError("unsuccessful/unidentified response")
        return result

    def manifest(self, path: Path) -> None:
        write_json(
            path,
            {
                "requests": self.requests,
                "bytes": self.total_bytes,
                "promotion_authorized": False,
                "historical_only": True,
            },
        )
