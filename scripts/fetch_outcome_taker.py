"""Extract existing timestamped books and fetch only public native resolutions."""

from __future__ import annotations

import argparse
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fetch_research_history import PublicResearchClient

from hyperbot2.research.artifacts import checked_input, file_sha256, write_json

SOURCE = Path(
    "/workspaces/trident/server-data/hip4/logs/hip4_nautilus_shadow/book_snapshots.jsonl"
)
EXPECTED = "e23544528c2e64b6c72ae42e93458e4ed6a002993aa4808e75ce933cb435d959"
PROTOCOL = Path("reports/outcome_taker_2026-09-07/PROTOCOL.md")


def timestamp(value: str) -> int:
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp() * 1000)


def extract(output: Path) -> None:
    actual = file_sha256(SOURCE)
    if actual != EXPECTED:
        raise ValueError("legacy snapshot changed; do not use a mutable source")
    selected: dict[tuple[str, str, str], dict[str, Any]] = {}
    markets: dict[str, dict[str, Any]] = {}
    count = 0
    for count, line in enumerate(SOURCE.open(), 1):
        row = json.loads(line)
        market = row.get("market_id", "")
        parts = market.split("_")
        if len(parts) != 5 or parts[0] not in {"BTC", "ETH", "SOL", "HYPE"}:
            continue
        expiry = int(
            datetime.strptime(parts[3] + parts[4], "%Y%m%d%H%M")
            .replace(tzinfo=UTC)
            .timestamp()
            * 1000
        )
        decision = expiry - 18 * 3_600_000 + 5000
        event, received = timestamp(row["ts_event"]), timestamp(row["ts_init"])
        side = row["side_name"].upper()
        coin = row["coin"]
        outcome = int(coin.lstrip("#")) // 10
        if side not in {"YES", "NO"} or int(coin.lstrip("#")) % 10 != (
            0 if side == "YES" else 1
        ):
            raise ValueError("unexpected dual-book encoding")
        identity = {
            "underlying": parts[0],
            "strike": parts[2],
            "expiry_ms": expiry,
            "decision_ms": decision,
            "outcome": outcome,
        }
        if market in markets and markets[market] != identity:
            raise ValueError("contract mapping changed")
        markets[market] = identity
        windows = (
            ("decision", decision - 60_000, decision),
            ("execution", decision + 1000, decision + 60_000),
            ("delay", decision + 60_000, decision + 120_000),
        )
        for stage, start, end in windows:
            if not start <= received <= end:
                continue
            key = market, side, stage
            old = selected.get(key)
            if old and (
                (stage == "decision" and old["received_ms"] >= received)
                or (stage != "decision" and old["received_ms"] <= received)
            ):
                continue
            selected[key] = {
                "market": market,
                "side": side,
                "stage": stage,
                "event_ms": event,
                "received_ms": received,
                "source_line": count,
                "raw": row,
            }
    if file_sha256(SOURCE) != actual:
        raise ValueError("source changed during extraction")
    write_json(output / "books.json", [selected[k] for k in sorted(selected)])
    write_json(output / "markets.json", markets)
    write_json(
        output / "manifest.json",
        {
            "source": str(SOURCE),
            "source_sha256": actual,
            "source_lines": count,
            "markets": len(markets),
            "selected_books": len(selected),
            "dataset_tier": "B; legacy exploratory taker, not actual fills",
            "adapter": "outcome-taker-1",
            "script_sha256": file_sha256(Path(__file__)),
            "protocol_sha256": file_sha256(PROTOCOL),
            "books_sha256": checked_input(output / "books.json"),
            "markets_sha256": checked_input(output / "markets.json"),
        },
    )
    print("source lines", count, "markets", len(markets), "books", len(selected))


def labels(root: Path, output: Path) -> None:
    checked_input(root / "markets.json")
    markets = json.loads((root / "markets.json").read_text())
    ids = sorted({m["outcome"] for m in markets.values()} - {111, 762, 1715})
    if len(ids) > 150:
        raise ValueError("label request budget exceeded")
    client = PublicResearchClient(output / "batch-0")
    records = []
    for index, outcome in enumerate(ids):
        if index == 75:
            client = PublicResearchClient(output / "batch-1")
        client.info({"type": "settledOutcome", "outcome": outcome})
        records.append(client.records[-1])
        if index % 20 == 0:
            print("resolutions fetched", index + 1, flush=True)
        time.sleep(0.25)
    write_json(
        output / "manifest.json",
        {
            "requests": records,
            "script_sha256": file_sha256(Path(__file__)),
            "client_sha256": file_sha256(Path("scripts/fetch_research_history.py")),
            "markets_sha256": checked_input(root / "markets.json"),
            "protocol_sha256": file_sha256(PROTOCOL),
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--labels-from", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    if args.labels_from:
        labels(args.labels_from, args.output)
    else:
        extract(args.output)


if __name__ == "__main__":
    main()
