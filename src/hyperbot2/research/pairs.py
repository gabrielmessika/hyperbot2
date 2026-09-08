"""Frozen BTC/ETH relative-value features for exploratory research only."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PairModel:
    alpha: float
    beta: float
    sigma: float
    return_correlation: float
    residual_phi: float
    descriptive_half_life_hours: float | None

    def z(self, log_btc: float, log_eth: float) -> float:
        return (log_eth - self.alpha - self.beta * log_btc) / self.sigma


def covariance(x: list[float], y: list[float]) -> float:
    mx, my = sum(x) / len(x), sum(y) / len(y)
    return sum((a - mx) * (b - my) for a, b in zip(x, y, strict=True))


def fit_pair(log_btc: list[float], log_eth: list[float]) -> PairModel:
    if len(log_btc) != len(log_eth) or len(log_btc) < 4:
        raise ValueError("aligned training observations required")
    if not all(math.isfinite(v) for v in (*log_btc, *log_eth)):
        raise ValueError("finite training observations required")
    vx = covariance(log_btc, log_btc)
    if vx <= 1e-24:
        raise ValueError("degenerate BTC variation")
    beta = covariance(log_btc, log_eth) / vx
    alpha = (sum(log_eth) - beta * sum(log_btc)) / len(log_btc)
    residual = [y - alpha - beta * x for x, y in zip(log_btc, log_eth, strict=True)]
    sigma = math.sqrt(sum(r * r for r in residual) / (len(residual) - 2))
    if sigma <= 1e-12:
        raise ValueError("degenerate residual scale")
    rx = [b - a for a, b in zip(log_btc, log_btc[1:], strict=False)]
    ry = [b - a for a, b in zip(log_eth, log_eth[1:], strict=False)]
    denominator = math.sqrt(covariance(rx, rx) * covariance(ry, ry))
    correlation = covariance(rx, ry) / denominator if denominator else 0.0
    lag_variance = covariance(residual[:-1], residual[:-1])
    phi = (
        covariance(residual[:-1], residual[1:]) / lag_variance if lag_variance else 0.0
    )
    half_life = -math.log(2) / math.log(phi) if 0 < phi < 1 else None
    return PairModel(alpha, beta, sigma, correlation, phi, half_life)


def model_at(log_btc: list[float], log_eth: list[float], index: int) -> PairModel:
    """Exclude the signal bar and all future bars from a 720-hour fit."""
    if index < 720 or index >= min(len(log_btc), len(log_eth)):
        raise ValueError("720 past observations and a signal bar required")
    return fit_pair(log_btc[index - 720 : index], log_eth[index - 720 : index])
