"""Acquire and qualify bounded native Korean equity history without PnL."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from fetch_research_history import END, START, PublicResearchClient
from investigate_funding_normalization import load

from hyperbot2.research.artifacts import checked_input, file_sha256, write_json
from hyperbot2.research.rotation import HOUR

REPORT = Path("reports/korea_opening_2026-09-07")
DATA = Path("data/korea_opening_2026-09-07")
COIN = "xyz:SKHX"


def fetch(output: Path, protocol: str) -> None:
    output.mkdir(parents=True, exist_ok=False)
    client = PublicResearchClient(output)

    def request(payload: dict) -> list:
        if len(client.records) >= 11 or client.total_bytes >= 5_000_000:
            raise ValueError("registered Korean acquisition budget exceeded")
        rows = client.info(payload)
        time.sleep(3)
        if not isinstance(rows, list):
            raise ValueError("expected native list response")
        return rows

    try:
        candles = request(
            {
                "type": "candleSnapshot",
                "req": {
                    "coin": COIN,
                    "interval": "1h",
                    "startTime": START,
                    "endTime": END - 1,
                },
            }
        )
        print(COIN, "candles", len(candles), flush=True)
        cursor, count = START, 0
        for _ in range(10):
            rows = request(
                {
                    "type": "fundingHistory",
                    "coin": COIN,
                    "startTime": cursor,
                    "endTime": END - 1,
                }
            )
            if not rows:
                break
            times = [int(row["time"]) for row in rows]
            if min(times) < cursor or max(times) >= END:
                raise ValueError("funding page outside requested period")
            count += len(rows)
            cursor = max(times) + 1
            if cursor >= END - HOUR:
                break
        else:
            raise ValueError("funding pagination incomplete within budget")
        print(COIN, "funding", count, flush=True)
    finally:
        write_json(
            output / "manifest.json",
            {
                "requests": client.records,
                "response_bytes": client.total_bytes,
                "start_ms": START,
                "end_ms_exclusive": END,
                "protocol_sha256": protocol,
                "script_sha256": file_sha256(Path(__file__)),
                "data_cost_usd": 0,
            },
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fetch", action="store_true")
    args = parser.parse_args()
    checked_input(REPORT / "qualification_registration.json")
    protocol = file_sha256(REPORT / "QUALIFICATION_PROTOCOL.md")
    registration = json.loads((REPORT / "qualification_registration.json").read_text())
    if registration["protocol_sha256"] != protocol:
        raise ValueError("registered qualification changed")
    if args.fetch:
        fetch(args.output, protocol)
        return
    args.output.mkdir(parents=True, exist_ok=False)
    _, _, _, quality = load([DATA / "history"], [COIN], START, END)
    _, _, _, reference_quality = load(
        [Path("data/weekend_repricing_2026-09-07/history")],
        ["xyz:NVDA"],
        START,
        END,
    )
    metadata = Path("data/weekend_repricing_2026-09-07/xyz_meta.json")
    checked_input(metadata)
    native = json.loads(metadata.read_text())["response"][0]
    selected = [row for row in native["universe"] if row["name"] in (COIN, "xyz:NVDA")]
    if len(selected) != 2:
        raise ValueError("missing Korean/reference metadata")
    documentation = {}
    for path in sorted((DATA / "documentation").glob("*.json")):
        documentation[str(path)] = checked_input(path)
        if json.loads(path.read_text())["returncode"]:
            raise ValueError("failed official documentation snapshot")
    write_json(
        args.output / "quality.json",
        {
            "run_id": "korea-opening-qualification-20260907-v1",
            "protocol_sha256": protocol,
            "script_sha256": file_sha256(Path(__file__)),
            "quality": quality,
            "reference_quality": reference_quality,
            "metadata": selected,
            "metadata_sha256": checked_input(metadata),
            "documentation": documentation,
            "decision": "HOURLY_RESEARCH_DATA_AVAILABLE_EXECUTION_UNQUALIFIED",
            "pnl_computed": False,
            "live_enabled": False,
            "promotion_authorized": False,
        },
    )
    print(quality["assets"], reference_quality["assets"], flush=True)


if __name__ == "__main__":
    main()
