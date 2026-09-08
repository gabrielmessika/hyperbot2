from datetime import datetime

from hyperbot2.research.equity_weekend import NY
from hyperbot2.research.oil_calendar import oil_entry_allowed, oil_signal_window_allowed


def at(day: int, hour: int) -> int:
    return int(datetime(2026, 6, day, hour, tzinfo=NY).timestamp() * 1000)


def test_roll_blackout_covers_entry_and_training_and_holiday() -> None:
    assert oil_entry_allowed(at(1, 9))
    assert not oil_entry_allowed(at(1, 15))
    assert not oil_entry_allowed(at(5, 10))
    assert oil_entry_allowed(at(18, 10))
    assert not oil_signal_window_allowed(at(18, 9))
    assert not oil_entry_allowed(at(19, 10))  # Registered US holiday.
    assert oil_entry_allowed(at(22, 10))
    assert oil_signal_window_allowed(at(22, 9))
