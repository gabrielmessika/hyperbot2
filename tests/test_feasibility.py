"""Check time weighting and the distinction from receipt-only freshness."""

import runpy
from pathlib import Path

import pytest

diagnostic = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "scripts/diagnose_feasibility.py")
)
activation_count = diagnostic["activation_count"]
coverage = diagnostic["coverage"]


def test_fresh_receipts_do_not_imply_continuous_freshness() -> None:
    assert coverage([(1000, 750), (1500, 1250), (2000, 1750)]) == {
        "observed_ms": 1000,
        "fresh_ms": 500,
        "stale_ms": 500,
    }
    assert activation_count([250, 250, 250], 350, 50) == 0
    assert activation_count([250, 250, 250], 200, 50) == 3


def test_invalid_future_timestamp_and_unobserved_tail() -> None:
    assert coverage([(1000, 1100), (1200, 1150)])["fresh_ms"] == 0
    assert coverage([(1000, 900)])["observed_ms"] == 0
    with pytest.raises(ValueError, match="regressed"):
        coverage([(1000, 900), (999, 900)])


def test_activation_boundary_and_negative_age() -> None:
    assert activation_count([-1, 100, 101], 350, 50) == 1
