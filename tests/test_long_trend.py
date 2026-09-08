import runpy
from decimal import Decimal as D

import pytest

MODULE = runpy.run_path("scripts/investigate_long_trend.py")


def test_daily_funding_proxy_uses_each_payment_day_and_excludes_entry() -> None:
    start, hour, day = MODULE["START"], MODULE["HOUR"], MODULE["DAY"]
    rates = {t: D(0) for t in range(start, start + 7 * day + hour, hour)}
    rates[start] = D(999)
    rates[start + hour] = D("0.01")
    rates[start + day] = D("0.02")
    prices = [D(100)] + [D(200)] * 7
    long = MODULE["daily_leg"](prices, rates, 0, 1, D(0), D(0), "signed")
    short = MODULE["daily_leg"](prices, rates, 0, -1, D(0), D(0), "signed")
    assert long["funding_cost_bps"] == D(500)
    assert long["net_bps"] == D(9500)
    assert short["net_bps"] == D(-9500)


def test_missing_hourly_funding_cannot_become_zero() -> None:
    with pytest.raises(KeyError):
        MODULE["daily_leg"]([D(100)] * 8, {}, 0, 1, D(0), D(0), "signed")
