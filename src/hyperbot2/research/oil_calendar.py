"""Conservative registered roll blackout, not a full CME/ICE calendar."""

from __future__ import annotations

from datetime import datetime

from hyperbot2.research.equity_weekend import HOLIDAYS, NY
from hyperbot2.research.rotation import HOUR


def outside_oil_roll(at: int) -> bool:
    day = datetime.fromtimestamp(at / 1000, NY).day
    return day < 4 or day > 17


def oil_entry_allowed(at: int) -> bool:
    dt = datetime.fromtimestamp(at / 1000, NY)
    return (
        dt.weekday() < 5
        and dt.date() not in HOLIDAYS
        and 9 <= dt.hour <= 14
        and dt.minute == dt.second == 0
        and outside_oil_roll(at)
    )


def oil_signal_window_allowed(signal_bar_open: int) -> bool:
    return all(
        outside_oil_roll(at)
        for at in range(signal_bar_open - 24 * HOUR, signal_bar_open + HOUR, HOUR)
    )
