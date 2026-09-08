"""Past-only funding normalization and timestamp-aware event accounting."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal

from hyperbot2.research.rotation import HOUR, leg_return

D = Decimal


def normalization(rates: Sequence[Decimal], entry_index: int) -> int:
    """Return the original funding sign; never inspect entry-hour funding."""
    if entry_index < 12 or entry_index > len(rates):
        raise ValueError("twelve completed hours required")
    old = sum(rates[entry_index - 12 : entry_index - 4], D(0)) / 8
    recent = sum(rates[entry_index - 4 : entry_index], D(0)) / 4
    if not old.is_finite() or not recent.is_finite():
        raise ValueError("non-finite funding")
    if abs(old) < D("0.00005") or not D("-0.25") <= recent / old <= D("0.5"):
        return 0
    return 1 if old > 0 else -1


def event_return(
    opens: Sequence[Decimal],
    start_ms: int,
    payments: Mapping[int, Decimal],
    entry_index: int,
    horizon: int,
    side: int,
    fee: Decimal,
    slip: Decimal,
    funding_mode: str,
) -> dict[str, Decimal]:
    """Reuse price/fee accounting; include only payments while actually held."""
    if funding_mode not in {"signed", "adverse", "zero"}:
        raise ValueError("unknown funding mode")
    result = leg_return(opens, (), entry_index, horizon, side, fee, slip, "zero")
    entry_ms = start_ms + entry_index * HOUR + 60_000
    exit_ms = entry_ms + horizon * HOUR
    quantity = 1 / (opens[entry_index] * (1 + side * slip))
    cost = D(0)
    if funding_mode != "zero":
        for at, rate in payments.items():
            if entry_ms < at <= exit_ms:
                if not rate.is_finite():
                    raise ValueError("non-finite funding payment")
                price = opens[(at - start_ms) // HOUR]
                cost += (
                    quantity
                    * price
                    * (side * rate if funding_mode == "signed" else abs(rate))
                )
    result["funding_cost_bps"] = cost * 10000
    result["net_bps"] -= cost * 10000
    return result
