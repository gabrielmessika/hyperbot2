"""Bounded causal assembly of recorded public events into replay windows."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Callable, Iterator
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from typing import Any

from hyperbot2.event_store import JsonlEventStore
from hyperbot2.models import Side
from hyperbot2.outcomes.config import OutcomeConfig
from hyperbot2.outcomes.contracts import FairValue, OutcomeDefinition, book_from_public
from hyperbot2.outcomes.fair_value import CausalFairValueModel, ReferencePrice
from hyperbot2.outcomes.session import OutcomeTrade, OutcomeWindow
from hyperbot2.research.artifacts import checked_input, file_sha256


class ReferenceJoin:
    """Consume explicit, hashed settlement-reference observations by receipt time."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path
        self.sha256 = checked_input(path) if path else None
        self.models: dict[str, CausalFairValueModel] = {}
        self.rows = self._rows()
        self.next_row = next(self.rows, None)

    def _rows(self) -> Iterator[dict[str, Any]]:
        if self.path is None:
            return
        previous = -1
        with self.path.open() as stream:
            for line in stream:
                row = json.loads(line)
                if row.get("kind") != "settlement_mark":
                    raise ValueError("unqualified reference source kind")
                received = row["received_ms"]
                if type(received) is not int or received < previous:
                    raise ValueError("reference receipt order is invalid")
                previous = received
                proof = row.get("source_sha256", "")
                if len(proof) != 64 or any(c not in "0123456789abcdef" for c in proof):
                    raise ValueError("reference provenance missing")
                yield row

    def predict(self, definition: OutcomeDefinition, now_ms: int) -> FairValue | None:
        while self.next_row is not None and self.next_row["received_ms"] <= now_ms:
            row = self.next_row
            model = self.models.setdefault(row["underlying"], CausalFairValueModel())
            model.observe(
                ReferencePrice(
                    row["exchange_ms"], row["received_ms"], Decimal(row["price"])
                )
            )
            self.next_row = next(self.rows, None)
        selected_model = self.models.get(definition.underlying)
        value = selected_model.predict(definition, now_ms) if selected_model else None
        if value is not None:
            from hyperbot2.outcomes.contracts import digest

            value = replace(
                value, source_sha256=digest((self.sha256, value.source_sha256))
            )
        return value

    def verify(self) -> None:
        if self.path and file_sha256(self.path) != self.sha256:
            raise ValueError("reference input changed during join")

    def close(self) -> None:
        self.rows.close() if hasattr(self.rows, "close") else None


class WindowAssembler:
    """One global exposure window; rotate markets and never grant queue proof."""

    def __init__(
        self,
        definitions: tuple[OutcomeDefinition, ...],
        config: OutcomeConfig,
        emit: Callable[[OutcomeWindow], None],
        references: ReferenceJoin | None = None,
    ) -> None:
        if not definitions:
            raise ValueError("no supported definitions")
        self.definitions = {d.outcome_id: d for d in definitions}
        self.order = tuple(self.definitions)
        self.next_market = 0
        self.config, self.emit = config, emit
        self.references = references or ReferenceJoin()
        self.pending: OutcomeWindow | None = None
        self.deadline = -1
        self.previous_ms = -1
        self.counts: Counter[str] = Counter()
        self.reasons: Counter[str] = Counter()
        self.last_healthy = False

    def consume(self, event: dict[str, Any]) -> None:
        received = event["receive_ts_ms"]
        if received < self.previous_ms:
            self.reasons["receipt_order_violation"] += 1
            if self.pending:
                self.pending = replace(self.pending, exposure_healthy=False)
            return
        self.previous_ms = received
        if self.pending and received > self.deadline:
            self._emit()
        if "kind" in event:
            if event["kind"] in {
                "gap",
                "clock_skew",
                "queue_drop",
                "malformed_message",
                "subscription_rejected",
                "disconnected",
            }:
                self.last_healthy = False
                self.reasons[f"collector:{event['kind']}"] += 1
                if self.pending:
                    self.pending = replace(self.pending, exposure_healthy=False)
            return
        try:
            raw = json.loads(event["payload_json"])
            coin = str(event["coin"])
            if not coin.startswith("#"):
                return
            encoded = int(coin[1:])
            market, side = divmod(encoded, 10)
            if market not in self.definitions or side not in (0, 1):
                self.reasons["unsupported_market"] += 1
                return
            if event["channel"] == "l2Book":
                self.counts["public_books"] += 1
                if side:
                    self.counts["no_book_representation_skipped"] += 1
                    return
                book = book_from_public(
                    raw, received_ms=received, sequence=event["local_sequence"]
                )
                self.last_healthy = True
                if self.pending:
                    if (
                        self.pending.definition.outcome_id == market
                        and received > self.pending.now_ms
                    ):
                        self.pending = replace(
                            self.pending,
                            future_books=(*self.pending.future_books, book),
                        )
                elif market == self.order[self.next_market]:
                    definition = self.definitions[market]
                    fair = self.references.predict(definition, received)
                    self.pending = OutcomeWindow(received, definition, book, fair)
                    self.deadline = (
                        received + self.config.ttl_ms + self.config.cancel_ms
                    )
                    self.next_market = (self.next_market + 1) % len(self.order)
                    self.reasons.update(definition.reasons(received))
                    if fair is None:
                        self.reasons["settlement_reference_or_warmup_missing"] += 1
                    if (
                        book.age(received)
                        + self.config.placement_ms
                        + self.config.clock_uncertainty_ms
                        > self.config.stale_ms
                    ):
                        self.reasons["insufficient_causal_freshness"] += 1
                    self.reasons["public_queue_unqualified"] += 1
            elif (
                event["channel"] == "trades"
                and self.pending
                and market == self.pending.definition.outcome_id
            ):
                # Subscription snapshots contain old executions; skip them.
                if not self.pending.now_ms < int(raw["time"]) <= received:
                    self.counts["historical_trade_snapshot_skipped"] += 1
                    return
                if "tid" not in raw or raw.get("side") not in ("B", "A"):
                    raise ValueError("trade identity/aggressor missing")
                trade = OutcomeTrade(
                    market,
                    str(raw["tid"]),
                    side,
                    int(raw["time"]),
                    received,
                    event["local_sequence"],
                    Side.BUY if raw["side"] == "B" else Side.SELL,
                    Decimal(raw["px"]),
                    Decimal(raw["sz"]),
                )
                trade.canonical()
                self.pending = replace(
                    self.pending, trades=(*self.pending.trades, trade)
                )
            if (
                self.pending
                and len(self.pending.future_books) + len(self.pending.trades) > 10_000
            ):
                raise RuntimeError("exposure window event budget exceeded")
        except (ValueError, KeyError, ArithmeticError) as error:
            self.reasons[f"invalid_public_event:{type(error).__name__}"] += 1
            if self.pending:
                self.pending = replace(self.pending, exposure_healthy=False)

    def _emit(self) -> None:
        assert self.pending is not None
        self.emit(self.pending)
        self.counts["windows"] += 1
        self.pending = None

    def finish(self) -> None:
        if self.pending:
            # Keep the incomplete tail and invalidate its exposure evidence.
            self.pending = replace(self.pending, exposure_healthy=False)
            self.reasons["incomplete_terminal_window"] += 1
            self._emit()
        self.references.verify()
        self.references.close()


def recorded_events(
    root: Path,
    data_stream: str = "outcomes-fast-public",
    control_stream: str = "outcomes-fast-control",
) -> Iterator[dict[str, Any]]:
    import heapq

    store = JsonlEventStore(root)

    def rows(name: str) -> Iterator[dict[str, Any]]:
        for record in store.iter_records(name):
            payload = record["payload"]
            assert isinstance(payload, dict)
            yield payload

    yield from heapq.merge(
        rows(data_stream), rows(control_stream), key=lambda e: e["receive_ts_ms"]
    )
