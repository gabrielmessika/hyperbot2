"""Reuse the unchanged weekend study on two registered additional markets."""

from __future__ import annotations

import argparse
import importlib.util
import json
import runpy
import sys
import time
from pathlib import Path

from hyperbot2.research.artifacts import checked_input, file_sha256, write_json

COINS = ("xyz:COIN", "xyz:MSTR")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--fetch", action="store_true")
    args = parser.parse_args()
    protocol = Path("reports/weekend_repricing_2026-09-07/REPLICATION.md")
    checked_input(protocol.parent / "replication_registration.json")
    if json.loads((protocol.parent / "replication_registration.json").read_text())[
        "protocol_sha256"
    ] != file_sha256(protocol):
        raise ValueError("modified replication protocol")
    fetch_path = Path(__file__).with_name("fetch_weekend_repricing.py")
    original = runpy.run_path(str(fetch_path))
    start, end, hour = original["START"], original["END"], original["HOUR"]
    if args.fetch:
        args.raw.mkdir(parents=True, exist_ok=False)
        client_path = Path(__file__).with_name("fetch_research_history.py")
        client = runpy.run_path(str(client_path))["PublicResearchClient"](args.raw)
        try:
            for coin in COINS:
                rows = client.info(
                    {
                        "type": "candleSnapshot",
                        "req": {
                            "coin": coin,
                            "interval": "1h",
                            "startTime": start,
                            "endTime": end - 1,
                        },
                    }
                )
                print(coin, "candles", len(rows), flush=True)
                cursor, count = start, 0
                for _ in range(10):
                    if len(client.records) >= 24:
                        raise ValueError("replication budget exhausted")
                    rows = client.info(
                        {
                            "type": "fundingHistory",
                            "coin": coin,
                            "startTime": cursor,
                            "endTime": end - 1,
                        }
                    )
                    if not rows:
                        break
                    times = [int(r["time"]) for r in rows]
                    if min(times) < cursor or max(times) >= end:
                        raise ValueError("funding range mismatch")
                    cursor = max(times) + 1
                    count += len(rows)
                    time.sleep(2.5)
                    if cursor >= end - hour:
                        break
                print(coin, "funding", count, flush=True)
        finally:
            write_json(
                args.raw / "manifest.json",
                {
                    "coins": COINS,
                    "start_ms": start,
                    "end_ms_exclusive": end,
                    "requests": client.records,
                    "response_bytes": client.total_bytes,
                    "code_hashes": {
                        str(p): file_sha256(p)
                        for p in (Path(__file__), client_path, fetch_path)
                    },
                    "data_cost_usd": 0,
                },
            )
        return
    if args.output is None:
        parser.error("--output required for analysis")
    # Apply the registered universe through the unchanged study module.
    study_path = Path(__file__).with_name("investigate_weekend_repricing.py")
    spec = importlib.util.spec_from_file_location(
        "registered_weekend_replication", study_path
    )
    if spec is None or spec.loader is None:
        raise ValueError("unable to load registered study")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.COINS = COINS
    original_loader = module.load
    module.load = lambda unused: original_loader(args.raw)
    sys.argv = [str(study_path), "--output", str(args.output)]
    module.main()
    # Preserve the common engine result verbatim, with a separate wrapper manifest.
    write_json(
        args.output / "replication.json",
        {
            "run_id": "weekend-replication-2026-09-07",
            "coins": COINS,
            "raw": str(args.raw),
            "protocol_sha256": file_sha256(protocol),
            "parent_protocol_sha256": file_sha256(protocol.parent / "PROTOCOL.md"),
            "code_hashes": {
                str(p): file_sha256(p) for p in (Path(__file__), study_path)
            },
            "result_sha256": checked_input(args.output / "summary.json"),
            "selected_after_initial_results": True,
            "promotion_authorized": False,
        },
    )


if __name__ == "__main__":
    main()
