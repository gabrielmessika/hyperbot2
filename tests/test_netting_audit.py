from decimal import Decimal as D

import pytest

from hyperbot2.research.funding_portfolio import AllocationSleeve, simulate_portfolio
from hyperbot2.research.netting_audit import audit_net_positions
from hyperbot2.research.rotation import HOUR
from hyperbot2.research.volume import VolumeBar


def fixture(fraction: str = "0.5", slow: int = 2, scenario: str = "zero_cost") -> tuple:
    rows = [
        VolumeBar(i * HOUR, D(100), D(110), D(90), D(100), D(100)) for i in range(5)
    ]
    rates = {i * HOUR + 10: D("0.0001") for i in range(5)}
    names = {"fast::X": "fast", "slow::X": "slow"}
    source = simulate_portfolio(
        dict.fromkeys(names, rows),
        dict.fromkeys(names, rates),
        {"fast::X": [0, 1, 0, 0, 0], "slow::X": [0, -1, 0, 0, 0]},
        dict.fromkeys(names, 3),
        gross_cap=D("1.5"),
        scenario=scenario,
        monthly_infra=D(0),
        drawdown_limit=D("0.3"),
        allocation_sleeves={
            "fast": AllocationSleeve(D(fraction), 1),
            "slow": AllocationSleeve(1 - D(fraction), slow),
        },
        asset_sleeves=names,
    )
    return {"X": rows}, {"X": rates}, {"X": 3}, dict.fromkeys(names, "X"), source


def test_netting_cancels_opposite_entries_but_keeps_later_exposure() -> None:
    inputs = fixture()
    result = audit_net_positions(*inputs)
    s = result["summary"]
    assert s["virtual_order_legs"] == 4
    assert s["net_order_deltas"] == 2
    assert s["exact_cancellations"] == 1
    assert [o["delta"] for o in result["orders"]] == [D("-2.5"), D("2.5")]
    assert s["direct_delta_minimums_passed"]
    assert s["execution_savings_credited_usd"] == 0
    assert result["curve"][1]["net_gross_notional"] == 0
    assert (
        s["net_exposure_drawdown_envelope"]
        < inputs[-1]["summary"]["max_ohlc_drawdown_envelope"]
    )


def test_valid_virtual_lots_can_create_unexecutable_small_net_orders() -> None:
    result = audit_net_positions(*fixture("0.505", 1))
    assert result["summary"]["below_minimum_orders"] == 2
    assert not result["summary"]["direct_delta_minimums_passed"]
    assert {o["notional_usd"] for o in result["orders"]} == {D(5)}
    assert {o["kind"] for o in result["orders"]} == {"increase_or_open", "reduction"}


@pytest.mark.parametrize("scenario", ["base", "cost_stress", "funding_adverse"])
def test_costs_and_funding_are_reconstructed_without_savings(scenario: str) -> None:
    inputs = fixture(scenario=scenario)
    s = audit_net_positions(*inputs)["summary"]
    assert s["cash_and_equity_reconstruction_passed"]
    assert (
        s["baseline_net_total_usd_unchanged"] == inputs[-1]["summary"]["net_total_usd"]
    )
    assert s["execution_savings_credited_usd"] == 0


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("quantity", D("2.5001"), "lot"),
        ("opened_ms", 1, "grid"),
        ("fees_usd", D(1), "fees"),
    ],
)
def test_corrupted_source_fails_closed(field: str, value: object, error: str) -> None:
    inputs = fixture()
    inputs[-1]["cycles"][0][field] = value
    with pytest.raises(ValueError, match=error):
        audit_net_positions(*inputs)
