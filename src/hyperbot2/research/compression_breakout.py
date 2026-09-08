"""Completed-bar compression breakout signals with disjoint reference windows."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from statistics import median

from hyperbot2.research.volume import VolumeBar

D = Decimal


def width(rows: Sequence[VolumeBar]) -> Decimal:
    return (max(b.high for b in rows) - min(b.low for b in rows)) / rows[0].open


def compression_signal(
    rows: Sequence[VolumeBar], entry_index: int, *, require_compression: bool = True
) -> int:
    """Use only bars completed strictly before the proposed entry hour."""
    if entry_index < 193 or entry_index > len(rows):
        raise ValueError("193 completed bars required")
    i = entry_index
    box, signal = rows[i - 25 : i - 1], rows[i - 1]
    typical_volume = median(b.volume for b in box)
    if typical_volume <= 0 or signal.volume < 2 * typical_volume:
        return 0
    side = (
        1
        if signal.close > max(b.high for b in box) and signal.close > signal.open
        else -1
        if signal.close < min(b.low for b in box) and signal.close < signal.open
        else 0
    )
    if not side or not require_compression:
        return side
    reference = median(
        width(rows[i - 25 - 24 * k : i - 25 - 24 * (k - 1)]) for k in range(1, 8)
    )
    return side if D(0) < width(box) <= reference / 2 else 0


def compression_entries(
    rows: Sequence[VolumeBar], *, require_compression: bool = True
) -> tuple[int, ...]:
    entries = [0] * len(rows)
    next_allowed = 0
    for i in range(193, len(rows) - 25):
        if i < next_allowed:
            continue
        side = compression_signal(rows, i, require_compression=require_compression)
        if side:
            entries[i] = side
            next_allowed = i + 25
    return tuple(entries)
