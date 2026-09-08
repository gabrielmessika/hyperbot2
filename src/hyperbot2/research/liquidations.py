"""Historical liquidation validation and causal, fixed event selection."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

D = Decimal
HOUR = 3_600_000
BASE_FEE = D("0.00045")
BASE_SLIP = D("0.0002")


def timestamp(value: str) -> int:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timezone required")
    return int(parsed.timestamp() * 1000)


@dataclass(frozen=True)
class LiquidationHour:
    time: int
    long_usd: Decimal
    short_usd: Decimal
    long_count: int
    short_count: int


def volume_hours(
    rows: list[dict[str, Any]], coin: str, start: int, end: int
) -> dict[int, LiquidationHour]:
    result = {}
    for row in rows:
        at = timestamp(row["timestamp"])
        if not start <= at < end:
            continue
        if at % HOUR or at in result or row["coin"] != coin or row["symbol"] != coin:
            raise ValueError("volume identity, alignment or duplicate")
        long, short, total = (
            D(str(row[k])) for k in ("long_usd", "short_usd", "total_usd")
        )
        counts = [row[k] for k in ("long_count", "short_count", "count")]
        if (
            any(not x.is_finite() or x < 0 for x in (long, short, total))
            or any(type(n) is not int or n < 0 for n in counts)
            or counts[0] + counts[1] != counts[2]
            or abs(long + short - total) > D("0.01")
            or (long > 0 and counts[0] == 0)
            or (short > 0 and counts[1] == 0)
        ):
            raise ValueError("invalid liquidation aggregate")
        result[at] = LiquidationHour(at, long, short, counts[0], counts[1])
    return result


def quantile(values: list[Decimal], fraction: float) -> Decimal:
    if not values or not 0 < fraction <= 1:
        raise ValueError("invalid quantile")
    return sorted(values)[math.ceil(fraction * len(values)) - 1]


def selected_hours(
    volumes: Mapping[int, LiquidationHour],
    returns: Mapping[int, Decimal],
    coin: str,
    start: int,
    end: int,
    lookback_hours: int = 168,
) -> list[dict[str, Any]]:
    """Use only prior published positive hours; missing records are not zeros."""
    if coin not in ("BTC", "ETH"):
        raise ValueError("unsupported coin")
    floor = D(100000 if coin == "BTC" else 50000)
    events = []
    next_time = start + lookback_hours * HOUR
    for at, row in sorted(volumes.items()):
        # All horizons and a one-hour delay must have an open inside the archive.
        if at < next_time or at + 26 * HOUR >= end:
            continue
        prior = [
            r.long_usd
            for t, r in volumes.items()
            if at - lookback_hours * HOUR <= t < at and r.long_usd > 0
        ]
        if len(prior) < 60:
            continue
        threshold = max(floor, quantile(prior, 0.95))
        if (
            row.long_usd >= threshold
            and row.long_count >= 5
            and row.long_usd >= D("0.8") * (row.long_usd + row.short_usd)
            and returns[at] <= D("-0.005")
        ):
            events.append(
                {
                    "hour_ms": at,
                    "coin": coin,
                    "threshold_usd": threshold,
                    "prior_positive_hours": len(prior),
                    "long_usd": row.long_usd,
                    "hour_return": returns[at],
                }
            )
            next_time = at + 25 * HOUR
    return events


def reconcile_raw(
    rows: list[dict[str, Any]], coin: str, expected: LiquidationHour
) -> dict[str, Any]:
    totals, counts = {"A": D(0), "B": D(0)}, {"A": 0, "B": 0}
    seen: set[tuple[Any, ...]] = set()
    duplicates = same_users = 0
    for row in rows:
        at = timestamp(row["timestamp"])
        if not expected.time <= at < expected.time + HOUR:
            continue
        if row["coin"] != coin or row["symbol"] != coin:
            raise ValueError("raw identity mismatch")
        side = row["side"]
        if (
            side not in totals
            or row["direction"] != {"A": "Close Long", "B": "Close Short"}[side]
        ):
            raise ValueError("ambiguous liquidation direction")
        if row.get("trade_id") is None or not row.get("tx_hash"):
            raise ValueError("missing liquidation identity")
        identity = (row["trade_id"], row["tx_hash"], row["liquidated_user"])
        if identity in seen:
            duplicates += 1
            continue
        seen.add(identity)
        price, size = D(row["price"]), D(row["size"])
        if any(not x.is_finite() or x <= 0 for x in (price, size)):
            raise ValueError("invalid liquidation price/size")
        totals[side] += price * size
        counts[side] += 1
        same_users += row["liquidated_user"] == row["liquidator_user"]
    valid = (
        abs(totals["A"] - expected.long_usd) <= D("0.01")
        and abs(totals["B"] - expected.short_usd) <= D("0.01")
        and counts["A"] == expected.long_count
        and counts["B"] == expected.short_count
        and duplicates == 0
    )
    return {
        "valid": valid,
        "duplicates": duplicates,
        "same_user_rows": same_users,
        "long_usd": totals["A"],
        "short_usd": totals["B"],
        "long_count": counts["A"],
        "short_count": counts["B"],
    }


def long_return(
    opens: Mapping[int, Decimal],
    funding: Mapping[int, Decimal],
    entry: int,
    horizon: int,
    fee: Decimal = BASE_FEE,
    slip: Decimal = BASE_SLIP,
    charge_funding: bool = True,
) -> dict[str, Decimal]:
    """One unit of executed entry notional; funding uses hourly open as proxy."""
    exit_at = entry + horizon * HOUR
    raw_entry, raw_exit = opens[entry], opens[exit_at]
    quantity = 1 / (raw_entry * (1 + slip))
    exit_notional = quantity * raw_exit * (1 - slip)
    funding_cost = (
        sum(
            (
                quantity * opens[t] * abs(funding[t])
                for t in range(entry + HOUR, exit_at + HOUR, HOUR)
            ),
            D(0),
        )
        if charge_funding
        else D(0)
    )
    fees = fee * (1 + exit_notional)
    return {
        "gross_bps": (raw_exit / raw_entry - 1) * 10000,
        "net_bps": (exit_notional - 1 - fees - funding_cost) * 10000,
        "fees_bps": fees * 10000,
        "funding_adverse_bps": funding_cost * 10000,
    }
