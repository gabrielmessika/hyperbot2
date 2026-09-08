from decimal import Decimal as D

import pytest

from hyperbot2.research.rotation import COINS, leg_return, signals


def test_funding_rank_is_causal_and_positive_funding_is_sold() -> None:
    prices = {c: [D(100)] * 800 for c in COINS}
    rates = {c: [D(0)] * 800 for c in COINS}
    rates["BTC"][719] = D("0.001")
    rates["ETH"][719] = D("-0.001")
    result = signals(prices, prices, rates, 720, "carry_relative")
    assert result[0] == {"BTC": -1, "ETH": 1}
    for c in COINS:
        rates[c][720:] = [D(999)] * 80
        prices[c][720:] = [D(999)] * 80
    assert signals(prices, prices, rates, 720, "carry_relative") == result
    with pytest.raises(ValueError, match="completed"):
        signals(prices, prices, rates, 719, "carry_relative")


def test_momentum_skips_last_day_and_ties_do_not_invent_a_pair() -> None:
    closes = {c: [D(100)] * 800 for c in COINS}
    rates = {c: [D(0)] * 800 for c in COINS}
    assert signals(closes, closes, rates, 720, "momentum7d")[0] == {}
    closes["SOL"][695] = D(120)
    closes["ETH"][695] = D(90)
    result = signals(closes, closes, rates, 720, "momentum7d")
    assert result[0] == {"SOL": 1, "ETH": -1}
    closes["BTC"][696:] = [D(999)] * 104
    assert signals(closes, closes, rates, 720, "momentum7d") == result


def test_signed_funding_and_both_sides_of_fees_reconcile() -> None:
    opens = [D(100), D(110), D(120)]
    rates = [D("0.9"), D("0.001"), D("0.002")]
    long = leg_return(opens, rates, 0, 2, 1, D("0.01"), D(0), "signed")
    short = leg_return(opens, rates, 0, 2, -1, D("0.01"), D(0), "signed")
    assert long["funding_cost_bps"] == D(35)
    assert short["funding_cost_bps"] == D(-35)
    assert long["fees_bps"] == short["fees_bps"] == D(220)
    assert long["net_bps"] == D(1745)
    assert short["net_bps"] == D(-2185)
    adverse = leg_return(opens, rates, 0, 2, -1, D("0.01"), D(0), "adverse")
    assert adverse["net_bps"] == D(-2255)


def test_short_slippage_is_adverse_and_missing_exit_fails() -> None:
    opens = [D(100), D(100)]
    result = leg_return(opens, [D(0), D(0)], 0, 1, -1, D(0), D("0.01"), "zero")
    assert result["net_bps"] < -200
    assert result["gross_bps"] == 0
    with pytest.raises(IndexError):
        leg_return(opens, [D(0)] * 2, 0, 2, 1, D(0), D(0), "zero")
