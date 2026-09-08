"""Fixed aggressive-flow hypotheses and taker round-trip accounting."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_DOWN, Decimal

D = Decimal


def micro_signal(
    *,
    rule: str,
    coin: str,
    valid: bool,
    flow: Decimal,
    notional: Decimal,
    count: int,
    imbalance: Decimal,
    return_bps: Decimal,
    spread_bps: Decimal,
) -> int:
    if rule not in {"continuation", "absorption"} or coin not in {"BTC", "ETH", "HYPE"}:
        raise ValueError("unregistered microstructure rule or coin")
    if (
        not valid
        or count < 30
        or notional < (50_000 if coin == "HYPE" else 100_000)
        or abs(flow) < D("0.7")
        or spread_bps > 2
    ):
        return 0
    direction = 1 if flow > 0 else -1
    if rule == "continuation":
        return (
            direction
            if direction * imbalance >= D("0.5") and direction * return_bps >= 5
            else 0
        )
    return (
        -direction
        if direction * imbalance <= D("-0.5") and direction * return_bps <= 2
        else 0
    )


@dataclass(frozen=True, slots=True)
class MicroQuote:
    time: int
    bid: Decimal
    ask: Decimal
    bid_size: Decimal
    ask_size: Decimal


def taker_return(
    coin: str,
    side: int,
    entry: MicroQuote,
    exit: MicroQuote,
    funding: tuple[tuple[int, Decimal, Decimal], ...],
    *,
    stress: bool = False,
) -> dict[str, Decimal] | None:
    if (
        side not in {-1, 1}
        or coin not in {"BTC", "ETH", "HYPE"}
        or exit.time <= entry.time
    ):
        raise ValueError("valid side, coin and chronological quotes required")
    if any(
        not value.is_finite() or value <= 0
        for quote in (entry, exit)
        for value in (quote.bid, quote.ask, quote.bid_size, quote.ask_size)
    ) or any(q.bid >= q.ask for q in (entry, exit)):
        raise ValueError("valid uncrossed quotes required")
    raw_entry, raw_exit = (entry.ask, exit.bid) if side == 1 else (entry.bid, exit.ask)
    quantum = D(1).scaleb(-{"BTC": 5, "ETH": 4, "HYPE": 2}[coin])
    quantity = (D(50) / raw_entry).quantize(quantum, rounding=ROUND_DOWN)
    entry_size = entry.ask_size if side == 1 else entry.bid_size
    exit_size = exit.bid_size if side == 1 else exit.ask_size
    if quantity * raw_entry < 10 or quantity > min(entry_size, exit_size) * D("0.1"):
        return None
    slippage, fee = (
        (D("0.0003"), D("0.0007")) if stress else (D("0.0001"), D("0.00045"))
    )
    px = raw_entry * (1 + side * slippage)
    end = raw_exit * (1 - side * slippage)
    funding_cost = (
        side
        * quantity
        * sum(
            (
                rate * oracle_proxy
                for time, rate, oracle_proxy in funding
                if entry.time < time <= exit.time
            ),
            D(0),
        )
    )
    net = side * quantity * (end - px) - quantity * (px + end) * fee - funding_cost
    entry_mid = (entry.bid + entry.ask) / 2
    exit_mid = (exit.bid + exit.ask) / 2
    return {
        "quantity": quantity,
        "entry_notional": quantity * raw_entry,
        "pnl_usd": net,
        "net_bps": net / (quantity * raw_entry) * 10_000,
        "mid_markout_bps": side * (exit_mid / entry_mid - 1) * 10_000,
        "funding_cost_usd": funding_cost,
    }
