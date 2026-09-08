"""Dollar-hedged ratio exploration with frozen entry statistics and hourly equity."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from decimal import ROUND_FLOOR, Decimal
from typing import Any

from hyperbot2.research.rotation import HOUR
from hyperbot2.research.volume import VolumeBar

D = Decimal
GOLD, SILVER = "xyz:GOLD", "xyz:SILVER"


@dataclass(frozen=True, slots=True)
class RatioFrame:
    mean: Decimal
    sigma: Decimal
    z: Decimal


@dataclass(frozen=True, slots=True)
class RatioPosition:
    side: int
    gold_quantity: Decimal
    silver_quantity: Decimal
    gold_entry: Decimal
    silver_entry: Decimal
    model: RatioFrame
    opened: int
    equity_at_entry: Decimal
    entry_fee: Decimal
    funding_cost: Decimal = D(0)

    def pnl(self, gold: Decimal, silver: Decimal) -> Decimal:
        return self.side * (
            self.gold_quantity * (gold - self.gold_entry)
            - self.silver_quantity * (silver - self.silver_entry)
        )


def ratio_frames(
    log_ratios: Sequence[Decimal], *, lookback: int = 240
) -> tuple[RatioFrame | None, ...]:
    if lookback < 3:
        raise ValueError("at least three past observations required")
    frames: list[RatioFrame | None] = []
    for i, value in enumerate(log_ratios):
        if not value.is_finite():
            raise ValueError("finite log ratios required")
        if i < lookback:
            frames.append(None)
            continue
        past = log_ratios[i - lookback : i]
        mean = sum(past, D(0)) / lookback
        sigma = (sum(((r - mean) ** 2 for r in past), D(0)) / (lookback - 1)).sqrt()
        frames.append(
            RatioFrame(mean, sigma, (value - mean) / sigma)
            if sigma >= D("0.002")
            else None
        )
    return tuple(frames)


def simulate_ratio(
    bars: Mapping[str, Sequence[VolumeBar]],
    funding: Mapping[str, Mapping[int, Decimal]],
    frames: Sequence[RatioFrame | None],
    fees: Mapping[str, Decimal],
    decimals: Mapping[str, int],
    *,
    gross_cap: Decimal,
    scenario: str,
    monthly_infra: Decimal,
    assets: tuple[str, str] = (GOLD, SILVER),
    max_holding_hours: int = 72,
    allowed_entries: frozenset[int] | None = None,
) -> dict[str, Any]:
    # Legacy serialized gold/silver fields refer to first/second respectively.
    # Adapters for other markets must label these fields explicitly in artifacts.
    first, second = assets
    if first == second or max_holding_hours <= 0:
        raise ValueError("distinct assets and a positive holding duration required")
    if gross_cap not in (D("0.5"), D(1), D("1.5")) or monthly_infra not in (
        D(0),
        D(20),
    ):
        raise ValueError("unregistered risk or infrastructure")
    if scenario not in {"base", "cost_stress", "delay", "funding_adverse", "zero_cost"}:
        raise ValueError("unregistered cost scenario")
    times = [b.time for b in bars[first]]
    if (
        not times
        or len(frames) != len(times)
        or any(b - a != HOUR for a, b in zip(times, times[1:], strict=False))
    ):
        raise ValueError("aligned hourly frames required")
    if [b.time for b in bars[second]] != times or any(
        t not in funding[c] for c in (first, second) for t in times
    ):
        raise ValueError("aligned native prices/funding required")
    ratios = [
        (g.close / s.close).ln() for g, s in zip(bars[first], bars[second], strict=True)
    ]
    slip = (
        D(0)
        if scenario == "zero_cost"
        else D("0.0005")
        if scenario == "cost_stress"
        else D("0.0002")
    )
    rates = {
        c: D(0)
        if scenario == "zero_cost"
        else fees[c] * (2 if scenario == "cost_stress" else 1)
        for c in (first, second)
    }
    delay = 1 if scenario == "delay" else 0
    cash = peak = peak_bound = D(1000)
    max_dd = max_bound_dd = D(0)
    underwater = longest = 0
    position: RatioPosition | None = None
    pending_exit: str | None = None
    halted = False
    halt_at = None
    cooldown = 0
    curve: list[dict[str, Any]] = []
    cycles: list[dict[str, Any]] = []
    months: dict[str, Decimal] = {}

    def close(gold: Decimal, silver: Decimal, at: int, reason: str) -> None:
        nonlocal cash, position, cooldown, pending_exit
        assert position is not None
        p = position
        g = gold * (1 - p.side * slip)
        s = silver * (1 + p.side * slip)
        exit_fee = (
            p.gold_quantity * g * rates[first] + p.silver_quantity * s * rates[second]
        )
        gross = p.pnl(g, s)
        cash += gross - exit_fee
        cycles.append(
            {
                "opened_ms": p.opened,
                "closed_ms": at,
                "side_gold": p.side,
                "gold_quantity": p.gold_quantity,
                "silver_quantity": p.silver_quantity,
                "gold_entry": p.gold_entry,
                "silver_entry": p.silver_entry,
                "gold_exit": g,
                "silver_exit": s,
                "entry_mean": p.model.mean,
                "entry_sigma": p.model.sigma,
                "entry_z": p.model.z,
                "gross_pnl": gross,
                "fees": p.entry_fee + exit_fee,
                "funding_cost": p.funding_cost,
                "net_pnl": gross - p.entry_fee - exit_fee - p.funding_cost,
                "reason": reason,
            }
        )
        position = None
        pending_exit = None
        cooldown = at + 24 * HOUR

    for i, at in enumerate(times):
        g, s = bars[first][i], bars[second][i]
        cash -= monthly_infra / 720
        source = i - 1 - delay
        if position is not None:
            p = position
            signed = p.side * (
                p.gold_quantity * g.open * funding[first][at]
                - p.silver_quantity * s.open * funding[second][at]
            )
            adverse = p.gold_quantity * g.open * abs(
                funding[first][at]
            ) + p.silver_quantity * s.open * abs(funding[second][at])
            charge = (
                D(0)
                if scenario == "zero_cost"
                else adverse
                if scenario == "funding_adverse"
                else signed
            )
            cash -= charge
            position = replace(p, funding_cost=p.funding_cost + charge)
        open_equity = cash + (position.pnl(g.open, s.open) if position else D(0))
        peak_bound = max(peak_bound, open_equity)
        if position is not None:
            p = position
            z = (ratios[source] - p.model.mean) / p.model.sigma if source >= 0 else None
            reason = pending_exit
            if halted:
                reason = "drawdown_next_open"
            elif at - p.opened >= max_holding_hours * HOUR:
                reason = reason or "time"
            elif z is not None:
                if p.side * z <= D("-4"):
                    reason = reason or "ratio_stop"
                elif p.side * z >= D("-0.5"):
                    reason = reason or "convergence"
            if reason is not None:
                close(g.open, s.open, at, reason)
        if (
            not halted
            and position is None
            and at >= cooldown
            and (allowed_entries is None or at in allowed_entries)
            and source >= 0
            and g.volume > 0
            and s.volume > 0
        ):
            frame = frames[source]
            if frame is not None and D(2) <= abs(frame.z) < 4 and cash > 0:
                side = -1 if frame.z > 0 else 1
                gp, sp = g.open * (1 + side * slip), s.open * (1 - side * slip)
                notional = cash * gross_cap / 2
                gs, ss = D(10) ** (-decimals[first]), D(10) ** (-decimals[second])
                gq = (notional / gp / gs).to_integral_value(rounding=ROUND_FLOOR) * gs
                sq = (notional / sp / ss).to_integral_value(rounding=ROUND_FLOOR) * ss
                if min(gq * gp, sq * sp) >= 10:
                    fee = gq * gp * rates[first] + sq * sp * rates[second]
                    balance = cash
                    cash -= fee
                    position = RatioPosition(
                        side, gq, sq, gp, sp, frame, at, balance, fee
                    )
        adverse_equity = favorable_equity = cash
        if position is not None:
            p = position
            adverse_equity += p.pnl(
                g.low if p.side == 1 else g.high, s.high if p.side == 1 else s.low
            )
            favorable_equity += p.pnl(
                g.high if p.side == 1 else g.low, s.low if p.side == 1 else s.high
            )
        peak_bound = max(peak_bound, favorable_equity)
        if i == len(times) - 1 and position is not None:
            close(g.close, s.close, at + HOUR, "terminal")
        marked = cash + (position.pnl(g.close, s.close) if position else D(0))
        peak = max(peak, marked)
        dd = 1 - marked / peak
        max_dd = max(max_dd, dd)
        peak_bound = max(peak_bound, marked)
        bound_dd = 1 - min(open_equity, adverse_equity, marked) / peak_bound
        max_bound_dd = max(max_bound_dd, bound_dd)
        underwater = underwater + 1 if marked < peak else 0
        longest = max(longest, underwater)
        if not halted and dd >= D("0.2"):
            halted = True
            halt_at = at + HOUR
        if position is not None:
            total = (
                position.pnl(g.close, s.close)
                - position.entry_fee
                - position.funding_cost
            )
            if total <= -D("0.03") * position.equity_at_entry:
                pending_exit = "pair_loss_next_open"
        curve.append(
            {
                "time_ms": at + HOUR,
                "equity": marked,
                "cash": cash,
                "unrealized_pnl": marked - cash,
                "drawdown": dd,
                "drawdown_envelope": bound_dd,
                "adverse_equity_envelope": adverse_equity,
                "gross_notional": position.gold_quantity * g.close
                + position.silver_quantity * s.close
                if position
                else D(0),
                "position_open": position is not None,
                "halted": halted,
            }
        )
        months[
            datetime.fromtimestamp((at + HOUR - 1) / 1000, UTC).strftime("%Y-%m")
        ] = marked
    infra = monthly_infra * len(times) / 720
    if abs(cash - 1000 + infra - sum((c["net_pnl"] for c in cycles), D(0))) > D(
        "1e-18"
    ):
        raise ValueError("portfolio accounting does not reconcile")
    previous = D(1000)
    monthly: list[dict[str, Any]] = []
    for month, e in months.items():
        monthly.append(
            {
                "month": month,
                "pnl_usd": e - previous,
                "return": e / previous - 1 if previous > 0 else None,
            }
        )
        previous = e
    days = D(len(times)) / 24
    summary = {
        "gross_cap": gross_cap,
        "scenario": scenario,
        "monthly_infra": monthly_infra,
        "days": days,
        "round_trips": len(cycles),
        "end_equity": cash,
        "net_total_usd": cash - 1000,
        "net_trading_usd": cash - 1000 + infra,
        "infrastructure_usd": infra,
        "equivalent_monthly_compound": (cash / 1000) ** (D(30) / days) - 1
        if cash > 0
        else None,
        "max_hourly_drawdown": max_dd,
        "max_ohlc_drawdown_envelope": max_bound_dd,
        "hourly_drawdown_le_20pct": max_dd <= D("0.2"),
        "ohlc_envelope_le_20pct": max_bound_dd <= D("0.2"),
        "longest_underwater_days": D(longest) / 24,
        "unrecovered_at_end_days": D(underwater) / 24,
        "green_months": sum(v["pnl_usd"] > 0 for v in monthly),
        "red_months": sum(v["pnl_usd"] < 0 for v in monthly),
        "months": monthly,
        "halted": halted,
        "halt_at_ms": halt_at,
        "live_enabled": False,
        "promotion_authorized": False,
    }
    return {"summary": summary, "cycles": cycles, "curve": curve}
