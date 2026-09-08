from datetime import UTC, datetime
from decimal import Decimal as D

from hyperbot2.research.rotation import HOUR
from hyperbot2.research.weekly_relative import weekly_entries, weekly_selection


def test_skip_day_and_future_prices_do_not_change_ranking() -> None:
    closes = {str(j): [D(100)] * 220 for j in range(6)}
    for j, rows in enumerate(closes.values()):
        rows[168] = D(90 + j * 5)
    sides, scores = weekly_selection(closes, 193)
    assert sides == {"0": -1, "1": -1, "2": -1, "3": 1, "4": 1, "5": 1}
    for rows in closes.values():
        rows[169:] = [D(999)] * (len(rows) - 169)
    assert weekly_selection(closes, 193) == (sides, scores)


def test_equal_scores_do_not_create_an_arbitrary_trade() -> None:
    assert weekly_selection({str(j): [D(100)] * 220 for j in range(6)}, 193)[0] == {}


def test_calendar_keeps_complete_delayed_week_and_equal_sides() -> None:
    start = int(datetime(2026, 3, 10, tzinfo=UTC).timestamp() * 1000)
    times = [start + i * HOUR for i in range(600)]
    closes = {
        str(j): [D(100) + D(i * (j + 1)) / 100 for i in range(600)] for j in range(6)
    }
    entries, records = weekly_entries(closes, times)
    assert len(records) == 1
    assert records[0]["time_ms"] == int(
        datetime(2026, 3, 23, tzinfo=UTC).timestamp() * 1000
    )
    assert sorted(rows[312] for rows in entries.values()) == [-1, -1, -1, 1, 1, 1]
