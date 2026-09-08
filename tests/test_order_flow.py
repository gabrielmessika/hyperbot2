from dataclasses import replace
from decimal import Decimal as D

import pytest

from hyperbot2.research.order_flow import FlowBar, classify_flow
from hyperbot2.research.volume import VolumeBar


def test_flow_causality_absorption_and_acceptance():
    b = VolumeBar(0, D(100), D(101), D(99), D(100), D(10))
    baseline = [FlowBar(b, D(5))] * 168
    absorbed = FlowBar(replace(b, volume=D(20)), D(12))
    accepted = FlowBar(replace(absorbed.bar, close=D("100.5")), D(12))
    assert classify_flow(baseline + [absorbed], 168) == {"absorbed_pressure": -1}
    assert classify_flow(baseline + [accepted], 168) == {"accepted_pressure": 1}
    assert classify_flow(baseline + [accepted, absorbed], 168) == classify_flow(
        baseline + [accepted], 168
    )
    assert (
        classify_flow(baseline + [replace(absorbed, taker_buy_volume=D(10))], 168) == {}
    )


@pytest.mark.parametrize("volume", [D(-1), D(11), D("NaN")])
def test_impossible_buy_volume_fails_closed(volume):
    with pytest.raises(ValueError, match="invalid aggressive"):
        FlowBar(VolumeBar(0, D(100), D(101), D(99), D(100), D(10)), volume)
