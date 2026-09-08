from decimal import Decimal as D

import pytest

from hyperbot2.research.collective_shock import downside_breadth, shock_observations
from hyperbot2.research.rotation import HOUR


def test_threshold_and_past_only_endpoints() -> None:
    rows = {str(i): [D(100)] * 24 + [D(95) if i < 8 else D(99)] for i in range(11)}
    returns, count = downside_breadth(rows, 25)
    assert count == 8 and returns["0"] == D("-.05")
    future = {c: v + [D("NaN")] * 50 for c, v in rows.items()}
    assert downside_breadth(future, 25) == (returns, count)
    rows["0"][24] = D("95.0001")
    assert downside_breadth(rows, 25)[1] == 7
    with pytest.raises(ValueError):
        downside_breadth(rows, 24)
    with pytest.raises(ValueError):
        downside_breadth(future, 26)


def test_extended_shock_spacing_and_delayed_exit_coverage() -> None:
    times = [1704067200000 + i * HOUR for i in range(110)]
    rows = {str(c): [D(100) * D(".99") ** i for i in range(110)] for c in range(11)}
    records = shock_observations(rows, times)
    assert [r.index for r in records if r.eligible] == [25, 51, 77]
    assert all(r.shock for r in records)
    assert records[-1].index == 84  # Delayed exit needs candle index 109.
    assert sum(r.shock and not r.eligible for r in records) == 57


def test_quiet_and_misaligned_panels() -> None:
    times = [i * HOUR for i in range(100)]
    rows = {str(c): [D(100)] * 100 for c in range(11)}
    assert not any(r.eligible for r in shock_observations(rows, times))
    with pytest.raises(ValueError):
        shock_observations(rows, times[:-1] + [times[-1] + HOUR])
    rows.pop("0")
    with pytest.raises(ValueError):
        shock_observations(rows, times)
