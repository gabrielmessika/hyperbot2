"""Fixed weekly low-minus-high past volatility baskets."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from hyperbot2.research.rotation import HOUR

D = Decimal


def daily_volatility(closes: Sequence[Decimal], index: int) -> Decimal:
    if index < 721 or index > len(closes):
        raise ValueError("thirty completed daily returns required")
    prices = [closes[index - 1 - 24 * j] for j in range(31)]
    if any(not p.is_finite() or p <= 0 for p in prices):
        raise ValueError("finite positive historical prices required")
    returns = [(prices[j] / prices[j + 1]).ln() for j in range(30)]
    mean = sum(returns, D(0)) / 30
    return (sum(((r - mean) ** 2 for r in returns), D(0)) / 29).sqrt()


def volatility_selection(
    closes: Mapping[str, Sequence[Decimal]], index: int
) -> tuple[dict[str, int], dict[str, Decimal]]:
    if len(closes) < 6:
        raise ValueError("six assets required")
    scores = {c: daily_volatility(rows, index) for c, rows in closes.items()}
    ordered = sorted(scores, key=lambda c: (scores[c], c))
    if (
        scores[ordered[2]] == scores[ordered[3]]
        or scores[ordered[-4]] == scores[ordered[-3]]
    ):
        return {}, scores
    return {**dict.fromkeys(ordered[:3], 1), **dict.fromkeys(ordered[-3:], -1)}, scores


@dataclass(frozen=True, slots=True)
class VolatilityBasket:
    index: int
    time_ms: int
    sides: tuple[tuple[str, int], ...]
    scores: tuple[tuple[str, Decimal], ...]


def volatility_baskets(
    closes: Mapping[str, Sequence[Decimal]], times: Sequence[int]
) -> list[VolatilityBasket]:
    if not times or any(len(rows) != len(times) for rows in closes.values()):
        raise ValueError("aligned historical prices required")
    if any(t % HOUR for t in times) or any(
        b - a != HOUR for a, b in zip(times, times[1:], strict=False)
    ):
        raise ValueError("regular UTC hourly times required")
    records = []
    for i, at in enumerate(times):
        date = datetime.fromtimestamp(at / 1000, UTC)
        if i < 721 or i + 169 >= len(times) or date.weekday() != 0 or date.hour:
            continue
        sides, scores = volatility_selection(closes, i)
        records.append(
            VolatilityBasket(
                i, at, tuple(sorted(sides.items())), tuple(sorted(scores.items()))
            )
        )
    return records
