"""Causal native inventory replay with pending small deltas and one capital."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal
from typing import Any

from hyperbot2.research.funding_portfolio import AllocationSleeve, sleeve_budgets
from hyperbot2.research.rotation import HOUR
from hyperbot2.research.volume import VolumeBar

D = Decimal
DEFAULT_GROSS_CAP = D("1.5")


def adverse_price(price: Decimal, side: int, decimals: int) -> Decimal:
    """Round a hypothetical perp execution price to an admissible adverse tick."""
    if (
        not price.is_finite()
        or price <= 0
        or side not in (-1, 1)
        or not 0 <= decimals <= 6
    ):
        raise ValueError("invalid native price/side/size precision")
    tick = D(10) ** max(min(0, price.adjusted() - 4), decimals - 6)
    result = (price / tick).to_integral_value(
        rounding=ROUND_CEILING if side == 1 else ROUND_FLOOR
    ) * tick
    if result <= 0:
        raise ValueError("no positive adverse tick")
    return result


@dataclass(frozen=True, slots=True)
class NativePosition:
    quantity: Decimal
    price: Decimal
    opened_ms: int
    realized: Decimal = D(0)
    fees: Decimal = D(0)
    funding: Decimal = D(0)


@dataclass(frozen=True, slots=True)
class TargetLot:
    quantity: Decimal
    opened_ms: int


class NativeAccount:
    """One collateral account, with average-cost native position episodes."""

    def __init__(self) -> None:
        self.cash = D(1000)
        self.positions: dict[str, NativePosition] = {}
        self.cycles: list[dict[str, Any]] = []
        self.orders: list[dict[str, Any]] = []
        self.realized = self.fees = self.funding = self.infrastructure = D(0)

    def quantities(self, coins: Sequence[str]) -> dict[str, Decimal]:
        return {
            c: self.positions[c].quantity if c in self.positions else D(0)
            for c in coins
        }

    def equity(self, prices: Mapping[str, Decimal]) -> Decimal:
        return self.cash + sum(
            (p.quantity * (prices[c] - p.price) for c, p in self.positions.items()),
            D(0),
        )

    def pay_funding(
        self, prices: Mapping[str, Decimal], rates: Mapping[str, Decimal], scenario: str
    ) -> None:
        for c, p in tuple(self.positions.items()):
            charge = (
                D(0)
                if scenario == "zero_cost"
                else prices[c]
                * (
                    abs(p.quantity) * abs(rates[c])
                    if scenario == "funding_adverse"
                    else p.quantity * rates[c]
                )
            )
            self.positions[c] = replace(p, funding=p.funding + charge)
            self.cash -= charge
            self.funding += charge

    def fill(
        self, coin: str, delta: Decimal, price: Decimal, fee_rate: Decimal, at: int
    ) -> None:
        if not delta.is_finite() or not price.is_finite() or delta == 0 or price <= 0:
            raise ValueError("invalid native fill")
        p = self.positions.get(coin)
        old = p.quantity if p else D(0)
        new = old + delta
        fee = abs(delta) * price * fee_rate
        realized = D(0)
        closing = min(abs(old), abs(delta)) if old * delta < 0 else D(0)
        if p is not None and closing:
            realized = (1 if old > 0 else -1) * closing * (price - p.price)
        if p is None:
            self.positions[coin] = NativePosition(new, price, at, fees=fee)
        elif new == 0 or new * old < 0:
            closing_fee = fee * closing / abs(delta)
            total_realized = p.realized + realized
            total_fees = p.fees + closing_fee
            self.cycles.append(
                {
                    "coin": coin,
                    "opened_ms": p.opened_ms,
                    "closed_ms": at,
                    "gross_pnl_usd": total_realized,
                    "fees_usd": total_fees,
                    "funding_cost_usd": p.funding,
                    "net_pnl_usd": total_realized - total_fees - p.funding,
                }
            )
            if new == 0:
                del self.positions[coin]
            else:
                self.positions[coin] = NativePosition(
                    new, price, at, fees=fee - closing_fee
                )
        else:
            average = (
                (abs(old) * p.price + abs(delta) * price) / abs(new)
                if old * delta > 0
                else p.price
            )
            self.positions[coin] = replace(
                p,
                quantity=new,
                price=average,
                realized=p.realized + realized,
                fees=p.fees + fee,
            )
        self.cash += realized - fee
        self.realized += realized
        self.fees += fee
        self.orders.append(
            {
                "coin": coin,
                "time_ms": at,
                "before": old,
                "after": new,
                "delta": delta,
                "price": price,
                "notional_usd": abs(delta) * price,
                "fee_usd": fee,
                "realized_pnl_usd": realized,
            }
        )


def simulate_native_portfolio(
    bars: Mapping[str, Sequence[VolumeBar]],
    payments: Mapping[str, Mapping[int, Decimal]],
    entries: Mapping[str, Sequence[int]],
    decimals: Mapping[str, int],
    virtual_to_native: Mapping[str, str],
    asset_sleeves: Mapping[str, str],
    sleeves: Mapping[str, AllocationSleeve],
    *,
    scenario: str,
    monthly_infra: Decimal,
    drawdown_limit: Decimal,
    gross_cap: Decimal = DEFAULT_GROSS_CAP,
    entry_weights: Mapping[str, Sequence[Decimal]] | None = None,
) -> dict[str, Any]:
    if gross_cap not in (D("0.5"), D("1.5")):
        raise ValueError("unregistered native allocation")
    if scenario not in {"base", "cost_stress", "delay", "funding_adverse", "zero_cost"}:
        raise ValueError("unregistered cost scenario")
    if monthly_infra not in (D(0), D(20)) or drawdown_limit not in (D("0.2"), D("0.3")):
        raise ValueError("unregistered risk/infra scenario")
    coins, virtual = tuple(sorted(bars)), tuple(sorted(entries))
    if (
        not coins
        or not virtual
        or set(virtual_to_native) != set(virtual)
        or set(asset_sleeves) != set(virtual)
    ):
        raise ValueError("exact native/virtual mapping required")
    if set(virtual_to_native.values()) != set(coins) or set(
        asset_sleeves.values()
    ) != set(sleeves):
        raise ValueError("uncovered native asset/sleeve")
    if (
        any(
            not s.fraction.is_finite()
            or s.fraction <= 0
            or s.holding_hours is None
            or s.holding_hours <= 0
            for s in sleeves.values()
        )
        or sum((s.fraction for s in sleeves.values()), D(0)) != 1
    ):
        raise ValueError("valid fixed-horizon sleeves covering one capital required")
    times = [b.time for b in bars[coins[0]]]
    if not times or any(b - a != HOUR for a, b in zip(times, times[1:], strict=False)):
        raise ValueError("continuous hourly bars required")
    if any(
        len(entries[v]) != len(times) or any(s not in (-1, 0, 1) for s in entries[v])
        for v in virtual
    ):
        raise ValueError("invalid entry series")
    if entry_weights is not None and (
        set(entry_weights) != set(virtual)
        or any(
            len(entry_weights[v]) != len(times)
            or any(
                not w.is_finite() or w < 0 or (entries[v][i] != 0 and w <= 0)
                for i, w in enumerate(entry_weights[v])
            )
            for v in virtual
        )
    ):
        raise ValueError("positive finite weights required for every entry")
    funding: dict[str, dict[int, Decimal]] = {}
    for c in coins:
        if [b.time for b in bars[c]] != times or not 0 <= decimals[c] <= 6:
            raise ValueError("unaligned native data/invalid lot")
        funding[c] = {}
        for at, rate in payments[c].items():
            bucket = at // HOUR * HOUR
            if (
                not rate.is_finite()
                or not 0 <= at % HOUR <= 60_000
                or bucket in funding[c]
            ):
                raise ValueError("invalid native funding timestamp/rate")
            funding[c][bucket] = rate
        if sorted(funding[c]) != times:
            raise ValueError("funding coverage failure")
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
    cost_fraction = slip + fee * (1 + slip)
    delay = int(scenario == "delay")
    account = NativeAccount()
    targets: dict[str, TargetLot] = {}
    curve: list[dict[str, Any]] = []
    attempts: list[dict[str, Any]] = []
    rejected: Counter[str] = Counter()
    peak = bound_peak = D(1000)
    max_dd = max_bound = max_ratio = max_residual = D(0)
    min_buffer: Decimal | None = None
    halted = margin_breach = False
    halt_at: int | None = None
    residual_hours = underwater = longest_underwater = 0
    monthly: dict[str, Decimal] = {}

    def observe(value: Decimal, at: int) -> None:
        nonlocal peak, max_dd, halted, halt_at
        peak = max(peak, value)
        dd = 1 - value / peak
        max_dd = max(max_dd, dd)
        if dd >= drawdown_limit and not halted:
            halted, halt_at = True, at

    def target_net() -> dict[str, Decimal]:
        result = dict.fromkeys(coins, D(0))
        for v, p in targets.items():
            result[virtual_to_native[v]] += p.quantity
        return result

    for i, at in enumerate(times):
        execution_ms = at + 60_000
        prices = {c: bars[c][i].open for c in coins}
        before = account.quantities(coins)
        previous_target = target_net()
        phases = [account.equity(prices)]
        observe(phases[-1], at)
        account.cash -= monthly_infra / 720
        account.infrastructure += monthly_infra / 720
        account.pay_funding(prices, {c: funding[c][at] for c in coins}, scenario)
        phases.append(account.equity(prices))
        observe(phases[-1], execution_ms)
        gross_before = sum((abs(before[c]) * prices[c] for c in coins), D(0))
        if phases[-1] < D("0.2") * gross_before:
            margin_breach = True
            if not halted:
                halted, halt_at = True, execution_ms
        expired_notional = D(0)
        for v, p in tuple(targets.items()):
            horizon = sleeves[asset_sleeves[v]].holding_hours
            assert horizon is not None
            if (
                halted
                or i == len(times) - 1
                or execution_ms - p.opened_ms >= horizon * HOUR
            ):
                expired_notional += abs(p.quantity) * prices[virtual_to_native[v]]
                del targets[v]
        eligible = []
        source = i - delay
        for v in virtual:
            if source < 0 or not entries[v][source]:
                continue
            horizon = sleeves[asset_sleeves[v]].holding_hours
            assert horizon is not None
            reason = (
                "halted"
                if halted
                else "occupied"
                if v in targets
                else "terminal"
                if i + horizon >= len(times)
                else None
            )
            if reason:
                rejected[reason] += 1
            else:
                eligible.append(v)
        old_residual = sum(
            (abs(before[c] - previous_target[c]) * prices[c] for c in coins), D(0)
        )
        if eligible:
            # Reserve gross sleeve risk even when native positions cancel.
            used = {
                name: sum(
                    (
                        abs(p.quantity) * prices[virtual_to_native[v]]
                        for v, p in targets.items()
                        if asset_sleeves[v] == name
                    ),
                    D(0),
                )
                for name in sleeves
            }
            balance = (
                account.equity(prices)
                - (expired_notional + old_residual) * cost_fraction
            )
            gross = sum(used.values(), D(0)) + old_residual
            available = max(
                D(0), (gross_cap * balance - gross) / (1 + gross_cap * cost_fraction)
            )
            conservative_balance = balance - available * cost_fraction
            budgets = sleeve_budgets(
                sleeves,
                asset_sleeves,
                eligible,
                used,
                gross_cap,
                conservative_balance,
                available,
            )
            weighted: dict[str, Decimal] = {}
            if entry_weights is not None:
                for name, spec in sleeves.items():
                    members = [v for v in eligible if asset_sleeves[v] == name]
                    total_weight = sum(
                        (entry_weights[v][source] for v in members), D(0)
                    )
                    pool = len(members) * max(D(0), budgets[name])
                    for v in members:
                        weighted[v] = min(
                            pool * entry_weights[v][source] / total_weight,
                            max(
                                D(0),
                                gross_cap * spec.fraction * conservative_balance / 3,
                            ),
                        )
            for v in eligible:
                c = virtual_to_native[v]
                step = D(10) ** -decimals[c]
                q = (
                    max(
                        D(0),
                        weighted[v]
                        if entry_weights is not None
                        else budgets[asset_sleeves[v]],
                    )
                    / prices[c]
                    / step
                ).to_integral_value(rounding=ROUND_FLOOR) * step
                side = entries[v][source]
                price = adverse_price(prices[c] * (1 + side * slip), side, decimals[c])
                if q * price < 10:
                    rejected["target_below_minimum"] += 1
                else:
                    targets[v] = TargetLot(side * q, execution_ms)
        desired = target_net()

        # Risk-reducing deltas first; remaining orders have a stable lexical order.
        ordered = sorted(
            (not (before[c] * desired[c] >= 0 and abs(desired[c]) < abs(before[c])), c)
            for c in coins
        )
        for _, c in ordered:
            old = account.positions[c].quantity if c in account.positions else D(0)
            target = D(0) if halted else desired[c]
            delta = target - old
            if not delta:
                continue
            side = 1 if delta > 0 else -1
            price = adverse_price(prices[c] * (1 + side * slip), side, decimals[c])
            notional = abs(delta) * price
            if abs(delta) % (D(10) ** -decimals[c]):
                raise ValueError("native delta violates lot")
            reason = "below_minimum" if notional < 10 else None
            reduce_only = old * target >= 0 and abs(target) < abs(old)
            balance = account.equity(prices)
            projected = balance - delta * (price - prices[c]) - notional * fee
            gross = sum(
                (abs(p.quantity) * prices[n] for n, p in account.positions.items()),
                D(0),
            )
            gross_after = gross + (abs(target) - abs(old)) * prices[c]
            if (
                reason is None
                and not reduce_only
                and (
                    gross_after > gross_cap * projected + D("1e-18")
                    or gross_after / 2 > projected
                )
            ):
                reason = "entry_risk_budget"
            if reason:
                rejected[reason] += 1
                attempts.append(
                    {
                        "coin": c,
                        "time_ms": execution_ms,
                        "delta": delta,
                        "target": target,
                        "actual": old,
                        "notional_usd": notional,
                        "reason": reason,
                    }
                )
                continue
            account.fill(c, delta, price, fee, execution_ms)
            phases.append(account.equity(prices))
            if abs(phases[-1] - projected) > D("1e-18"):
                raise ValueError("fill equity reconciliation failed")
            observe(phases[-1], execution_ms)
            if phases[-1] > 0:
                max_ratio = max(max_ratio, gross_after / phases[-1])
        if halted:
            targets.clear()
            desired = dict.fromkeys(coins, D(0))
        after = account.quantities(coins)
        adverse_move = favorable_move = D(0)
        for c in coins:
            positive, negative = (
                max(D(0), before[c], after[c]),
                min(D(0), before[c], after[c]),
            )
            b = bars[c][i]
            adverse_move += positive * (b.low - b.open) + negative * (b.high - b.open)
            favorable_move += positive * (b.high - b.open) + negative * (b.low - b.open)
        adverse, favorable = min(phases) + adverse_move, max(phases) + favorable_move
        closes = {c: bars[c][i].close for c in coins}
        marked = account.equity(closes)
        observe(marked, at + HOUR)
        bound_peak = max(bound_peak, favorable, marked, peak)
        bound = 1 - min(adverse, marked) / bound_peak
        max_bound = max(max_bound, bound)
        gross_bound = sum(
            (max(abs(before[c]), abs(after[c])) * bars[c][i].high for c in coins), D(0)
        )
        buffer = adverse - D("0.2") * gross_bound
        min_buffer = buffer if min_buffer is None else min(min_buffer, buffer)
        gross_close = sum((abs(after[c]) * closes[c] for c in coins), D(0))
        if marked < D("0.2") * gross_close:
            margin_breach = True
            if not halted:
                halted, halt_at = True, at + HOUR
        for value, gross in [
            (phases[0], gross_before),
            (phases[1], gross_before),
            (marked, gross_close),
        ]:
            if value > 0:
                max_ratio = max(max_ratio, gross / value)
        residual = sum((abs(after[c] - desired[c]) * closes[c] for c in coins), D(0))
        residual_hours += bool(residual)
        max_residual = max(max_residual, residual)
        underwater = underwater + 1 if marked < peak else 0
        longest_underwater = max(longest_underwater, underwater)
        curve.append(
            {
                "time_ms": at + HOUR,
                "cash": account.cash,
                "equity": marked,
                "unrealized_pnl": marked - account.cash,
                "peak_observed": peak,
                "drawdown": 1 - marked / peak,
                "drawdown_envelope": bound,
                "margin_envelope_buffer_usd": buffer,
                "gross_notional": gross_close,
                "native_quantities": after,
                "target_quantities": desired,
                "residual_notional_usd": residual,
                "halted": halted,
            }
        )
        month = datetime.fromtimestamp((at + HOUR - 1) / 1000, UTC).strftime("%Y-%m")
        monthly[month] = marked
    if abs(
        account.cash
        - 1000
        - account.realized
        + account.fees
        + account.funding
        + account.infrastructure
    ) > D("1e-18"):
        raise ValueError("cash ledger reconciliation failed")
    accounted = sum((c["net_pnl_usd"] for c in account.cycles), D(0)) + sum(
        (p.realized - p.fees - p.funding for p in account.positions.values()), D(0)
    )
    if abs(account.cash - 1000 + account.infrastructure - accounted) > D("1e-18"):
        raise ValueError("native episode reconciliation failed")
    previous = D(1000)
    months = []
    for month, value in monthly.items():
        months.append(
            {
                "month": month,
                "pnl_usd": value - previous,
                "return": value / previous - 1 if previous > 0 else None,
            }
        )
        previous = value
    end = curve[-1]["equity"]
    days = D(len(times)) / 24
    return {
        "orders": account.orders,
        "cycles": account.cycles,
        "curve": curve,
        "deferred_attempts": attempts,
        "summary": {
            "gross_cap_at_entry": gross_cap,
            "drawdown_limit": drawdown_limit,
            "scenario": scenario,
            "monthly_infra": monthly_infra,
            "days": days,
            "start_ms": times[0],
            "end_ms_exclusive": times[-1] + HOUR,
            "end_equity": end,
            "net_total_usd": end - 1000,
            "equivalent_monthly_compound": (end / 1000) ** (D(30) / days) - 1
            if end > 0
            else None,
            "realized_pnl_usd": account.realized,
            "fees_usd": account.fees,
            "funding_cost_usd": account.funding,
            "infrastructure_usd": account.infrastructure,
            "max_hourly_drawdown": max_dd,
            "max_ohlc_drawdown_envelope": max_bound,
            "max_observed_gross_ratio": max_ratio,
            "minimum_margin_envelope_buffer_usd": min_buffer,
            "margin_observed_breach": margin_breach,
            "halted": halted,
            "halt_at_ms": halt_at,
            "native_orders": len(account.orders),
            "round_trips": len(account.cycles),
            "terminal_positions": account.quantities(coins),
            "terminal_flat": not account.positions,
            "residual_hours": residual_hours,
            "max_residual_notional_usd": max_residual,
            "rejected": dict(rejected),
            "months": months,
            "longest_underwater_days": D(longest_underwater) / 24,
            "cash_and_episode_reconciliation_passed": True,
            "live_enabled": False,
            "promotion_authorized": False,
        },
    }
