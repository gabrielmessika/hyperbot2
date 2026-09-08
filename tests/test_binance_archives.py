from decimal import Decimal as D
from pathlib import Path

import pytest

from hyperbot2.research.artifacts import write_json
from hyperbot2.research.binance_archives import (
    hourly_payments,
    load_archives,
    year_bounds,
)
from hyperbot2.research.rotation import HOUR


def test_payment_offsets_and_verified_non_payment_hours_are_preserved() -> None:
    result = hourly_payments(
        [
            (15, 8, D("0.001")),
            (8 * HOUR, 8, D("-0.002")),
            (12 * HOUR + 10, 4, D("0.003")),
        ],
        0,
        16 * HOUR,
    )
    assert len(result) == 16
    assert result[15] == D("0.001") and 0 not in result
    assert result[8 * HOUR] == D("-0.002")
    assert result[12 * HOUR + 10] == D("0.003")
    assert result[7 * HOUR] == 0


@pytest.mark.parametrize(
    "rows",
    [
        [(0, 8, D(0)), (16 * HOUR, 8, D(0))],
        [(HOUR, 8, D(0)), (9 * HOUR, 8, D(0))],
        [(0, 8, D(0)), (8 * HOUR + 60001, 8, D(0))],
        [(0, 8, D(0)), (8 * HOUR, 4, D(0))],
        [(0, 8, D("NaN")), (8 * HOUR, 8, D(0))],
        [(0, 8, D(0)), (0, 8, D(0))],
    ],
)
def test_unknown_funding_gaps_or_corruption_never_become_zero(rows: list) -> None:
    with pytest.raises(ValueError):
        hourly_payments(rows, 0, 16 * HOUR)


def test_final_unobserved_interval_cannot_be_assumed_complete() -> None:
    with pytest.raises(ValueError, match="final"):
        hourly_payments([(0, 8, D(0)), (8 * HOUR, 8, D(0))], 0, 17 * HOUR)


def test_year_bounds_include_leap_day_without_changing_2025() -> None:
    start, end = year_bounds(2024)
    assert (start, end) == (1704067200000, 1735689600000)
    assert (end - start) // HOUR == 8784
    assert year_bounds(2025) == (1735689600000, 1767225600000)
    with pytest.raises(ValueError):
        year_bounds(2023)


def test_manifest_year_mismatch_fails_before_reading_any_archive(
    tmp_path: Path,
) -> None:
    write_json(
        tmp_path / "manifest.json",
        {
            "complete": True,
            "coins": ["A"],
            "start_ms": 1735689600000,
            "end_ms_exclusive": 1767225600000,
            "archives": [],
        },
    )
    with pytest.raises(ValueError, match="different"):
        load_archives(tmp_path, ["A"], year=2024)
