from decimal import Decimal as D

import pytest

from hyperbot2.research.rotation import HOUR
from hyperbot2.research.volatility_spread import (
    daily_volatility,
    volatility_baskets,
    volatility_selection,
)


def prices(amplitude: D, count: int = 1000) -> list[D]:
    return [(amplitude * ((i // 24) % 2)).exp() for i in range(count)]


def test_analytic_volatility_without_direction_or_floor() -> None:
    rows = prices(D("0.005"))
    assert rows[720] == rows[0]  # Zero 30-day direction still has volatility.
    expected = D("0.005") * (D(30) / 29).sqrt()
    assert abs(daily_volatility(rows, 721) - expected) < D("1e-25")
    assert daily_volatility([D(3)] * 721, 721) == 0
    assert daily_volatility(rows[:721] + [D("NaN")] * 279, 721) == daily_volatility(
        rows, 721
    )


def test_ranking_sides_and_tied_boundaries_abstain() -> None:
    rows = {str(i): prices(D(i) / 100) for i in range(1, 9)}
    sides, scores = volatility_selection(rows, 721)
    assert sides == {"1": 1, "2": 1, "3": 1, "6": -1, "7": -1, "8": -1}
    assert scores["1"] < scores["8"]
    rows["4"] = rows["3"]
    assert volatility_selection(rows, 721)[0] == {}
    assert volatility_selection({str(i): [D(1)] * 721 for i in range(6)}, 721)[0] == {}


def test_calendar_warmup_and_delayed_exit_coverage() -> None:
    times = [1735689600000 + i * HOUR for i in range(1000)]
    rows = {str(i): prices(D(i) / 100) for i in range(1, 9)}
    records = volatility_baskets(rows, times)
    assert len(records) == 1
    assert records[0].time_ms == 1738540800000  # 2025-02-03 00 UTC.
    assert records[0].index == 792
    truncated = {c: v[:961] for c, v in rows.items()}
    assert volatility_baskets(truncated, times[:961]) == []


def test_invalid_history_fails_closed() -> None:
    with pytest.raises(ValueError):
        daily_volatility([D(1)] * 721, 720)
    with pytest.raises(ValueError):
        daily_volatility([D(0)] * 721, 721)
    with pytest.raises(ValueError):
        volatility_baskets({"A": [D(1), D(1)]}, [0, 2 * HOUR])
    with pytest.raises(ValueError):
        volatility_selection({"A": [D(1)] * 721}, 721)
