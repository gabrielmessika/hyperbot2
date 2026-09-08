from dataclasses import replace
from decimal import Decimal as D
from pathlib import Path

import pytest

from hyperbot2.research.archive_overlay import (
    DISPUTED,
    OCTOBER_END,
    OCTOBER_START,
    overlay_october,
)
from hyperbot2.research.binance_archives import load_archives
from hyperbot2.research.rotation import HOUR
from hyperbot2.research.volume import VolumeBar


def histories() -> tuple[list[VolumeBar], list[VolumeBar]]:
    raw = [
        VolumeBar(t, D(10), D(10), D(10), D(10), D(1))
        for t in range(OCTOBER_START - HOUR, OCTOBER_END + HOUR, HOUR)
    ]
    raw = [replace(b, volume=D(0)) if b.time == DISPUTED[0] else b for b in raw]
    rest = [
        replace(b, volume=D(2)) if b.time in DISPUTED else b
        for b in raw
        if OCTOBER_START <= b.time < OCTOBER_END
    ]
    return raw, rest


def test_overlay_changes_exactly_two_bars_without_mutating_original() -> None:
    raw, rest = histories()
    before = list(raw)
    corrected = overlay_october(raw, rest)
    assert raw == before and len(corrected) == len(raw)
    assert [a.time for a, b in zip(raw, corrected, strict=True) if a != b] == list(
        DISPUTED
    )
    assert corrected[0] is raw[0] and corrected[-1] is raw[-1]
    assert all(b.volume > 0 for b in corrected)


def test_extra_disagreement_or_missing_bar_fails_closed() -> None:
    raw, rest = histories()
    bad = list(rest)
    bad[0] = replace(bad[0], volume=D(3))
    with pytest.raises(ValueError, match="scope"):
        overlay_october(raw, bad)
    with pytest.raises(ValueError, match="complete"):
        overlay_october(raw, rest[:-1])
    missing_second_change = [
        replace(b, volume=D(1)) if b.time == DISPUTED[1] else b for b in rest
    ]
    with pytest.raises(ValueError, match="scope"):
        overlay_october(raw, missing_second_change)


def test_zero_volume_replacement_rejected() -> None:
    raw, rest = histories()
    with pytest.raises(ValueError, match="positive"):
        overlay_october(
            raw, [replace(b, volume=D(0)) if b.time == DISPUTED[0] else b for b in rest]
        )


def test_correction_cannot_be_used_for_another_year(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="only applies"):
        load_archives(tmp_path, ["A"], year=2025, october_2024_rest=tmp_path)
