"""Offline comparison of simultaneous native and archive market-data captures."""

from __future__ import annotations

import argparse
import json
import runpy
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from hyperbot2.event_store import JsonlEventStore
from hyperbot2.models import BookLevel
from hyperbot2.research.artifacts import checked_input, file_sha256, write_json
from hyperbot2.research.l4_archive import ArchiveBook, canonical_yes_levels
from hyperbot2.research.paired_l4 import closed_states, state_at

DIAGNOSTIC = runpy.run_path(str(Path(__file__).with_name("diagnose_feasibility.py")))
distribution, coverage = DIAGNOSTIC["distribution"], DIAGNOSTIC["coverage"]


def load_events(path: Path, checksum: str) -> list[dict]:
    if file_sha256(path) != checksum:
        raise ValueError("raw checksum mismatch")
    events = [
        r["payload"] for r in JsonlEventStore(path.parent).iter_records(path.stem)
    ]
    for i, event in enumerate(events):
        if event["local_sequence"] != i:
            raise ValueError("local sequence gap")
        if i and event["receive_monotonic_ns"] < events[i - 1]["receive_monotonic_ns"]:
            raise ValueError("monotonic receipt regressed")
    return events


def rest_pair(
    manifest_path: Path, manifest: dict, selection: dict
) -> list[ArchiveBook]:
    books = []
    for side, name in enumerate(selection["snapshot_paths"]):
        path = manifest_path.parent / Path(name).name
        digest = checked_input(path)
        request = next(r for r in manifest["requests"] if r["path"] == name)
        if digest != request["sha256"]:
            raise ValueError("REST response differs from request manifest")
        data = json.loads(path.read_text(), parse_float=Decimal)["data"]
        timestamp = int(
            datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00")).timestamp()
            * 1000
        )
        book = ArchiveBook.snapshot(data)
        if (
            timestamp != selection["exchange_ms"]
            or book.coin != f"#{selection['outcome_id'] * 10 + side}"
        ):
            raise ValueError("REST checkpoint does not match native selection")
        books.append(book)
    return books


def analyze(root: Path, rest_manifest: Path | None = None) -> dict:
    checked_input(root / "capture.json")
    checked_input(root / "archive/report.json")
    capture = json.loads((root / "capture.json").read_text())
    archive = json.loads((root / "archive/report.json").read_text())
    native_events = load_events(
        root / "raw/native.jsonl", capture["native"]["raw_sha256"]
    )
    archive_events = load_events(
        root / "archive/raw/archive-l4.jsonl", archive["raw_sha256"]
    )
    yes, no = (f"#{capture['outcome_id'] * 10 + side}" for side in (0, 1))
    messages = [
        (e["receive_ts_ms"], json.loads(e["payload_json"], parse_float=Decimal))
        for e in archive_events
    ]
    native = [
        e | {"book": json.loads(e["payload_json"])["data"]}
        for e in native_events
        if e["channel"] == "l2Book"
    ]
    rows = {
        coin: [
            (e["receive_ts_ms"], e["exchange_ts_ms"])
            for e in native
            if e["coin"] == coin
        ]
        for coin in (yes, no)
    }
    ages = [r - t for values in rows.values() for r, t in values]
    archive_ages = [
        received - v["ts"]
        for received, m in messages
        if m["type"] == "l4_batch"
        for v in m["data"]
    ]
    reconstruction_error = None
    initial_books = None
    rest_baseline = None
    rest_checks = []
    if rest_manifest is not None:
        checked_input(rest_manifest)
        manifest = json.loads(rest_manifest.read_text())
        selection = next(
            c
            for c in manifest["checks"]
            if c["outcome_id"] == capture["outcome_id"] and c["native_index"] == 0
        )
        initial_books = {
            b.coin: b for b in rest_pair(rest_manifest, manifest, selection)
        }
        rest_baseline = {
            "manifest_sha256": file_sha256(rest_manifest),
            "selection": selection,
            "historical_only": True,
        }
        yes_native = [e for e in native if e["coin"] == yes]
        for selected in manifest["checks"]:
            if selected["outcome_id"] != capture["outcome_id"]:
                continue
            event = yes_native[selected["native_index"]]
            if event["exchange_ts_ms"] != selected["exchange_ms"]:
                raise ValueError("native checkpoint selection differs from capture")
            merged = canonical_yes_levels(*rest_pair(rest_manifest, manifest, selected))
            expected = tuple(
                tuple(
                    BookLevel(Decimal(v["px"]), Decimal(v["sz"]), v["n"]) for v in side
                )
                for side in event["book"]["levels"]
            )
            rest_checks.append(
                {
                    "native_index": selected["native_index"],
                    "exchange_ms": selected["exchange_ms"],
                    "exact_top5_match": tuple(side[:5] for side in merged) == expected,
                }
            )
        repaired = []
        for received, message in messages:
            if message["type"] == "l4_snapshot":
                continue
            if message["type"] == "l4_batch":
                coin = message["coin"]
                message = message | {
                    "data": [
                        e
                        for e in message["data"]
                        if e["bn"] > initial_books[coin].block
                    ]
                }
            repaired.append((received, message))
        messages = repaired
    try:
        states = closed_states(messages, initial_books=initial_books)
    except (ValueError, KeyError, TypeError) as exc:
        states = {}
        reconstruction_error = str(exc)
    comparisons = []
    for event in native:
        if event["coin"] != yes:
            continue
        timestamp = event["exchange_ts_ms"]
        sides = [state_at(states.get(coin, []), timestamp) for coin in (yes, no)]
        if any(s is None for s in sides):
            continue
        try:
            depth = canonical_yes_levels(sides[0].book, sides[1].book)
            expected = tuple(
                tuple(
                    BookLevel(Decimal(v["px"]), Decimal(v["sz"]), v["n"]) for v in side
                )
                for side in event["book"]["levels"]
            )
            matched = tuple(s[:5] for s in depth) == expected
            error = None
        except ValueError as exc:
            matched, error = False, str(exc)
        comparisons.append(
            {
                "native_exchange_ms": timestamp,
                "native_receive_ms": event["receive_ts_ms"],
                "exact_top5_match": matched,
                "error": error,
                "last_applied_event_minus_native_receipt_ms": max(
                    s.applied_received_ms for s in sides
                )
                - event["receive_ts_ms"],
                "confirmation_minus_native_receipt_ms": max(
                    s.confirmed_received_ms for s in sides
                )
                - event["receive_ts_ms"],
                "blocks": [s.block for s in sides],
            }
        )
    windows = []
    for coin, values in rows.items():
        for index, (start, _) in enumerate(values):
            end = start + 1350
            if end > values[-1][0]:
                continue
            healthy = True
            for j in range(index, len(values)):
                received, timestamp = values[j]
                until = min(end, values[j + 1][0] if j + 1 < len(values) else end)
                if received >= end:
                    break
                if timestamp > received or until - timestamp > 500:
                    healthy = False
            windows.append(
                {"coin": coin, "start_ms": start, "fresh_through_1350_ms": healthy}
            )
    return {
        "run_id": capture["run_id"],
        "outcome_id": capture["outcome_id"],
        "analyzer_sha256": file_sha256(Path(__file__)),
        "reconstructor_sha256": file_sha256(
            Path(__file__).resolve().parents[1] / "src/hyperbot2/research/paired_l4.py"
        ),
        "capture": capture,
        "archive_stop_reason": archive["stop_reason"],
        "native_raw_sha256": capture["native"]["raw_sha256"],
        "archive_raw_sha256": archive["raw_sha256"],
        "native_age_ms": distribution(ages),
        "archive_event_age_ms": distribution(archive_ages),
        "native_admissible_100_ms": sum(0 <= a <= 100 for a in ages),
        "archive_events_under_100_ms": sum(0 <= a <= 100 for a in archive_ages),
        "native_fresh_at_receipt_500_ms": sum(0 <= a <= 500 for a in ages),
        "native_time_coverage_by_coin": {c: coverage(v) for c, v in rows.items()},
        "native_windows": {
            "count": len(windows),
            "passing": sum(w["fresh_through_1350_ms"] for w in windows),
            "details": windows,
        },
        "reconstruction_error": reconstruction_error,
        "historical_rest_baseline": rest_baseline,
        "rest_checkpoint_checks": rest_checks,
        "completed_blocks": {c: len(s) for c, s in states.items()},
        "depth_comparisons": comparisons,
        "depth_matches": sum(c["exact_top5_match"] for c in comparisons),
        "queue_qualified": False,
        "promotion_authorized": False,
        "limits": [
            "per-coin ordering assumed from provider contract, not proved",
            "completion needs next changed block per coin; quiet intervals censored",
            "event age and block-confirmation wait are not measured order latency",
            "native windows overlap and are not independent trials",
            "native depth has no block ID; alignment uses exchange timestamps",
            "historical equality does not authorize a trade at an earlier receipt",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--historical-rest-manifest", type=Path)
    args = parser.parse_args()
    write_json(args.output, analyze(args.capture, args.historical_rest_manifest))
    print(args.output)


if __name__ == "__main__":
    main()
