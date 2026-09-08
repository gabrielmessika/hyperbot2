from decimal import Decimal as D

import pytest

from hyperbot2.research.funding_portfolio import (
    AllocationSleeve,
    funding_entries,
    simulate_portfolio,
)
from hyperbot2.research.rotation import HOUR
from hyperbot2.research.volume import VolumeBar


def run(
    prices: dict[str, list[int]],
    signals: dict[str, list[int]],
    *,
    rates: dict | None = None,
    **kwargs: object,
) -> dict:
    bars = {
        c: [
            VolumeBar(i * HOUR, D(p), D(p), D(p), D(p), D(100))
            for i, p in enumerate(values)
        ]
        for c, values in prices.items()
    }
    funding = rates or {
        c: {i * HOUR + 10: D(0) for i in range(len(values))}
        for c, values in prices.items()
    }
    return simulate_portfolio(
        bars,
        funding,
        signals,
        dict.fromkeys(prices, 3),
        gross_cap=D("1.5"),
        scenario="zero_cost",
        monthly_infra=D(0),
        **kwargs,
    )


def test_simultaneous_entries_share_capital_and_keep_price_gain() -> None:
    result = run(
        {c: [100, 100, 110, 110] for c in ("A", "B", "C", "D")},
        {c: [0, 1, 0, 0] for c in ("A", "B", "C", "D")},
        holding_hours=1,
    )
    assert len(result["cycles"]) == 4
    assert {p["quantity"] for p in result["cycles"]} == {D("3.75")}
    assert result["summary"]["net_total_usd"] == 150
    assert result["summary"]["max_positions"] == 4


def test_gap_beyond_drawdown_limit_is_retained_and_halts_reentry() -> None:
    result = run(
        {"A": [100, 100, 40, 40, 100]}, {"A": [0, 1, 0, 1, 0]}, holding_hours=None
    )
    assert result["summary"]["halted"]
    assert result["summary"]["max_hourly_drawdown"] == D("0.3")
    assert result["summary"]["net_total_usd"] == -300
    assert len(result["cycles"]) == 1
    assert result["cycles"][0]["reason"] == "drawdown_or_margin"


def test_latent_loss_is_counted_before_recovery_and_next_open_exit() -> None:
    bars = {
        "A": [
            VolumeBar(
                i * HOUR,
                D(100),
                D(100),
                D(50) if i == 1 else D(100),
                D(50) if i == 1 else D(100),
                D(100),
            )
            for i in range(4)
        ]
    }
    result = simulate_portfolio(
        bars,
        {"A": {i * HOUR + 10: D(0) for i in range(4)}},
        {"A": [0, 1, 0, 0]},
        {"A": 3},
        gross_cap=D("1.5"),
        scenario="zero_cost",
        monthly_infra=D(0),
        holding_hours=None,
    )
    assert result["summary"]["max_hourly_drawdown"] == D("0.25")
    assert result["summary"]["net_total_usd"] == 0
    assert result["cycles"][0]["closed_ms"] == 2 * HOUR + 60_000


def test_funding_excludes_entry_hour_and_includes_exit_payment() -> None:
    bars = {
        "A": [
            VolumeBar(i * HOUR, D(100), D(100), D(100), D(100), D(100))
            for i in range(4)
        ]
    }
    payments = {
        "A": {
            10: D(0),
            HOUR + 10: D("0.9"),
            2 * HOUR + 10: D("0.001"),
            3 * HOUR + 10: D(0),
        }
    }
    result = simulate_portfolio(
        bars,
        payments,
        {"A": [0, -1, 0, 0]},
        {"A": 3},
        gross_cap=D(1),
        scenario="base",
        monthly_infra=D(20),
        holding_hours=1,
    )
    p = result["cycles"][0]
    assert p["funding_cost_usd"] == -p["quantity"] * D("0.1")
    assert result["summary"]["net_total_usd"] == pytest.approx(
        p["net_pnl_usd"] - D(20) * 4 / 720
    )
    assert abs(result["curve"][-1]["unrealized_pnl"]) == 0


def test_incomplete_or_late_payment_fails_closed() -> None:
    with pytest.raises(ValueError, match="funding coverage"):
        run({"A": [100] * 3}, {"A": [0, 0, 0]}, rates={"A": {10: D(0)}})
    with pytest.raises(ValueError, match="precede execution"):
        run({"A": [100] * 3}, {"A": [0, 0, 0]}, rates={"A": {60_001: D(0)}})


def test_continuous_signals_do_not_rearm_at_an_arbitrary_fold() -> None:
    rates = [D("0.0001")] * 8 + [D("0.00002")] * 200
    signals = funding_entries(rates)
    assert signals[12] == 1
    assert sum(bool(v) for v in signals) == 1
    assert signals == funding_entries(rates[:100] + rates[100:])


def test_thirty_percent_can_hold_through_twenty_five_percent_loss() -> None:
    prices, signals = {"A": [100, 100, 50, 100, 100]}, {"A": [0, 1, 0, 0, 0]}
    old = run(prices, signals, holding_hours=None)
    wider = run(prices, signals, holding_hours=None, drawdown_limit=D("0.3"))
    assert old["summary"]["halted"]
    assert old["summary"]["net_total_usd"] == -250
    assert not wider["summary"]["halted"]
    assert wider["summary"]["max_hourly_drawdown"] == D("0.25")
    assert wider["summary"]["net_total_usd"] == 0


def test_thirty_percent_still_retains_gap_overshoot_and_rejects_reentry() -> None:
    result = run(
        {"A": [100, 100, 30, 100, 100]},
        {"A": [0, 1, 0, 1, 0]},
        holding_hours=None,
        drawdown_limit=D("0.3"),
    )
    assert result["summary"]["halted"]
    assert result["summary"]["max_hourly_drawdown"] == D("0.35")
    assert result["summary"]["net_total_usd"] == -350
    assert len(result["cycles"]) == 1
    with pytest.raises(ValueError, match="drawdown limit"):
        run({"A": [100] * 3}, {"A": [0] * 3}, drawdown_limit=D("0.4"))


def test_sleeves_share_one_capital_and_keep_distinct_horizons() -> None:
    names = {f"{group}{i}": group for group in ("fast", "slow") for i in range(3)}
    result = run(
        {c: [100, 100, 110, 120, 120] for c in names},
        {c: [0, 1, 0, 0, 0] for c in names},
        allocation_sleeves={
            "fast": AllocationSleeve(D("0.5"), 1),
            "slow": AllocationSleeve(D("0.5"), 2),
        },
        asset_sleeves=names,
    )
    assert {p["quantity"] for p in result["cycles"]} == {D("2.5")}
    assert result["summary"]["net_total_usd"] == 225
    assert {
        p["closed_ms"] for p in result["cycles"] if p["coin"].startswith("fast")
    } == {2 * HOUR + 60_000}
    assert {
        p["closed_ms"] for p in result["cycles"] if p["coin"].startswith("slow")
    } == {3 * HOUR + 60_000}


def test_idle_sleeve_budget_is_not_borrowed_by_active_sleeve() -> None:
    names = {**dict.fromkeys(("A", "B", "C"), "active"), "D": "idle"}
    result = run(
        {c: [100] * 4 for c in names},
        {c: [0, int(c != "D"), 0, 0] for c in names},
        allocation_sleeves={
            "active": AllocationSleeve(D("0.5"), 1),
            "idle": AllocationSleeve(D("0.5"), 1),
        },
        asset_sleeves=names,
    )
    assert sum(p["quantity"] * p["entry_price"] for p in result["cycles"]) == 750


def test_invalid_sleeve_capital_or_mapping_fails_closed() -> None:
    with pytest.raises(ValueError, match="exactly one capital"):
        run(
            {"A": [100] * 3},
            {"A": [0] * 3},
            allocation_sleeves={"a": AllocationSleeve(D("1.5"), 1)},
            asset_sleeves={"A": "a"},
        )
    with pytest.raises(ValueError, match="both sleeve"):
        run({"A": [100] * 3}, {"A": [0] * 3}, asset_sleeves={"A": "a"})


def test_global_loss_halts_both_sleeves_without_reentry() -> None:
    result = run(
        {c: [100, 100, 30, 100, 100] for c in ("A", "B")},
        {c: [0, 1, 0, 1, 0] for c in ("A", "B")},
        allocation_sleeves={
            "a": AllocationSleeve(D("0.5"), None),
            "b": AllocationSleeve(D("0.5"), None),
        },
        asset_sleeves={"A": "a", "B": "b"},
        drawdown_limit=D("0.3"),
    )
    assert result["summary"]["halted"]
    assert result["summary"]["net_total_usd"] == -350
    assert len(result["cycles"]) == 2
    assert {p["reason"] for p in result["cycles"]} == {"drawdown_or_margin"}
