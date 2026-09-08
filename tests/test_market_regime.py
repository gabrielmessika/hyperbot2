from decimal import Decimal as D

import pytest

from hyperbot2.research.market_regime import collective_trend, join_panels
from hyperbot2.research.rotation import HOUR
from hyperbot2.research.volatility_spread import volatility_baskets
from hyperbot2.research.volume import VolumeBar


def test_collective_trend_uses_median_and_only_available_closes() -> None:
    rows = {str(i): [D(100)] * 720 + [D(90)] + [D(1000)] * 20 for i in range(11)}
    rows["0"][720] = D(10000)
    assert collective_trend(rows, 721) == D("-0.1")
    assert collective_trend({c: v[:721] for c, v in rows.items()}, 721) == D("-0.1")
    assert collective_trend({str(i): [D(100)] * 721 for i in range(11)}, 721) == 0
    with pytest.raises(ValueError):
        collective_trend(rows, 720)


def test_join_retains_payment_offsets_and_rejects_gaps_or_overlap() -> None:
    def bar(i: int) -> VolumeBar:
        return VolumeBar(i * HOUR, D(10), D(10), D(10), D(10), D(1))

    left, right = {"A": [bar(0), bar(1)]}, {"A": [bar(2), bar(3)]}
    lp, rp = {"A": {15: D(1), HOUR: D(0)}}, {"A": {2 * HOUR + 20: D(2), 3 * HOUR: D(0)}}
    bars, payments = join_panels(left, lp, right, rp)
    assert [b.time for b in bars["A"]] == [i * HOUR for i in range(4)]
    assert payments["A"][2 * HOUR + 20] == 2 and len(left["A"]) == 2
    with pytest.raises(ValueError, match="boundary"):
        join_panels(left, lp, {"A": [bar(3)]}, rp)
    with pytest.raises(ValueError, match="overlapping"):
        join_panels(left, lp, right, {"A": {15: D(1)}})
    with pytest.raises(ValueError, match="coverage"):
        join_panels(left, lp, right, {"A": {2 * HOUR: D(0)}})


def test_weekly_selection_keeps_january_without_annual_warmup_reset() -> None:
    start = 1733011200000  # 2024-12-01.
    times = [start + i * HOUR for i in range(24 * 75)]
    closes = {
        str(c): [(D(c) / 100 * ((i // 24) % 2)).exp() for i in range(len(times))]
        for c in range(1, 12)
    }
    records = volatility_baskets(closes, times)
    assert records[0].time_ms == 1736121600000  # 2025-01-06.
    assert all(len(r.sides) == 6 for r in records)
