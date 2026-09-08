from decimal import Decimal as D

from hyperbot2.research.microstructure import MicroQuote, micro_signal, taker_return


def test_flow_rules_require_opposite_book_confirmation() -> None:
    kwargs = dict(
        coin="BTC",
        valid=True,
        flow=D("0.8"),
        notional=D(200_000),
        count=40,
        imbalance=D("0.6"),
        return_bps=D(6),
        spread_bps=D(1),
    )
    assert micro_signal(rule="continuation", **kwargs) == 1
    assert micro_signal(rule="absorption", **kwargs) == 0
    assert (
        micro_signal(
            rule="absorption",
            **(kwargs | {"imbalance": D("-0.6"), "return_bps": D(-1)}),
        )
        == -1
    )
    assert micro_signal(rule="continuation", **(kwargs | {"valid": False})) == 0
    assert micro_signal(rule="continuation", **(kwargs | {"count": 29})) == 0


def test_taker_costs_and_funding_boundary() -> None:
    a = MicroQuote(1000, D(100), D("100.01"), D(100), D(100))
    b = MicroQuote(301_000, D(100), D("100.01"), D(100), D(100))
    base = taker_return("ETH", 1, a, b, ())
    stress = taker_return("ETH", 1, a, b, (), stress=True)
    assert base is not None and stress is not None
    assert stress["net_bps"] < base["net_bps"] < -10
    assert base["mid_markout_bps"] == 0
    funded = taker_return(
        "ETH", 1, a, b, ((1000, D(1), D(100)), (301_000, D("0.001"), D(100)))
    )
    assert funded is not None
    assert funded["funding_cost_usd"] == funded["quantity"] * D("0.1")
    short = taker_return("ETH", -1, a, b, ((301_000, D("0.001"), D(100)),))
    assert short is not None and short["funding_cost_usd"] < 0


def test_insufficient_depth_is_not_a_fill() -> None:
    a = MicroQuote(1000, D(100), D("100.01"), D("0.1"), D("0.1"))
    b = MicroQuote(301_000, D(100), D("100.01"), D(100), D(100))
    assert taker_return("ETH", 1, a, b, ()) is None
