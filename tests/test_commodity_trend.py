from decimal import Decimal as D

from hyperbot2.research.commodity_trend import TrendFrame, simulate_trend, trend_frames
from hyperbot2.research.rotation import HOUR
from hyperbot2.research.volume import VolumeBar


def test_breakout_excludes_signal_bar_from_channel_and_future() -> None:
    bars = [
        VolumeBar(i * HOUR, D(100), D(101), D(99), D(100), D(10)) for i in range(240)
    ]
    bars.append(VolumeBar(240 * HOUR, D(100), D(111), D(99), D(110), D(10)))
    before = trend_frames(bars)
    assert before[-1].side == 1
    bars.append(VolumeBar(241 * HOUR, D(110), D(1000), D(1), D(500), D(10)))
    assert trend_frames(bars)[:-1] == before


def test_latent_profit_is_marked_and_gap_loss_not_clipped_to_stop() -> None:
    bars = [
        VolumeBar(0, D(100), D(101), D(99), D(100), D(10)),
        VolumeBar(HOUR, D(100), D(120), D(99), D(110), D(10)),
        VolumeBar(2 * HOUR, D(70), D(80), D(60), D(75), D(10)),
    ]
    result = simulate_trend(
        {"TEST": bars},
        {"TEST": {b.time: D(0) for b in bars}},
        {"TEST": [TrendFrame(1, D(10)), TrendFrame(0, D(10)), TrendFrame(0, D(10))]},
        {"TEST": D(0)},
        {"TEST": 4},
        gross_cap=D(1),
        scenario="zero_cost",
        monthly_infra=D(0),
    )
    assert result["curve"][1]["unrealized_pnl"] == 10
    assert result["curve"][1]["equity"] == 1010
    assert result["cycles"][0]["exit_price"] == 70
    assert result["summary"]["net_total_usd"] == -30
    assert (
        result["summary"]["max_ohlc_drawdown_envelope"]
        >= result["summary"]["max_hourly_drawdown"]
    )


def test_drawdown_halt_preserves_overshoot_and_prevents_later_reentry() -> None:
    bars = [
        VolumeBar(i * HOUR, D(100), D(101), D(99), D(100), D(10)) for i in range(2)
    ] + [VolumeBar(i * HOUR, D(10), D(11), D(9), D(10), D(10)) for i in range(2, 32)]
    result = simulate_trend(
        {"TEST": bars},
        {"TEST": {b.time: D(0) for b in bars}},
        {"TEST": [TrendFrame(1, D(2)) for b in bars]},
        {"TEST": D(0)},
        {"TEST": 4},
        gross_cap=D(1),
        scenario="zero_cost",
        monthly_infra=D(0),
    )
    assert result["summary"]["halted"]
    assert result["summary"]["max_hourly_drawdown"] > D("0.2")
    assert result["summary"]["end_equity"] < 800
    assert len(result["cycles"]) == 1
    assert result["curve"][-1]["positions"] == 0
