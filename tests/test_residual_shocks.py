import random
from decimal import Decimal as D

import pytest

from hyperbot2.research.residual_shocks import residual_shock


def paths() -> tuple[list[D], list[D]]:
    rng = random.Random(7)
    asset, hedge = [D(0)], [D(0)]
    for _ in range(219):
        x, e = D(str(rng.gauss(0, 0.004))), D(str(rng.gauss(0, 0.003)))
        hedge.append(hedge[-1] + x)
        asset.append(asset[-1] + 2 * x + e)
    return asset, hedge


def test_signal_block_is_excluded_from_fitted_model() -> None:
    asset, hedge = paths()
    original = residual_shock(asset, hedge, 175)
    assert original is not None
    asset[174] += D("0.05")
    changed = residual_shock(asset, hedge, 175)
    assert changed is not None
    assert changed[0] == original[0]
    assert changed[1] > original[1]


def test_future_prices_do_not_change_signal_or_hedge() -> None:
    asset, hedge = paths()
    before = residual_shock(asset, hedge, 175)
    assert before == residual_shock(asset[:175], hedge[:175], 175)
    asset[175:] = [D(999)] * (len(asset) - 175)
    hedge[175:] = [D(-999)] * (len(hedge) - 175)
    assert before == residual_shock(asset, hedge, 175)


def test_insufficient_training_is_rejected() -> None:
    with pytest.raises(ValueError):
        residual_shock([D(0)] * 174, [D(0)] * 174, 174)
