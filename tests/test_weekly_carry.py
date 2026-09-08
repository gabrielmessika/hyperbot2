from decimal import Decimal as D

import pytest

from hyperbot2.research.rotation import HOUR
from hyperbot2.research.weekly_carry import carry_baskets, carry_selection


def rates(count: int = 600) -> dict[str, list[D]]:
    return {str(i): [D(i) / 100000] * count for i in range(8)}


def test_receipt_sides_and_frequency_normalization() -> None:
    hourly = rates()
    sides, scores, receipt = carry_selection(hourly, 168)
    assert sides == {"0": 1, "1": 1, "2": 1, "5": -1, "6": -1, "7": -1}
    assert receipt == D("0.0042")
    eight_hour = {
        c: [r * 8 if i % 8 == 0 else D(0) for i, r in enumerate(v)]
        for c, v in hourly.items()
    }
    assert carry_selection(eight_hour, 168) == (sides, scores, receipt)


def test_signal_ignores_current_settlement_and_future() -> None:
    original = rates()
    changed = {c: v[:168] + [D("NaN")] * 432 for c, v in original.items()}
    assert carry_selection(changed, 168) == carry_selection(original, 168)
    with pytest.raises(ValueError):
        carry_selection(changed, 169)
    with pytest.raises(ValueError):
        carry_selection(original, 167)
    original["3"] = original["2"]
    assert carry_selection(original, 168)[0] == {}


def test_calendar_hurdle_offsets_and_missing_bucket() -> None:
    start = 1704067200000  # Monday 2024-01-01.
    times = [start + i * HOUR for i in range(600)]
    payments = {
        c: {t + 20: v[i] for i, t in enumerate(times)} for c, v in rates().items()
    }
    baskets = carry_baskets(payments, times)
    assert [b.index for b in baskets] == [168, 336]
    assert all(b.eligible and b.expected_receipt == D("0.0042") for b in baskets)
    small = {c: {t: v / 10 for t, v in rows.items()} for c, rows in payments.items()}
    assert all(
        not b.eligible and len(b.sides) == 6 for b in carry_baskets(small, times)
    )
    del payments["0"][times[2] + 20]
    with pytest.raises(ValueError):
        carry_baskets(payments, times)
    with pytest.raises(ValueError):
        carry_baskets(small, times[:-1] + [times[-1] + HOUR])
