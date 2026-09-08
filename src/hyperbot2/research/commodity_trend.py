"""Hourly research portfolio with causal signals, latent PnL and explicit costs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from decimal import ROUND_FLOOR, Decimal
from typing import Any

from hyperbot2.research.rotation import HOUR
from hyperbot2.research.volume import VolumeBar

D = Decimal


@dataclass(frozen=True, slots=True)
class TrendFrame:
    side: int
    distance: Decimal


@dataclass(frozen=True, slots=True)
class TrendPosition:
    side: int
    quantity: Decimal
    price: Decimal
    stop: Decimal
    opened: int
    entry_fee: Decimal
    funding: Decimal = D(0)


def trend_frames(bars: Sequence[VolumeBar]) -> tuple[TrendFrame, ...]:
    frames = []
    for i, bar in enumerate(bars):
        if i < 240:
            frames.append(TrendFrame(0, D(0)))
            continue
        past = bars[i - 240 : i]
        side = (
            1
            if bar.close > max(b.high for b in past)
            else -1
            if bar.close < min(b.low for b in past)
            else 0
        )
        atr = (
            sum(
                (
                    max(
                        bars[j].high - bars[j].low,
                        abs(bars[j].high - bars[j - 1].close),
                        abs(bars[j].low - bars[j - 1].close),
                    )
                    for j in range(i - 23, i + 1)
                ),
                D(0),
            )
            / 24
        )
        frames.append(TrendFrame(side if bar.volume > 0 else 0, 3 * atr))
    return tuple(frames)


def simulate_trend(
    bars: Mapping[str, Sequence[VolumeBar]],
    funding: Mapping[str, Mapping[int, Decimal]],
    frames: Mapping[str, Sequence[TrendFrame]],
    fees: Mapping[str, Decimal],
    decimals: Mapping[str, int],
    *,
    gross_cap: Decimal,
    scenario: str,
    monthly_infra: Decimal,
) -> dict[str, Any]:
    if gross_cap not in (D("0.5"), D(1), D("1.5")) or monthly_infra not in (
        D(0),
        D(20),
    ):
        raise ValueError("unregistered risk or infrastructure scenario")
    if scenario not in {"base", "cost_stress", "delay", "funding_adverse", "zero_cost"}:
        raise ValueError("unregistered cost scenario")
    coins = tuple(bars)
    times = [b.time for b in bars[coins[0]]]
    if not times or any(b - a != HOUR for a, b in zip(times, times[1:], strict=False)):
        raise ValueError("continuous hourly series required")
    if any(
        [b.time for b in bars[c]] != times
        or len(frames[c]) != len(times)
        or any(t not in funding[c] for t in times)
        for c in coins
    ):
        raise ValueError("aligned prices, frames and funding required")
    positions: dict[str, TrendPosition] = {}
    cooldown: dict[str, int] = {}
    cash = peak = peak_bound = D(1000)
    max_dd = max_bound_dd = D(0)
    underwater = longest_underwater = 0
    halted = False
    halt_at = None
    cycles: list[dict[str, Any]] = []
    curve: list[dict[str, Any]] = []
    monthly_last: dict[str, Decimal] = {}
    delay = 1 if scenario == "delay" else 0
    slip = (
        D(0)
        if scenario == "zero_cost"
        else D("0.0005")
        if scenario == "cost_stress"
        else D("0.0002")
    )
    fee_rates = {
        c: D(0)
        if scenario == "zero_cost"
        else fees[c] * (2 if scenario == "cost_stress" else 1)
        for c in coins
    }

    def equity(index: int, field: str) -> Decimal:
        return cash + sum(
            (
                p.side * p.quantity * (getattr(bars[c][index], field) - p.price)
                for c, p in positions.items()
            ),
            D(0),
        )

    def close(coin: str, raw: Decimal, at: int, reason: str) -> None:
        nonlocal cash
        p = positions.pop(coin)
        execution = raw * (1 - p.side * slip)
        exit_fee = p.quantity * execution * fee_rates[coin]
        gross = p.side * p.quantity * (execution - p.price)
        cash += gross - exit_fee
        cooldown[coin] = at + 24 * HOUR
        cycles.append(
            {
                "coin": coin,
                "side": p.side,
                "opened_ms": p.opened,
                "closed_ms": at,
                "quantity": p.quantity,
                "entry_price": p.price,
                "exit_price": execution,
                "gross_pnl": gross,
                "fees": p.entry_fee + exit_fee,
                "funding_cost": p.funding,
                "net_pnl": gross - p.entry_fee - exit_fee - p.funding,
                "reason": reason,
            }
        )

    for i, at in enumerate(times):
        cash -= monthly_infra / 720
        for coin, p in tuple(positions.items()):
            rate = funding[coin][at]
            charge = (
                D(0)
                if scenario == "zero_cost"
                else p.quantity
                * bars[coin][i].open
                * (abs(rate) if scenario == "funding_adverse" else p.side * rate)
            )
            cash -= charge
            positions[coin] = replace(p, funding=p.funding + charge)
        open_equity = equity(i, "open")
        peak_bound = max(peak_bound, open_equity)
        if halted:
            for coin in tuple(positions):
                close(coin, bars[coin][i].open, at, "drawdown_next_open")
        else:
            for coin, p in tuple(positions.items()):
                if at - p.opened >= 168 * HOUR:
                    close(coin, bars[coin][i].open, at, "time")
            for coin in coins:
                source = i - 1 - delay
                if (
                    source < 0
                    or coin in positions
                    or at < cooldown.get(coin, 0)
                    or bars[coin][i].volume <= 0
                ):
                    continue
                frame = frames[coin][source]
                if not frame.side or frame.distance <= 0:
                    continue
                balance = equity(i, "open")
                if balance <= 0:
                    continue
                entry = bars[coin][i].open * (1 + frame.side * slip)
                gross = sum(
                    (p.quantity * bars[c][i].open for c, p in positions.items()), D(0)
                )
                cap = min(
                    balance * gross_cap / 3, max(D(0), balance * gross_cap - gross)
                )
                qty = min(balance * D("0.01") / frame.distance, cap / entry)
                step = D(10) ** (-decimals[coin])
                qty = (qty / step).to_integral_value(rounding=ROUND_FLOOR) * step
                if qty * entry < 10 or entry - frame.side * frame.distance <= 0:
                    continue
                fee = qty * entry * fee_rates[coin]
                cash -= fee
                positions[coin] = TrendPosition(
                    frame.side, qty, entry, entry - frame.side * frame.distance, at, fee
                )
        # Independent OHLC extrema give an adverse envelope, not an observed path.
        favorable = cash + sum(
            (
                p.side
                * p.quantity
                * ((bars[c][i].high if p.side == 1 else bars[c][i].low) - p.price)
                for c, p in positions.items()
            ),
            D(0),
        )
        adverse = cash + sum(
            (
                p.side
                * p.quantity
                * ((bars[c][i].low if p.side == 1 else bars[c][i].high) - p.price)
                for c, p in positions.items()
            ),
            D(0),
        )
        peak_bound = max(peak_bound, favorable)
        for coin, p in tuple(positions.items()):
            bar = bars[coin][i]
            raw = (
                min(p.stop, bar.open)
                if p.side == 1 and bar.low <= p.stop
                else max(p.stop, bar.open)
                if p.side == -1 and bar.high >= p.stop
                else None
            )
            if raw is not None:
                close(coin, raw, at + HOUR - 1, "stop_within_hour_unknown")
        if i == len(times) - 1:
            for coin in tuple(positions):
                close(coin, bars[coin][i].close, at + HOUR, "terminal")
        marked = equity(i, "close")
        peak = max(peak, marked)
        drawdown = 1 - marked / peak
        max_dd = max(max_dd, drawdown)
        peak_bound = max(peak_bound, marked)
        bound_dd = 1 - min(adverse, open_equity, marked) / peak_bound
        max_bound_dd = max(max_bound_dd, bound_dd)
        if marked < peak:
            underwater += 1
            longest_underwater = max(longest_underwater, underwater)
        else:
            underwater = 0
        if not halted and drawdown >= D("0.2"):
            halted = True
            halt_at = at + HOUR
        for coin, p in tuple(positions.items()):
            distance = frames[coin][i].distance
            if distance > 0:
                proposed = bars[coin][i].close - p.side * distance
                stop = max(p.stop, proposed) if p.side == 1 else min(p.stop, proposed)
                positions[coin] = replace(p, stop=stop)
        curve.append(
            {
                "time_ms": at + HOUR,
                "equity": marked,
                "cash": cash,
                "unrealized_pnl": marked - cash,
                "drawdown": drawdown,
                "adverse_equity_envelope": adverse,
                "drawdown_envelope": bound_dd,
                "gross_notional": sum(
                    (p.quantity * bars[c][i].close for c, p in positions.items()), D(0)
                ),
                "positions": len(positions),
                "halted": halted,
            }
        )
        month = datetime.fromtimestamp((at + HOUR - 1) / 1000, UTC).strftime("%Y-%m")
        monthly_last[month] = marked
    infra = monthly_infra * len(times) / 720
    if abs(cash - 1000 + infra - sum((c["net_pnl"] for c in cycles), D(0))) > D(
        "1e-18"
    ):
        raise ValueError("cash, costs and cycles do not reconcile")
    previous = D(1000)
    months: list[dict[str, Any]] = []
    for month, value in monthly_last.items():
        months.append(
            {
                "month": month,
                "pnl_usd": value - previous,
                "return": value / previous - 1 if previous > 0 else None,
            }
        )
        previous = value
    days = D(len(times)) / 24
    monthly_compound = (cash / 1000) ** (D(30) / days) - 1 if cash > 0 else None
    summary = {
        "gross_cap": gross_cap,
        "scenario": scenario,
        "monthly_infra": monthly_infra,
        "hours": len(times),
        "days": days,
        "round_trips": len(cycles),
        "end_equity": cash,
        "net_trading_usd": cash - 1000 + infra,
        "infrastructure_usd": infra,
        "net_total_usd": cash - 1000,
        "equivalent_monthly_compound": monthly_compound,
        "max_hourly_drawdown": max_dd,
        "max_ohlc_drawdown_envelope": max_bound_dd,
        "hourly_drawdown_le_20pct": max_dd <= D("0.2"),
        "ohlc_envelope_le_20pct": max_bound_dd <= D("0.2"),
        "longest_underwater_days": D(longest_underwater) / 24,
        "unrecovered_at_end_days": D(underwater) / 24,
        "months": months,
        "green_months": sum(m["pnl_usd"] > 0 for m in months),
        "red_months": sum(m["pnl_usd"] < 0 for m in months),
        "halted": halted,
        "halt_at_ms": halt_at,
        "live_enabled": False,
        "promotion_authorized": False,
    }
    return {"summary": summary, "cycles": cycles, "curve": curve}
