from decimal import Decimal as D

import pytest

from hyperbot2.research.liquidations import (
    HOUR,
    LiquidationHour,
    long_return,
    reconcile_raw,
    selected_hours,
    volume_hours,
)


def test_sparse_aggregates_do_not_impute_zero_or_include_end() -> None:
    row = {
        "timestamp": "1970-01-01T00:00:00Z",
        "coin": "BTC",
        "symbol": "BTC",
        "long_usd": "20",
        "short_usd": 0,
        "total_usd": 20,
        "long_count": 2,
        "short_count": 0,
        "count": 2,
    }
    boundary = dict(row, timestamp="1970-01-01T03:00:00Z")
    assert list(volume_hours([row, boundary], "BTC", 0, 3 * HOUR)) == [0]
    with pytest.raises(ValueError, match="duplicate"):
        volume_hours([row, row], "BTC", 0, HOUR)
    with pytest.raises(ValueError, match="aggregate"):
        volume_hours([dict(row, total_usd=25)], "BTC", 0, HOUR)


def test_event_selection_excludes_current_and_future_from_threshold() -> None:
    volumes = {
        t * HOUR: LiquidationHour(t * HOUR, D(10), D(0), 1, 0) for t in range(108, 168)
    }
    at = 168 * HOUR
    volumes[at] = LiquidationHour(at, D(100000), D(0), 5, 0)
    returns = {t: D("-0.01") for t in volumes}
    first = selected_hours(volumes, returns, "BTC", 0, 240 * HOUR)
    assert len(first) == 1
    assert first[0]["prior_positive_hours"] == 60
    volumes[200 * HOUR] = LiquidationHour(200 * HOUR, D("1e12"), D(0), 5, 0)
    returns[200 * HOUR] = D(0)
    assert selected_hours(volumes, returns, "BTC", 0, 240 * HOUR) == first
    del volumes[108 * HOUR]
    assert selected_hours(volumes, returns, "BTC", 0, 240 * HOUR) == []


def test_raw_duplicate_and_ambiguous_direction_fail_qualification() -> None:
    row = {
        "timestamp": "1970-01-01T00:01:00Z",
        "coin": "BTC",
        "symbol": "BTC",
        "side": "A",
        "direction": "Close Long",
        "trade_id": 1,
        "tx_hash": "hash",
        "liquidated_user": "user",
        "liquidator_user": "user",
        "price": "100",
        "size": "2",
    }
    expected = LiquidationHour(0, D(200), D(0), 1, 0)
    assert reconcile_raw([row], "BTC", expected)["valid"]
    duplicate = reconcile_raw([row, row], "BTC", expected)
    assert duplicate["long_usd"] == D(200)
    assert not duplicate["valid"]
    with pytest.raises(ValueError, match="ambiguous"):
        reconcile_raw([dict(row, direction="Open Short")], "BTC", expected)


def test_fees_slippage_and_funding_use_executed_notional_and_payment_times() -> None:
    prices = {0: D(100), HOUR: D(110), 2 * HOUR: D(120)}
    funding = {0: D("0.5"), HOUR: D("-0.001"), 2 * HOUR: D("0.002")}
    result = long_return(prices, funding, 0, 2, D("0.01"), D("0.02"))
    quantity = 1 / D(102)
    exit_value = quantity * D("117.6")
    funding_cost = quantity * (D("0.11") + D("0.24"))
    expected = (exit_value - 1 - D("0.01") * (1 + exit_value) - funding_cost) * 10000
    assert abs(result["net_bps"] - expected) < D("1e-20")
    assert result["gross_bps"] == 2000
    assert abs(result["funding_adverse_bps"] - funding_cost * 10000) < D("1e-20")
    with pytest.raises(KeyError):
        long_return(prices, {0: D(0), HOUR: D(0)}, 0, 2)
