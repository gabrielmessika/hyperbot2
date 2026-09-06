"""Closed-loop outcome replay/shadow sharing strategy, ledger and risk authority."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, replace
from decimal import Decimal
from typing import Any

from hyperbot2.models import DatasetTier, EventContext, Side
from hyperbot2.outcomes.config import OutcomeConfig
from hyperbot2.outcomes.contracts import (
    ONE,
    ZERO,
    FairValue,
    OutcomeBook,
    OutcomeDefinition,
)
from hyperbot2.outcomes.ledger import OutcomeLedger
from hyperbot2.outcomes.strategy import SelectiveOutcomeStrategy
from hyperbot2.replay.engine import (
    FillModelKind,
    ReplayBook,
    ReplayConfig,
    ReplayDataError,
    ReplayEngine,
    ReplayMarketEvent,
    ReplayQuote,
    ReplayTrade,
)


@dataclass(frozen=True, slots=True)
class OutcomeTrade:
    outcome_id: int
    match_id: str
    side_index: int
    exchange_ms: int
    received_ms: int
    sequence: int
    aggressor: Side
    price: Decimal
    size: Decimal

    def canonical(self) -> ReplayTrade:
        if self.side_index not in (0, 1) or not self.match_id:
            raise ValueError("trade side/match identity missing")
        if not self.price.is_finite() or not 0 < self.price < 1:
            raise ValueError("invalid outcome trade price")
        side = self.aggressor
        price = self.price
        if self.side_index:
            side = Side.SELL if side is Side.BUY else Side.BUY
            price = ONE - price
        return ReplayTrade(
            f"outcome:{self.outcome_id}",
            self.exchange_ms,
            self.sequence,
            side,
            price,
            self.size,
            self.received_ms,
        )


@dataclass(frozen=True, slots=True)
class OutcomeWindow:
    now_ms: int
    definition: OutcomeDefinition
    book: OutcomeBook
    fair: FairValue | None
    future_books: tuple[OutcomeBook, ...] = ()
    trades: tuple[OutcomeTrade, ...] = ()
    healthy: bool = True


class OutcomeSession:
    """Global non-overlapping windows bound memory and keep inventory causal.

    Only YES orders are emitted. All visible merged liquidity is put ahead of
    our order; central permits observed queue reductions, pessimistic does not.
    No price-side priority benefit from dual orders is claimed.
    """

    def __init__(
        self,
        config: OutcomeConfig,
        context: EventContext,
        model: FillModelKind,
        *,
        shadow: bool = False,
    ) -> None:
        self.config, self.context, self.model, self.shadow = (
            config,
            context,
            model,
            shadow,
        )
        self.ledger = OutcomeLedger(config.equity_usd)
        self.strategy = SelectiveOutcomeStrategy(config)
        self.definitions: dict[int, OutcomeDefinition] = {}
        self.books: dict[int, OutcomeBook] = {}
        self.counts: Counter[str] = Counter()
        self.last_end_ms = -1
        self.last_frame_ms = -1
        self.first_ms: int | None = None
        self.blocked = False
        self.max_drawdown = ZERO
        self.min_equity = config.equity_usd
        self.maximum_committed_cash = ZERO
        self.dataset_tiers: set[str] = set()
        self.fills: list[dict[str, Any]] = []
        self.lifecycle: list[dict[str, Any]] = []
        self.finished = False

    def process(self, window: OutcomeWindow) -> None:
        if self.finished:
            raise ValueError("session already finalized")
        if window.now_ms < self.last_frame_ms:
            raise ValueError("frames must be in causal receipt order")
        self.last_frame_ms = window.now_ms
        self.first_ms = window.now_ms if self.first_ms is None else self.first_ms
        self.counts["frames"] += 1
        if window.now_ms <= self.last_end_ms:
            self.counts["window_busy"] += 1
            return
        d, b = window.definition, window.book
        self.dataset_tiers.add(b.tier.value)
        self.definitions[d.outcome_id], self.books[b.outcome_id] = d, b
        if self.blocked:
            self.counts["session_data_blocked"] += 1
            return
        if self.model is not FillModelKind.OPTIMISTIC_TOUCH and (
            b.tier is not DatasetTier.A
            or not b.queue_qualified
            or not b.dual_priority_qualified
        ):
            self.blocked = True
            self.counts["unqualified_maker_evidence"] += 1
            return
        decision = self.strategy.decide(
            context=self.context,
            now_ms=window.now_ms,
            definition=d,
            book=b,
            fair=window.fair,
            ledger=self.ledger,
            definitions=self.definitions,
            books=self.books,
            healthy=window.healthy,
        )
        self.counts.update(decision.reasons)
        unavailable = {
            "market_status_unqualified",
            "tick_or_lot_unknown",
            "settlement_rule_unqualified",
            "specification_provenance_missing",
            "fees_unknown_or_expired",
            "future_definition",
            "fair_value_missing",
            "book_definition_mismatch",
        }
        if unavailable.intersection(decision.reasons):
            self.blocked = True
        self.counts["approved_quotes"] += len(decision.approved)
        self.maximum_committed_cash = max(
            self.maximum_committed_cash,
            self.ledger.initial - self.ledger.available_cash,
        )
        if not decision.approved:
            return
        end_ms = window.now_ms + self.config.ttl_ms + self.config.cancel_ms
        self.last_end_ms = end_ms
        future = tuple(x for x in window.future_books if x.received_ms <= end_ms)
        try:
            if any(
                x.outcome_id != d.outcome_id or x.received_ms <= window.now_ms
                for x in future
            ):
                raise ReplayDataError("future book identity/order mismatch")
            if any(
                x.outcome_id != d.outcome_id or x.received_ms <= window.now_ms
                for x in window.trades
            ):
                raise ReplayDataError("trade identity/order mismatch")
            if self.model is not FillModelKind.OPTIMISTIC_TOUCH:
                chain = (b, *sorted(future, key=lambda x: x.received_ms))
                for idx, book in enumerate(chain):
                    book.age(book.received_ms)
                    until = (
                        chain[idx + 1].received_ms if idx + 1 < len(chain) else end_ms
                    )
                    if (
                        book.tier is not DatasetTier.A
                        or not book.queue_qualified
                        or not book.dual_priority_qualified
                    ):
                        raise ReplayDataError("queue provenance lost after emission")
                    if until - book.exchange_ms > self.config.stale_ms:
                        raise ReplayDataError("stale queue during exposure")
                    if any(not book.covers(q.side, q.price) for q in decision.approved):
                        raise ReplayDataError(
                            "quote left observed depth during exposure"
                        )
            events: list[ReplayMarketEvent] = [
                ReplayBook(
                    d.market, x.exchange_ms, x.sequence, x.bids, x.asks, x.received_ms
                )
                for x in (b, *future)
            ]
            seen: dict[str, tuple[object, ...]] = {}
            for trade in sorted(
                window.trades, key=lambda x: (x.received_ms, x.sequence)
            ):
                if trade.received_ms > end_ms:
                    continue
                canonical = trade.canonical()
                economic = (
                    canonical.timestamp_ms,
                    canonical.price,
                    canonical.size,
                    canonical.aggressor_side,
                )
                if trade.match_id in seen:
                    if seen[trade.match_id] != economic:
                        raise ReplayDataError("conflicting dual trade copies")
                    self.counts["deduplicated_dual_trades"] += 1
                    continue
                seen[trade.match_id] = economic
                events.append(canonical)
            # ALO crossing at activation rejects the quote.
            active_ms = window.now_ms + self.config.placement_ms
            active_books = [x for x in (b, *future) if x.received_ms <= active_ms]
            activation_book = max(active_books, key=lambda x: x.received_ms)
            quotes: list[ReplayQuote] = []
            for q in decision.approved:
                self.lifecycle.append(
                    {
                        "intent_id": q.intent_id,
                        "event": "submitted",
                        "at_ms": window.now_ms,
                    }
                )
                crossed = (
                    q.price >= activation_book.asks[0].price
                    if q.side is Side.BUY
                    else q.price <= activation_book.bids[0].price
                )
                if crossed:
                    self.counts["alo_rejected"] += 1
                    self.lifecycle.append(
                        {
                            "intent_id": q.intent_id,
                            "event": "alo_rejected",
                            "at_ms": active_ms,
                        }
                    )
                    continue
                self.lifecycle.append(
                    {
                        "intent_id": q.intent_id,
                        "event": "ack_simulated",
                        "at_ms": active_ms,
                    }
                )
                quotes.append(
                    ReplayQuote(
                        q.intent_id,
                        q.market,
                        q.side,
                        q.price,
                        q.size,
                        window.now_ms,
                        window.now_ms + self.config.ttl_ms,
                        ZERO,
                    )
                )
            config = ReplayConfig(
                self.context.run_id,
                self.context.code_version,
                self.model,
                (b.tier,),
                self.config.placement_ms,
                self.config.cancel_ms,
                central_queue_fraction=ONE,
            )
            result = ReplayEngine().run(
                config=config, events=tuple(events), quotes=tuple(quotes)
            )
            for idx, fill in enumerate(result.fills):
                fees_before = self.ledger.fees_paid
                self.ledger.fill(
                    fill_id=f"{fill.quote_id}:{idx}",
                    intent_id=fill.quote_id,
                    quantity=fill.size,
                    price=fill.price,
                    now_ms=fill.fill_ts_ms,
                    definition=d,
                )
                self.fills.append(
                    {**asdict(fill), "fee_usd": self.ledger.fees_paid - fees_before}
                )
                self.lifecycle.append(
                    {
                        "intent_id": fill.quote_id,
                        "event": "fill_simulated",
                        "at_ms": fill.fill_ts_ms,
                    }
                )
            self.counts["fills"] += len(result.fills)
        except (ReplayDataError, ValueError) as exc:
            # Do not drop bad future intervals and publish a survivor-only strategy.
            self.blocked = True
            self.counts[f"exposure_data_failure:{exc}"] += 1
        finally:
            for q in decision.approved:
                self.ledger.release(q.intent_id)
                self.lifecycle.append(
                    {
                        "intent_id": q.intent_id,
                        "event": "cancel_effective_simulated",
                        "at_ms": end_ms,
                    }
                )
        if future:
            self.books[d.outcome_id] = max(future, key=lambda x: x.received_ms)
        portfolio = self.ledger.portfolio(end_ms, self.definitions, self.books)
        self.max_drawdown = max(
            self.max_drawdown, portfolio.peak_equity_usd - portfolio.equity_usd
        )
        self.min_equity = min(self.min_equity, portfolio.equity_usd)

    def finish(self) -> dict[str, Any]:
        if self.finished:
            raise ValueError("session already finalized")
        self.finished = True
        end_ms = max(self.last_end_ms, self.last_frame_ms, 0)
        trading_pnl = self.ledger.realized
        residual = {
            str(m): str(self.ledger.quantity(m))
            for m in self.definitions
            if self.ledger.quantity(m)
        }
        for market, definition in self.definitions.items():
            if not self.ledger.quantity(market):
                continue
            if definition.fees is None or not (
                definition.fees.observed_ms <= end_ms < definition.fees.valid_until_ms
            ):
                self.blocked = True
                self.counts["terminal_fees_unknown_or_expired"] += 1
            book = self.books.get(market)
            # Worst-payoff terminal liquidation; no future settlement label invented.
            if (
                book is None
                or end_ms - book.exchange_ms > self.config.stale_ms
                or self.blocked
            ):
                self.ledger.terminal_close(definition, now_ms=end_ms)
                continue
            for level in book.bids:
                amount = min(self.ledger.quantity(market), level.size)
                if amount <= 0:
                    break
                # Value each visible level once, including its closing fee.
                assert definition.fees is not None
                from hyperbot2.outcomes.contracts import Operation

                fee = definition.fees.cost(Operation.TAKER_CLOSE, amount, level.price)
                self.ledger._close(
                    market, amount, level.price, fee, end_ms, terminal=True
                )
                self.ledger.fees_paid += fee
            if self.ledger.quantity(market):
                self.ledger.terminal_close(definition, now_ms=end_ms)
        cycles: dict[str, dict[str, Any]] = {}
        for part in self.ledger.cycles:
            row = cycles.setdefault(
                part.entry_id,
                {
                    "entry_id": part.entry_id,
                    "outcome_id": part.outcome_id,
                    "opened_ms": part.opened_ms,
                    "closed_ms": part.closed_ms,
                    "entry_notional": ZERO,
                    "pnl": ZERO,
                    "terminal": False,
                },
            )
            row["entry_notional"] += part.entry_notional
            row["pnl"] += part.pnl
            row["closed_ms"] = max(row["closed_ms"], part.closed_ms)
            row["terminal"] = row["terminal"] or part.terminal
        gains = sum((r["pnl"] for r in cycles.values() if r["pnl"] > 0), ZERO)
        losses = -sum((r["pnl"] for r in cycles.values() if r["pnl"] < 0), ZERO)
        first_ms = end_ms if self.first_ms is None else self.first_ms
        elapsed_days = Decimal(max(end_ms - first_ms, 0)) / Decimal(86_400_000)
        infra = self.config.monthly_infrastructure_usd * elapsed_days / 30
        return {
            "run_id": self.context.run_id,
            "code_version": self.context.code_version,
            "config_sha256": self.context.config_hash,
            "model": self.model.value,
            "first_decision_ms": self.first_ms,
            "last_decision_ms": self.last_frame_ms if self.last_frame_ms >= 0 else None,
            "terminal_ms": end_ms,
            "dataset_tiers": sorted(self.dataset_tiers),
            "placement_ms": self.config.placement_ms,
            "cancel_ms": self.config.cancel_ms,
            "central_queue_fraction": "1",
            "shadow_only": True,
            "shadow_mode": self.shadow,
            "verdict": "DATA_BLOCKED" if self.blocked else "INCONCLUSIVE",
            "economic_result_publishable": not self.blocked,
            "net_pnl_usd": None
            if self.blocked
            else self.ledger.cash - self.ledger.initial,
            "diagnostic_cash_usd": self.ledger.cash,
            "diagnostic_realized_before_terminal_usd": trading_pnl,
            "diagnostic_terminal_pnl_usd": self.ledger.realized - trading_pnl,
            "maximum_committed_cash_usd": self.maximum_committed_cash,
            "cash_benchmark_pnl_usd": ZERO,
            "fees_usd": self.ledger.fees_paid,
            "infrastructure_usd": infra,
            "net_after_infrastructure_usd": None
            if self.blocked
            else self.ledger.cash - self.ledger.initial - infra,
            "profit_factor": gains / losses if losses else None,
            "gross_cycle_gains_usd": gains,
            "gross_cycle_losses_usd": losses,
            "round_trips": sum(not r["terminal"] for r in cycles.values()),
            "terminal_cycles": sum(r["terminal"] for r in cycles.values()),
            "entry_turnover_usd": sum(
                (r["entry_notional"] for r in cycles.values()), ZERO
            ),
            "maximum_drawdown_usd": max(
                self.max_drawdown, self.ledger.peak - self.ledger.cash
            ),
            "terminal_inventory_before_liquidation": residual,
            "terminal_inventory_after_liquidation": "0",
            "counts": dict(self.counts),
            "simulated_actions_remaining": self.strategy.remaining_actions,
            "cycles": list(cycles.values()),
            "fills": self.fills,
            "lifecycle": self.lifecycle,
            "promotion_authorized": False,
            "limits": [
                "simulation only",
                "no automatic OOS promotion",
                "single YES representation",
                "conservative merged queue; no dual-side priority benefit",
            ],
        }


def stressed_config(config: OutcomeConfig, scenario: str) -> OutcomeConfig:
    if scenario == "latency_x2":
        return replace(
            config, placement_ms=config.placement_ms * 2, cancel_ms=config.cancel_ms * 2
        )
    if scenario not in ("base", "fees_x2"):
        raise ValueError("unknown scenario")
    return config
