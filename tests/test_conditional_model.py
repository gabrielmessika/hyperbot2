from dataclasses import replace
from decimal import Decimal as D

import pytest

from hyperbot2.research.conditional_model import (
    DAY,
    Observation,
    chronological_predictions,
    features_at,
    fit_before,
    fit_ridge,
)
from hyperbot2.research.rotation import HOUR
from hyperbot2.research.volume import VolumeBar


def test_ridge_matches_analytic_solution_and_handles_collinearity() -> None:
    model = fit_ridge([[-1.0], [1.0]], [-2.0, 2.0])
    assert model.intercept == 0
    assert model.coefficients == pytest.approx((1.0,))
    assert model.predict([1.0]) == pytest.approx(1)
    duplicate = fit_ridge([[-1.0, -1.0], [1.0, 1.0]], [-2.0, 2.0])
    assert duplicate.coefficients == pytest.approx((2 / 3, 2 / 3))
    constant = fit_ridge([[4.0], [4.0]], [1.0, 3.0])
    assert constant.predict([400.0]) == 2


def test_training_label_clipping_and_invalid_values() -> None:
    assert fit_ridge([[0.0], [0.0]], [100.0, 100.0]).intercept == 5
    with pytest.raises(ValueError):
        fit_ridge([[float("nan")], [1.0]], [0.0, 1.0])
    with pytest.raises(ValueError):
        fit_ridge([[1.0], [2.0]], [0.0, float("inf")])


def observation(time: int, value: float = 1.0) -> Observation:
    return Observation("A", 0, time, time + 6 * HOUR + 60_000, (value,), 1.0, value)


def test_purge_boundary_and_training_only_standardization() -> None:
    now = 100 * DAY
    rows = [observation(now - 8 * HOUR, -1), observation(now - 9 * HOUR, 1)]
    # Exactly one hour of embargo is eligible; one millisecond less is not.
    edge = replace(observation(now - 10 * HOUR, 3), label_known_ms=now - HOUR)
    poisoned = replace(
        edge, features=(1e10,), label=1e10, label_known_ms=now - HOUR + 1
    )
    old = observation(now - 90 * DAY - 1, 1e10)
    future = observation(now + HOUR, 1e10)
    expected = fit_before([*rows, edge], now, minimum=2)
    assert expected is not None and expected[1:] == (3, now - HOUR)
    assert expected[0].means == (1.0,)
    assert fit_before([*rows, edge, poisoned, old, future], now, 2) == expected
    assert fit_before(rows, now, 3) is None


def test_monthly_fit_is_frozen_and_future_labels_do_not_change_predictions() -> None:
    start = 1735689600000  # 2025-01-01
    april = start + 90 * DAY
    rows = [
        observation(april - 2 * DAY, -1),
        observation(april - DAY, 1),
        observation(april, 2),
        observation(april + DAY, -2),
    ]
    predictions, fits = chronological_predictions(rows, start, minimum=2)
    assert len(fits) == 1 and fits[0].time_ms == april
    assert [p.trained_ms for p in predictions] == [april, april]
    poisoned = [*rows[:2], *[replace(o, label=1e9) for o in rows[2:]]]
    other, other_fits = chronological_predictions(poisoned, start, minimum=2)
    assert other_fits == fits
    assert [p.predicted for p in other] == [p.predicted for p in predictions]
    # Ninety days are required before the month boundary, not merely prediction.
    assert chronological_predictions(rows, start + DAY, minimum=2) == ([], [])


def test_features_do_not_read_future_bars_or_funding() -> None:
    rows = [
        VolumeBar(
            i * HOUR, D(100 + i), D(100 + i), D(100 + i), D(100 + i), D(10 + i % 7)
        )
        for i in range(200)
    ]
    baseline = features_at({"A": rows}, {"A": [0.0] * 200}, 169)
    altered = rows[:169] + [replace(r, volume=D("1e10")) for r in rows[169:]]
    assert (
        features_at({"A": altered}, {"A": [0.0] * 169 + [1e10] * 31}, 169) == baseline
    )
    assert len(baseline["A"][0]) == 8
    assert all(-5 <= x <= 5 for x in baseline["A"][0])
    with pytest.raises(ValueError):
        features_at({"A": rows}, {"A": [0.0] * 200}, 168)
    with pytest.raises(ValueError):
        features_at(
            {"A": [replace(r, volume=D(0)) for r in rows]}, {"A": [0.0] * 200}, 169
        )
