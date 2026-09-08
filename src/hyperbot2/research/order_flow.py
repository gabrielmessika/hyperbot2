"""Causal classification of externally observed aggressive volume shocks."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from statistics import median

from hyperbot2.research.volume import VolumeBar

D = Decimal


@dataclass(frozen=True)
class FlowBar:
    bar: VolumeBar
    taker_buy_volume: Decimal

    def __post_init__(self) -> None:
        if (
            not self.taker_buy_volume.is_finite()
            or not 0 <= self.taker_buy_volume <= self.bar.volume
        ):
            raise ValueError("invalid aggressive buy volume")


def classify_flow(rows: Sequence[FlowBar], index: int) -> dict[str, int]:
    if index < 168:
        return {}
    current = rows[index]
    baseline = median(r.bar.volume for r in rows[index - 168 : index])
    if baseline <= 0 or current.bar.volume < 2 * baseline:
        return {}
    imbalance = 2 * current.taker_buy_volume / current.bar.volume - 1
    if abs(imbalance) < D("0.15"):
        return {}
    side = 1 if imbalance > 0 else -1
    change = current.bar.close / current.bar.open - 1
    result = {}
    if abs(change) >= D("0.0025") and change * side > 0:
        result["accepted_pressure"] = side
    if abs(change) <= D("0.0025"):
        result["absorbed_pressure"] = -side
    return result
