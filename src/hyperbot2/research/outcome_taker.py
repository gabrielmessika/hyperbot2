"""Conservative exploratory buy-to-settlement accounting, without order routing."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_CEILING, Decimal

D = Decimal


@dataclass(frozen=True, slots=True)
class TakerBook:
    event_ms: int
    received_ms: int
    ask: Decimal
    ask_size: Decimal

    def fresh(self, now_ms: int) -> bool:
        return (
            0 <= now_ms - self.event_ms <= 60_000
            and self.event_ms <= self.received_ms <= now_ms
            and now_ms - self.received_ms <= 60_000
            and self.ask.is_finite()
            and D(0) < self.ask < D(1)
            and self.ask_size.is_finite()
            and self.ask_size > 0
        )


@dataclass(frozen=True, slots=True)
class TakerIntent:
    side: str
    decision_ms: int
    quantity: Decimal
    decision_ask: Decimal
    limit: Decimal
    conservative_probability: Decimal


def select_intent(
    decision_ms: int,
    yes_probabilities: tuple[Decimal, ...],
    books: dict[str, TakerBook],
) -> TakerIntent | None:
    if not yes_probabilities or any(
        not p.is_finite() or not D(0) <= p <= D(1) for p in yes_probabilities
    ):
        raise ValueError("valid causal probabilities required")
    candidates: list[tuple[Decimal, TakerIntent]] = []
    for side in ("YES", "NO"):
        book = books.get(side)
        if book is None or not book.fresh(decision_ms):
            continue
        if not D("0.15") <= book.ask <= D("0.85"):
            continue
        probabilities = (
            yes_probabilities
            if side == "YES"
            else tuple(1 - p for p in yes_probabilities)
        )
        conservative = max(D(0), min(probabilities) - D("0.03"))
        limit = min(D("0.85"), conservative * D("0.998") - D("0.05"))
        quantity = (D(10) / book.ask).to_integral_value(rounding=ROUND_CEILING)
        if (
            book.ask > limit
            or quantity * book.ask > 11
            or quantity > book.ask_size * D("0.1")
        ):
            continue
        intent = TakerIntent(side, decision_ms, quantity, book.ask, limit, conservative)
        candidates.append((conservative * D("0.998") - book.ask, intent))
    return max(candidates, key=lambda item: item[0])[1] if candidates else None


def execution_price(
    intent: TakerIntent, book: TakerBook | None, *, delay: bool = False
) -> Decimal | None:
    if book is None:
        return None
    minimum, maximum = (60_000, 120_000) if delay else (1000, 60_000)
    lag = book.received_ms - intent.decision_ms
    price = max(intent.decision_ask, book.ask)
    if (
        not minimum <= lag <= maximum
        or not book.fresh(book.received_ms)
        or price > intent.limit
        or intent.quantity > book.ask_size * D("0.1")
        or intent.quantity * price > 11
    ):
        return None
    return price


def settlement_pnl(
    intent: TakerIntent,
    price: Decimal,
    yes_fraction: Decimal,
    *,
    stress: bool = False,
) -> Decimal:
    if yes_fraction not in (D(0), D(1)):
        raise ValueError("official binary resolution required")
    if not price.is_finite() or not D(0) < price < D(1):
        raise ValueError("valid execution price required")
    payout = yes_fraction if intent.side == "YES" else 1 - yes_fraction
    fee = D("0.002") if stress else D("0.0007")
    slippage = D("0.01") if stress else D(0)
    return intent.quantity * (payout * (1 - fee) - price - slippage)
