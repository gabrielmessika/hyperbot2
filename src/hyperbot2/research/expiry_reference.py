"""Causal, quote-currency-specific reference qualification for exploration."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any


def okx_usdt_midpoint(
    record: dict[str, Any], *, underlying: str, decision_ms: int
) -> Decimal | None:
    if underlying not in {"BTC", "ETH", "SOL"}:
        return None
    logged = int(record["logged_ms"])
    if not 0 <= decision_ms - logged <= 60_000:
        return None
    quotes = [r for r in record["reference_sources"] if r["source"] == "okx"]
    if len(quotes) != 1:
        return None
    raw = quotes[0].get("raw", {})
    if raw.get("instId") != underlying + "-USDT" or raw.get("instType") != "SPOT":
        return None
    try:
        exchange_ms = int(raw["ts"])
        bid, ask = Decimal(str(raw["bidPx"])), Decimal(str(raw["askPx"]))
    except (KeyError, ValueError, TypeError, InvalidOperation):
        return None
    if (
        not 0 <= decision_ms - exchange_ms <= 60_000
        or exchange_ms > logged
        or not bid.is_finite()
        or not ask.is_finite()
        or not 0 < bid <= ask
    ):
        return None
    return (bid + ask) / 2
