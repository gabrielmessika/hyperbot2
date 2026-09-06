"""Streaming descriptive screen using the existing, provenance-aware HIP-4 adapter."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from hyperbot2.legacy.adapters import (
    AdaptationContext,
    LegacyAdaptationError,
    LegacyHip4Adapter,
)
from hyperbot2.models import (
    DatasetTier,
    EventContext,
    LegacyBookObservation,
)
from hyperbot2.outcomes.contracts import UNIVERSE, ZERO
from hyperbot2.research.artifacts import CampaignBudget, file_sha256


@dataclass(frozen=True, slots=True)
class ScreenRequest:
    source_path: Path
    start_ms: int | None = None
    end_ms: int | None = None
    max_records: int | None = None
    gap_ms: int = 30_000


def screen_legacy(
    request: ScreenRequest,
    context: EventContext,
    budget: CampaignBudget,
) -> dict[str, Any]:
    path = request.source_path
    if path.is_symlink() or path.name != "book_snapshots.jsonl":
        raise ValueError("an explicit HIP-4 raw book_snapshots.jsonl is required")
    source_hash = file_sha256(path)
    adapter = LegacyHip4Adapter()
    counts: Counter[str] = Counter()
    groups: dict[str, dict[str, Any]] = {}
    previous: dict[tuple[str, str], tuple[int, Decimal]] = {}
    pending: dict[tuple[str, str], deque[tuple[int, Decimal, Decimal]]] = defaultdict(
        deque
    )
    hist: dict[str, Counter[int]] = defaultdict(Counter)
    first: int | None = None
    last: int | None = None
    read_hash = hashlib.sha256()
    for underlying in UNIVERSE:
        groups[underlying] = {
            "observations": 0,
            "min_order_depth_both_sides": 0,
            "clock_ambiguous": 0,
            "fresh_at_receipt_500ms": 0,
            "gaps": 0,
            "observed_elapsed_ms": 0,
            "bounded_covered_ms": 0,
            "markout_30s_count": 0,
            "bid_to_mid_30s_sum": ZERO,
            "ask_to_mid_30s_sum": ZERO,
        }
    with path.open("rb") as stream:
        for line_number, line in enumerate(stream, 1):
            if request.max_records is not None and line_number > request.max_records:
                break
            read_hash.update(line)
            counts["raw_records"] += 1
            if line_number % 1000 == 0:
                budget.check()
            try:
                raw = json.loads(line)
                adaptation = AdaptationContext(
                    context,
                    DatasetTier.B,
                    str(path),
                    source_hash,
                    line_number,
                    hashlib.sha256(line).hexdigest(),
                    "raw_line_sha256",
                )
                events = adapter.adapt(raw, adaptation)
                event = events[0]
                if not isinstance(event, LegacyBookObservation):
                    raise ValueError("expected book observation")
                ts = event.exchange_ts_ms
                if request.start_ms is not None and ts < request.start_ms:
                    continue
                if request.end_ms is not None and ts >= request.end_ms:
                    continue
                market = event.market_id or ""
                underlying = market.split("_")[0]
                if underlying not in UNIVERSE or event.outcome_side not in (
                    "YES",
                    "NO",
                ):
                    counts["unsupported_market"] += 1
                    continue
                bid, ask = event.best_bid, event.best_ask
                if bid is None or ask is None or not 0 < bid < ask < 1:
                    counts["invalid_book"] += 1
                    continue
                received = int(
                    datetime.fromisoformat(
                        str(raw["ts_init"]).replace("Z", "+00:00")
                    ).timestamp()
                    * 1000
                )
                if received < ts:
                    groups[underlying]["clock_ambiguous"] += 1
                elif received - ts <= 500:
                    groups[underlying]["fresh_at_receipt_500ms"] += 1
                key = (market, event.outcome_side)
                midpoint = (bid + ask) / 2
                prev = previous.get(key)
                if prev is not None and ts <= prev[0]:
                    counts["duplicate_or_out_of_order"] += 1
                    continue
                if prev is not None:
                    gap = ts - prev[0]
                    groups[underlying]["observed_elapsed_ms"] += gap
                    groups[underlying]["bounded_covered_ms"] += min(gap, request.gap_ms)
                    groups[underlying]["gaps"] += int(gap > request.gap_ms)
                previous[key] = (ts, midpoint)
                queue = pending[key]
                while queue and ts - queue[0][0] >= 30_000:
                    old_ts, old_bid, old_ask = queue.popleft()
                    if ts - old_ts <= 35_000:
                        groups[underlying]["markout_30s_count"] += 1
                        groups[underlying]["bid_to_mid_30s_sum"] += midpoint - old_bid
                        groups[underlying]["ask_to_mid_30s_sum"] += old_ask - midpoint
                    else:
                        counts["missing_markout_30s"] += 1
                if len(queue) >= 1000:
                    counts["markout_buffer_overflow"] += 1
                    queue.popleft()
                queue.append((ts, bid, ask))
                hist[underlying][int((ask - bid) * 100_000)] += 1
                groups[underlying]["observations"] += 1
                groups[underlying]["min_order_depth_both_sides"] += int(
                    (event.bid_size or ZERO) * bid >= 10
                    and (event.ask_size or ZERO) * ask >= 10
                )
                first = ts if first is None else min(first, ts)
                last = ts if last is None else max(last, ts)
                counts["valid_records"] += 1
            except LegacyAdaptationError as exc:
                counts[f"rejected:{exc.code}"] += 1
            except (ValueError, KeyError, TypeError, ArithmeticError) as exc:
                counts[f"rejected:{type(exc).__name__}"] += 1
    complete = (
        request.max_records is None or counts["raw_records"] < request.max_records
    )
    if complete and read_hash.hexdigest() != source_hash:
        raise ValueError("source changed while screening")
    for underlying, values in hist.items():
        target = sum(values.values()) // 2
        cumulative = 0
        for value, count in sorted(values.items()):
            cumulative += count
            if cumulative > target:
                groups[underlying]["spread_median_1e5_bin"] = Decimal(value) / 100_000
                break
    counts["unresolved_markout_tail"] = sum(len(q) for q in pending.values())
    return {
        "run_id": context.run_id,
        "code_version": context.code_version,
        "config_sha256": context.config_hash,
        "source_path": str(path),
        "source_sha256": source_hash,
        "adapter": f"{adapter.name}@{adapter.version}",
        "tier": "B",
        "first_exchange_ms": first,
        "last_exchange_ms": last,
        "source_complete_scan": complete,
        "schema": "hip4_nautilus_book_snapshots",
        "counts": dict(counts),
        "by_underlying": groups,
        "verdict": "DATA_BLOCKED",
        "candidate_pnl_usd": None,
        "promotion_authorized": False,
        "missing_for_candidate": [
            "qualified historical outcome specifications and effective fees",
            "causal reference, volatility and calibration joined to each decision",
            "tier A qualified merged queue for central/pessimistic fills",
        ],
        "interpretation": "spread and unconditional quote-to-mid markouts; no fills",
        "limits": [
            "event weighted; YES/NO representations are not independent liquidity",
            "coverage summed by market-side; no portfolio uptime qualification",
            "30s markouts: first event within 30-35s; missing labels retained",
            "tick-binned median, not a return",
            "B data cannot qualify execution",
        ],
    }


def legacy_paper_summary(path: Path) -> dict[str, Any]:
    before = file_sha256(path)
    gains = losses = ZERO
    counts: Counter[str] = Counter()
    pnls: dict[str, Decimal] = defaultdict(lambda: ZERO)
    markets: set[str] = set()
    with path.open() as stream:
        for row in csv.DictReader(stream):
            pnl = Decimal(row["net_pnl_usdc"])
            if not pnl.is_finite():
                raise ValueError("invalid paper PnL")
            gains += max(pnl, ZERO)
            losses += max(-pnl, ZERO)
            counts[row["result"]] += 1
            pnls[row["underlying"]] += pnl
            markets.add(row["market_id"])
    if file_sha256(path) != before:
        raise ValueError("paper source changed while reading")
    return {
        "source_path": str(path),
        "sha256": before,
        "tier": "B",
        "mode": "legacy_paper",
        "net_pnl_usd": gains - losses,
        "profit_factor": gains / losses if losses else None,
        "closure_types": dict(counts),
        "distinct_markets": len(markets),
        "by_underlying": dict(pnls),
    }
