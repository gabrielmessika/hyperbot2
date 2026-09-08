from decimal import Decimal as D

import pytest

from hyperbot2.research.cash_carry import HOUR, carry_period
from hyperbot2.research.volume import VolumeBar


def series(prices):
    return {
        i * HOUR: VolumeBar(i * HOUR, *(D(p) for _ in range(4)), D(1))
        for i, p in enumerate(prices)
    }


ZERO = {
    "fee_hl": D(0),
    "fee_spot": D(0),
    "slip_hl": D(0),
    "slip_spot": D(0),
    "fx_cost": D(0),
}


def test_fixed_quantity_cancels_market_move_and_earns_signed_funding():
    prices = series([100, 110])
    result = carry_period(
        prices, prices, series([1, 1]), {HOUR: D("0.001")}, 0, HOUR, **ZERO
    )
    assert result["quantity"] == 5
    assert result["planned_exit_net_usdc"] == D("0.55")


def test_spot_profit_cannot_rescue_perpetual_margin():
    prices = series([100, 300, 100])
    result = carry_period(
        prices,
        prices,
        series([1, 1, 1]),
        {HOUR: D(0), 2 * HOUR: D(0)},
        0,
        2 * HOUR,
        **ZERO,
    )
    assert result["status"] == "MARGIN_STRESS_BREACH"
    assert result["first_breach_ms"] == HOUR
    assert result["planned_exit_net_usdc"] is None


def test_fx_translation_and_missing_payment():
    result = carry_period(
        series([100, 100]),
        series([100, 101]),
        series([1, "1.01"]),
        {HOUR: D(0)},
        0,
        HOUR,
        **ZERO,
    )
    assert result["planned_exit_net_usdc"] == 0
    with pytest.raises(ValueError, match="funding coverage"):
        carry_period(
            series([100, 100]), series([100, 100]), series([1, 1]), {}, 0, HOUR, **ZERO
        )
