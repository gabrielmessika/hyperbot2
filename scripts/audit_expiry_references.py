"""Audit legacy near-expiry reference provenance without generating signals."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

from fetch_outcome_taker import timestamp

from hyperbot2.research.artifacts import checked_input, file_sha256, write_json

LEGACY = Path("/workspaces/trident/server-data/hip4/logs")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    market_path = Path("data/outcome_taker_2026-09-07/extract_verified/markets.json")
    sources = {str(market_path): checked_input(market_path)}
    markets = json.loads(market_path.read_text())
    summaries = {}
    for directory in ("hip4_outcome_mainnet", "hip4_outcome_mainnet_paper"):
        path = LEGACY / directory / "short_expiry_features.csv"
        sources[str(path)] = file_sha256(path)
        rows = list(csv.DictReader(path.open()))
        lags = []
        after_expiry = 0
        for r in rows:
            parts = r["market_id"].split("_")
            expiry = timestamp(
                f"{parts[3][:4]}-{parts[3][4:6]}-{parts[3][6:]}T06:00:00Z"
            )
            logged = timestamp(r["ts"])
            implied_loop = expiry - int(r["seconds_left"]) * 1000
            lags.append(logged - implied_loop)
            after_expiry += logged >= expiry
        lags.sort()
        summaries[directory] = {
            "rows": len(rows),
            "markets": len({r["market_id"] for r in rows}),
            "dates": len({r["ts"][:10] for r in rows}),
            "log_minus_implied_loop_ms": {
                "minimum": lags[0],
                "median": lags[len(lags) // 2],
                "p95": lags[int(len(lags) * 0.95)],
                "maximum": lags[-1],
            },
            "logged_at_or_after_expiry": after_expiry,
            "native_reference_exchange_timestamps_in_csv": False,
        }
        if file_sha256(path) != sources[str(path)]:
            raise ValueError("feature source changed")
    path = LEGACY / "hip4_outcome_mainnet/decisions.jsonl"
    sources[str(path)] = file_sha256(path)
    selected = {}
    for number, line in enumerate(path.open(), 1):
        # All relevant decisions end at 05:55 UTC; this filter only avoids parsing
        # records that cannot contain a matching timestamp anywhere in the row.
        if "T05:5" not in line:
            continue
        row = json.loads(line)
        signal = row.get("signal", {})
        market = signal.get("market_id")
        if market not in markets:
            continue
        point = markets[market]["expiry_ms"] - 300_000
        logged = timestamp(row["ts"])
        if not point - 60_000 <= logged <= point:
            continue
        metadata = signal.get("metadata", {})
        references = metadata.get("reference_sources")
        if not references:
            continue
        if market not in selected or selected[market]["logged_ms"] < logged:
            selected[market] = {
                "market": market,
                "decision_ms": point,
                "logged_ms": logged,
                "source_line": number,
                "reference_sources": references,
                "reference_price": metadata.get("reference_price"),
            }
    if file_sha256(path) != sources[str(path)]:
        raise ValueError("decision source changed")
    status: Counter[str] = Counter()
    for item in selected.values():
        for reference in item["reference_sources"]:
            source = reference["source"]
            raw = reference.get("raw", {})
            at = None
            if source == "okx" and raw.get("ts"):
                at = int(raw["ts"])
            elif source == "coinbase" and raw.get("time"):
                at = timestamp(raw["time"])
            if at is None:
                status[source + ":exchange_timestamp_missing"] += 1
            else:
                age = item["decision_ms"] - at
                reference["observed_exchange_age_at_decision_ms"] = age
                status[
                    source
                    + (":age_le_60s" if 0 <= age <= 60_000 else ":stale_or_future")
                ] += 1
    write_json(
        args.output / "selected_references.json",
        [selected[k] for k in sorted(selected)],
    )
    summary = {
        "run_id": "expiry-reference-quality-20260907-v1",
        "sources": sources,
        "feature_csvs": summaries,
        "book_universe_markets": len(markets),
        "markets_with_predecision_reference_record": len(selected),
        "quote_timestamp_status": dict(status),
        "selection_limitation": (
            "decision log only records legacy detected opportunities; "
            "missing references are not a random sample"
        ),
        "interpretation": (
            "use logged availability time, never loop-start seconds_left; "
            "no legacy probability used"
        ),
        "script_sha256": file_sha256(Path(__file__)),
        "live_enabled": False,
    }
    write_json(args.output / "summary.json", summary)
    print(json.dumps({k: v for k, v in summary.items() if k != "sources"}, indent=2))


if __name__ == "__main__":
    main()
