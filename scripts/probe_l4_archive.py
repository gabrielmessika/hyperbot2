"""Bounded authenticated HIP-4 L4 audit; credentials never enter command arguments."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import time
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode

from hyperbot2.research.artifacts import file_sha256, write_json
from hyperbot2.research.l4_archive import ArchiveBook


def read_key(path: Path) -> str:
    """Accept a raw key or one explicitly named dotenv assignment."""
    lines = [
        s.strip()
        for s in path.read_text().splitlines()
        if s.strip() and not s.lstrip().startswith("#")
    ]
    named = []
    for line in lines:
        name, separator, value = line.partition("=")
        if separator and name.strip().removeprefix("export ") == "OXARCHIVE_API_KEY":
            named.append(value.strip().strip("\"'"))
    if len(named) == 1:
        return named[0]
    if not named and len(lines) == 1 and "=" not in lines[0]:
        return lines[0]
    raise ValueError("provide a raw key or one OXARCHIVE_API_KEY assignment")


class ArchiveProbe:
    def __init__(self, output: Path, key: str) -> None:
        if not key or any(c in key for c in "\r\n\x00"):
            raise ValueError("invalid key format")
        self.output, self.key = output, key
        self.requests: list[dict[str, Any]] = []
        self.bytes = 0

    def get(self, coin: str, suffix: str, parameters: dict[str, Any]) -> dict[str, Any]:
        if not re.fullmatch(r"#?\d+", coin) or suffix not in ("", "/diffs"):
            raise ValueError("HIP-4 read-only route required")
        if len(self.requests) >= 14 or self.bytes >= 20_000_000:
            raise ValueError("probe budget exhausted")
        url = (
            "https://api.0xarchive.io/v1/hyperliquid/hip4/orderbook/"
            + quote(coin, safe="")
            + "/l4"
            + suffix
            + "?"
            + urlencode(parameters)
        )
        started = time.time_ns() // 1_000_000
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
                "-w",
                "\n%{http_code}",
                url,
            ],
            input=("X-API-Key: " + self.key + "\n").encode(),
            capture_output=True,
            timeout=25,
            check=False,
        )
        raw, _, status = response.stdout.rpartition(b"\n")
        received = time.time_ns() // 1_000_000
        record = {
            "url": url,
            "sent_ms": started,
            "received_ms": received,
            "http_status": status.decode(),
            "curl_exit": response.returncode,
        }
        if response.returncode or status != b"200":
            self.requests.append(record)
            raise ValueError(f"provider request failed (HTTP {status.decode()})")
        self.bytes += len(raw)
        path = self.output / f"response-{len(self.requests):02d}.json"
        with path.open("xb") as stream:
            stream.write(raw)
        checksum = hashlib.sha256(raw).hexdigest()
        path.with_suffix(".json.sha256").write_text(checksum + "  " + path.name + "\n")
        self.requests.append(
            record | {"path": str(path), "sha256": checksum, "bytes": len(raw)}
        )
        result = json.loads(raw, parse_float=Decimal)
        if not isinstance(result, dict) or result.get("success") is not True:
            raise ValueError("unsuccessful provider response envelope")
        if not result.get("meta", {}).get("request_id"):
            raise ValueError("provider request identity missing")
        return result

    def reconcile(self, coin: str, start: int, end: int) -> dict[str, Any]:
        first = self.get(coin, "", {"timestamp": start})
        last = self.get(coin, "", {"timestamp": end})
        initial, target = (
            ArchiveBook.snapshot(first["data"]),
            ArchiveBook.snapshot(last["data"]),
        )
        if initial.block >= target.block:
            raise ValueError("checkpoints did not advance")
        initial_ms = int(
            datetime.fromisoformat(
                first["data"]["timestamp"].replace("Z", "+00:00")
            ).timestamp()
            * 1000
        )
        target_ms = int(
            datetime.fromisoformat(
                last["data"]["timestamp"].replace("Z", "+00:00")
            ).timestamp()
            * 1000
        )
        if (
            not initial_ms <= start < target_ms <= end
            or target_ms - initial_ms > 60_000
        ):
            raise ValueError("checkpoint times outside bounded historical window")
        if initial.coin.lstrip("#") != coin.lstrip("#") or target.coin.lstrip(
            "#"
        ) != coin.lstrip("#"):
            raise ValueError("checkpoint coin differs from request")
        cursor = None
        seen = set()
        state = initial
        applied = ignored_boundary = 0
        for _ in range(5):
            params: dict[str, Any] = {
                "start": initial_ms,
                "end": target_ms,
                "limit": 1000,
            }
            if cursor is not None:
                params["cursor"] = cursor
            response = self.get(coin, "/diffs", params)
            for event in response["data"]:
                # Completed-block snapshots: retain boundary events in raw data.
                if (
                    event["block_number"] <= initial.block
                    or event["block_number"] > target.block
                ):
                    ignored_boundary += 1
                    continue
                state = state.apply(event)
                applied += 1
            cursor = response["meta"].get("next_cursor")
            if cursor is None:
                break
            if not isinstance(cursor, str) or not cursor or cursor in seen:
                raise ValueError("invalid/repeated pagination cursor")
            seen.add(cursor)
        else:
            raise ValueError("diff window exceeds pagination budget")
        matched = state.reconcile(target)
        return {
            "coin": coin,
            "initial_block": initial.block,
            "target_block": target.block,
            "applied_events": applied,
            "excluded_boundary_events": ignored_boundary,
            "checkpoint_matched": matched,
            "initial_orders": len(initial.orders),
            "target_orders": len(target.orders),
            "queue_qualified": False,
            "limits": [
                "checkpoint equality is not a continuity proof between checkpoints",
                "provider history has no historical local receipt timestamps",
                "dual-side priority and fill attribution still require audit",
            ],
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outcome-id", type=int, required=True)
    parser.add_argument("--start-ms", type=int, required=True)
    parser.add_argument("--end-ms", type=int, required=True)
    parser.add_argument("--key-file", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.outcome_id < 0 or not 0 < args.end_ms - args.start_ms <= 60_000:
        parser.error("nonnegative outcome and a 1..60000 ms window required")
    args.output.mkdir(parents=True, exist_ok=False)
    key = (
        read_key(args.key_file)
        if args.key_file
        else os.environ.get("OXARCHIVE_API_KEY", "")
    )
    results: dict[str, Any] = {
        "script_sha256": file_sha256(Path(__file__)),
        "reconstructor_sha256": file_sha256(
            Path(__file__).resolve().parents[1] / "src/hyperbot2/research/l4_archive.py"
        ),
        "start_ms": args.start_ms,
        "end_ms": args.end_ms,
        "outcome_id": args.outcome_id,
        "promotion_authorized": False,
        "verdict": "DATA_BLOCKED",
        "results": [],
    }
    if not key:
        results["reason"] = "OXARCHIVE_API_KEY or --key-file required; no network call"
    else:
        client = ArchiveProbe(args.output, key)
        try:
            for side in (0, 1):
                results["results"].append(
                    client.reconcile(
                        f"#{args.outcome_id * 10 + side}", args.start_ms, args.end_ms
                    )
                )
            if all(r["checkpoint_matched"] for r in results["results"]):
                results["verdict"] = "CHECKPOINTS_MATCHED_RESEARCH_ONLY"
        except (ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
            # No provider exception repr: it may contain request/credential details.
            results["reason"] = "probe_failed:" + type(exc).__name__
        results["requests"] = client.requests
        results["response_bytes"] = client.bytes
    write_json(args.output / "report.json", results)
    print(args.output / "report.json")


if __name__ == "__main__":
    main()
