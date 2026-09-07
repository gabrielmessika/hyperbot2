"""Explicit JSON window schema for bounded replay; Decimal values stay strings."""

from __future__ import annotations

from dataclasses import asdict
from decimal import Decimal
from typing import Any

from hyperbot2.models import BookLevel, DatasetTier, Side
from hyperbot2.outcomes.contracts import (
    FairValue,
    FeeSchedule,
    OutcomeBook,
    OutcomeDefinition,
)
from hyperbot2.outcomes.session import OutcomeTrade, OutcomeWindow


def window_payload(window: OutcomeWindow) -> dict[str, Any]:
    return {"schema_version": 1, **asdict(window)}


def _book(raw: dict[str, Any]) -> OutcomeBook:
    r = dict(raw)
    for side in ("bids", "asks"):
        r[side] = tuple(
            BookLevel(Decimal(x["price"]), Decimal(x["size"])) for x in r[side]
        )
    r["tier"] = DatasetTier(r["tier"])
    for name in ("full_depth", "queue_qualified", "dual_priority_qualified"):
        if name in r and type(r[name]) is not bool:
            raise ValueError("book qualification must be boolean")
    return OutcomeBook(**r)


def window_from_payload(raw: dict[str, Any]) -> OutcomeWindow:
    allowed = {
        "schema_version",
        "now_ms",
        "definition",
        "book",
        "fair",
        "future_books",
        "trades",
        "healthy",
        "exposure_healthy",
    }
    if set(raw) - allowed or raw.get("schema_version") != 1:
        raise ValueError("unknown window schema/fields")
    d = dict(raw["definition"])
    for name in ("strike", "tick", "size_increment"):
        if d.get(name) is not None:
            d[name] = Decimal(d[name])
    if d.get("fees") is not None:
        fees = dict(d["fees"])
        for name in ("maker_close_rate", "taker_close_rate", "settlement_rate"):
            fees[name] = Decimal(fees[name])
        d["fees"] = FeeSchedule(**fees)
    if (
        type(d.get("active", False)) is not bool
        or type(raw.get("healthy", True)) is not bool
        or type(raw.get("exposure_healthy", True)) is not bool
    ):
        raise ValueError("status must be boolean")
    f = raw.get("fair")
    fair = None
    if f is not None:
        f = dict(f)
        for name in ("probability", "uncertainty", "adverse_selection"):
            f[name] = Decimal(f[name])
        fair = FairValue(**f)
    trades = []
    for t in raw.get("trades", []):
        t = dict(t)
        t["aggressor"] = Side(t["aggressor"])
        t["price"] = Decimal(t["price"])
        t["size"] = Decimal(t["size"])
        trades.append(OutcomeTrade(**t))
    return OutcomeWindow(
        int(raw["now_ms"]),
        OutcomeDefinition(**d),
        _book(raw["book"]),
        fair,
        tuple(_book(x) for x in raw.get("future_books", [])),
        tuple(trades),
        raw.get("healthy", True),
        raw.get("exposure_healthy", True),
    )
