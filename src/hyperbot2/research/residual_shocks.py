"""Causal six-hour return shock relative to a prior BTC hedge model."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from hyperbot2.research.return_hedge import ReturnHedge, fit_return_hedge


def residual_shock(
    asset_logs: Sequence[Decimal], hedge_logs: Sequence[Decimal], entry_index: int
) -> tuple[ReturnHedge, Decimal] | None:
    if entry_index < 175 or min(len(asset_logs), len(hedge_logs)) < entry_index:
        raise ValueError("28 prior six-hour returns plus a completed signal required")
    endpoints = [entry_index - 7 - 6 * k for k in reversed(range(28))]
    model = fit_return_hedge(
        [asset_logs[j] - asset_logs[j - 6] for j in endpoints],
        [hedge_logs[j] - hedge_logs[j - 6] for j in endpoints],
    )
    if model is None:
        return None
    z = model.score(
        asset_logs[entry_index - 1] - asset_logs[entry_index - 7],
        hedge_logs[entry_index - 1] - hedge_logs[entry_index - 7],
    )
    return model, z
