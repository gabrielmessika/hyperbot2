"""Fixed-intent native net exposure audit without crediting execution savings."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any

from hyperbot2.research.rotation import HOUR
from hyperbot2.research.volume import VolumeBar

D = Decimal


def audit_net_positions(
    bars: Mapping[str, Sequence[VolumeBar]],
    payments: Mapping[str, Mapping[int, Decimal]],
    decimals: Mapping[str, int],
    virtual_to_native: Mapping[str, str],
    source: Mapping[str, Any],
) -> dict[str, Any]:
    coins = tuple(sorted(bars))
    if not coins:
        raise ValueError("native bars required")
    times = [b.time for b in bars[coins[0]]]
    if not times:
        raise ValueError("native bars required")
    if any(b - a != HOUR for a, b in zip(times, times[1:], strict=False)):
        raise ValueError("continuous native hours required")
    if any([b.time for b in bars[c]] != times for c in coins):
        raise ValueError("unaligned native assets")
    if len(source["curve"]) != len(times) or any(
        row["time_ms"] != at + HOUR
        for row, at in zip(source["curve"], times, strict=True)
    ):
        raise ValueError("unaligned source equity curve")
    funding: dict[str, dict[int, Decimal]] = {}
    for c in coins:
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
            raise ValueError("native funding coverage failure")
    scenario = source["summary"]["scenario"]
    if scenario not in {"base", "cost_stress", "delay", "funding_adverse", "zero_cost"}:
        raise ValueError("unknown source cost model")
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
    infra = D(source["summary"]["monthly_infra"])
    opens: dict[int, list[int]] = defaultdict(list)
    closes: dict[int, list[int]] = defaultdict(list)
    cycles: list[dict[str, Any]] = []
    indices = {at + 60_000: i for i, at in enumerate(times)}
    for row in source["cycles"]:
        name = row["coin"]
        if name not in virtual_to_native or virtual_to_native[name] not in bars:
            raise ValueError("unmapped virtual position")
        c = virtual_to_native[name]
        q, side = D(row["quantity"]), int(row["side"])
        if (
            not q.is_finite()
            or q <= 0
            or side not in (-1, 1)
            or q % (D(10) ** -decimals[c])
        ):
            raise ValueError("invalid native position lot")
        if row["opened_ms"] not in indices or row["closed_ms"] not in indices:
            raise ValueError("position outside exact execution grid")
        a, b = indices[row["opened_ms"]], indices[row["closed_ms"]]
        if a >= b:
            raise ValueError("positive position lifetime required")
        entry, exit_price = D(row["entry_price"]), D(row["exit_price"])
        if entry != bars[c][a].open * (1 + side * slip) or exit_price != bars[c][
            b
        ].open * (1 - side * slip):
            raise ValueError("source execution price disagrees with native open proxy")
        if abs(q * (entry + exit_price) * fee - D(row["fees_usd"])) > D("1e-18"):
            raise ValueError("source trading fees do not reconcile")
        uid = len(cycles)
        cycles.append(
            {
                "native": c,
                "virtual": name,
                "q": q,
                "side": side,
                "entry": entry,
                "exit": exit_price,
            }
        )
        opens[a].append(uid)
        closes[b].append(uid)
    active: dict[int, dict[str, Any]] = {}
    cash = bound_peak = D(1000)
    max_bound = max_net_ratio = D(0)
    min_margin: Decimal | None = None
    orders, curve = [], []
    violations = lot_violations = exact_cancellations = opposing_hours = 0
    virtual_turnover = net_turnover = D(0)

    def equity(i: int, field: str) -> Decimal:
        return cash + sum(
            (
                p["side"] * p["q"] * (getattr(bars[p["native"]][i], field) - p["entry"])
                for p in active.values()
            ),
            D(0),
        )

    def net() -> dict[str, Decimal]:
        result = dict.fromkeys(coins, D(0))
        for p in active.values():
            result[p["native"]] += p["side"] * p["q"]
        return result

    for i, at in enumerate(times):
        before = net()
        pre_equity = equity(i, "open")
        cash -= infra / 720
        for p in active.values():
            c = p["native"]
            rate = funding[c][at]
            if scenario != "zero_cost":
                cash -= (
                    p["q"]
                    * bars[c][i].open
                    * (abs(rate) if scenario == "funding_adverse" else p["side"] * rate)
                )
        funded = equity(i, "open")
        legs: dict[str, int] = defaultdict(int)
        for uid in closes[i]:
            if uid not in active:
                raise ValueError("close of inactive virtual position")
            p = active.pop(uid)
            cash += (
                p["side"] * p["q"] * (p["exit"] - p["entry"]) - p["q"] * p["exit"] * fee
            )
            virtual_turnover += p["q"] * p["exit"]
            legs[p["native"]] += 1
        for uid in opens[i]:
            p = cycles[uid]
            if any(a["virtual"] == p["virtual"] for a in active.values()):
                raise ValueError("overlapping positions in one virtual asset")
            cash -= p["q"] * p["entry"] * fee
            virtual_turnover += p["q"] * p["entry"]
            legs[p["native"]] += 1
            active[uid] = p
        after = net()
        post_equity = equity(i, "open")
        for c, count in legs.items():
            delta = after[c] - before[c]
            if delta == 0:
                exact_cancellations += 1
                continue
            price = bars[c][i].open * (1 + (1 if delta > 0 else -1) * slip)
            notional = abs(delta) * price
            too_small = notional < 10
            bad_lot = bool(abs(delta) % (D(10) ** -decimals[c]))
            violations += too_small
            lot_violations += bad_lot
            net_turnover += notional
            kind = (
                "flip"
                if before[c] * after[c] < 0
                else "reduction"
                if abs(after[c]) < abs(before[c])
                else "increase_or_open"
            )
            orders.append(
                {
                    "time_ms": at + 60_000,
                    "coin": c,
                    "before": before[c],
                    "after": after[c],
                    "delta": delta,
                    "notional_usd": notional,
                    "kind": kind,
                    "virtual_legs": count,
                    "below_minimum": too_small,
                    "bad_lot": bad_lot,
                }
            )
        adverse_move = favorable_move = D(0)
        for c in coins:
            positive, negative = (
                max(D(0), before[c], after[c]),
                min(D(0), before[c], after[c]),
            )
            bar = bars[c][i]
            adverse_move += positive * (bar.low - bar.open) + negative * (
                bar.high - bar.open
            )
            favorable_move += positive * (bar.high - bar.open) + negative * (
                bar.low - bar.open
            )
        marked = equity(i, "close")
        original = source["curve"][i]
        if abs(marked - D(original["equity"])) > D("1e-18") or abs(
            cash - D(original["cash"])
        ) > D("1e-18"):
            raise ValueError(
                "original costs, cash or marked equity failed reconstruction"
            )
        adverse = min(pre_equity, funded, post_equity) + adverse_move
        favorable = max(pre_equity, funded, post_equity) + favorable_move
        bound_peak = max(bound_peak, favorable, marked, D(original["peak_observed"]))
        bound = 1 - min(adverse, marked) / bound_peak
        max_bound = max(max_bound, bound)
        gross_net = sum((abs(after[c]) * bars[c][i].close for c in coins), D(0))
        if marked > 0:
            max_net_ratio = max(max_net_ratio, gross_net / marked)
        gross_bound = max(
            sum((abs(q[c]) * bars[c][i].high for c in coins), D(0))
            for q in (before, after)
        )
        buffer = adverse - D("0.2") * gross_bound
        min_margin = buffer if min_margin is None else min(min_margin, buffer)
        opposed = any(
            any(p["native"] == c and p["side"] == 1 for p in active.values())
            and any(p["native"] == c and p["side"] == -1 for p in active.values())
            for c in coins
        )
        opposing_hours += opposed
        curve.append(
            {
                "time_ms": at + HOUR,
                "net_gross_notional": gross_net,
                "original_gross_notional": original["gross_notional"],
                "original_equity": marked,
                "net_exposure_drawdown_envelope": bound,
                "net_margin_envelope_buffer": buffer,
            }
        )
    if active:
        raise ValueError("unclosed source positions")
    return {
        "orders": orders,
        "curve": curve,
        "summary": {
            "source_round_trips": len(cycles),
            "virtual_order_legs": 2 * len(cycles),
            "net_order_deltas": len(orders),
            "exact_cancellations": exact_cancellations,
            "below_minimum_orders": violations,
            "bad_lot_orders": lot_violations,
            "virtual_turnover_usd": virtual_turnover,
            "net_delta_turnover_usd": net_turnover,
            "opposing_position_hours": opposing_hours,
            "hours": len(times),
            "net_exposure_drawdown_envelope": max_bound,
            "max_net_gross_ratio_at_close": max_net_ratio,
            "minimum_net_margin_envelope_buffer": min_margin,
            "baseline_net_total_usd_unchanged": source["summary"]["net_total_usd"],
            "cash_and_equity_reconstruction_passed": True,
            "direct_delta_minimums_passed": violations == lot_violations == 0,
            "execution_savings_credited_usd": D(0),
            "live_enabled": False,
            "promotion_authorized": False,
        },
    }
