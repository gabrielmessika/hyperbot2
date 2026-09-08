from datetime import UTC, date, datetime

from hyperbot2.research.equity_weekend import weekend_frame


def test_weekend_anchors_account_for_dst_transition():
    frame = weekend_frame(date(2026, 3, 8))
    assert frame is not None
    reference, signal, entry, exit_time = frame
    assert datetime.fromtimestamp(reference / 1000, UTC) == datetime(
        2026, 3, 6, 20, tzinfo=UTC
    )
    assert datetime.fromtimestamp(entry / 1000, UTC) == datetime(
        2026, 3, 8, 16, tzinfo=UTC
    )
    assert datetime.fromtimestamp(exit_time / 1000, UTC) == datetime(
        2026, 3, 9, 14, tzinfo=UTC
    )
    assert entry - signal == 3600000


def test_holiday_friday_or_monday_prevents_signal():
    for sunday in (
        date(2026, 2, 15),
        date(2026, 4, 5),
        date(2026, 5, 24),
        date(2026, 6, 21),
        date(2026, 7, 5),
        date(2026, 9, 6),
    ):
        assert weekend_frame(sunday) is None
    assert weekend_frame(date(2026, 7, 12)) is not None
