from decimal import Decimal as D

from hyperbot2.research.cross_venue import paired_return


def test_equal_quantities_cancel_common_price_move_and_capture_spread():
    common = paired_return(
        [D(100), D(110)],
        [D(100), D(110)],
        [D(0)] * 2,
        {},
        0,
        1,
        1,
        D(0),
        D(0),
        D(0),
        "zero",
    )
    assert common["net_bps"] == 0
    convergence = paired_return(
        [D(99), D(110)],
        [D(101), D(110)],
        [D(0)] * 2,
        {},
        0,
        1,
        1,
        D(0),
        D(0),
        D(0),
        "zero",
    )
    assert convergence["net_bps"] == D(100)


def test_each_venue_fee_and_funding_sign_and_boundary():
    result = paired_return(
        [D(100)] * 3,
        [D(100)] * 3,
        [D("0.1"), D("0.001"), D("0.002")],
        {0: (D("0.8"), D(100)), 7200000: (D("0.01"), D(101))},
        0,
        2,
        1,
        D("0.001"),
        D("0.002"),
        D(0),
        "signed",
    )
    assert result["fees_bps"] == D(30)
    assert result["funding_cost_bps"] == D("-35.5")
    assert result["net_bps"] == D("5.5")


def test_slippage_charges_four_executions():
    result = paired_return(
        [D(100)] * 2,
        [D(100)] * 2,
        [D(0)] * 2,
        {},
        0,
        1,
        1,
        D(0),
        D(0),
        D("0.0002"),
        "zero",
    )
    assert result["net_bps"] == D(-4)
