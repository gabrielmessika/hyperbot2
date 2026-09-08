from decimal import Decimal as D

import pytest

from hyperbot2.research.funding_normalization import event_return, normalization
from hyperbot2.research.rotation import HOUR


@pytest.mark.parametrize("sign", [-1, 1])
def test_signal_uses_completed_funding_only(sign: int) -> None:
    rates = [D(sign) * D("0.0001")] * 8 + [D(sign) * D("0.00002")] * 4
    assert normalization(rates + [D(999)], 12) == sign
    assert normalization(rates + [D(-999)], 12) == sign
    assert normalization([D(sign) * D("0.00001")] * 12, 12) == 0


def test_payment_boundaries_preserve_signed_and_adverse_funding() -> None:
    opens = [D(100)] * 4
    payments = {
        HOUR + 10: D("0.5"),  # Paid before the assumed entry at +60 seconds.
        HOUR + 60_000: D("0.5"),  # Entry instant is excluded.
        2 * HOUR + 10: D("0.001"),
        2 * HOUR + 60_000: D("0.002"),  # Exit instant is included.
        2 * HOUR + 60_001: D("0.5"),
    }
    short = event_return(opens, 0, payments, 1, 1, -1, D(0), D(0), "signed")
    adverse = event_return(opens, 0, payments, 1, 1, -1, D(0), D(0), "adverse")
    assert short["net_bps"] == 30
    assert adverse["net_bps"] == -30


def test_normalization_rejects_large_opposite_regime() -> None:
    assert normalization([D("0.0001")] * 8 + [D("-0.0001")] * 4, 12) == 0
    with pytest.raises(ValueError):
        normalization([D(0)] * 11, 11)
