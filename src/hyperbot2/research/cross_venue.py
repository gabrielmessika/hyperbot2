"""Equal-coin-quantity, opposing USDC perpetual legs for offline research."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal

D = Decimal


def paired_return(
    hl_opens: Sequence[Decimal],
    bn_opens: Sequence[Decimal],
    hl_rates: Sequence[Decimal],
    bn_payments: Mapping[int, tuple[Decimal, Decimal]],
    index: int,
    horizon: int,
    side: int,
    fee_hl: Decimal,
    fee_bn: Decimal,
    slip: Decimal,
    funding_mode: str,
) -> dict[str, Decimal]:
    """One coin each side, divided by total executed entry notional.

    Binance payment keys are milliseconds since the first candle open.
    Funding at entry is excluded; funding at exit is included.
    """
    if side not in (-1, 1) or funding_mode not in ("signed", "adverse", "zero"):
        raise ValueError("invalid side/funding mode")
    if horizon <= 0 or not all(0 <= c < 1 for c in (fee_hl, fee_bn, slip)):
        raise ValueError("invalid holding period/cost")
    end = index + horizon
    h_in, h_out = hl_opens[index] * (1 + side * slip), hl_opens[end] * (1 - side * slip)
    b_in, b_out = bn_opens[index] * (1 - side * slip), bn_opens[end] * (1 + side * slip)
    notional = h_in + b_in
    gross = side * (hl_opens[end] - hl_opens[index] - bn_opens[end] + bn_opens[index])
    trading = side * (h_out - h_in - b_out + b_in)
    fees = (h_in + h_out) * fee_hl + (b_in + b_out) * fee_bn
    funding = D(0)
    if funding_mode != "zero":
        for t in range(index + 1, end + 1):
            rate_h = side * hl_rates[t]
            if funding_mode == "adverse":
                rate_h = abs(rate_h)
            funding += rate_h * hl_opens[t]
        for at, (rate_b, mark_b) in bn_payments.items():
            if index * 3600000 < at <= end * 3600000:
                signed = abs(rate_b) if funding_mode == "adverse" else -side * rate_b
                funding += signed * mark_b
    return {
        "gross_bps": gross / notional * 10000,
        "slippage_bps": (gross - trading) / notional * 10000,
        "fees_bps": fees / notional * 10000,
        "funding_cost_bps": funding / notional * 10000,
        "net_bps": (trading - fees - funding) / notional * 10000,
    }
