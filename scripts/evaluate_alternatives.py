"""Fixed-rule hourly research screens, never an execution qualification."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

from hyperbot2.research.artifacts import checked_input, file_sha256, write_json

D = Decimal
HOUR = 3_600_000
DAY = HOUR * 24
COINS = ("BTC", "ETH", "SOL", "HYPE")


@dataclass(frozen=True)
class Candle:
    time: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal


@dataclass(frozen=True)
class Position:
    coin: str
    side: int
    quantity: Decimal
    price: Decimal
    stop: Decimal
    opened: int
    entry_fee: Decimal
    funding: Decimal = D(0)


def signal(rows: list[Candle], index: int, strategy: str) -> tuple[int, Decimal]:
    """Only closed bars through index are accessed; prior channel excludes index."""
    if index < 25:
        return 0, D(0)
    previous = rows[index - 24 : index]
    current = rows[index]
    if strategy == "breakout24":
        side = (
            1
            if current.close > max(c.high for c in previous)
            else (-1 if current.close < min(c.low for c in previous) else 0)
        )
    elif strategy == "reversion24":
        mean = sum(c.close for c in previous) / 24
        deviation = (sum((c.close - mean) ** 2 for c in previous) / 24).sqrt()
        side = (
            1
            if current.close < mean - 2 * deviation
            else (-1 if current.close > mean + 2 * deviation else 0)
        )
    else:
        raise ValueError("unregistered strategy")
    atr = (
        sum(
            max(
                rows[j].high - rows[j].low,
                abs(rows[j].high - rows[j - 1].close),
                abs(rows[j].low - rows[j - 1].close),
            )
            for j in range(index - 23, index + 1)
        )
        / 24
    )
    return side, 2 * atr


def stop_price(position: Position, bar: Candle) -> Decimal | None:
    if position.side == 1 and bar.low <= position.stop:
        return min(position.stop, bar.open)
    if position.side == -1 and bar.high >= position.stop:
        return max(position.stop, bar.open)
    return None


def load_history(
    root: Path,
) -> tuple[
    dict[str, list[Candle]], dict[str, dict[int, Decimal]], int, int, dict[str, Any]
]:
    checked_input(root / "manifest.json")
    manifest = json.loads((root / "manifest.json").read_text())
    start, end = manifest["start_ms"], manifest["end_ms_exclusive"]
    candles: dict[str, list[Candle]] = {}
    funding: dict[str, dict[int, Decimal]] = defaultdict(dict)
    provenance = {}
    for request in manifest["requests"]:
        p = Path(request["path"])
        checksum = checked_input(p)
        if checksum != request["sha256"]:
            raise ValueError("manifest checksum mismatch")
        provenance[str(p)] = checksum
        row = json.loads(p.read_text())
        query, data = row["request"], row["response"]
        if query["type"] == "candleSnapshot":
            coin = query["req"]["coin"]
            parsed = []
            for c in data:
                if c["s"] != coin or c["i"] != "1h" or c["T"] != c["t"] + HOUR - 1:
                    raise ValueError("candle identity or interval mismatch")
                bar = Candle(int(c["t"]), *(D(c[k]) for k in ("o", "h", "l", "c")))
                if (
                    not all(
                        x.is_finite() and x > 0
                        for x in (bar.open, bar.high, bar.low, bar.close)
                    )
                    or not bar.low
                    <= min(bar.open, bar.close)
                    <= max(bar.open, bar.close)
                    <= bar.high
                ):
                    raise ValueError("invalid OHLC")
                if start <= bar.time < end:
                    parsed.append(bar)
            candles[coin] = sorted(parsed, key=lambda c: c.time)
        elif query["type"] == "fundingHistory":
            coin = query["coin"]
            for f in data:
                bucket = int(f["time"]) // HOUR * HOUR
                if f["coin"] != coin or bucket in funding[coin]:
                    raise ValueError("funding identity/duplicate hour")
                rate = D(f["fundingRate"])
                if not rate.is_finite():
                    raise ValueError("non-finite funding")
                funding[coin][bucket] = rate
    expected = list(range(start, end, HOUR))
    for coin in COINS:
        if [c.time for c in candles[coin]] != expected:
            raise ValueError(f"candle gap/duplicate: {coin}")
        if sorted(funding[coin]) != expected:
            raise ValueError(f"funding gap/duplicate: {coin}")
    return candles, dict(funding), start, end, provenance


def simulate(
    candles: dict[str, list[Candle]],
    funding: dict[str, dict[int, Decimal]],
    start: int,
    end: int,
    strategy: str,
    scenario: str,
) -> dict[str, Any]:
    costs = {
        "base": (D("0.00045"), D("0.0002"), 0),
        "cost_stress": (D("0.0009"), D("0.0005"), 0),
        "delay_stress": (D("0.00045"), D("0.0002"), 1),
        "zero_cost_control": (D(0), D(0), 0),
    }
    fee, slippage, delay = costs[scenario]
    positions: dict[str, Position] = {}
    cash = peak = D(1000)
    day_open = month_peak = cash
    last_day = last_month = -1
    blocked_today = hard_stop = False
    cycles: list[dict[str, Any]] = []
    daily: dict[int, Decimal] = {}
    drawdown = D(0)
    hours = 0

    def close(coin: str, raw: Decimal, at: int, reason: str) -> None:
        nonlocal cash
        p = positions.pop(coin)
        execution = raw * (1 - p.side * slippage)
        exit_fee = p.quantity * execution * fee
        gross = p.side * p.quantity * (execution - p.price)
        cash += gross - exit_fee
        cycles.append(
            {
                "coin": coin,
                "side": p.side,
                "opened_ms": p.opened,
                "closed_ms": at,
                "entry_price": p.price,
                "exit_price": execution,
                "quantity": p.quantity,
                "gross_pnl": gross,
                "fees": p.entry_fee + exit_fee,
                "funding_cost": p.funding,
                "net_pnl": gross - p.entry_fee - exit_fee - p.funding,
                "reason": reason,
            }
        )

    for index, anchor in enumerate(candles["BTC"]):
        at = anchor.time
        if not start <= at < end:
            continue
        hours += 1
        day, month = at // DAY, (at - start) // (30 * DAY)
        open_equity = cash + sum(
            p.side * p.quantity * (candles[c][index].open - p.price)
            for c, p in positions.items()
        )
        if day != last_day:
            day_open, last_day, blocked_today = open_equity, day, False
        if month != last_month:
            month_peak, last_month = open_equity, month
        exited = set()
        for coin, old in tuple(positions.items()):
            bar = candles[coin][index]
            # Adverse absolute funding is a stress proxy, never a predicted credit.
            charge = (
                D(0)
                if scenario == "zero_cost_control"
                else (old.quantity * bar.open * abs(funding[coin][at]))
            )
            positions[coin] = replace(old, funding=old.funding + charge)
            cash -= charge
            if at - old.opened >= 24 * HOUR:
                close(coin, bar.open, at, "time")
                exited.add(coin)
        if not hard_stop and not blocked_today:
            for coin in COINS:
                if coin in positions or coin in exited:
                    continue
                source_index = index - 1 - delay
                if source_index < 0 or candles[coin][source_index].time < start:
                    continue
                side, distance = signal(candles[coin], source_index, strategy)
                if side == 0 or distance <= 0:
                    continue
                entry = candles[coin][index].open * (1 + side * slippage)
                multiplier = D("0.5") if month_peak - open_equity >= 80 else D(1)
                quantity = min(D(50) / entry, D("2.5") / distance) * multiplier
                if quantity * entry < 10 or entry - side * distance <= 0:
                    continue
                entry_fee = quantity * entry * fee
                cash -= entry_fee
                positions[coin] = Position(
                    coin, side, quantity, entry, entry - side * distance, at, entry_fee
                )
        for coin, position in tuple(positions.items()):
            price = stop_price(position, candles[coin][index])
            if price is not None:
                close(coin, price, at + HOUR - 1, "stop_time_within_bar_unknown")
        equity = cash + sum(
            p.side * p.quantity * (candles[c][index].close - p.price)
            for c, p in positions.items()
        )
        peak, month_peak = max(peak, equity), max(month_peak, equity)
        drawdown = max(drawdown, peak - equity)
        if day_open - equity >= 15 or peak - equity >= 120:
            hard_stop = hard_stop or peak - equity >= 120
            blocked_today = True
            for coin in tuple(positions):
                close(coin, candles[coin][index].close, at + HOUR - 1, "portfolio_stop")
            equity = cash
        if at + HOUR == end:
            for coin in tuple(positions):
                close(coin, candles[coin][index].close, end, "fold_terminal")
            equity = cash
        drawdown = max(drawdown, peak - equity)
        daily[day] = equity
    gains = sum(max(c["net_pnl"], D(0)) for c in cycles)
    losses = -sum(min(c["net_pnl"], D(0)) for c in cycles)
    infra = D(20) * D(hours) / 720
    assert abs(cash - 1000 - sum(c["net_pnl"] for c in cycles)) < D("1e-20")
    return {
        "strategy": strategy,
        "scenario": scenario,
        "start_ms": start,
        "end_ms_exclusive": end,
        "hours": hours,
        "cycles": cycles,
        "round_trips": len(cycles),
        "net_trading_usd": cash - 1000,
        "infrastructure_usd": infra,
        "net_after_infra_usd": cash - 1000 - infra,
        "profit_factor": gains / losses if losses else None,
        "max_close_to_close_drawdown_usd": drawdown,
        "daily_equity": daily,
        "hard_stop": hard_stop,
        "verdict": "EXPLORATORY_ONLY",
        "promotion_authorized": False,
        "limits": [
            "historical OHLC, no observed entry depth or receipt causality",
            "funding charged adversely at hourly open on carried positions",
            "intrabar ordering and portfolio loss excursions unknown",
            "stops do not guarantee losses bounded in gaps",
            "fixed notionals; no leverage or parameter optimization",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--phase", choices=("development", "holdout"), required=True)
    args = parser.parse_args()
    candles, funding, start, end, sources = load_history(args.history)
    args.output.mkdir(parents=True, exist_ok=False)
    blocks = (0, 1, 2) if args.phase == "development" else (3, 4, 5)
    rows = []
    for strategy in ("breakout24", "reversion24"):
        for scenario in ("base", "cost_stress", "delay_stress", "zero_cost_control"):
            for block in blocks:
                a, b = start + block * 30 * DAY, start + (block + 1) * 30 * DAY
                result = simulate(candles, funding, a, b, strategy, scenario)
                path = args.output / f"{strategy}-{scenario}-{block}.json"
                checksum = write_json(path, result)
                rows.append(
                    {
                        k: v
                        for k, v in result.items()
                        if k not in ("cycles", "daily_equity", "limits")
                    }
                    | {"block": block, "path": str(path), "sha256": checksum}
                )
    carry = {}
    for coin in COINS:
        carry[coin] = [
            {
                "block": block,
                "hours": 720,
                "constant_500_usd_short_funding_usd": D(500)
                * sum(
                    rate
                    for at, rate in funding[coin].items()
                    if start + block * 30 * DAY <= at < start + (block + 1) * 30 * DAY
                ),
            }
            for block in blocks
        ]
    write_json(
        args.output / "summary.json",
        {
            "phase": args.phase,
            "source_hashes": sources,
            "script_sha256": file_sha256(Path(__file__)),
            "simulations": rows,
            "carry_favorable_benchmark": carry,
            "history_start_ms": start,
            "history_end_ms_exclusive": end,
            "candles_and_funding_complete": True,
            "hours_per_coin": len(candles["BTC"]),
            "carry_limits": (
                "No fees, basis, borrowing, rebalancing or wrapper risk priced"
            ),
            "live_authorized": False,
        },
    )
    print(args.output / "summary.json")


if __name__ == "__main__":
    main()
