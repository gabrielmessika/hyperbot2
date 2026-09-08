"""Causal rotation signals and fixed-notional basket research accounting."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal

D = Decimal
HOUR = 3_600_000
COINS = ("BTC", "ETH", "SOL", "HYPE")


def signals(
    closes: Mapping[str, Sequence[Decimal]],
    opens: Mapping[str, Sequence[Decimal]],
    rates: Mapping[str, Sequence[Decimal]],
    index: int,
    strategy: str,
) -> tuple[dict[str, int], dict[str, Decimal]]:
    if index < 720:
        raise ValueError("30 completed days required")
    if strategy == "momentum7d":
        scores = {c: closes[c][index - 25] / closes[c][index - 193] - 1 for c in COINS}
    elif strategy == "carry_relative":
        scores = {c: sum(rates[c][index - 24 : index], D(0)) / 24 for c in COINS}
    elif strategy == "trend30d":
        scores = {c: closes[c][index - 1] / opens[c][index - 720] - 1 for c in COINS}
        return {c: 1 if v > 0 else -1 for c, v in scores.items() if v}, scores
    else:
        raise ValueError("unregistered strategy")
    if len(set(scores.values())) == 1:
        return {}, scores
    lowest = min(COINS, key=lambda c: (scores[c], c))
    highest = min(COINS, key=lambda c: (-scores[c], c))
    sides = {highest: 1, lowest: -1}
    if strategy == "carry_relative":
        sides = {c: -s for c, s in sides.items()}
    return sides, scores


def leg_return(
    opens: Sequence[Decimal],
    rates: Sequence[Decimal],
    index: int,
    horizon: int,
    side: int,
    fee: Decimal,
    slip: Decimal,
    funding_mode: str,
) -> dict[str, Decimal]:
    """PnL per executed entry notional; no predicted funding enters the signal."""
    if side not in (-1, 1) or funding_mode not in ("signed", "adverse", "zero"):
        raise ValueError("invalid side/funding mode")
    if horizon <= 0 or not 0 <= fee < 1 or not 0 <= slip < 1:
        raise ValueError("invalid horizon/costs")
    entry = opens[index] * (1 + side * slip)
    exit_price = opens[index + horizon] * (1 - side * slip)
    quantity = 1 / entry
    gross = side * (opens[index + horizon] / opens[index] - 1)
    after_slip = side * quantity * (exit_price - entry)
    fees = fee * (1 + quantity * exit_price)
    funding = (
        sum(
            (
                quantity
                * opens[t]
                * (side * rates[t] if funding_mode == "signed" else abs(rates[t]))
                for t in range(index + 1, index + horizon + 1)
            ),
            D(0),
        )
        if funding_mode != "zero"
        else D(0)
    )
    return {
        "gross_bps": gross * 10000,
        "slippage_bps": (gross - after_slip) * 10000,
        "fees_bps": fees * 10000,
        "funding_cost_bps": funding * 10000,
        "net_bps": (after_slip - fees - funding) * 10000,
    }
