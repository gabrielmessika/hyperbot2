import runpy
from datetime import UTC, datetime


def test_overnight_frames_exclude_mondays_holidays_and_missing_previous_close():
    script = runpy.run_path("scripts/investigate_overnight_repricing.py")
    start = int(datetime(2026, 2, 12, tzinfo=UTC).timestamp() * 1000)
    end = int(datetime(2026, 9, 6, tzinfo=UTC).timestamp() * 1000)
    slots = script["frames"](start, end)
    dates = {
        datetime.fromtimestamp(e / 1000, script["NY"]).date() for _, _, e, _ in slots
    }
    assert all(day.weekday() in (1, 2, 3, 4) for day in dates)
    assert datetime(2026, 5, 26).date() not in dates
    assert datetime(2026, 7, 3).date() not in dates
    for ref, signal, entry, exit_time in slots:
        assert ref < signal < entry < exit_time < end
        assert exit_time - entry == 7200000
