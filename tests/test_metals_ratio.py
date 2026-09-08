from decimal import Decimal as D

from hyperbot2.research.metals_ratio import (
    GOLD,
    SILVER,
    RatioFrame,
    ratio_frames,
    simulate_ratio,
)
from hyperbot2.research.rotation import HOUR
from hyperbot2.research.volume import VolumeBar


def test_ratio_statistics_exclude_current_and_future_values() -> None:
    xs = [D("0.01") if i % 2 else D(0) for i in range(240)] + [D("0.017")]
    frames = ratio_frames(xs)
    assert frames[-1] is not None
    assert frames[-1].mean == D("0.005")
    assert 2 < frames[-1].z < 4
    assert ratio_frames(xs + [D(100)])[:-1] == frames
    assert ratio_frames([D(0)] * 241)[-1] is None


def test_dollar_hedge_and_funding_cash_reconcile() -> None:
    bs = [
        VolumeBar(0, D(100), D(100), D(100), D(100), D(10)),
        VolumeBar(HOUR, D(100), D(100), D(100), D(100), D(10)),
        VolumeBar(2 * HOUR, D(110), D(110), D(110), D(110), D(10)),
    ]
    # Frozen statistics imply a short gold/long silver trade with equal dollars.
    frames = [RatioFrame(D("-0.025"), D("0.01"), D("2.5")) for _ in bs]
    result = simulate_ratio(
        {GOLD: bs, SILVER: bs},
        {GOLD: {b.time: D(0) for b in bs}, SILVER: {b.time: D(0) for b in bs}},
        frames,
        {GOLD: D(0), SILVER: D(0)},
        {GOLD: 4, SILVER: 2},
        gross_cap=D(1),
        scenario="zero_cost",
        monthly_infra=D(0),
    )
    assert result["summary"]["net_total_usd"] == 0
    assert result["cycles"][0]["gold_quantity"] == 5
    assert result["cycles"][0]["silver_quantity"] == 5
    assert result["curve"][1]["position_open"]

    kwargs = dict(
        bars={GOLD: bs, SILVER: bs},
        frames=frames,
        fees={GOLD: D(0), SILVER: D(0)},
        decimals={GOLD: 4, SILVER: 2},
        gross_cap=D(1),
        scenario="base",
        monthly_infra=D(0),
    )
    zero = {c: {b.time: D(0) for b in bs} for c in (GOLD, SILVER)}
    baseline = simulate_ratio(funding=zero, **kwargs)
    paid = {c: dict(rates) for c, rates in zero.items()}
    paid[GOLD][2 * HOUR] = D("0.001")
    credit = simulate_ratio(funding=paid, **kwargs)
    expected = baseline["cycles"][0]["gold_quantity"] * 110 * D("0.001")
    assert abs(
        credit["summary"]["end_equity"] - baseline["summary"]["end_equity"] - expected
    ) < D("1e-20")


def test_portfolio_halt_counts_next_open_gap_instead_of_clipping_loss() -> None:
    gs = [D(100), D(100), D(160)] + [D(170)] * 29
    gold = [VolumeBar(i * HOUR, p, p, p, p, D(10)) for i, p in enumerate(gs)]
    silver = [
        VolumeBar(i * HOUR, D(100), D(100), D(100), D(100), D(10))
        for i in range(len(gs))
    ]
    result = simulate_ratio(
        {GOLD: gold, SILVER: silver},
        {c: {i * HOUR: D(0) for i in range(len(gs))} for c in (GOLD, SILVER)},
        [RatioFrame(D("-0.025"), D("0.01"), D("2.5")) for _ in gs],
        {GOLD: D(0), SILVER: D(0)},
        {GOLD: 4, SILVER: 2},
        gross_cap=D(1),
        scenario="zero_cost",
        monthly_infra=D(0),
    )
    assert result["summary"]["end_equity"] == 650
    assert result["summary"]["max_hourly_drawdown"] == D("0.35")
    assert result["summary"]["halted"]
    assert len(result["cycles"]) == 1
    assert result["cycles"][0]["reason"] == "drawdown_next_open"


def test_asset_mapping_calendar_and_holding_override_preserve_pair_accounting() -> None:
    bs = [VolumeBar(i * HOUR, D(100), D(100), D(100), D(100), D(10)) for i in range(6)]
    common = dict(
        bars={"A": bs, "B": bs},
        funding={c: {b.time: D(0) for b in bs} for c in ("A", "B")},
        frames=[RatioFrame(D("-0.025"), D("0.01"), D("2.5")) for b in bs],
        fees={"A": D(0), "B": D(0)},
        decimals={"A": 4, "B": 2},
        gross_cap=D(1),
        scenario="zero_cost",
        monthly_infra=D(0),
        assets=("A", "B"),
        max_holding_hours=2,
    )
    excluded = simulate_ratio(**common, allowed_entries=frozenset())
    assert not excluded["cycles"]
    included = simulate_ratio(**common, allowed_entries=frozenset({2 * HOUR}))
    assert included["cycles"][0]["opened_ms"] == 2 * HOUR
    assert included["cycles"][0]["closed_ms"] == 4 * HOUR
    assert included["cycles"][0]["reason"] == "time"
    assert included["summary"]["end_equity"] == 1000
