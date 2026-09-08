from dataclasses import replace
from decimal import Decimal as D

import pytest

from hyperbot2.research.compression_breakout import (
    compression_entries,
    compression_signal,
)
from hyperbot2.research.rotation import HOUR
from hyperbot2.research.volume import VolumeBar


def fixture(side: int = 1) -> list[VolumeBar]:
    rows = [
        VolumeBar(i * HOUR, D(100), D(110), D(90), D(100), D(10)) for i in range(240)
    ]
    for i in range(168, 192):
        rows[i] = replace(rows[i], high=D(101), low=D(99))
    rows[192] = replace(
        rows[192],
        high=D(104 if side == 1 else 100),
        low=D(100 if side == 1 else 96),
        close=D(100 + 3 * side),
        volume=D(30),
    )
    return rows


@pytest.mark.parametrize("side", [-1, 1])
def test_future_and_entry_bar_cannot_change_signal(side: int) -> None:
    rows = fixture(side)
    assert compression_signal(rows, 193) == side
    assert compression_signal(rows[:193], 193) == side
    rows[193:] = [replace(b, high=D(999), close=D(999)) for b in rows[193:]]
    assert compression_signal(rows, 193) == side


def test_high_volume_breakout_requires_a_quiet_prior_box() -> None:
    rows = fixture()
    for i in range(168):
        rows[i] = replace(rows[i], high=D(101), low=D(99))
    assert compression_signal(rows, 193) == 0
    assert compression_signal(rows, 193, require_compression=False) == 1
    rows[192] = replace(rows[192], volume=D(10))
    assert compression_signal(rows, 193, require_compression=False) == 0


def test_spacing_and_terminal_hours_are_reserved() -> None:
    rows = fixture()
    entries = compression_entries(rows)
    assert entries[193] == 1
    assert not any(entries[194:218])
    assert not any(compression_entries(rows[:218]))
