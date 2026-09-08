"""US regular-session calendar anchors for the registered 2026 research window."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
HOUR = 3600000
HOLIDAYS = frozenset(
    date.fromisoformat(s)
    for s in (
        "2026-02-16",
        "2026-04-03",
        "2026-05-25",
        "2026-06-19",
        "2026-07-03",
        "2026-09-07",
    )
)


def weekend_frame(sunday: date) -> tuple[int, int, int, int] | None:
    """Return Friday reference bar, Sunday signal/entry, Monday exit opens."""
    if sunday.weekday() != 6 or not date(2026, 2, 12) <= sunday <= date(2026, 9, 6):
        raise ValueError("Sunday outside the registered calendar window")
    friday, monday = sunday - timedelta(days=2), sunday + timedelta(days=1)
    if friday in HOLIDAYS or monday in HOLIDAYS:
        return None
    reference = int(datetime.combine(friday, time(15), NY).timestamp() * 1000)
    entry = int(datetime.combine(sunday, time(12), NY).timestamp() * 1000)
    exit_time = int(datetime.combine(monday, time(10), NY).timestamp() * 1000)
    return reference, entry - HOUR, entry, exit_time
