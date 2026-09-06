"""Selective recurring outcome quotes using the shared HyperBot risk supervisor."""

from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal

from hyperbot2.models import EventContext, QuoteIntent, Side
from hyperbot2.outcomes.config import OutcomeConfig
from hyperbot2.outcomes.contracts import (
    ZERO,
    FairValue,
    OutcomeBook,
    OutcomeDefinition,
    digest,
)
from hyperbot2.outcomes.ledger import OutcomeLedger
from hyperbot2.risk.supervisor import (
    IntentMetadata,
    OutcomeTokenSide,
    RiskLimits,
    RiskSupervisor,
    StrategyKind,
)
from hyperbot2.strategies.common import (
    round_size,
    round_to_tick,
    size_for_minimum_notional,
)


@dataclass(frozen=True, slots=True)
class QuoteDecision:
    approved: tuple[QuoteIntent, ...]
    reasons: tuple[str, ...]


class SelectiveOutcomeStrategy:
    name = "outcome_selective_v2"

    def __init__(self, config: OutcomeConfig) -> None:
        self.config = config
        self.risk = RiskSupervisor(RiskLimits(reference_equity_usd=config.equity_usd))
        self.remaining_actions = config.research_action_budget

    def decide(
        self,
        *,
        context: EventContext,
        now_ms: int,
        definition: OutcomeDefinition,
        book: OutcomeBook,
        fair: FairValue | None,
        ledger: OutcomeLedger,
        definitions: dict[int, OutcomeDefinition],
        books: dict[int, OutcomeBook],
        healthy: bool = True,
    ) -> QuoteDecision:
        c = self.config
        reasons = list(definition.reasons(now_ms))
        if not healthy:
            reasons.append("feed_unhealthy")
        if definition.outcome_id != book.outcome_id:
            reasons.append("book_definition_mismatch")
        try:
            age = book.age(now_ms)
        except ValueError:
            age = c.stale_ms + 1
            reasons.append("clock_ambiguity")
        if age + c.placement_ms + c.clock_uncertainty_ms > c.stale_ms:
            reasons.append("insufficient_causal_freshness")
        if definition.expiry_ms - now_ms < c.no_entry_before_expiry_ms:
            reasons.append("near_expiry")
        if fair is None:
            reasons.append("fair_value_missing")
        elif fair.available_ms > now_ms or now_ms - fair.reference_ms > c.stale_ms:
            reasons.append("fair_value_future_or_stale")
        elif not c.minimum_probability <= fair.probability <= c.maximum_probability:
            reasons.append("probability_outside_range")
        if reasons:
            return QuoteDecision((), tuple(reasons))
        assert fair is not None and definition.fees is not None
        assert definition.tick is not None and definition.size_increment is not None
        # One-sided settlement risk is charged on a conservative exit/settle basis.
        fee_margin = max(
            definition.fees.maker_close_rate,
            definition.fees.taker_close_rate,
            definition.fees.settlement_rate,
        )
        half = (
            fee_margin
            + fair.uncertainty
            + fair.adverse_selection
            + c.inventory_charge
            + c.additional_margin
        )
        skew = min(
            ledger.quantity(definition.outcome_id) * definition.tick, Decimal("0.05")
        )
        prices = (
            (
                Side.BUY,
                round_to_tick(
                    min(book.bids[0].price, fair.probability - half - skew),
                    definition.tick,
                    Side.BUY,
                ),
            ),
            (
                Side.SELL,
                round_to_tick(
                    max(book.asks[0].price, fair.probability + half - skew),
                    definition.tick,
                    Side.SELL,
                ),
            ),
        )
        approved: list[QuoteIntent] = []
        for side, price in prices:
            if self.remaining_actions < 2:
                reasons.append("simulated_action_budget_exhausted")
                continue
            if not c.minimum_probability <= price <= c.maximum_probability:
                reasons.append("quote_price_outside_range")
                continue
            if not book.covers(side, price):
                reasons.append("quote_outside_visible_depth")
                continue
            if side is Side.BUY:
                size = size_for_minimum_notional(
                    c.order_usd, price, definition.size_increment
                )
            else:
                size = round_size(
                    min(
                        ledger.available_quantity(definition.outcome_id),
                        c.order_usd / price,
                    ),
                    definition.size_increment,
                )
                if size * price < c.order_usd:
                    # Sell the smallest eligible lot without borrowing token inventory.
                    size = size_for_minimum_notional(
                        c.order_usd, price, definition.size_increment
                    )
                if size > ledger.available_quantity(definition.outcome_id):
                    reasons.append("no_unreserved_sale_inventory")
                    continue
            identity = digest(
                (
                    context.run_id,
                    self.name,
                    definition.sha256,
                    now_ms,
                    book.sequence,
                    side.value,
                    str(price),
                )
            )[:32]
            intent = QuoteIntent(
                context,
                identity,
                self.name,
                definition.market,
                side,
                price,
                size,
                c.ttl_ms,
                fair.probability,
                ZERO,
                ledger.quantity(definition.outcome_id),
                ("selective_outcome",),
            )
            metadata = IntentMetadata(
                StrategyKind.OUTCOME,
                "outcome",
                age,
                "ALO",
                definition.sha256,
                definition.sha256,
                definition.tick,
                definition.market,
                OutcomeTokenSide.YES,
                "crypto",
            )
            portfolio = ledger.portfolio(now_ms, definitions, books, healthy=healthy)
            result = self.risk.evaluate(intent, metadata, portfolio)
            if result.approved is None:
                reasons.extend(result.rejection_reasons)
                continue
            intent = replace(
                intent,
                size=round_size(
                    result.approved.approved_size, definition.size_increment
                ),
            )
            try:
                ledger.reserve(intent, definition)
            except ValueError as exc:
                reasons.append(str(exc))
                continue
            approved.append(intent)
            # Prepay placement and cancellation; no volume-based replenishment.
            self.remaining_actions -= 2
        return QuoteDecision(tuple(approved), tuple(reasons))
