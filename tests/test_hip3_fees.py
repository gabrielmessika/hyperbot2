from decimal import Decimal as D

import pytest

from hyperbot2.research.hip3_fees import reprice_fees, taker_fee
from hyperbot2.research.rotation import leg_return


def test_fee_scale_and_growth_exception() -> None:
    assert taker_fee(deployer_fee_scale=D(1), growth_mode="enabled") == D("0.00009")
    assert taker_fee(deployer_fee_scale=D(1), growth_mode=None) == D("0.0009")
    assert taker_fee(deployer_fee_scale=D("0.5"), growth_mode="enabled") == D(
        "0.0000675"
    )
    assert taker_fee(deployer_fee_scale=D(2), growth_mode="enabled") == D("0.00018")
    with pytest.raises(ValueError):
        taker_fee(deployer_fee_scale=D(1), growth_mode="pending")


@pytest.mark.parametrize("side", [-1, 1])
def test_fee_only_repricing_preserves_execution_and_funding(side: int) -> None:
    prices = [D(100), D(120), D(125)]
    rates = [D(0), D("0.0001"), D("-0.0002")]
    old = leg_return(prices, rates, 0, 2, side, D("0.0009"), D("0.0002"), "signed")
    exact = leg_return(prices, rates, 0, 2, side, D("0.00009"), D("0.0002"), "signed")
    adjusted = reprice_fees(old, D("0.1"))
    for key in exact:
        assert abs(adjusted[key] - exact[key]) < D("1e-20")
    assert adjusted["funding_cost_bps"] == old["funding_cost_bps"]
    assert adjusted["gross_bps"] == old["gross_bps"]
