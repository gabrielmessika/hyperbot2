from decimal import Decimal as D

import pytest

from hyperbot2.research.funding_portfolio import AllocationSleeve
from hyperbot2.research.native_portfolio import simulate_native_portfolio
from hyperbot2.research.rotation import HOUR
from hyperbot2.research.slow_trend import slow_entries, slow_signal
from hyperbot2.research.volume import VolumeBar


def test_direction_floor_and_future_prices_are_past_only() -> None:
    up = [D(100) * (D(i) / 2400).exp() for i in range(800)]
    assert slow_signal(up, 721) == (1, D(100))
    assert slow_signal(list(reversed(up)), 721)[0] == -1
    assert slow_signal([D(100)] * 800, 721) == (0, D(0))
    assert slow_signal(up[:721] + [D(1)] * 79, 721) == slow_signal(up, 721)
    with pytest.raises(ValueError, match="thirty"):
        slow_signal(up, 720)


def test_volatile_asset_receives_smaller_raw_weight() -> None:
    quiet = [(D(i // 24) / 100).exp() for i in range(721)]
    noisy = [(D(i // 24) / 100 + D("0.1") * ((i // 24) % 2)).exp() for i in range(721)]
    assert slow_signal(quiet, 721)[0] == slow_signal(noisy, 721)[0] == 1
    assert slow_signal(noisy, 721)[1] < slow_signal(quiet, 721)[1] / 5


def test_first_2025_basket_is_february_third_with_full_horizon() -> None:
    start = 1735689600000
    times = [start + i * HOUR for i in range(1500)]
    entries, weights, records = slow_entries(
        {"A": [D(100 + i) for i in range(1500)]}, times
    )
    assert records[0]["time_ms"] == 1738540800000
    first = next(i for i, value in enumerate(entries["A"]) if value)
    assert first == 792 and weights["A"][first] > 0


def weighted(scenario: str = "zero_cost", invalid: bool = False) -> dict:
    coins = ("A", "B", "C", "D")
    rows = [
        VolumeBar(i * HOUR, D(100), D(100), D(100), D(100), D(100)) for i in range(5)
    ]
    weights = {c: [D(0), D(i + 1), D(0), D(0), D(0)] for i, c in enumerate(coins)}
    if invalid:
        weights["A"][1] = D(0)
    return simulate_native_portfolio(
        dict.fromkeys(coins, rows),
        {c: {i * HOUR: D(0) for i in range(5)} for c in coins},
        dict.fromkeys(coins, (0, 1, 0, 0, 0)),
        dict.fromkeys(coins, 3),
        {c: c for c in coins},
        dict.fromkeys(coins, "one"),
        {"one": AllocationSleeve(D(1), 1)},
        scenario=scenario,
        monthly_infra=D(0),
        drawdown_limit=D("0.3"),
        entry_weights=weights,
    )


def test_weighted_budget_caps_one_asset_without_redistributing_excess() -> None:
    r = weighted()
    opens = {o["coin"]: o["delta"] for o in r["orders"] if o["before"] == 0}
    assert opens == {"A": D("1.5"), "B": D(3), "C": D("4.5"), "D": D(5)}
    assert r["curve"][1]["gross_notional"] == 1400
    assert r["summary"]["net_total_usd"] == 0


def test_delay_uses_signal_date_weights_not_execution_date_weights() -> None:
    a, b = weighted("base"), weighted("delay")
    assert [o["delta"] for o in a["orders"]] == [o["delta"] for o in b["orders"]]
    assert b["orders"][0]["time_ms"] == a["orders"][0]["time_ms"] + HOUR


def test_zero_weight_for_active_signal_fails_closed() -> None:
    with pytest.raises(ValueError, match="weights"):
        weighted(invalid=True)
