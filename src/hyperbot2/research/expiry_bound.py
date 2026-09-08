"""Fractional perfect-foresight relaxation; never a tradable strategy result."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

D = Decimal


@dataclass(frozen=True, slots=True)
class WinningOffer:
    market: str
    ask: Decimal
    size: Decimal


def parse_offer(row: dict[str, Any], market: str) -> WinningOffer | None:
    """Legacy empty asks may be null, an empty string or a nonfinite number."""
    try:
        ask, size = D(str(row["best_ask"])), D(str(row["ask_size"]))
    except InvalidOperation:
        return None
    if not ask.is_finite() or not size.is_finite() or not 0 < ask < 1 or size <= 0:
        return None
    return WinningOffer(market, ask, size)


def oracle_allocation(
    offers: tuple[WinningOffer, ...],
    *,
    capital: Decimal,
    payout_fee: Decimal,
    depth_fraction: Decimal | None,
) -> dict[str, object]:
    if (
        not capital.is_finite()
        or capital <= 0
        or not payout_fee.is_finite()
        or not D(0) <= payout_fee < 1
        or (
            depth_fraction is not None
            and (not depth_fraction.is_finite() or not D(0) < depth_fraction <= 1)
        )
    ):
        raise ValueError("invalid bound assumptions")
    if len({o.market for o in offers}) != len(offers):
        raise ValueError("one winning offer per contract required")
    if any(
        not o.ask.is_finite()
        or not D(0) < o.ask < 1
        or not o.size.is_finite()
        or o.size <= 0
        for o in offers
    ):
        raise ValueError("invalid observed ask or size")
    remaining, profit = capital, D(0)
    allocations = []
    for offer in sorted(offers, key=lambda o: (o.ask, o.market)):
        unit_gain = 1 - payout_fee - offer.ask
        if unit_gain <= 0:
            continue
        capacity = (
            remaining
            if depth_fraction is None
            else offer.ask * offer.size * depth_fraction
        )
        spend = min(remaining, capacity)
        if spend <= 0:
            continue
        quantity = spend / offer.ask
        gain = quantity * unit_gain
        allocations.append(
            {
                "market": offer.market,
                "spend": spend,
                "quantity": quantity,
                "oracle_gain": gain,
            }
        )
        remaining -= spend
        profit += gain
    return {
        "oracle_gain_usd": profit,
        "spent_usd": capital - remaining,
        "allocations": allocations,
    }
