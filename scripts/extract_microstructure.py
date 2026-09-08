"""Reduce immutable existing Hyperbot exports to causal one-second features."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
from collections import Counter, deque
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from hyperbot2.research.artifacts import file_sha256, write_json

D = Decimal
COINS = ("BTC", "ETH", "HYPE")
ROOT = Path("/workspaces/hyperbot/data/server-fetches")
REPORT = Path("reports/microstructure_2026-09-07")
COLUMNS = (
    "time",
    "coin",
    "valid",
    "bid",
    "ask",
    "bid_size",
    "ask_size",
    "event_ms",
    "received_ms",
    "flow",
    "notional",
    "count",
    "imbalance",
    "return_bps",
    "spread_bps",
)


class Reducer:
    def __init__(self, writer: Any) -> None:
        self.writer = writer
        self.next_ms = 0
        self.last_receive = 0
        self.warm = 0
        self.books: dict[str, tuple[int, int, Decimal, Decimal, Decimal, Decimal]] = {}
        self.trades: dict[str, deque[tuple[int, Decimal, Decimal]]] = {
            c: deque() for c in COINS
        }
        self.total = dict.fromkeys(COINS, D(0))
        self.signed = dict.fromkeys(COINS, D(0))
        self.mids: dict[str, dict[int, Decimal]] = {c: {} for c in COINS}
        self.seen: set[tuple[str, int, int]] = set()
        self.seen_times: deque[tuple[int, tuple[str, int, int]]] = deque()
        self.run_id = ""
        self.counts: Counter[str] = Counter()

    def reset(self, now: int) -> None:
        self.books.clear()
        for coin in COINS:
            self.trades[coin].clear()
            self.mids[coin].clear()
            self.total[coin] = self.signed[coin] = D(0)
        self.warm = now + 60_000

    def emit(self, now: int) -> None:
        for coin in COINS:
            trades = self.trades[coin]
            while trades and trades[0][0] < now - 60_000:
                _, total, signed = trades.popleft()
                self.total[coin] -= total
                self.signed[coin] -= signed
            b = self.books.get(coin)
            if b is None:
                continue
            event, received, bid, ask, bs, az = b
            fresh = 0 <= now - event <= 2000 and 0 < now - received <= 2000
            mid = (bid + ask) / 2
            previous = self.mids[coin].get(now - 60_000)
            if fresh:
                self.mids[coin][now] = mid
            self.mids[coin].pop(now - 61_000, None)
            valid = fresh and now >= self.warm and previous is not None
            self.counts["seconds_valid" if valid else "seconds_invalid"] += 1
            self.writer.writerow(
                (
                    now,
                    coin,
                    int(valid),
                    bid if fresh else "",
                    ask if fresh else "",
                    bs if fresh else "",
                    az if fresh else "",
                    event,
                    received,
                    self.signed[coin] / self.total[coin] if self.total[coin] else 0,
                    self.total[coin],
                    len(trades),
                    (bs - az) / (bs + az),
                    (mid / previous - 1) * 10_000 if previous is not None else "",
                    (ask - bid) / mid * 10_000,
                )
            )

    def observe(self, payload: dict[str, Any]) -> None:
        coin, channel = payload["coin"], payload["channel"]
        received, event = payload["receive_ts_ms"], payload["exchange_ts_ms"]
        run_id = payload["context"]["run_id"]
        if run_id != self.run_id:
            self.reset(received)
            self.run_id = run_id
            self.counts["collector_runs"] += 1
        if received < self.last_receive:
            self.counts["receipt_regression"] += 1
            self.reset(self.last_receive)
            return
        if not self.next_ms:
            self.next_ms = (received // 1000 + 1) * 1000
            self.reset(received)
        elif received - self.last_receive > 10_000:
            self.counts["receipt_gaps_over_10s"] += 1
            self.reset(received)
            self.next_ms = (received // 1000 + 1) * 1000
        while self.next_ms <= received:
            self.emit(self.next_ms)
            self.next_ms += 1000
        self.last_receive = received
        while self.seen_times and self.seen_times[0][0] < received - 120_000:
            self.seen.discard(self.seen_times.popleft()[1])
        self.counts[channel] += 1
        if not 0 <= received - event <= 2000:
            self.counts["event_late_or_future"] += 1
            return
        data = json.loads(payload["payload_json"])
        if data["coin"] != coin or data["time"] != event:
            raise ValueError("native event identity differs from wrapper")
        if channel == "bbo":
            if len(data["bbo"]) != 2 or any(level is None for level in data["bbo"]):
                self.books.pop(coin, None)
                self.counts["empty_bbo"] += 1
                return
            bid, ask = data["bbo"]
            px, ax, bs, az = D(bid["px"]), D(ask["px"]), D(bid["sz"]), D(ask["sz"])
            if not all(v.is_finite() and v > 0 for v in (px, ax, bs, az)) or px >= ax:
                self.books.pop(coin, None)
                self.counts["invalid_bbo"] += 1
                return
            self.books[coin] = event, received, px, ax, bs, az
        elif channel == "trades":
            key = coin, event, int(data["tid"])
            if key in self.seen:
                self.counts["duplicate_trade"] += 1
                return
            self.seen.add(key)
            self.seen_times.append((received, key))
            notional = D(data["px"]) * D(data["sz"])
            if (
                not notional.is_finite()
                or notional <= 0
                or data["side"] not in {"A", "B"}
            ):
                raise ValueError("invalid native trade")
            signed = notional if data["side"] == "B" else -notional
            self.trades[coin].append((received, notional, signed))
            self.total[coin] += notional
            self.signed[coin] += signed


def inventory(day: str) -> list[dict[str, Any]]:
    files: dict[str, dict[str, Any]] = {}
    for manifest in sorted(ROOT.glob("*/export/manifest.json")):
        data = json.loads(manifest.read_text())
        for item in data["files"]:
            path = item["path"]
            if "/public-market-data/" not in path or not path.endswith(".jsonl.gz"):
                continue
            if not Path(path).name.startswith(day):
                continue
            if path in files and files[path]["sha256"] != item["sha256"]:
                raise ValueError("conflicting export snapshots")
            files.setdefault(
                path,
                dict(
                    item,
                    local_path=str(manifest.parent.parent / "payload" / path),
                    export_manifest=str(manifest),
                    export_sha256=file_sha256(manifest),
                ),
            )
    return [files[k] for k in sorted(files)]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--day", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    start = int(
        datetime.strptime(args.day, "%Y-%m-%d").replace(tzinfo=UTC).timestamp() * 1000
    )
    files = inventory(args.day)
    if not files or len(files) > 120:
        raise ValueError("empty or excessive daily inventory")
    args.output.mkdir(parents=True, exist_ok=False)
    write_json(args.output / "source_manifest.json", files)
    target = args.output / "seconds.csv.gz"
    rows = selected = 0
    needles = tuple(('"coin":"' + coin + '"').encode() for coin in COINS)
    with target.open("xb") as raw:
        # Empty embedded filename and fixed mtime make gzip output reproducible.
        import io

        with (
            gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as compressed,
            io.TextIOWrapper(compressed, encoding="utf-8", newline="") as output,
        ):
            writer = csv.writer(output)
            writer.writerow(COLUMNS)
            reducer = Reducer(writer)
            for index, item in enumerate(files):
                path = Path(item["local_path"])
                if (
                    file_sha256(path) != item["sha256"]
                    or path.stat().st_size != item["size_bytes"]
                ):
                    raise ValueError("export file checksum or size mismatch")
                with gzip.open(path, "rb") as source:
                    first_selected = True
                    for line in source:
                        rows += 1
                        if not any(needle in line for needle in needles):
                            continue
                        record = json.loads(line)
                        p = record["payload"]
                        if p["coin"] not in COINS or p["channel"] not in {
                            "bbo",
                            "trades",
                        }:
                            continue
                        if (
                            record["schema_version"] != 2
                            or record["event_type"] != "PublicMarketDataEvent"
                        ):
                            raise ValueError("unexpected Hyperbot event schema")
                        if start <= p["receive_ts_ms"] < start + 86_400_000:
                            if first_selected:
                                reducer.reset(p["receive_ts_ms"])
                                first_selected = False
                            selected += 1
                            reducer.observe(p)
                if file_sha256(path) != item["sha256"]:
                    raise ValueError("source changed during scan")
                if index % 10 == 0:
                    print(
                        args.day,
                        "files",
                        index + 1,
                        "/",
                        len(files),
                        "selected",
                        selected,
                        flush=True,
                    )
    checksum = file_sha256(target)
    target.with_suffix(".gz.sha256").write_text(checksum + "  " + target.name + "\n")
    write_json(
        args.output / "manifest.json",
        {
            "day": args.day,
            "source_files": len(files),
            "raw_rows": rows,
            "selected_rows": selected,
            "quality": dict(reducer.counts),
            "seconds_sha256": checksum,
            "source_manifest_sha256": file_sha256(args.output / "source_manifest.json"),
            "script_sha256": file_sha256(Path(__file__)),
            "protocol_sha256": file_sha256(REPORT / "PROTOCOL.md"),
            "adapter_sha256": file_sha256(REPORT / "ADAPTER.md"),
            "origin": "Hyperbot A public receipt events; exploratory reduction",
            "live_enabled": False,
        },
    )
    print(args.day, "complete", dict(reducer.counts), flush=True)


if __name__ == "__main__":
    main()
