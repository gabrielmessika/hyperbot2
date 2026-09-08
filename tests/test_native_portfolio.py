from decimal import Decimal as D

import pytest

from hyperbot2.research.funding_portfolio import AllocationSleeve
from hyperbot2.research.native_portfolio import (
    NativeAccount,
    adverse_price,
    simulate_native_portfolio,
)
from hyperbot2.research.rotation import HOUR
from hyperbot2.research.volume import VolumeBar


def replay(
    prices: list[int],
    *,
    fraction: str = "0.5",
    horizons: tuple[int, int] = (1, 2),
    scenario: str = "zero_cost",
    signals: dict | None = None,
) -> dict:
    bars = {
        "X": [
            VolumeBar(i * HOUR, D(p), D(p), D(p), D(p), D(100))
            for i, p in enumerate(prices)
        ]
    }
    names = {"fast::X": "fast", "slow::X": "slow"}
    entries = signals or {
        "fast::X": [0, 1] + [0] * (len(prices) - 2),
        "slow::X": [0, -1] + [0] * (len(prices) - 2),
    }
    return simulate_native_portfolio(
        bars,
        {"X": {i * HOUR + 10: D("0.001") for i in range(len(prices))}},
        entries,
        {"X": 3},
        dict.fromkeys(names, "X"),
        names,
        {
            "fast": AllocationSleeve(D(fraction), horizons[0]),
            "slow": AllocationSleeve(1 - D(fraction), horizons[1]),
        },
        scenario=scenario,
        monthly_infra=D(0),
        drawdown_limit=D("0.3"),
    )


@pytest.mark.parametrize(
    ("price", "side", "decimals", "expected"),
    [
        ("1234.56", 1, 0, "1234.6"),
        ("1234.56", -1, 0, "1234.5"),
        ("0.012345", 1, 1, "0.01235"),
        ("0.012345", -1, 1, "0.01234"),
        ("123456.1", 1, 0, "123457"),
        ("123456", -1, 0, "123456"),
    ],
)
def test_adverse_native_price_precision(
    price: str, side: int, decimals: int, expected: str
) -> None:
    assert adverse_price(D(price), side, decimals) == D(expected)


def test_average_cost_partial_exit_and_flip_reconcile_cash_and_episodes() -> None:
    a = NativeAccount()
    for at, (q, price) in enumerate([(2, 100), (1, 110), (-1, 120), (-3, 90), (1, 80)]):
        a.fill("X", D(q), D(price), D("0.001"), at)
    assert not a.positions
    assert abs(a.cash - D("999.22")) < D("1e-18")
    assert abs(sum(c["net_pnl_usd"] for c in a.cycles) + D("0.78")) < D("1e-18")
    assert len(a.cycles) == 2


def test_opposite_targets_pay_no_fee_or_funding_until_native_exposure_exists() -> None:
    r = replay([100] * 5, scenario="base")
    assert len(r["orders"]) == 2
    assert r["curve"][1]["native_quantities"]["X"] == 0
    q = abs(r["orders"][0]["delta"])
    assert r["summary"]["funding_cost_usd"] == -q * D("0.1")
    assert r["summary"]["fees_usd"] == sum(o["fee_usd"] for o in r["orders"])


def test_pending_small_order_never_receives_unexecuted_price_gain() -> None:
    r = replay([100, 100, 300, 400, 400, 400], fraction="0.505", horizons=(3, 3))
    assert r["curve"][1]["native_quantities"]["X"] == 0
    assert r["curve"][1]["residual_notional_usd"] == 5
    assert r["orders"][0]["time_ms"] == 2 * HOUR + 60_000
    assert r["orders"][0]["notional_usd"] == 15
    assert r["summary"]["net_total_usd"] == 5
    assert r["summary"]["terminal_flat"]


def test_small_target_can_expire_without_any_fill_or_fee() -> None:
    r = replay([100] * 5, fraction="0.505", horizons=(1, 1))
    assert not r["orders"]
    assert r["summary"]["net_total_usd"] == 0
    assert r["summary"]["residual_hours"] == 1


def one_sleeve(prices: list[int], signals: list[int]) -> dict:
    bars = {
        "X": [
            VolumeBar(i * HOUR, D(p), D(p), D(p), D(p), D(100))
            for i, p in enumerate(prices)
        ]
    }
    return simulate_native_portfolio(
        bars,
        {"X": {i * HOUR + 10: D(0) for i in range(len(prices))}},
        {"a": signals},
        {"X": 3},
        {"a": "X"},
        {"a": "one"},
        {"one": AllocationSleeve(D(1), 1)},
        scenario="zero_cost",
        monthly_infra=D(0),
        drawdown_limit=D("0.3"),
    )


def test_unclosable_dust_stays_in_inventory_after_halt_and_at_terminal() -> None:
    r = one_sleeve([100, 100, 1, 1, 1], [0, 1, 0, 1, 0])
    s = r["summary"]
    assert s["halted"] and not s["terminal_flat"]
    assert s["terminal_positions"]["X"] == 5
    assert s["net_total_usd"] == -495
    assert s["max_hourly_drawdown"] == D("0.495")
    assert s["rejected"]["below_minimum"] == 3
    assert len(r["orders"]) == 1


def test_halt_retries_exit_when_dust_becomes_executable_without_reentry() -> None:
    r = one_sleeve([100, 100, 1, 100, 100], [0, 1, 0, 1, 0])
    assert r["summary"]["halted"] and r["summary"]["terminal_flat"]
    assert r["summary"]["max_hourly_drawdown"] == D("0.495")
    assert r["summary"]["net_total_usd"] == 0
    assert len(r["orders"]) == 2


def test_new_quantity_uses_actual_native_equity() -> None:
    r = one_sleeve([100, 100, 200, 200, 200, 200], [0, 1, 0, 1, 0, 0])
    assert [o["delta"] for o in r["orders"]] == [D(5), D(-5), D("3.75"), D("-3.75")]
    assert r["summary"]["net_total_usd"] == 500


def test_future_price_change_cannot_change_earlier_orders_or_equity() -> None:
    a = replay([100, 100, 120, 110, 110, 110])
    b = replay([100, 100, 120, 900, 10, 100])
    assert a["curve"][:3] == b["curve"][:3]
    assert [o for o in a["orders"] if o["time_ms"] < 3 * HOUR] == [
        o for o in b["orders"] if o["time_ms"] < 3 * HOUR
    ]


def test_half_exposure_passive_control_keeps_one_capital_and_terminal_exit() -> None:
    coins = ("A", "B", "C")
    rows = [
        VolumeBar(i * HOUR, D(p), D(p), D(p), D(p), D(100))
        for i, p in enumerate([100, 100, 110, 110])
    ]
    result = simulate_native_portfolio(
        dict.fromkeys(coins, rows),
        {c: {i * HOUR + 10: D(0) for i in range(4)} for c in coins},
        dict.fromkeys(coins, (0, 1, 0, 0)),
        dict.fromkeys(coins, 3),
        {c: c for c in coins},
        dict.fromkeys(coins, "passive"),
        {"passive": AllocationSleeve(D(1), 2)},
        scenario="zero_cost",
        monthly_infra=D(0),
        drawdown_limit=D("0.3"),
        gross_cap=D("0.5"),
    )
    assert result["summary"]["net_total_usd"] == D("49.98")
    assert result["curve"][1]["gross_notional"] == D("499.8")
    assert result["summary"]["terminal_flat"]
    assert {c["closed_ms"] for c in result["cycles"]} == {3 * HOUR + 60_000}
