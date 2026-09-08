"""Unfitted rolling return hedge and fixed-total-notional research accounting."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from hyperbot2.research.rotation import leg_return

D = Decimal


@dataclass(frozen=True, slots=True)
class ReturnHedge:
    alpha: Decimal
    beta: Decimal
    sigma: Decimal
    correlation: Decimal

    def score(self, asset_return: Decimal, hedge_return: Decimal) -> Decimal:
        return (asset_return - self.alpha - self.beta * hedge_return) / self.sigma


def fit_return_hedge(
    asset_returns: Sequence[Decimal], hedge_returns: Sequence[Decimal]
) -> ReturnHedge | None:
    n = len(asset_returns)
    if n != len(hedge_returns) or n < 3:
        raise ValueError(
            "aligned return samples with residual degrees of freedom required"
        )
    if any(not x.is_finite() for x in (*asset_returns, *hedge_returns)):
        raise ValueError("finite returns required")
    mean_y = sum(asset_returns, D(0)) / n
    mean_x = sum(hedge_returns, D(0)) / n
    xs = [x - mean_x for x in hedge_returns]
    ys = [y - mean_y for y in asset_returns]
    xx = sum((x * x for x in xs), D(0))
    yy = sum((y * y for y in ys), D(0))
    if xx <= 0 or yy <= 0:
        return None
    xy = sum((x * y for x, y in zip(xs, ys, strict=True)), D(0))
    beta = xy / xx
    alpha = mean_y - beta * mean_x
    residual = [
        y - alpha - beta * x for y, x in zip(asset_returns, hedge_returns, strict=True)
    ]
    variance = sum((r * r for r in residual), D(0)) / (n - 2)
    if variance <= D("1e-40"):
        return None
    return ReturnHedge(alpha, beta, variance.sqrt(), xy / (xx * yy).sqrt())


def hedged_return(
    asset_opens: Sequence[Decimal],
    hedge_opens: Sequence[Decimal],
    asset_rates: Sequence[Decimal],
    hedge_rates: Sequence[Decimal],
    *,
    index: int,
    horizon: int,
    side: int,
    beta: Decimal,
    asset_fee: Decimal,
    hedge_fee: Decimal,
    asset_slip: Decimal,
    hedge_slip: Decimal,
    funding_mode: str,
) -> dict[str, object]:
    if not beta.is_finite() or beta <= 0:
        raise ValueError("positive finite hedge ratio required")
    asset = leg_return(
        asset_opens,
        asset_rates,
        index,
        horizon,
        side,
        asset_fee,
        asset_slip,
        funding_mode,
    )
    hedge = leg_return(
        hedge_opens,
        hedge_rates,
        index,
        horizon,
        -side,
        hedge_fee,
        hedge_slip,
        funding_mode,
    )
    asset_weight = 1 / (1 + beta)
    hedge_weight = 1 - asset_weight
    return {
        "asset_weight": asset_weight,
        "hedge_weight": hedge_weight,
        "asset": asset,
        "hedge": hedge,
        "basket": {
            key: asset_weight * asset[key] + hedge_weight * hedge[key] for key in asset
        },
    }
