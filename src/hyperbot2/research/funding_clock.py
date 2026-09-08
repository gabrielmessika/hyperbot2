"""Expected next funding clock from one already observed payment only."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from hyperbot2.research.rotation import HOUR

D = Decimal


@dataclass(frozen=True, slots=True)
class FundingObservation:
    time_ms: int
    interval_hours: int
    rate: Decimal


@dataclass(frozen=True, slots=True)
class ClockSignal:
    known_ms: int
    expected_payment_ms: int
    side: int
    previous_rate: Decimal


def next_clock_signal(
    previous: FundingObservation, start: int, end: int
) -> ClockSignal | None:
    if start % HOUR or end % HOUR or start >= end:
        raise ValueError("aligned positive history period required")
    if (
        not start <= previous.time_ms < end
        or not 0 <= previous.time_ms % HOUR <= 60_000
        or previous.interval_hours not in (4, 8)
        or not previous.rate.is_finite()
    ):
        raise ValueError("invalid observed funding payment")
    expected = previous.time_ms // HOUR * HOUR + previous.interval_hours * HOUR
    if abs(previous.rate) < D("0.001") or expected + 3 * HOUR >= end:
        return None
    return ClockSignal(
        previous.time_ms, expected, 1 if previous.rate > 0 else -1, previous.rate
    )
