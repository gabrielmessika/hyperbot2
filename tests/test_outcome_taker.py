from decimal import Decimal as D

import pytest

from hyperbot2.research.outcome_taker import (
    TakerBook,
    execution_price,
    select_intent,
    settlement_pnl,
)


def test_causal_book_depth_and_probability_uncertainty() -> None:
    now = 100_000
    probabilities = (D("0.7"), D("0.65"), D("0.75"))
    book = TakerBook(now - 200, now - 100, D("0.5"), D(1000))
    intent = select_intent(now, probabilities, {"YES": book})
    assert intent is not None and intent.quantity == 20
    assert intent.conservative_probability == D("0.62")
    assert (
        select_intent(now, probabilities, {"YES": TakerBook(1, 2, D("0.5"), D(1000))})
        is None
    )
    assert (
        select_intent(
            now, probabilities, {"YES": TakerBook(now, now + 1, D("0.5"), D(1000))}
        )
        is None
    )
    assert (
        select_intent(
            now, probabilities, {"YES": TakerBook(now, now, D("0.5"), D(199))}
        )
        is None
    )
    assert select_intent(now, (D("0.6"), D("0.55")), {"YES": book}) is None


def test_frozen_intent_does_not_improve_fill_with_future_ask() -> None:
    intent = select_intent(
        100_000, (D("0.7"),), {"YES": TakerBook(99_999, 100_000, D("0.5"), D(1000))}
    )
    assert intent is not None
    assert execution_price(
        intent, TakerBook(101_000, 101_001, D("0.49"), D(1000))
    ) == D("0.5")
    assert (
        execution_price(intent, TakerBook(101_000, 101_001, D("0.56"), D(1000))) is None
    )  # spend > $11
    assert (
        execution_price(intent, TakerBook(100_000, 100_500, D("0.5"), D(1000))) is None
    )
    assert execution_price(
        intent, TakerBook(161_000, 161_001, D("0.5"), D(1000)), delay=True
    ) == D("0.5")
    assert (
        execution_price(intent, TakerBook(161_000, 161_001, D("0.5"), D(1000))) is None
    )


def test_settlement_no_open_fee_and_no_loser_settlement_fee() -> None:
    intent = select_intent(
        100_000, (D("0.3"),), {"NO": TakerBook(99_999, 100_000, D("0.5"), D(1000))}
    )
    assert intent is not None and intent.side == "NO"
    assert settlement_pnl(intent, D("0.5"), D(0)) == D("9.986")
    assert settlement_pnl(intent, D("0.5"), D(1)) == D(-10)
    assert settlement_pnl(intent, D("0.5"), D(0), stress=True) == D("9.76")
    with pytest.raises(ValueError):
        settlement_pnl(intent, D("0.5"), D("0.5"))
