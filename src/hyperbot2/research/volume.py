"""Completed-bar volume shock classification, without execution assumptions."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from statistics import median

D = Decimal


@dataclass(frozen=True)
class VolumeBar:
    time: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal

    def __post_init__(self) -> None:
        if (
            not all(
                x.is_finite() and x > 0
                for x in (self.open, self.high, self.low, self.close)
            )
            or not self.volume.is_finite()
            or self.volume < 0
            or not self.low
            <= min(self.open, self.close)
            <= max(self.open, self.close)
            <= self.high
        ):
            raise ValueError("invalid OHLCV")


def classify(rows: Sequence[VolumeBar], index: int) -> dict[str, int]:
    """Index denotes the last closed bar; no later row is accessed."""
    if index < 168:
        return {}
    past, bar = rows[index - 168 : index], rows[index]
    volume = median(b.volume for b in past)
    typical_range = median((b.high - b.low) / b.open for b in past)
    width = bar.high - bar.low
    if (
        volume <= 0
        or typical_range <= 0
        or width <= 0
        or bar.volume < 3 * volume
        or width / bar.open < max(2 * typical_range, D("0.005"))
    ):
        return {}
    location = (bar.close - bar.low) / width
    body = bar.close / bar.open - 1
    result = {}
    if body >= D("0.005") and location >= D("0.8"):
        result["continuation"] = 1
    elif body <= D("-0.005") and location <= D("0.2"):
        result["continuation"] = -1
    if min(bar.open, bar.close) - bar.low >= width / 2 and location > D("0.5"):
        result["rejection"] = 1
    elif bar.high - max(bar.open, bar.close) >= width / 2 and location < D("0.5"):
        result["rejection"] = -1
    return result
