"""Offline, receipt-causal freshness diagnostics; never infer maker fills."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from hyperbot2.event_store import JsonlEventStore
from hyperbot2.research.artifacts import file_sha256, write_json


def distribution(values: list[float]) -> dict[str, float | int]:
    """Use nearest-rank quantiles, including minimum and maximum."""
    if not values:
        return {"n": 0}
    ordered = sorted(values)
    return {
        "n": len(values),
        "min": ordered[0],
        **{
            f"p{p}": ordered[max(0, math.ceil(p / 100 * len(ordered)) - 1)]
            for p in (50, 90, 95, 99)
        },
        "max": ordered[-1],
    }


def coverage(rows: list[tuple[int, int]], stale_ms: int = 500) -> dict[str, int]:
    """Integrate freshness until the next receipt; omit unobserved tail time.

    A future exchange timestamp is invalid until replaced, matching book.age.
    Each row is (receipt time, exchange time), in causal receipt order.
    """
    fresh = total = 0
    for (received, exchange), (until, _) in zip(rows, rows[1:], strict=False):
        if until < received:
            raise ValueError("receipt clock regressed")
        total += until - received
        if exchange <= received:
            fresh += max(0, min(until, exchange + stale_ms) - received)
    return {"observed_ms": total, "fresh_ms": fresh, "stale_ms": total - fresh}


def activation_count(ages: list[int], placement: int, uncertainty: int) -> int:
    return sum(age >= 0 and age + placement + uncertainty <= 500 for age in ages)


def diagnose(raw: Path, windows: Path | None) -> dict[str, Any]:
    books: dict[str, list[tuple[int, int]]] = defaultdict(list)
    offsets = []
    channels: Counter[str] = Counter()
    fields: set[str] = set()
    contexts: set[str] = set()
    fast = 0
    store = JsonlEventStore(raw.parent)
    for record in store.iter_records(raw.stem):
        event = record["payload"]
        assert isinstance(event, dict)
        channels[str(event["channel"])] += 1
        contexts.add(json.dumps(event["context"], sort_keys=True))
        received = int(str(event["receive_ts_ms"]))
        offsets.append(received - int(str(event["receive_monotonic_ns"])) / 1e6)
        if event["channel"] != "l2Book":
            continue
        exchange = int(str(event["exchange_ts_ms"]))
        books[str(event["coin"])].append((received, exchange))
        payload = json.loads(str(event["payload_json"]))
        fast += payload.get("fast") is True
        for side in payload["levels"]:
            for level in side:
                fields.update(level)
    ages = [r - e for rows in books.values() for r, e in rows]
    steady = [r - e for rows in books.values() for r, e in rows[1:]]
    per_coin = {}
    for coin, rows in sorted(books.items()):
        per_coin[coin] = {
            "age_ms": distribution([r - e for r, e in rows]),
            "receipt_interval_ms": distribution(
                [b[0] - a[0] for a, b in zip(rows, rows[1:], strict=False)]
            ),
            "exchange_interval_ms": distribution(
                [b[1] - a[1] for a, b in zip(rows, rows[1:], strict=False)]
            ),
            "distinct_exchange_times": len({e for _, e in rows}),
            "time_coverage": coverage(rows),
        }
    total = sum(x["time_coverage"]["observed_ms"] for x in per_coin.values())
    fresh = sum(x["time_coverage"]["fresh_ms"] for x in per_coin.values())
    result: dict[str, Any] = {
        "raw_path": str(raw),
        "raw_sha256": file_sha256(raw),
        "payload_integrity_verified": True,
        "contexts": [json.loads(c) for c in sorted(contexts)],
        "channels": dict(channels),
        "books": len(ages),
        "fast_confirmed": fast,
        "level_fields": sorted(fields),
        "negative_age": sum(a < 0 for a in ages),
        "fresh_at_receipt": sum(0 <= a <= 500 for a in ages),
        "receipt_age_ms": distribution(ages),
        "receipt_age_excluding_first_per_coin_ms": distribution(steady),
        "wall_minus_monotonic_range_ms": max(offsets) - min(offsets),
        "activation_sensitivity": [
            {
                "placement_ms": p,
                "clock_uncertainty_ms": u,
                "passing_books": activation_count(ages, p, u),
            }
            for u in (0, 50)
            for p in (0, 50, 100, 150, 200, 250, 300, 350, 700)
        ],
        "pooled_coin_time": {
            "observed_ms": total,
            "fresh_ms": fresh,
            "fresh_fraction": fresh / total if total else None,
        },
        "per_coin": per_coin,
        "limits": [
            "short observational sample",
            "not order latency measurements",
            "pooled coin-time is not portfolio uptime",
            "no fill qualification",
        ],
    }
    if windows:
        diagnostics = []
        for line in windows.read_text().splitlines():
            window = json.loads(line)
            start = window["now_ms"]
            end = start + 1350  # Current fixed TTL + cancellation assumption.
            chain = [
                window["book"],
                *sorted(
                    (b for b in window["future_books"] if b["received_ms"] <= end),
                    key=lambda b: b["received_ms"],
                ),
            ]
            maxima = {}
            for placement in (0, 100, 350):
                observed_ages = []
                for idx, book in enumerate(chain):
                    until = (
                        chain[idx + 1]["received_ms"] if idx + 1 < len(chain) else end
                    )
                    if until > max(start + placement, book["received_ms"]):
                        observed_ages.append(until - book["exchange_ms"])
                maxima[str(placement)] = max(observed_ages)
            diagnostics.append(
                {
                    "now_ms": start,
                    "exposure_healthy": window["exposure_healthy"],
                    "max_age_during_exposure_ms_by_activation": maxima,
                    "current_freshness_only_pass": maxima["0"] <= 500,
                }
            )
        result["windows"] = {
            "path": str(windows),
            "sha256": file_sha256(windows),
            "count": len(diagnostics),
            "complete": sum(d["exposure_healthy"] for d in diagnostics),
            "freshness_only_pass": sum(
                d["current_freshness_only_pass"] for d in diagnostics
            ),
            "details": diagnostics,
            "limits": (
                "Counterfactual necessary condition; no replay or quotes executed"
            ),
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--windows", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = diagnose(args.raw, args.windows)
    result["diagnostic_script_sha256"] = file_sha256(Path(__file__))
    result["fixed_assumptions"] = {"stale_ms": 500, "ttl_ms": 1000, "cancel_ms": 350}
    write_json(args.output, result)
    print(args.output)


if __name__ == "__main__":
    main()
