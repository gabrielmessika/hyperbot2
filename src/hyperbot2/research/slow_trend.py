"""Weekly time-series direction and inverse past daily volatility weights."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

D = Decimal


def slow_signal(closes: Sequence[Decimal], index: int) -> tuple[int, Decimal]:
    if index < 721 or index > len(closes):
        raise ValueError("thirty completed daily returns required")
    prices = [closes[index - 1 - 24 * j] for j in range(31)]
    if any(not p.is_finite() or p <= 0 for p in prices):
        raise ValueError("invalid historical prices")
    returns = [(prices[j] / prices[j + 1]).ln() for j in range(30)]
    mean = sum(returns, D(0)) / 30
    volatility = (sum(((r - mean) ** 2 for r in returns), D(0)) / 29).sqrt()
    direction = (prices[0] > prices[-1]) - (prices[0] < prices[-1])
    return direction, 1 / max(D("0.01"), volatility) if direction else D(0)


def slow_entries(
    closes: Mapping[str, Sequence[Decimal]], times: Sequence[int]
) -> tuple[
    dict[str, tuple[int, ...]], dict[str, tuple[Decimal, ...]], list[dict[str, Any]]
]:
    if not closes or any(len(rows) != len(times) for rows in closes.values()):
        raise ValueError("aligned historical closes required")
    entries = {c: [0] * len(times) for c in closes}
    weights = {c: [D(0)] * len(times) for c in closes}
    records = []
    for i, at in enumerate(times):
        dt = datetime.fromtimestamp(at / 1000, UTC)
        if i < 721 or i + 169 >= len(times) or dt.weekday() != 0 or dt.hour != 0:
            continue
        selected = {}
        for c, rows in closes.items():
            direction, weight = slow_signal(rows, i)
            entries[c][i], weights[c][i] = direction, weight
            selected[c] = {"side": direction, "raw_inverse_volatility": weight}
        records.append({"time_ms": at, "assets": selected})
    return (
        {c: tuple(v) for c, v in entries.items()},
        {c: tuple(v) for c, v in weights.items()},
        records,
    )
