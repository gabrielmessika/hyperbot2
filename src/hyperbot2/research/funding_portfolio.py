"""Continuous fixed-horizon research portfolio, with latent risk and native lots."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from decimal import ROUND_FLOOR, Decimal
from typing import Any

from hyperbot2.research.funding_normalization import normalization
from hyperbot2.research.rotation import HOUR
from hyperbot2.research.volume import VolumeBar

D = Decimal
DEFAULT_DRAWDOWN_LIMIT = D("0.2")


@dataclass(frozen=True, slots=True)
class AllocationSleeve:
    fraction: Decimal
    holding_hours: int | None


@dataclass(frozen=True, slots=True)
class HeldPosition:
    side: int
    quantity: Decimal
    price: Decimal
    opened_ms: int
    entry_fee: Decimal
    funding_cost: Decimal = D(0)


def sleeve_budgets(
    specs: Mapping[str, AllocationSleeve],
    names: Mapping[str, str],
    eligible: Sequence[str],
    used: Mapping[str, Decimal],
    gross_cap: Decimal,
    conservative_balance: Decimal,
    available: Decimal,
) -> dict[str, Decimal]:
    """Separate fixed sleeve budgets; never lend an inactive sleeve's capital."""
    capacities = {
        name: max(D(0), gross_cap * spec.fraction * conservative_balance - used[name])
        if any(names[c] == name for c in eligible)
        else D(0)
        for name, spec in specs.items()
    }
    requested = sum(capacities.values(), D(0))
    scale = min(D(1), available / requested) if requested else D(0)
    result = {}
    for name, spec in specs.items():
        count = sum(names[c] == name for c in eligible)
        result[name] = (
            min(
                capacities[name] * scale / count,
                gross_cap * spec.fraction * conservative_balance / 3,
            )
            if count
            else D(0)
        )
    return result


def funding_entries(rates: Sequence[Decimal]) -> tuple[int, ...]:
    """Preserve event spacing continuously across prior/discovery boundaries."""
    output = [0] * len(rates)
    previous = next_allowed = 0
    for i in range(12, len(rates) - 73):
        signal = normalization(rates, i)
        if signal and not previous and i >= next_allowed:
            output[i] = signal
            next_allowed = i + 73
        previous = signal
    return tuple(output)


def simulate_portfolio(
    bars: Mapping[str, Sequence[VolumeBar]],
    payments: Mapping[str, Mapping[int, Decimal]],
    entries: Mapping[str, Sequence[int]],
    decimals: Mapping[str, int],
    *,
    gross_cap: Decimal,
    scenario: str,
    monthly_infra: Decimal,
    holding_hours: int | None = 72,
    drawdown_limit: Decimal = DEFAULT_DRAWDOWN_LIMIT,
    allocation_sleeves: Mapping[str, AllocationSleeve] | None = None,
    asset_sleeves: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    if drawdown_limit not in (D("0.2"), D("0.3")):
        raise ValueError("unregistered drawdown limit")
    if gross_cap not in (
        D("0.4"),
        D("0.5"),
        D(1),
        D("1.5"),
        D(2),
    ) or monthly_infra not in (
        D(0),
        D(20),
    ):
        raise ValueError("unregistered allocation/infra scenario")
    if scenario not in {"base", "cost_stress", "delay", "funding_adverse", "zero_cost"}:
        raise ValueError("unknown cost scenario")
    if holding_hours is not None and holding_hours <= 0:
        raise ValueError("positive holding horizon required")
    coins = tuple(sorted(bars))
    if not coins:
        raise ValueError("empty asset universe")
    if (allocation_sleeves is None) != (asset_sleeves is None):
        raise ValueError("both sleeve definitions and asset mapping required")
    sleeve_names: dict[str, str] = dict(asset_sleeves or {})
    specs = dict(allocation_sleeves or {})
    if allocation_sleeves is not None and (
        set(sleeve_names) != set(coins)
        or set(sleeve_names.values()) != set(specs)
        or any(
            not s.fraction.is_finite()
            or s.fraction <= 0
            or (s.holding_hours is not None and s.holding_hours <= 0)
            for s in specs.values()
        )
        or sum((s.fraction for s in specs.values()), D(0)) != 1
    ):
        raise ValueError("valid sleeves covering exactly one capital required")

    def horizon_for(coin: str) -> int | None:
        return specs[sleeve_names[coin]].holding_hours if specs else holding_hours

    times = [b.time for b in bars[coins[0]]]
    if not times or any(b - a != HOUR for a, b in zip(times, times[1:], strict=False)):
        raise ValueError("continuous hourly bars required")
    funding: dict[str, dict[int, Decimal]] = {}
    for c in coins:
        if [b.time for b in bars[c]] != times or len(entries[c]) != len(times):
            raise ValueError("misaligned entries/prices")
        if any(s not in (-1, 0, 1) for s in entries[c]) or decimals[c] < 0:
            raise ValueError("invalid signal/lot")
        funding[c] = {}
        for at, rate in payments[c].items():
            bucket = at // HOUR * HOUR
            if not 0 <= at % HOUR <= 60_000 or not rate.is_finite():
                raise ValueError("funding must precede execution within its hour")
            if bucket in funding[c]:
                raise ValueError("duplicate funding bucket")
            funding[c][bucket] = rate
        if sorted(funding[c]) != times:
            raise ValueError("funding coverage failure")
    delay = int(scenario == "delay")
    fee = (
        D(0)
        if scenario == "zero_cost"
        else D("0.0009")
        if scenario == "cost_stress"
        else D("0.00045")
    )
    slip = (
        D(0)
        if scenario == "zero_cost"
        else D("0.0005")
        if scenario == "cost_stress"
        else D("0.0002")
    )
    positions: dict[str, HeldPosition] = {}
    cash = peak = bound_peak = D(1000)
    max_dd = max_bound_dd = max_gross_ratio = D(0)
    min_margin_buffer: Decimal | None = None
    max_open_positions = underwater = longest_underwater = 0
    halted = margin_breach = False
    halt_at: int | None = None
    cycles: list[dict[str, Any]] = []
    curve: list[dict[str, Any]] = []
    monthly_last: dict[str, Decimal] = {}
    rejected = {"occupied": 0, "no_budget_or_minimum": 0, "terminal": 0, "halted": 0}

    def equity(i: int, field: str) -> Decimal:
        return cash + sum(
            (
                p.side * p.quantity * (getattr(bars[c][i], field) - p.price)
                for c, p in positions.items()
            ),
            D(0),
        )

    def observe(value: Decimal, at: int) -> None:
        nonlocal peak, max_dd, halted, halt_at
        peak = max(peak, value)
        drawdown = 1 - value / peak
        max_dd = max(max_dd, drawdown)
        if drawdown >= drawdown_limit and not halted:
            halted, halt_at = True, at

    def close(c: str, i: int, at: int, reason: str) -> None:
        nonlocal cash
        p = positions.pop(c)
        price = bars[c][i].open * (1 - p.side * slip)
        exit_fee = p.quantity * price * fee
        gross = p.side * p.quantity * (price - p.price)
        cash += gross - exit_fee
        cycles.append(
            {
                "coin": c,
                "side": p.side,
                "quantity": p.quantity,
                "opened_ms": p.opened_ms,
                "closed_ms": at,
                "entry_price": p.price,
                "exit_price": price,
                "gross_pnl_usd": gross,
                "fees_usd": p.entry_fee + exit_fee,
                "funding_cost_usd": p.funding_cost,
                "net_pnl_usd": gross - p.entry_fee - exit_fee - p.funding_cost,
                "reason": reason,
            }
        )

    for i, at in enumerate(times):
        execution_ms = at + 60_000
        before = dict(positions)
        pre_equity = equity(i, "open")
        observe(pre_equity, at)
        cash -= monthly_infra / 720
        for c, p in tuple(positions.items()):
            rate = funding[c][at]
            charge = (
                D(0)
                if scenario == "zero_cost"
                else p.quantity
                * bars[c][i].open
                * (abs(rate) if scenario == "funding_adverse" else p.side * rate)
            )
            cash -= charge
            positions[c] = replace(p, funding_cost=p.funding_cost + charge)
        funded_equity = equity(i, "open")
        observe(funded_equity, execution_ms)
        gross_before = sum(
            (p.quantity * bars[c][i].open for c, p in positions.items()), D(0)
        )
        if funded_equity < D("0.2") * gross_before:
            margin_breach = True
            if not halted:
                halted, halt_at = True, execution_ms
        for c, p in tuple(positions.items()):
            horizon = horizon_for(c)
            reason = (
                "drawdown_or_margin"
                if halted
                else "terminal"
                if i == len(times) - 1
                else "time"
                if horizon is not None and execution_ms - p.opened_ms >= horizon * HOUR
                else None
            )
            if reason is not None:
                close(c, i, execution_ms, reason)
        source = i - delay
        candidates = [c for c in coins if source >= 0 and entries[c][source]]
        if halted:
            rejected["halted"] += len(candidates)
            candidates = []
        eligible = []
        for c in candidates:
            horizon = horizon_for(c)
            if c in positions:
                rejected["occupied"] += 1
            elif i == len(times) - 1 or (
                horizon is not None and i + horizon >= len(times)
            ):
                rejected["terminal"] += 1
            else:
                eligible.append(c)
        if eligible:
            balance = equity(i, "open")
            gross = sum(
                (p.quantity * bars[c][i].open for c, p in positions.items()), D(0)
            )
            # Conservatively reserve all immediate fees/slippage before allocating.
            cost_fraction = slip + fee * (1 + slip)
            available = max(
                D(0), (gross_cap * balance - gross) / (1 + gross_cap * cost_fraction)
            )
            conservative_balance = balance - available * cost_fraction
            allocation = max(
                D(0),
                min(available / len(eligible), gross_cap * conservative_balance / 3),
            )
            sleeve_allocations: dict[str, Decimal] = {}
            if specs:
                used = {
                    name: sum(
                        (
                            p.quantity * bars[c][i].open
                            for c, p in positions.items()
                            if sleeve_names[c] == name
                        ),
                        D(0),
                    )
                    for name in specs
                }
                sleeve_allocations = sleeve_budgets(
                    specs,
                    sleeve_names,
                    eligible,
                    used,
                    gross_cap,
                    conservative_balance,
                    available,
                )
            newly_opened = 0
            for c in eligible:
                side = entries[c][source]
                raw = bars[c][i].open
                step = D(10) ** -decimals[c]
                budget = sleeve_allocations[sleeve_names[c]] if specs else allocation
                qty = (budget / raw / step).to_integral_value(
                    rounding=ROUND_FLOOR
                ) * step
                price = raw * (1 + side * slip)
                if qty * price < 10:
                    rejected["no_budget_or_minimum"] += 1
                    continue
                entry_fee = qty * price * fee
                cash -= entry_fee
                positions[c] = HeldPosition(side, qty, price, execution_ms, entry_fee)
                newly_opened += 1
            balance_after = equity(i, "open")
            gross_after = sum(
                (p.quantity * bars[c][i].open for c, p in positions.items()), D(0)
            )
            if gross_after > max(gross, gross_cap * balance_after) + D("1e-18"):
                raise ValueError("entry allocation exceeds gross budget")
            if newly_opened and gross_after / 2 > balance_after:
                raise ValueError("fixed 2x initial margin violated")
        post_equity = equity(i, "open")
        observe(post_equity, execution_ms)
        # Include the positions on both sides of the transaction boundary. Their
        # full-hour adverse moves may not coexist; this is an upper risk bound.
        union = {(c, p.opened_ms): p for c, p in before.items()}
        union.update({(c, p.opened_ms): p for c, p in positions.items()})
        adverse_move = favorable_move = D(0)
        for (c, _), p in union.items():
            b = bars[c][i]
            adverse_move += (
                p.side * p.quantity * ((b.low if p.side == 1 else b.high) - b.open)
            )
            favorable_move += (
                p.side * p.quantity * ((b.high if p.side == 1 else b.low) - b.open)
            )
        adverse = min(pre_equity, funded_equity, post_equity) + adverse_move
        favorable = max(pre_equity, funded_equity, post_equity) + favorable_move
        marked = equity(i, "close")
        observe(marked, at + HOUR)
        bound_peak = max(bound_peak, favorable, marked, peak)
        bound_dd = 1 - min(adverse, marked) / bound_peak
        max_bound_dd = max(max_bound_dd, bound_dd)
        gross_envelope = max(
            sum((p.quantity * bars[c][i].high for c, p in snapshot.items()), D(0))
            for snapshot in (before, positions)
        )
        buffer = adverse - D("0.2") * gross_envelope
        min_margin_buffer = (
            buffer if min_margin_buffer is None else min(min_margin_buffer, buffer)
        )
        gross_close = sum(
            (p.quantity * bars[c][i].close for c, p in positions.items()), D(0)
        )
        if marked < D("0.2") * gross_close:
            margin_breach = True
            if not halted:
                halted, halt_at = True, at + HOUR
        if marked > 0:
            max_gross_ratio = max(max_gross_ratio, gross_close / marked)
        if pre_equity > 0:
            max_gross_ratio = max(max_gross_ratio, gross_before / pre_equity)
        if funded_equity > 0:
            max_gross_ratio = max(max_gross_ratio, gross_before / funded_equity)
        if post_equity > 0:
            post_gross = sum(
                (p.quantity * bars[c][i].open for c, p in positions.items()), D(0)
            )
            max_gross_ratio = max(max_gross_ratio, post_gross / post_equity)
        max_open_positions = max(max_open_positions, len(before), len(positions))
        underwater = underwater + 1 if marked < peak else 0
        longest_underwater = max(longest_underwater, underwater)
        curve.append(
            {
                "time_ms": at + HOUR,
                "cash": cash,
                "equity": marked,
                "unrealized_pnl": marked - cash,
                "peak_observed": peak,
                "drawdown": 1 - marked / peak,
                "adverse_equity_envelope": adverse,
                "drawdown_envelope": bound_dd,
                "margin_envelope_buffer_usd": buffer,
                "gross_notional": gross_close,
                "positions": len(positions),
                "halted": halted,
            }
        )
        month = datetime.fromtimestamp((at + HOUR - 1) / 1000, UTC).strftime("%Y-%m")
        monthly_last[month] = marked
    if positions:
        raise ValueError("terminal positions remain")
    infra = monthly_infra * len(times) / 720
    total_cycles = sum((c["net_pnl_usd"] for c in cycles), D(0))
    if abs(cash - 1000 + infra - total_cycles) > D("1e-18"):
        raise ValueError("cash/cycles/funding/infra reconciliation failed")
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
    contributions: dict[str, Decimal] = {}
    for cycle in cycles:
        c = cycle["coin"]
        contributions[c] = contributions.get(c, D(0)) + cycle["net_pnl_usd"]
    return {
        "cycles": cycles,
        "curve": curve,
        "summary": {
            "gross_cap_at_entry": gross_cap,
            "drawdown_limit": drawdown_limit,
            "scenario": scenario,
            "monthly_infra": monthly_infra,
            "days": days,
            "start_ms": times[0],
            "end_ms_exclusive": times[-1] + HOUR,
            "end_equity": cash,
            "net_trading_usd": cash - 1000 + infra,
            "infrastructure_usd": infra,
            "net_total_usd": cash - 1000,
            "equivalent_monthly_compound": (cash / 1000) ** (D(30) / days) - 1
            if cash > 0
            else None,
            "max_hourly_drawdown": max_dd,
            "max_ohlc_drawdown_envelope": max_bound_dd,
            "margin_observed_breach": margin_breach,
            "minimum_margin_envelope_buffer_usd": min_margin_buffer,
            "round_trips": len(cycles),
            "max_positions": max_open_positions,
            "max_observed_gross_ratio": max_gross_ratio,
            "longest_underwater_days": D(longest_underwater) / 24,
            "unrecovered_at_end_days": D(underwater) / 24,
            "months": months,
            "green_months": sum(m["pnl_usd"] > 0 for m in months),
            "red_months": sum(m["pnl_usd"] < 0 for m in months),
            "contributions_usd": contributions,
            "rejected_entries": rejected,
            "worst_cycle_usd": min((c["net_pnl_usd"] for c in cycles), default=D(0)),
            "halted": halted,
            "halt_at_ms": halt_at,
            "live_enabled": False,
            "promotion_authorized": False,
        },
    }
