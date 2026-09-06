"""Immutable, causal contracts for the qualified recurring outcome universe."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Any

from hyperbot2.models import BookLevel, DatasetTier, Side

ZERO = Decimal(0)
ONE = Decimal(1)
UNIVERSE = ("BTC", "ETH", "SOL", "HYPE")


def positive(value: Decimal, name: str, *, zero: bool = False) -> None:
    if not value.is_finite() or value < 0 or (not zero and value == 0):
        raise ValueError(f"invalid {name}")


def digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode()
    ).hexdigest()


class Operation(StrEnum):
    OPEN = "open"
    MAKER_CLOSE = "maker_close"
    TAKER_CLOSE = "taker_close"
    SETTLE = "settle"


@dataclass(frozen=True, slots=True)
class FeeSchedule:
    """Final effective rates, attested externally; no account tier inference."""

    maker_close_rate: Decimal
    taker_close_rate: Decimal
    settlement_rate: Decimal
    observed_ms: int
    valid_until_ms: int
    source_sha256: str

    def __post_init__(self) -> None:
        for rate in (
            self.maker_close_rate,
            self.taker_close_rate,
            self.settlement_rate,
        ):
            positive(rate, "fee rate", zero=True)
            if rate >= 1:
                raise ValueError("fee rate must be less than one")
        if not 0 <= self.observed_ms < self.valid_until_ms:
            raise ValueError("fee validity is invalid")
        if len(self.source_sha256) != 64 or any(
            c not in "0123456789abcdef" for c in self.source_sha256
        ):
            raise ValueError("fee source SHA-256 is required")

    def cost(self, operation: Operation, quantity: Decimal, price: Decimal) -> Decimal:
        positive(quantity, "quantity", zero=True)
        positive(price, "price", zero=True)
        if price > 1:
            raise ValueError("outcome price exceeds one")
        rate = {
            Operation.OPEN: ZERO,
            Operation.MAKER_CLOSE: self.maker_close_rate,
            Operation.TAKER_CLOSE: self.taker_close_rate,
            Operation.SETTLE: self.settlement_rate,
        }[operation]
        return quantity * price * rate


@dataclass(frozen=True, slots=True)
class OutcomeDefinition:
    outcome_id: int
    underlying: str
    strike: Decimal
    expiry_ms: int
    observed_ms: int
    tick: Decimal | None = None
    size_increment: Decimal | None = None
    fees: FeeSchedule | None = None
    settlement_rule: str | None = None
    specification_sha256: str | None = None
    active: bool = False
    fee_scale: str | None = None
    deployer_fee_scale: str | None = None

    def __post_init__(self) -> None:
        if (
            type(self.outcome_id) is not int
            or self.outcome_id < 0
            or self.underlying not in UNIVERSE
        ):
            raise ValueError("invalid outcome identity")
        positive(self.strike, "strike")
        if not 0 <= self.observed_ms < self.expiry_ms:
            raise ValueError("outcome must be observed before expiry")
        for value in (self.tick, self.size_increment):
            if value is not None:
                positive(value, "tick/lot")
        if self.tick is not None and self.tick >= 1:
            raise ValueError("tick must be smaller than one")
        if type(self.active) is not bool:
            raise ValueError("active must be a boolean")

    @property
    def market(self) -> str:
        return f"outcome:{self.outcome_id}"

    @property
    def coin(self) -> str:
        return f"#{10 * self.outcome_id}"

    @property
    def sha256(self) -> str:
        return digest(asdict(self))

    def reasons(self, now_ms: int) -> tuple[str, ...]:
        reasons: list[str] = []
        if not self.active:
            reasons.append("market_status_unqualified")
        if self.tick is None or self.size_increment is None:
            reasons.append("tick_or_lot_unknown")
        if self.settlement_rule != "mark_gt_strike":
            reasons.append("settlement_rule_unqualified")
        if (
            self.specification_sha256 is None
            or len(self.specification_sha256) != 64
            or any(c not in "0123456789abcdef" for c in self.specification_sha256)
        ):
            reasons.append("specification_provenance_missing")
        if (
            self.fees is None
            or not self.fees.observed_ms <= now_ms < self.fees.valid_until_ms
        ):
            reasons.append("fees_unknown_or_expired")
        if now_ms < self.observed_ms:
            reasons.append("future_definition")
        if now_ms >= self.expiry_ms:
            reasons.append("market_expired")
        return tuple(reasons)


@dataclass(frozen=True, slots=True)
class OutcomeBook:
    """One canonical YES book, never a sum of the YES and NO representations."""

    outcome_id: int
    exchange_ms: int
    received_ms: int
    sequence: int
    bids: tuple[BookLevel, ...]
    asks: tuple[BookLevel, ...]
    tier: DatasetTier
    full_depth: bool = False
    queue_qualified: bool = False
    dual_priority_qualified: bool = False

    def __post_init__(self) -> None:
        if min(self.outcome_id, self.exchange_ms, self.received_ms, self.sequence) < 0:
            raise ValueError("invalid book identity or timestamp")
        if not self.bids or not self.asks:
            raise ValueError("two-sided book required")
        if any(not 0 < x.price < 1 for x in (*self.bids, *self.asks)):
            raise ValueError("outcome prices must be inside (0, 1)")
        if any(
            a.price <= b.price for a, b in zip(self.bids, self.bids[1:], strict=False)
        ):
            raise ValueError("bids must be strictly descending")
        if any(
            a.price >= b.price for a, b in zip(self.asks, self.asks[1:], strict=False)
        ):
            raise ValueError("asks must be strictly ascending")
        if self.bids[0].price >= self.asks[0].price:
            raise ValueError("locked/crossed outcome book")

    def age(self, now_ms: int) -> int:
        if now_ms < self.received_ms or self.exchange_ms > now_ms:
            raise ValueError("future book or clock ambiguity")
        return max(now_ms - self.exchange_ms, now_ms - self.received_ms)

    def covers(self, side: Side, price: Decimal) -> bool:
        levels = self.bids if side is Side.BUY else self.asks
        if side is Side.BUY:
            return price >= levels[-1].price
        return price <= levels[-1].price


@dataclass(frozen=True, slots=True)
class FairValue:
    probability: Decimal
    available_ms: int
    reference_ms: int
    calibration_end_ms: int
    uncertainty: Decimal
    adverse_selection: Decimal
    source_sha256: str

    def __post_init__(self) -> None:
        if not self.probability.is_finite() or not 0 < self.probability < 1:
            raise ValueError("fair probability must be in (0, 1)")
        if not 0 <= self.reference_ms <= self.available_ms:
            raise ValueError("reference causality invalid")
        if not 0 <= self.calibration_end_ms <= self.available_ms:
            raise ValueError("calibration uses future labels")
        positive(self.uncertainty, "uncertainty", zero=True)
        positive(self.adverse_selection, "adverse selection", zero=True)
        if len(self.source_sha256) != 64 or any(
            c not in "0123456789abcdef" for c in self.source_sha256
        ):
            raise ValueError("fair-value provenance missing")


def book_from_public(
    payload: dict[str, Any],
    *,
    received_ms: int,
    sequence: int,
    tier: DatasetTier = DatasetTier.A,
) -> OutcomeBook:
    coin = str(payload["coin"])
    if not coin.startswith("#") or not coin[1:].isdigit():
        raise ValueError("outcome coin required")
    encoded = int(coin[1:])
    if encoded % 10 not in (0, 1):
        raise ValueError("invalid outcome side")
    levels = payload["levels"]
    bids = tuple(BookLevel(Decimal(x["px"]), Decimal(x["sz"])) for x in levels[0])
    asks = tuple(BookLevel(Decimal(x["px"]), Decimal(x["sz"])) for x in levels[1])
    if encoded % 10 == 1:
        bids, asks = (
            tuple(BookLevel(ONE - x.price, x.size) for x in asks),
            tuple(BookLevel(ONE - x.price, x.size) for x in bids),
        )
    return OutcomeBook(
        encoded // 10, int(payload["time"]), received_ms, sequence, bids, asks, tier
    )
