"""Completed daily downside breadth and nonoverlapping basket events."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal

from hyperbot2.research.rotation import HOUR

D = Decimal


@dataclass(frozen=True, slots=True)
class ShockObservation:
    index: int
    time_ms: int
    past_returns: tuple[tuple[str, Decimal], ...]
    declining_assets: int
    shock: bool
    eligible: bool


def downside_breadth(
    closes: Mapping[str, Sequence[Decimal]], index: int
) -> tuple[dict[str, Decimal], int]:
    if len(closes) != 11 or index < 25 or any(index > len(v) for v in closes.values()):
        raise ValueError("eleven assets and 25 completed hourly closes required")
    returns = {}
    for coin, rows in closes.items():
        before, latest = rows[index - 25], rows[index - 1]
        if any(not v.is_finite() or v <= 0 for v in (before, latest)):
            raise ValueError("finite positive past closes required")
        returns[coin] = latest / before - 1
    return returns, sum(r <= D("-0.05") for r in returns.values())


def shock_observations(
    closes: Mapping[str, Sequence[Decimal]], times: Sequence[int]
) -> list[ShockObservation]:
    if (
        not times
        or len(closes) != 11
        or any(len(v) != len(times) for v in closes.values())
    ):
        raise ValueError("aligned nonempty eleven-asset panel required")
    if any(t % HOUR for t in times) or any(
        b - a != HOUR for a, b in zip(times, times[1:], strict=False)
    ):
        raise ValueError("regular hourly UTC panel required")
    records = []
    next_allowed = 25
    for i in range(25, len(times) - 25):
        returns, count = downside_breadth(closes, i)
        shock = count >= 8
        eligible = shock and i >= next_allowed
        if eligible:
            next_allowed = i + 26
        records.append(
            ShockObservation(
                i,
                times[i],
                tuple(sorted(returns.items())),
                count,
                shock,
                eligible,
            )
        )
    return records
