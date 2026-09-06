"""Cash, FIFO lots and conservative reservations for a single YES representation."""

from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal

from hyperbot2.models import QuoteIntent, Side
from hyperbot2.outcomes.contracts import (
    ONE,
    ZERO,
    Operation,
    OutcomeBook,
    OutcomeDefinition,
)
from hyperbot2.risk.supervisor import OutcomeExposure, PortfolioState


@dataclass(frozen=True, slots=True)
class Lot:
    entry_id: str
    market: int
    opened_ms: int
    quantity: Decimal
    unit_cost: Decimal


@dataclass(frozen=True, slots=True)
class Reservation:
    intent: QuoteIntent
    outcome_id: int
    remaining: Decimal


@dataclass(frozen=True, slots=True)
class Cycle:
    entry_id: str
    outcome_id: int
    opened_ms: int
    closed_ms: int
    entry_notional: Decimal
    pnl: Decimal
    terminal: bool


class OutcomeLedger:
    """No borrowing, naked sales, split/merge or automatic leverage."""

    def __init__(self, equity: Decimal = Decimal("1000")) -> None:
        if not equity.is_finite() or equity <= 0:
            raise ValueError("invalid initial equity")
        self.initial = equity
        self.cash = equity
        self.fees_paid = ZERO
        self.realized = ZERO
        self.lots: list[Lot] = []
        self.reservations: dict[str, Reservation] = {}
        self.cycles: list[Cycle] = []
        self._fill_ids: set[str] = set()
        self.peak = equity
        self.daily_start = equity
        self.day: int | None = None

    def quantity(self, outcome_id: int) -> Decimal:
        return sum(
            (lot.quantity for lot in self.lots if lot.market == outcome_id), ZERO
        )

    def available_quantity(self, outcome_id: int) -> Decimal:
        reserved = sum(
            (
                r.remaining
                for r in self.reservations.values()
                if r.outcome_id == outcome_id and r.intent.side is Side.SELL
            ),
            ZERO,
        )
        return self.quantity(outcome_id) - reserved

    @property
    def available_cash(self) -> Decimal:
        return self.cash - sum(
            (
                r.remaining * r.intent.price
                for r in self.reservations.values()
                if r.intent.side is Side.BUY
            ),
            ZERO,
        )

    def reserve(self, intent: QuoteIntent, definition: OutcomeDefinition) -> None:
        if intent.intent_id in self.reservations:
            raise ValueError("duplicate reservation")
        if intent.market != definition.market:
            raise ValueError("reservation market mismatch")
        if intent.side is Side.BUY and intent.price * intent.size > self.available_cash:
            raise ValueError("insufficient available cash")
        if intent.side is Side.SELL and intent.size > self.available_quantity(
            definition.outcome_id
        ):
            raise ValueError("naked or already reserved sale")
        self.reservations[intent.intent_id] = Reservation(
            intent, definition.outcome_id, intent.size
        )

    def release(self, intent_id: str) -> None:
        self.reservations.pop(intent_id, None)

    def fill(
        self,
        *,
        fill_id: str,
        intent_id: str,
        quantity: Decimal,
        price: Decimal,
        now_ms: int,
        definition: OutcomeDefinition,
        operation: Operation | None = None,
    ) -> bool:
        if fill_id in self._fill_ids:
            return False
        r = self.reservations[intent_id]
        if definition.outcome_id != r.outcome_id or definition.fees is None:
            raise ValueError("fill definition/fees mismatch")
        if not definition.fees.observed_ms <= now_ms < definition.fees.valid_until_ms:
            raise ValueError("fees unavailable at fill")
        if not quantity.is_finite() or not 0 < quantity <= r.remaining:
            raise ValueError("fill exceeds reservation")
        if not price.is_finite() or not 0 < price < 1:
            raise ValueError("invalid fill price")
        if r.intent.side is Side.BUY and price > r.intent.price:
            raise ValueError("buy exceeds limit")
        if r.intent.side is Side.SELL and price < r.intent.price:
            raise ValueError("sale below limit")
        if operation is None:
            operation = (
                Operation.OPEN if r.intent.side is Side.BUY else Operation.MAKER_CLOSE
            )
        if r.intent.side is Side.BUY and operation is not Operation.OPEN:
            raise ValueError("invalid opening operation")
        if r.intent.side is Side.SELL and operation not in (
            Operation.MAKER_CLOSE,
            Operation.TAKER_CLOSE,
        ):
            raise ValueError("invalid closing operation")
        fee = definition.fees.cost(operation, quantity, price)
        if r.intent.side is Side.BUY:
            if quantity * price + fee > self.cash:
                raise ValueError("insufficient cash at fill")
            self.cash -= quantity * price + fee
            self.lots.append(
                Lot(intent_id, r.outcome_id, now_ms, quantity, price + fee / quantity)
            )
        else:
            self._close(r.outcome_id, quantity, price, fee, now_ms, terminal=False)
        self.fees_paid += fee
        self._fill_ids.add(fill_id)
        remaining = r.remaining - quantity
        if remaining:
            self.reservations[intent_id] = replace(r, remaining=remaining)
        else:
            self.release(intent_id)
        return True

    def _close(
        self,
        outcome_id: int,
        quantity: Decimal,
        price: Decimal,
        fee: Decimal,
        now_ms: int,
        *,
        terminal: bool,
    ) -> None:
        if quantity > self.quantity(outcome_id):
            raise ValueError("closing more than inventory")
        remaining = quantity
        lots: list[Lot] = []
        for lot in self.lots:
            if lot.market != outcome_id or not remaining:
                lots.append(lot)
                continue
            amount = min(remaining, lot.quantity)
            entry = amount * lot.unit_cost
            pnl = amount * price - fee * amount / quantity - entry
            self.realized += pnl
            self.cycles.append(
                Cycle(
                    lot.entry_id,
                    outcome_id,
                    lot.opened_ms,
                    now_ms,
                    entry,
                    pnl,
                    terminal,
                )
            )
            remaining -= amount
            if amount < lot.quantity:
                lots.append(replace(lot, quantity=lot.quantity - amount))
        self.lots = lots
        self.cash += quantity * price - fee

    def terminal_close(
        self,
        definition: OutcomeDefinition,
        *,
        now_ms: int,
        payout: Decimal = ZERO,
        settlement: bool = False,
    ) -> None:
        if not payout.is_finite() or not 0 <= payout <= 1:
            raise ValueError("invalid payout")
        if settlement and now_ms < definition.expiry_ms:
            raise ValueError("settlement before expiry")
        if definition.fees is None:
            raise ValueError("unknown terminal fees")
        if any(
            r.outcome_id == definition.outcome_id for r in self.reservations.values()
        ):
            raise ValueError("terminal close requires resolved orders")
        quantity = self.quantity(definition.outcome_id)
        if not quantity:
            return
        operation = Operation.SETTLE if settlement else Operation.TAKER_CLOSE
        fee = definition.fees.cost(operation, quantity, payout)
        self._close(definition.outcome_id, quantity, payout, fee, now_ms, terminal=True)
        self.fees_paid += fee

    def portfolio(
        self,
        now_ms: int,
        definitions: dict[int, OutcomeDefinition],
        books: dict[int, OutcomeBook],
        *,
        healthy: bool = True,
    ) -> PortfolioState:
        exposures: list[OutcomeExposure] = []
        liquidation = self.cash
        markets = {lot.market for lot in self.lots} | {
            r.outcome_id for r in self.reservations.values()
        }
        for market in sorted(markets):
            d = definitions[market]
            quantity = self.quantity(market)
            cost = sum(
                (
                    lot.quantity * lot.unit_cost
                    for lot in self.lots
                    if lot.market == market
                ),
                ZERO,
            )
            worst_fee = quantity * (d.fees.settlement_rate if d.fees else ONE)
            yes, no, gross = quantity - cost - worst_fee, -cost, cost
            for r in self.reservations.values():
                if r.outcome_id != market:
                    continue
                if r.intent.side is Side.BUY:
                    # Pending buys cannot offset a sell that might fill alone.
                    no -= r.remaining * r.intent.price
                    gross += r.remaining * r.intent.price
                else:
                    fee = (
                        d.fees.cost(Operation.MAKER_CLOSE, r.remaining, r.intent.price)
                        if d.fees
                        else r.remaining
                    )
                    yes -= r.remaining * (ONE - r.intent.price) + fee
                    no -= fee
            exposures.append(OutcomeExposure(d.market, "crypto", yes, no, gross))
            b = books.get(market)
            if (
                b is not None
                and d.fees is not None
                and b.received_ms <= now_ms
                and 0 <= now_ms - b.exchange_ms <= 500
            ):
                # Only visible liquidation depth counts; unknown residual is worth zero.
                left = quantity
                for level in b.bids:
                    amount = min(left, level.size)
                    liquidation += amount * level.price - d.fees.cost(
                        Operation.TAKER_CLOSE, amount, level.price
                    )
                    left -= amount
                    if not left:
                        break
        day = now_ms // 86_400_000
        if self.day is None:
            self.day = day
        elif self.day != day:
            self.day, self.daily_start = day, liquidation
        self.peak = max(self.peak, liquidation)
        positions = tuple(
            (str(m), self.quantity(m)) for m in sorted(markets) if self.quantity(m)
        )
        return PortfolioState(
            now_ms,
            max(liquidation, Decimal("0.000001")),
            self.peak,
            liquidation - self.daily_start,
            ZERO,
            healthy,
            0,
            True,
            positions,
            positions,
            tuple(exposures),
            (),
        )
