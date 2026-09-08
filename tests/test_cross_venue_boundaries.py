from decimal import Decimal as D

from hyperbot2.research.cross_venue import paired_return


def test_native_milliseconds_determine_funding_membership():
    result = paired_return(
        [D(100)] * 3,
        [D(100)] * 3,
        [D(0)] * 3,
        {1: (D("0.001"), D(100)), 7200001: (D("0.8"), D(100))},
        0,
        2,
        1,
        D(0),
        D(0),
        D(0),
        "signed",
    )
    assert result["funding_cost_bps"] == D(-5)
    adverse = paired_return(
        [D(100)] * 3,
        [D(100)] * 3,
        [D(0)] * 3,
        {1: (D("0.001"), D(100))},
        0,
        2,
        1,
        D(0),
        D(0),
        D(0),
        "adverse",
    )
    assert adverse["funding_cost_bps"] == D(5)
