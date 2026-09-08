from decimal import Decimal as D

from hyperbot2.research.return_hedge import fit_return_hedge, hedged_return


def test_return_hedge_recovers_beta_without_using_current_return() -> None:
    xs = [D(x) / 100 for x in (-2, -1, 0, 1, 2)]
    noise = [D(x) / 1000 for x in (1, -2, 2, -2, 1)]
    ys = [D("0.003") + 2 * x + e for x, e in zip(xs, noise, strict=True)]
    model = fit_return_hedge(ys, xs)
    assert model is not None
    assert abs(model.beta - 2) < D("1e-20")
    assert abs(model.alpha - D("0.003")) < D("1e-20")
    assert model.score(D("0.003") + 3 * model.sigma, D(0)) == 3
    assert fit_return_hedge([D(1)] * 5, xs) is None


def test_two_legs_share_total_notional_and_funding_signs() -> None:
    result = hedged_return(
        [D(100), D(120)],
        [D(100), D(110)],
        [D(0), D("0.001")],
        [D(0), D("0.001")],
        index=0,
        horizon=1,
        side=1,
        beta=D(2),
        asset_fee=D(0),
        hedge_fee=D(0),
        asset_slip=D(0),
        hedge_slip=D(0),
        funding_mode="signed",
    )
    assert result["asset_weight"] + result["hedge_weight"] == 1
    assert abs(result["basket"]["gross_bps"]) < D("1e-20")
    # Long pays 12 bps on its weight; short receives 11 bps on twice the weight.
    assert abs(result["basket"]["net_bps"] - D(10) / 3) < D("1e-20")
