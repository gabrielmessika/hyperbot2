from dataclasses import replace
from decimal import Decimal as D

import pytest

from hyperbot2.research.volume import VolumeBar, classify


def bar(o="100", h="100.1", low="99.9", c="100", v="10"):
    return VolumeBar(0, *(D(x) for x in (o, h, low, c, v)))


def test_volume_signal_is_causal_and_excludes_current_bar_from_baseline():
    rows = [bar()] * 168 + [bar(h="101", c="100.9", v="30")]
    assert classify(rows, 168) == {"continuation": 1}
    assert classify(rows + [bar(h="1000000", v="10000000")], 168) == classify(rows, 168)
    assert classify(rows[:168] + [replace(rows[168], volume=D("29.99"))], 168) == {}


def test_wick_rejection_is_directional_and_centered_doji_is_excluded():
    assert classify([bar()] * 168 + [bar(h="100.2", low="98", v="30")], 168) == {
        "rejection": 1
    }
    assert classify([bar()] * 168 + [bar(h="102", low="99.8", v="30")], 168) == {
        "rejection": -1
    }
    assert classify([bar()] * 168 + [bar(h="101", low="99", v="30")], 168) == {}


@pytest.mark.parametrize(
    "changes",
    [
        {"volume": D("NaN")},
        {"volume": D("-1")},
        {"high": D("99")},
        {"open": D("Infinity")},
    ],
)
def test_invalid_volume_bars_fail_closed(changes):
    with pytest.raises(ValueError, match="invalid OHLCV"):
        replace(bar(), **changes)
