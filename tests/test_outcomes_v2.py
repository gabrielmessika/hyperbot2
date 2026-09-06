from __future__ import annotations

import json
from dataclasses import replace
from decimal import Decimal as D
from pathlib import Path

import pytest

from hyperbot2.models import (
    BookLevel,
    DatasetTier,
    EventContext,
    QuoteIntent,
    Side,
    TimeSource,
)
from hyperbot2.outcomes.catalog import discover_recurring
from hyperbot2.outcomes.config import OutcomeConfig, load_config
from hyperbot2.outcomes.contracts import (
    FairValue,
    FeeSchedule,
    Operation,
    OutcomeBook,
    OutcomeDefinition,
    book_from_public,
)
from hyperbot2.outcomes.fair_value import CausalFairValueModel, ReferencePrice
from hyperbot2.outcomes.ledger import OutcomeLedger
from hyperbot2.outcomes.serialization import window_from_payload, window_payload
from hyperbot2.outcomes.session import OutcomeSession, OutcomeTrade, OutcomeWindow
from hyperbot2.outcomes.strategy import SelectiveOutcomeStrategy
from hyperbot2.replay.engine import FillModelKind
from hyperbot2.research.artifacts import (
    BudgetExceeded,
    CampaignBudget,
    checked_input,
    file_sha256,
    write_json,
)
from hyperbot2.research.campaign import run_campaign
from hyperbot2.research.promotion import PromotionEvidence, evaluate_promotion


@pytest.fixture
def definition() -> OutcomeDefinition:
    return OutcomeDefinition(
        1,
        "BTC",
        D("80000"),
        86_400_000,
        0,
        D("0.01"),
        D("0.1"),
        FeeSchedule(D("0.001"), D("0.002"), D("0.003"), 0, 100_000_000, "a" * 64),
        "mark_gt_strike",
        "b" * 64,
        True,
    )


def context() -> EventContext:
    return EventContext("synthetic-test", "test", "c" * 64, TimeSource.REPLAY)


def book(now: int = 1000, **changes: object) -> OutcomeBook:
    value = OutcomeBook(
        1,
        now,
        now,
        now,
        (BookLevel(D("0.45"), D("1")), BookLevel(D("0.30"), D("100"))),
        (BookLevel(D("0.55"), D("1")), BookLevel(D("0.70"), D("100"))),
        DatasetTier.A,
        True,
        True,
        True,
    )
    return replace(value, **changes)


def fair(now: int = 1000, **changes: object) -> FairValue:
    return replace(
        FairValue(D("0.50"), now, now, 0, D("0.01"), D("0.01"), "d" * 64), **changes
    )


def intent(identity: str, side: Side, price: str, size: str) -> QuoteIntent:
    return QuoteIntent(
        context(),
        identity,
        "test",
        "outcome:1",
        side,
        D(price),
        D(size),
        1000,
        D("0.5"),
        D(0),
        D(0),
        ("test",),
    )


def window(definition: OutcomeDefinition, **changes: object) -> OutcomeWindow:
    value = OutcomeWindow(
        1000,
        definition,
        book(),
        fair(),
        tuple(book(t) for t in (1300, 1600, 1900, 2200, 2350)),
        (
            OutcomeTrade(
                1, "match-1", 0, 1700, 1700, 1700, Side.SELL, D("0.45"), D("100")
            ),
        ),
    )
    return replace(value, **changes)


@pytest.mark.parametrize(
    ("operation", "expected"),
    [
        (Operation.OPEN, "0"),
        (Operation.MAKER_CLOSE, "0.01"),
        (Operation.TAKER_CLOSE, "0.02"),
        (Operation.SETTLE, "0.03"),
    ],
)
def test_fees_by_operation(
    definition: OutcomeDefinition, operation: Operation, expected: str
) -> None:
    assert definition.fees.cost(operation, D(20), D("0.5")) == D(expected)


def test_fifo_partial_fills_cash_fees_and_dedup(definition: OutcomeDefinition) -> None:
    ledger = OutcomeLedger()
    ledger.reserve(intent("buy", Side.BUY, "0.5", "20"), definition)
    assert ledger.available_cash == D(990)
    args = dict(
        fill_id="b1",
        intent_id="buy",
        quantity=D(8),
        price=D("0.5"),
        now_ms=1000,
        definition=definition,
    )
    assert ledger.fill(**args)
    assert not ledger.fill(**args)
    assert ledger.available_cash == D(990)
    ledger.fill(**{**args, "fill_id": "b2", "quantity": D(12)})
    ledger.reserve(intent("sell", Side.SELL, "0.6", "20"), definition)
    assert ledger.available_quantity(1) == 0
    ledger.fill(
        fill_id="s1",
        intent_id="sell",
        quantity=D(5),
        price=D("0.6"),
        now_ms=2000,
        definition=definition,
    )
    ledger.fill(
        fill_id="s2",
        intent_id="sell",
        quantity=D(15),
        price=D("0.6"),
        now_ms=2100,
        definition=definition,
    )
    assert ledger.cash == D("1001.988")
    assert ledger.fees_paid == D("0.012")
    assert ledger.realized == ledger.cash - ledger.initial
    assert ledger.quantity(1) == 0
    assert not ledger.reservations


def test_reservations_survive_until_explicit_release(
    definition: OutcomeDefinition,
) -> None:
    ledger = OutcomeLedger(D(10))
    q = intent("buy", Side.BUY, "0.5", "20")
    ledger.reserve(q, definition)
    with pytest.raises(ValueError, match="cash"):
        ledger.reserve(replace(q, intent_id="b2"), definition)
    with pytest.raises(ValueError, match="naked"):
        ledger.reserve(intent("sell", Side.SELL, "0.6", "1"), definition)
    ledger.release(q.intent_id)
    assert ledger.available_cash == 10


@pytest.mark.parametrize(
    ("quantity", "price", "now", "error"),
    [
        ("21", "0.5", 1000, "exceeds"),
        ("1", "0.6", 1000, "limit"),
        ("1", "0.5", 100_000_000, "fees"),
        ("NaN", "0.5", 1000, "exceeds"),
    ],
)
def test_invalid_fill_is_atomic(
    definition: OutcomeDefinition, quantity: str, price: str, now: int, error: str
) -> None:
    ledger = OutcomeLedger()
    ledger.reserve(intent("buy", Side.BUY, "0.5", "20"), definition)
    with pytest.raises(ValueError, match=error):
        ledger.fill(
            fill_id="bad",
            intent_id="buy",
            quantity=D(quantity),
            price=D(price),
            now_ms=now,
            definition=definition,
        )
    assert ledger.cash == 1000 and ledger.quantity(1) == 0


def test_terminal_conservation_and_stale_valuation(
    definition: OutcomeDefinition,
) -> None:
    ledger = OutcomeLedger()
    ledger.reserve(intent("buy", Side.BUY, "0.5", "20"), definition)
    ledger.fill(
        fill_id="b",
        intent_id="buy",
        quantity=D(20),
        price=D("0.5"),
        now_ms=1000,
        definition=definition,
    )
    assert ledger.portfolio(2000, {1: definition}, {1: book()}).equity_usd == 990
    with pytest.raises(ValueError, match="before expiry"):
        ledger.terminal_close(definition, now_ms=2000, payout=D(1), settlement=True)
    ledger.terminal_close(
        definition, now_ms=definition.expiry_ms, payout=D(1), settlement=True
    )
    assert ledger.cash == D("1009.94")
    assert ledger.realized == D("9.94")
    ledger.terminal_close(
        definition, now_ms=definition.expiry_ms, payout=D(1), settlement=True
    )
    assert ledger.cash == D("1009.94")


def decide(definition: OutcomeDefinition, **changes: object):
    args = dict(
        context=context(),
        now_ms=1000,
        definition=definition,
        book=book(),
        fair=fair(),
        ledger=OutcomeLedger(),
        definitions={1: definition},
        books={1: book()},
    )
    args.update(changes)
    return SelectiveOutcomeStrategy(OutcomeConfig()).decide(**args)


def test_strategy_reserves_only_funded_alo_buy(definition: OutcomeDefinition) -> None:
    ledger = OutcomeLedger()
    result = decide(definition, ledger=ledger)
    assert len(result.approved) == 1
    q = result.approved[0]
    assert q.side is Side.BUY and q.price == D("0.45")
    assert D(10) <= q.price * q.size < D("10.1")
    assert q.intent_id in ledger.reservations
    assert "no_unreserved_sale_inventory" in result.reasons


def test_action_budget_prepays_cancellation(definition: OutcomeDefinition) -> None:
    strategy = SelectiveOutcomeStrategy(OutcomeConfig(research_action_budget=2))
    ledger = OutcomeLedger()
    args = dict(
        context=context(),
        now_ms=1000,
        definition=definition,
        book=book(),
        fair=fair(),
        ledger=ledger,
        definitions={1: definition},
        books={1: book()},
    )
    assert len(strategy.decide(**args).approved) == 1
    assert strategy.remaining_actions == 0
    assert "simulated_action_budget_exhausted" in strategy.decide(**args).reasons


def test_optimistic_missing_fees_is_data_blocked(definition: OutcomeDefinition) -> None:
    session = OutcomeSession(OutcomeConfig(), context(), FillModelKind.OPTIMISTIC_TOUCH)
    session.process(window(replace(definition, fees=None)))
    result = session.finish()
    assert result["verdict"] == "DATA_BLOCKED"
    assert result["net_pnl_usd"] is None


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("active", False, "market_status_unqualified"),
        ("fees", None, "fees_unknown_or_expired"),
        ("tick", None, "tick_or_lot_unknown"),
        ("settlement_rule", "oracle", "settlement_rule_unqualified"),
        ("specification_sha256", "z" * 64, "specification_provenance_missing"),
        ("expiry_ms", 1_800_500, "near_expiry"),
    ],
)
def test_strategy_fails_closed_on_missing_definition(
    definition: OutcomeDefinition, field: str, value: object, reason: str
) -> None:
    result = decide(replace(definition, **{field: value}))
    assert not result.approved and reason in result.reasons


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"book": book(899)}, "insufficient_causal_freshness"),
        ({"book": book(1001)}, "clock_ambiguity"),
        ({"fair": None}, "fair_value_missing"),
        ({"fair": fair(1001)}, "fair_value_future_or_stale"),
        ({"fair": fair(probability=D("0.1"))}, "probability_outside_range"),
        ({"healthy": False}, "feed_unhealthy"),
    ],
)
def test_strategy_causality_and_health(
    definition: OutcomeDefinition, changes: dict, reason: str
) -> None:
    result = decide(definition, **changes)
    assert not result.approved and reason in result.reasons


def test_pending_orders_cannot_exceed_settlement_cap(
    definition: OutcomeDefinition,
) -> None:
    ledger = OutcomeLedger()
    assert decide(definition, ledger=ledger).approved
    assert decide(definition, ledger=ledger, now_ms=1001).approved
    third = decide(definition, ledger=ledger, now_ms=1002)
    assert not third.approved
    assert "outcome_settlement_loss_per_market" in third.reasons


@pytest.mark.parametrize("model", [FillModelKind.CENTRAL, FillModelKind.PESSIMISTIC])
def test_session_fills_and_liquidates_without_counting_terminal_as_roundtrip(
    definition: OutcomeDefinition, model: FillModelKind
) -> None:
    session = OutcomeSession(OutcomeConfig(), context(), model)
    session.process(window(definition))
    result = session.finish()
    assert result["counts"]["fills"] == 1
    assert result["terminal_cycles"] == 1 and result["round_trips"] == 0
    assert result["net_pnl_usd"] < 0
    assert session.ledger.quantity(1) == 0 and not session.ledger.reservations
    assert result["promotion_authorized"] is False
    with pytest.raises(ValueError, match="finalized"):
        session.process(window(definition))


def test_shadow_uses_same_strategy_and_accounting(
    definition: OutcomeDefinition,
) -> None:
    results = []
    for shadow in (False, True):
        session = OutcomeSession(
            OutcomeConfig(), context(), FillModelKind.CENTRAL, shadow=shadow
        )
        session.process(window(definition))
        result = session.finish()
        result.pop("shadow_mode")
        results.append(result)
    assert results[0] == results[1]


@pytest.mark.parametrize(
    "bad_book",
    [
        book(tier=DatasetTier.B),
        book(queue_qualified=False),
        book(dual_priority_qualified=False),
    ],
)
def test_session_does_not_promote_legacy_or_unqualified_queue(
    definition: OutcomeDefinition, bad_book: OutcomeBook
) -> None:
    session = OutcomeSession(OutcomeConfig(), context(), FillModelKind.CENTRAL)
    session.process(window(definition, book=bad_book))
    result = session.finish()
    assert result["verdict"] == "DATA_BLOCKED" and result["net_pnl_usd"] is None


def test_missing_future_exposure_invalidates_whole_session(
    definition: OutcomeDefinition,
) -> None:
    session = OutcomeSession(OutcomeConfig(), context(), FillModelKind.CENTRAL)
    session.process(window(definition, future_books=()))
    result = session.finish()
    assert result["verdict"] == "DATA_BLOCKED"
    assert not session.ledger.reservations


@pytest.mark.parametrize(("at_ms", "expected_fills"), [(1200, 0), (2200, 1), (2400, 0)])
def test_placement_and_pending_cancel_latency(
    definition: OutcomeDefinition, at_ms: int, expected_fills: int
) -> None:
    w = window(definition)
    trade = replace(w.trades[0], exchange_ms=at_ms, received_ms=at_ms, sequence=at_ms)
    session = OutcomeSession(OutcomeConfig(), context(), FillModelKind.CENTRAL)
    session.process(replace(w, trades=(trade,)))
    result = session.finish()
    assert result["counts"]["fills"] == expected_fills


def test_dual_trade_is_counted_once(definition: OutcomeDefinition) -> None:
    w = window(definition)
    dual = replace(w.trades[0], side_index=1, aggressor=Side.BUY, price=D("0.55"))
    session = OutcomeSession(OutcomeConfig(), context(), FillModelKind.CENTRAL)
    session.process(replace(w, trades=(*w.trades, dual)))
    result = session.finish()
    assert result["counts"]["deduplicated_dual_trades"] == 1
    assert result["counts"]["fills"] == 1


def test_alo_crossing_at_activation_rejects(definition: OutcomeDefinition) -> None:
    crossed = book(
        1300,
        bids=(BookLevel(D("0.40"), D(10)),),
        asks=(BookLevel(D("0.44"), D(10)), BookLevel(D("0.70"), D(10))),
    )
    w = window(definition)
    session = OutcomeSession(OutcomeConfig(), context(), FillModelKind.CENTRAL)
    session.process(replace(w, future_books=(crossed, *w.future_books[1:])))
    result = session.finish()
    assert result["counts"]["alo_rejected"] == 1
    assert result["counts"]["fills"] == 0


def test_no_book_transforms_without_summing_liquidity() -> None:
    b = book_from_public(
        {
            "coin": "#11",
            "time": 1000,
            "levels": [[{"px": "0.3", "sz": "7"}], [{"px": "0.6", "sz": "9"}]],
        },
        received_ms=1001,
        sequence=1,
    )
    assert b.bids[0] == BookLevel(D("0.4"), D(9))
    assert b.asks[0] == BookLevel(D("0.7"), D(7))
    assert not b.queue_qualified


@pytest.mark.parametrize(
    "changes",
    [
        {"live_enabled": True},
        {"shadow_only": False},
        {"public_data_only": False},
        {"equity_usd": D(1001)},
        {"additional_margin": D(".02")},
        {"stale_ms": 501},
    ],
)
def test_config_cannot_enable_live_or_weaken_gates(changes: dict) -> None:
    with pytest.raises(ValueError):
        OutcomeConfig(**changes)


def test_decimal_config_and_unknown_keys(tmp_path: Path) -> None:
    path = tmp_path / "test.toml"
    path.write_text("[outcomes]\nequity_usd = 1000\n")
    with pytest.raises(ValueError, match="decimal string"):
        load_config(path)
    path.write_text('[outcomes]\nprivate_key = "forbidden"\n')
    with pytest.raises(ValueError, match="unknown"):
        load_config(path)


def test_catalog_discovery_is_not_qualification() -> None:
    row = {
        "outcome": 1,
        "name": "Recurring",
        "description": (
            "class:priceBinary|underlying:BTC|expiry:20260907-0600|"
            "targetPrice:80000|period:1d"
        ),
        "sideSpecs": [{"name": "Yes"}, {"name": "No"}],
        "quoteToken": "USDC",
    }
    definitions, issues = discover_recurring({"outcomes": [row]}, observed_ms=1000)
    assert not issues and len(definitions) == 1
    assert "fees_unknown_or_expired" in definitions[0].reasons(1000)
    definitions, issues = discover_recurring({"outcomes": [row, row]}, observed_ms=1000)
    assert len(definitions) == 1 and "duplicate outcome" in issues[0]
    definitions, issues = discover_recurring(
        {"outcomes": [{**row, "description": row["description"] + "|period:1d"}]},
        observed_ms=1000,
    )
    assert not definitions and "duplicate descriptor" in issues[0]


def test_fair_value_rejects_future_labels_and_gap(
    definition: OutcomeDefinition,
) -> None:
    model = CausalFairValueModel(interval_ms=1000)
    for t, price in ((0, "80000"), (1000, "80001"), (2000, "79999")):
        model.observe(ReferencePrice(t, t, D(price)))
    assert model.predict(definition, 1999) is None
    assert model.predict(definition, 2000) is not None
    model.observe(ReferencePrice(10_000, 10_000, D("80000")))
    assert model.predict(definition, 10_000) is None
    with pytest.raises(ValueError, match="future"):
        FairValue(D("0.5"), 1000, 1000, 1001, D(0), D(0), "a" * 64)


def test_serialization_roundtrip_and_strict_flags(
    definition: OutcomeDefinition,
) -> None:
    raw = json.loads(json.dumps(window_payload(window(definition)), default=str))
    assert window_from_payload(raw) == window(definition)
    raw["book"]["queue_qualified"] = "false"
    with pytest.raises(ValueError, match="boolean"):
        window_from_payload(raw)


def test_campaign_preregisters_all_variants_and_checks_inputs(
    tmp_path: Path, definition: OutcomeDefinition
) -> None:
    source = tmp_path / "windows.jsonl"
    source.write_text(
        json.dumps(window_payload(window(definition)), default=str) + "\n"
    )
    source.with_suffix(".jsonl.sha256").write_text(file_sha256(source))
    result = run_campaign(
        source=source,
        output=tmp_path / "run",
        config=OutcomeConfig(),
        run_id="test",
        code_version="test",
        config_sha256="c" * 64,
        model=FillModelKind.CENTRAL,
    )
    assert len(result["variants"]) == 18
    assert result["promotion_authorized"] is False
    assert len((tmp_path / "run" / "variants.jsonl").read_text().splitlines()) == 18
    source.write_text("modified")
    with pytest.raises(ValueError, match="checksum"):
        checked_input(source)


def test_artifacts_are_append_only_and_budget_is_enforced(tmp_path: Path) -> None:
    write_json(tmp_path / "x.json", {"x": 1})
    assert checked_input(tmp_path / "x.json") == file_sha256(tmp_path / "x.json")
    with pytest.raises(FileExistsError):
        write_json(tmp_path / "x.json", {"x": 2})
    budget = CampaignBudget(OutcomeConfig(max_output_bytes=1), tmp_path)
    with pytest.raises(BudgetExceeded, match="output"):
        budget.check()


def test_promotion_counts_distinct_settlements_and_cycle_pf() -> None:
    evidence = PromotionEvidence(
        tiers=(DatasetTier.A,),
        continuous_days=30,
        completeness=D(1),
        distinct_settlement_ids=("same",) * 300,
        round_trip_pnls=(D("1.1"), D(-1)) * 250,
        fold_pnls=(D(1), D(1), D(1)),
        bootstrap_lower_usd=D(1),
        drawdown_fraction=D(".01"),
        maximum_underlying_contribution=D(".3"),
        central_pnl=D(1),
        pessimistic_pnl=D(1),
        double_fee_pnl=D(1),
        double_latency_pnl=D(1),
        queue_qualified=True,
        oos_locked=True,
        shadow_days=14,
        account_actions_qualified=True,
    )
    reasons = evaluate_promotion(evidence)
    assert "fewer_than_300_distinct_terminal_settlements" in reasons
    assert "cycle_profit_factor_failed" in reasons
    good = replace(
        evidence,
        distinct_settlement_ids=tuple(str(x) for x in range(300)),
        round_trip_pnls=(D(2), D(-1)) * 250,
    )
    assert evaluate_promotion(good) == ()
