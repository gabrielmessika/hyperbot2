import math
import runpy
from decimal import Decimal as D
from pathlib import Path

import pytest

from hyperbot2.research.pairs import PairModel

ROOT = Path(__file__).resolve().parents[1]
MODULE = runpy.run_path(str(ROOT / "scripts/investigate_pairs.py"))
Candle = runpy.run_path(str(ROOT / "scripts/evaluate_alternatives.py"))["Candle"]


def test_flat_pair_pays_four_executions_and_carried_hourly_funding():
    hour = MODULE["HOUR"]
    candles = {
        c: [Candle(i * hour, p, p, p, p) for i in range(30)]
        for c, p in (("BTC", D(100)), ("ETH", D(10)))
    }
    model = PairModel(math.log(10) - math.log(100) - 0.025, 1, 0.01, 1, 0.9, 6)
    events = [{"index": 0, "model": model, "z": 2.5, "eth_side": -1}]
    funding = {c: {i * hour: D(".0001") for i in range(30)} for c in candles}
    result = MODULE["simulate"](
        candles, funding, events, 0, 30 * hour, "base", {"BTC": 5, "ETH": 4}
    )
    assert result["round_trips"] == 1
    trade = result["cycles"][0]
    assert trade["closed_ms"] - trade["opened_ms"] == 24 * hour
    assert float(trade["fees"]) == pytest.approx(0.09, abs=0.001)
    assert float(trade["funding_adverse"]) == pytest.approx(0.24, abs=0.001)
    assert float(trade["net_pnl"]) == pytest.approx(-0.37, abs=0.002)
    assert abs(trade["funding_signed_proxy"]) < D(".001")
    assert result["net_trading_usd"] == trade["net_pnl"]
    assert not result["promotion_authorized"]


def test_common_proportional_move_cancels_equal_dollar_pair():
    pnl = MODULE["pnl"](
        {"ETH": D(1), "BTC": D(".1")},
        {"ETH": 1, "BTC": -1},
        {"ETH": D(100), "BTC": D(1000)},
        {"ETH": D(105), "BTC": D(1050)},
    )
    assert pnl == 0
