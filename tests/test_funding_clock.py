from decimal import Decimal as D

import pytest

from hyperbot2.research.funding_clock import FundingObservation, next_clock_signal
from hyperbot2.research.funding_normalization import event_return
from hyperbot2.research.rotation import HOUR


def test_signal_uses_previous_payment_and_projects_its_interval() -> None:
    signal = next_clock_signal(FundingObservation(15, 8, D("0.001")), 0, 24 * HOUR)
    assert signal is not None
    assert signal.side == 1 and signal.known_ms == 15
    assert signal.expected_payment_ms == 8 * HOUR
    other = next_clock_signal(FundingObservation(20, 4, D("-0.002")), 0, 24 * HOUR)
    assert other is not None and other.side == -1
    assert other.expected_payment_ms == 4 * HOUR


def test_small_rates_and_uncovered_controls_do_not_create_events() -> None:
    assert (
        next_clock_signal(FundingObservation(0, 8, D("0.00099")), 0, 24 * HOUR) is None
    )
    assert next_clock_signal(FundingObservation(0, 8, D("0.001")), 0, 11 * HOUR) is None


@pytest.mark.parametrize(
    "payment",
    [
        FundingObservation(60_001, 8, D("0.001")),
        FundingObservation(0, 1, D("0.001")),
        FundingObservation(0, 8, D("NaN")),
    ],
)
def test_unknown_schedule_or_bad_observation_fails_closed(
    payment: FundingObservation,
) -> None:
    with pytest.raises(ValueError):
        next_clock_signal(payment, 0, 24 * HOUR)


def test_entry_after_settlement_does_not_collect_that_funding() -> None:
    prices = [D(100)] * 12
    payments = {8 * HOUR + 20: D("0.1"), 9 * HOUR + 20: D("0.002")}
    result = event_return(prices, 0, payments, 8, 1, 1, D(0), D(0), "signed")
    assert result["funding_cost_bps"] == 20
    assert result["net_bps"] == -20
