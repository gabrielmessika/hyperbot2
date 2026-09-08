import math

import pytest

from hyperbot2.research.pairs import fit_pair, model_at


def series():
    x = [10 + 0.001 * i + 0.01 * math.sin(i) for i in range(750)]
    y = [2 + 0.7 * v + 0.02 * math.cos(i / 3) for i, v in enumerate(x)]
    return x, y


def test_model_excludes_signal_and_future_and_is_frozen():
    x, y = series()
    model = model_at(x, y, 720)
    prior_z = model.z(x[719], y[719])
    y[720:] = [100.0] * len(y[720:])
    assert model_at(x, y, 720) == model
    assert model.z(x[719], y[719]) == prior_z
    assert model.z(x[720], y[720]) > 100


def test_fit_recovers_known_relation_and_rejects_invalid_data():
    x, y = series()
    assert fit_pair(x, y).beta == pytest.approx(0.7, abs=0.005)
    with pytest.raises(ValueError, match="degenerate"):
        fit_pair([1.0] * 8, list(range(8)))
    with pytest.raises(ValueError, match="aligned"):
        fit_pair(x, y[:-1])
    with pytest.raises(ValueError, match="finite"):
        fit_pair(x, y[:-1] + [float("nan")])
