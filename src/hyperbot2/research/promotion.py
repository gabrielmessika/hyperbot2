"""Explicit research review gates; this module can never authorize live trading."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from hyperbot2.models import DatasetTier


@dataclass(frozen=True, slots=True)
class PromotionEvidence:
    tiers: tuple[DatasetTier, ...] = ()
    continuous_days: int = 0
    completeness: Decimal = Decimal(0)
    distinct_settlement_ids: tuple[str, ...] = ()
    round_trip_pnls: tuple[Decimal, ...] = ()
    fold_pnls: tuple[Decimal, ...] = ()
    bootstrap_lower_usd: Decimal = Decimal(0)
    drawdown_fraction: Decimal = Decimal(1)
    maximum_underlying_contribution: Decimal = Decimal(1)
    central_pnl: Decimal = Decimal(0)
    pessimistic_pnl: Decimal = Decimal(-1)
    double_fee_pnl: Decimal = Decimal(-1)
    double_latency_pnl: Decimal = Decimal(-1)
    queue_qualified: bool = False
    oos_locked: bool = False
    shadow_days: int = 0
    risk_violations: int = 0
    account_actions_qualified: bool = False


def evaluate_promotion(e: PromotionEvidence) -> tuple[str, ...]:
    values = (
        *e.round_trip_pnls,
        *e.fold_pnls,
        e.completeness,
        e.bootstrap_lower_usd,
        e.drawdown_fraction,
        e.maximum_underlying_contribution,
        e.central_pnl,
        e.pessimistic_pnl,
        e.double_fee_pnl,
        e.double_latency_pnl,
    )
    if any(not x.is_finite() for x in values):
        raise ValueError("non-finite promotion evidence")
    reasons = []
    if not e.tiers or any(t is not DatasetTier.A for t in e.tiers):
        reasons.append("tier_a_required")
    if e.continuous_days < 30 or not Decimal("0.99") <= e.completeness <= 1:
        reasons.append("continuous_coverage_missing")
    if len(set(e.distinct_settlement_ids)) < 300:
        reasons.append("fewer_than_300_distinct_terminal_settlements")
    if len(e.round_trip_pnls) < 500:
        reasons.append("fewer_than_500_round_trips")
    gains = sum((x for x in e.round_trip_pnls if x > 0), Decimal(0))
    losses = -sum((x for x in e.round_trip_pnls if x < 0), Decimal(0))
    if gains <= 0 or (losses and gains / losses <= Decimal("1.20")):
        reasons.append("cycle_profit_factor_failed")
    if len(e.fold_pnls) < 3 or any(x <= 0 for x in e.fold_pnls):
        reasons.append("three_positive_oos_folds_required")
    if e.bootstrap_lower_usd <= 0:
        reasons.append("bootstrap_lower_bound_not_positive")
    if not 0 <= e.drawdown_fraction < Decimal("0.10"):
        reasons.append("drawdown_failed")
    if not 0 <= e.maximum_underlying_contribution <= Decimal("0.40"):
        reasons.append("concentration_failed")
    if (
        e.central_pnl <= 0
        or min(e.pessimistic_pnl, e.double_fee_pnl, e.double_latency_pnl) < 0
    ):
        reasons.append("execution_stress_failed")
    if not e.queue_qualified or not e.oos_locked:
        reasons.append("causal_execution_or_oos_missing")
    if not e.account_actions_qualified:
        reasons.append("account_action_limits_unqualified")
    if e.shadow_days < 14 or e.risk_violations:
        reasons.append("shadow_gate_failed")
    # An empty tuple only means eligible for a human safety review, never live.
    return tuple(reasons)
