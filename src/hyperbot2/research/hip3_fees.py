"""Undiscounted HIP-3 fees from explicit public market metadata."""

from __future__ import annotations

from decimal import Decimal

D = Decimal


def taker_fee(*, deployer_fee_scale: Decimal, growth_mode: str | None) -> Decimal:
    if not deployer_fee_scale.is_finite() or not D(0) <= deployer_fee_scale <= 10:
        raise ValueError("unsupported deployer fee scale")
    if growth_mode not in (None, "disabled", "enabled"):
        raise ValueError("unknown growth-mode state")
    scale = 1 + deployer_fee_scale if deployer_fee_scale < 1 else 2 * deployer_fee_scale
    growth = D("0.1") if growth_mode == "enabled" else D(1)
    return D("0.00045") * scale * growth


def reprice_fees(result: dict[str, Decimal], ratio: Decimal) -> dict[str, Decimal]:
    if not ratio.is_finite() or ratio < 0:
        raise ValueError("finite nonnegative fee ratio required")
    adjusted = dict(result)
    adjusted["fees_bps"] = result["fees_bps"] * ratio
    adjusted["net_bps"] = result["net_bps"] + result["fees_bps"] - adjusted["fees_bps"]
    return adjusted
