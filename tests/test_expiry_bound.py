from decimal import Decimal as D

import pytest

from hyperbot2.research.expiry_bound import WinningOffer, oracle_allocation, parse_offer


def test_shared_capital_is_not_repeated_for_each_contract() -> None:
    offers = (WinningOffer("a", D("0.5"), D(200)), WinningOffer("b", D("0.8"), D(2000)))
    result = oracle_allocation(
        offers, capital=D(1000), payout_fee=D(0), depth_fraction=D(1)
    )
    assert result["spent_usd"] == 1000
    assert result["oracle_gain_usd"] == 325  # $100 on a, $900 on b
    bound = oracle_allocation(
        offers, capital=D(1000), payout_fee=D(0), depth_fraction=None
    )
    assert bound["oracle_gain_usd"] == 1000


def test_payout_fee_and_depth_limit_do_not_create_profit() -> None:
    offers = (WinningOffer("a", D("0.9999"), D(1000)),)
    result = oracle_allocation(
        offers, capital=D(1000), payout_fee=D("0.0007"), depth_fraction=D("0.1")
    )
    assert result["spent_usd"] == 0 and result["oracle_gain_usd"] == 0
    with pytest.raises(ValueError):
        oracle_allocation(
            offers + offers, capital=D(1000), payout_fee=D(0), depth_fraction=None
        )


@pytest.mark.parametrize("ask", [None, "", "NaN", "Infinity"])
def test_legacy_empty_and_nonfinite_asks_are_not_offers(ask: object) -> None:
    assert parse_offer({"best_ask": ask, "ask_size": 100}, "market") is None
