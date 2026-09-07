"""Research accounting, causal signals and gap handling."""

import runpy
from decimal import Decimal
from pathlib import Path

module = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "scripts/evaluate_alternatives.py")
)
D = Decimal
Candle = module["Candle"]
Position = module["Position"]


def test_signal_ignores_all_future_bars() -> None:
    rows = [Candle(i * 3600000, D(100), D(101), D(99), D(100)) for i in range(26)]
    rows.append(Candle(26 * 3600000, D(100), D(103), D(99), D(102)))
    signal = module["signal"]
    assert signal(rows, 26, "breakout24")[0] == 1
    poisoned = rows + [Candle(27 * 3600000, D(1), D(1), D(1), D(1))]
    assert signal(rows, 26, "breakout24") == signal(poisoned, 26, "breakout24")


def test_gap_fills_worse_than_stop_for_both_directions() -> None:
    long = Position("BTC", 1, D(1), D(100), D(95), 0, D(0))
    short = Position("BTC", -1, D(1), D(100), D(105), 0, D(0))
    assert module["stop_price"](long, Candle(0, D(90), D(96), D(89), D(95))) == 90
    assert module["stop_price"](short, Candle(0, D(110), D(112), D(104), D(105))) == 110


def test_round_trip_accounting_and_no_position_across_fold() -> None:
    rows = [Candle(i * 3600000, D(100), D(101), D(99), D(100)) for i in range(26)]
    rows += [Candle(i * 3600000, D(102), D(103), D(101), D(102)) for i in range(26, 40)]
    candles = {coin: rows for coin in module["COINS"]}
    funding = {coin: {c.time: D("0.0001") for c in rows} for coin in candles}
    result = module["simulate"](candles, funding, 0, 40 * 3600000, "breakout24", "base")
    assert result["round_trips"] == 4
    assert all(c["closed_ms"] == 40 * 3600000 for c in result["cycles"])
    assert all(c["funding_cost"] > 0 and c["fees"] > 0 for c in result["cycles"])
    assert result["net_trading_usd"] < 0
    assert abs(
        result["net_trading_usd"] - sum(c["net_pnl"] for c in result["cycles"])
    ) < D("1e-20")
    assert result["promotion_authorized"] is False


def test_no_signal_means_only_infrastructure_cost() -> None:
    rows = [Candle(i * 3600000, D(100), D(101), D(99), D(100)) for i in range(40)]
    candles = {coin: rows for coin in module["COINS"]}
    funding = {coin: {c.time: D(0) for c in rows} for coin in candles}
    result = module["simulate"](candles, funding, 0, 40 * 3600000, "breakout24", "base")
    assert result["round_trips"] == 0
    assert result["net_trading_usd"] == 0
    assert result["net_after_infra_usd"] == -result["infrastructure_usd"]
