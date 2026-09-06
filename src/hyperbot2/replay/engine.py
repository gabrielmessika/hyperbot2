"""Bit-reproducible replay with explicit queue and latency assumptions."""

from __future__ import annotations

import hashlib
import json
from bisect import bisect_right
from dataclasses import dataclass, fields, is_dataclass, replace
from decimal import Decimal
from enum import Enum, StrEnum
from typing import TypeAlias, cast

from hyperbot2.legacy.policy import ReplayUse, require_replay_use
from hyperbot2.models import BookLevel, DatasetTier, Side

REPLAY_SCHEMA_VERSION = 6
MARKOUT_HORIZONS_MS = (100, 1_000, 5_000, 30_000)
MAXIMUM_QUEUE_EVIDENCE_AGE_MS = 500


class ReplayError(RuntimeError):
    """Base deterministic replay error."""


class ReplayDataError(ReplayError):
    """Raised when queue evidence is absent or input ordering is ambiguous."""


class FillModelKind(StrEnum):
    PESSIMISTIC = "pessimistic"
    CENTRAL = "central"
    OPTIMISTIC_TOUCH = "optimistic_touch"


@dataclass(frozen=True, slots=True)
class ReplayBook:
    market: str
    timestamp_ms: int
    source_sequence: int
    bids: tuple[BookLevel, ...]
    asks: tuple[BookLevel, ...]
    receive_ts_ms: int | None = None

    def __post_init__(self) -> None:
        if not self.market.strip():
            raise ValueError("market must not be empty")
        if self.timestamp_ms < 0 or self.source_sequence < 0:
            raise ValueError("book timestamp and sequence must be non-negative")
        if self.receive_ts_ms is not None and self.receive_ts_ms < self.timestamp_ms:
            raise ValueError("book receive timestamp cannot precede exchange time")
        if self.bids and self.asks and self.bids[0].price > self.asks[0].price:
            raise ValueError("book must not be crossed")

    @property
    def midpoint(self) -> Decimal | None:
        if not self.bids or not self.asks:
            return None
        return (self.bids[0].price + self.asks[0].price) / 2

    @property
    def observed_ts_ms(self) -> int:
        return (
            self.receive_ts_ms if self.receive_ts_ms is not None else self.timestamp_ms
        )


@dataclass(frozen=True, slots=True)
class ReplayTrade:
    market: str
    timestamp_ms: int
    source_sequence: int
    aggressor_side: Side
    price: Decimal
    size: Decimal
    receive_ts_ms: int | None = None

    def __post_init__(self) -> None:
        if not self.market.strip():
            raise ValueError("market must not be empty")
        if self.timestamp_ms < 0 or self.source_sequence < 0:
            raise ValueError("trade timestamp and sequence must be non-negative")
        if self.receive_ts_ms is not None and self.receive_ts_ms < self.timestamp_ms:
            raise ValueError("trade receive timestamp cannot precede exchange time")
        if not self.price.is_finite() or self.price <= 0:
            raise ValueError("trade price must be finite and positive")
        if not self.size.is_finite() or self.size <= 0:
            raise ValueError("trade size must be finite and positive")

    @property
    def observed_ts_ms(self) -> int:
        return (
            self.receive_ts_ms if self.receive_ts_ms is not None else self.timestamp_ms
        )


@dataclass(frozen=True, slots=True)
class ReplayMark:
    """Top-of-book observation used for markouts, never for queue evidence."""

    market: str
    timestamp_ms: int
    source_sequence: int
    bid: Decimal
    ask: Decimal
    receive_ts_ms: int | None = None

    def __post_init__(self) -> None:
        if not self.market.strip():
            raise ValueError("market must not be empty")
        if self.timestamp_ms < 0 or self.source_sequence < 0:
            raise ValueError("mark timestamp and sequence must be non-negative")
        if self.receive_ts_ms is not None and self.receive_ts_ms < self.timestamp_ms:
            raise ValueError("mark receive timestamp cannot precede exchange time")
        if (
            not self.bid.is_finite()
            or not self.ask.is_finite()
            or self.bid <= 0
            or self.ask <= 0
            or self.bid > self.ask
        ):
            raise ValueError("mark prices must be finite, positive, and not crossed")

    @property
    def midpoint(self) -> Decimal:
        return (self.bid + self.ask) / 2

    @property
    def observed_ts_ms(self) -> int:
        return (
            self.receive_ts_ms if self.receive_ts_ms is not None else self.timestamp_ms
        )


@dataclass(frozen=True, slots=True)
class ReplayTopOfBook:
    """Exact two-sided BBO usable as bounded top-level queue evidence."""

    market: str
    timestamp_ms: int
    source_sequence: int
    bid: BookLevel
    ask: BookLevel
    receive_ts_ms: int | None = None

    def __post_init__(self) -> None:
        if not self.market.strip():
            raise ValueError("market must not be empty")
        if self.timestamp_ms < 0 or self.source_sequence < 0:
            raise ValueError("topbook timestamp and sequence must be non-negative")
        if self.receive_ts_ms is not None and self.receive_ts_ms < self.timestamp_ms:
            raise ValueError("topbook receive timestamp cannot precede exchange time")
        if self.bid.price > self.ask.price:
            raise ValueError("topbook must not be crossed")

    @property
    def midpoint(self) -> Decimal:
        return (self.bid.price + self.ask.price) / 2

    @property
    def observed_ts_ms(self) -> int:
        return (
            self.receive_ts_ms if self.receive_ts_ms is not None else self.timestamp_ms
        )


ReplayQueueEvent: TypeAlias = ReplayBook | ReplayTopOfBook
ReplayMarketEvent: TypeAlias = ReplayBook | ReplayTopOfBook | ReplayMark | ReplayTrade
ReplayPriceEvent: TypeAlias = ReplayBook | ReplayTopOfBook | ReplayMark


@dataclass(frozen=True, slots=True)
class ReplayQuote:
    quote_id: str
    market: str
    side: Side
    price: Decimal
    size: Decimal
    submitted_ts_ms: int
    cancel_requested_ts_ms: int | None
    maker_fee_bps: Decimal

    def __post_init__(self) -> None:
        if not self.quote_id.strip() or not self.market.strip():
            raise ValueError("quote_id and market must not be empty")
        if not self.price.is_finite() or self.price <= 0:
            raise ValueError("quote price must be finite and positive")
        if not self.size.is_finite() or self.size <= 0:
            raise ValueError("quote size must be finite and positive")
        if self.submitted_ts_ms < 0:
            raise ValueError("submitted_ts_ms must be non-negative")
        if (
            self.cancel_requested_ts_ms is not None
            and self.cancel_requested_ts_ms < self.submitted_ts_ms
        ):
            raise ValueError("cancel cannot precede quote submission")
        if not self.maker_fee_bps.is_finite() or self.maker_fee_bps < 0:
            raise ValueError("maker_fee_bps must be finite and non-negative")


@dataclass(frozen=True, slots=True)
class ReplayConfig:
    run_id: str
    code_version: str
    model: FillModelKind
    dataset_tiers: tuple[DatasetTier, ...]
    placement_latency_ms: int
    cancel_latency_ms: int
    central_queue_fraction: Decimal = Decimal("0.5")
    markout_tolerance_ms: int = 250

    def __post_init__(self) -> None:
        if not self.run_id.strip() or not self.code_version.strip():
            raise ValueError("run_id and code_version must not be empty")
        if not self.dataset_tiers:
            raise ValueError("dataset_tiers must not be empty")
        if self.placement_latency_ms < 0 or self.cancel_latency_ms < 0:
            raise ValueError("latencies must be non-negative")
        if self.markout_tolerance_ms < 0:
            raise ValueError("markout_tolerance_ms must be non-negative")
        if not Decimal(0) <= self.central_queue_fraction <= Decimal(1):
            raise ValueError("central_queue_fraction must be between zero and one")

    @property
    def sha256(self) -> str:
        return _hash(self)


@dataclass(frozen=True, slots=True)
class SimulatedFill:
    quote_id: str
    market: str
    side: Side
    fill_ts_ms: int
    price: Decimal
    size: Decimal
    fee_usd: Decimal
    queue_ahead_before: Decimal
    queue_ahead_after: Decimal
    model: FillModelKind
    markout_100ms: Decimal | None
    markout_1s: Decimal | None
    markout_5s: Decimal | None
    markout_30s: Decimal | None


@dataclass(frozen=True, slots=True)
class ReplayResult:
    schema_version: int
    run_id: str
    code_version: str
    config_sha256: str
    input_sha256: str
    model: FillModelKind
    evidence_label: str | None
    fills: tuple[SimulatedFill, ...]
    filled_notional_usd: Decimal
    fees_usd: Decimal
    gross_markout_30s_usd: Decimal
    economic_pnl_30s_usd: Decimal
    fills_missing_30s_markout: int
    result_sha256: str


@dataclass(frozen=True, slots=True)
class StressReplayResult:
    base: ReplayResult
    double_latency: ReplayResult
    double_fees: ReplayResult


@dataclass(slots=True)
class _QuoteState:
    quote: ReplayQuote
    active_ts_ms: int
    cancel_effective_ts_ms: int | None
    remaining_size: Decimal
    queue_ahead: Decimal | None


class VirtualClock:
    """Monotonic replay clock advanced only by ordered input events."""

    def __init__(self, initial_ts_ms: int = 0) -> None:
        if initial_ts_ms < 0:
            raise ValueError("initial timestamp must be non-negative")
        self._now_ms = initial_ts_ms

    @property
    def now_ms(self) -> int:
        return self._now_ms

    def advance_to(self, timestamp_ms: int) -> None:
        if timestamp_ms < self._now_ms:
            raise ReplayDataError("virtual clock cannot move backwards")
        self._now_ms = timestamp_ms


def _encode(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Enum):
        return str(value.value)
    if isinstance(value, tuple | list):
        return [_encode(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _encode(item) for key, item in value.items()}
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _encode(getattr(value, field.name)) for field in fields(value)
        }
    return value


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        _encode(value),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _hash(value: object) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _replay_input_hash(
    events: tuple[ReplayMarketEvent, ...],
    quotes: tuple[ReplayQuote, ...],
) -> str:
    """Hash the canonical replay input without materializing its full payload."""

    digest = hashlib.sha256()
    digest.update(b'{"events":[')
    for index, event in enumerate(events):
        if index:
            digest.update(b",")
        digest.update(_canonical_json(event))
    digest.update(b'],"quotes":[')
    for index, quote in enumerate(quotes):
        if index:
            digest.update(b",")
        digest.update(_canonical_json(quote))
    digest.update(b"]}")
    return digest.hexdigest()


def _event_sort_key(event: ReplayMarketEvent) -> tuple[int, int, str, int]:
    type_order = (
        0
        if isinstance(event, ReplayBook)
        else 1
        if isinstance(event, ReplayTopOfBook)
        else 2
        if isinstance(event, ReplayMark)
        else 3
    )
    return event.timestamp_ms, event.source_sequence, event.market, type_order


def _visible_size(book: ReplayBook, quote: ReplayQuote) -> Decimal:
    levels = book.bids if quote.side is Side.BUY else book.asks
    return sum(
        (level.size for level in levels if level.price == quote.price),
        Decimal(0),
    )


def _topbook_visible_size(
    topbook: ReplayTopOfBook,
    quote: ReplayQuote,
) -> Decimal | None:
    if quote.market != topbook.market:
        return None
    if quote.side is Side.BUY:
        if quote.price >= topbook.ask.price:
            return Decimal(0)
        if quote.price == topbook.bid.price:
            return topbook.bid.size
        if quote.price > topbook.bid.price:
            return Decimal(0)
        return None
    if quote.price <= topbook.bid.price:
        return Decimal(0)
    if quote.price == topbook.ask.price:
        return topbook.ask.size
    if quote.price < topbook.ask.price:
        return Decimal(0)
    return None


def _trade_reaches_quote(trade: ReplayTrade, quote: ReplayQuote) -> bool:
    if quote.market != trade.market:
        return False
    if quote.side is Side.BUY:
        return trade.aggressor_side is Side.SELL and trade.price <= quote.price
    return trade.aggressor_side is Side.BUY and trade.price >= quote.price


def _book_crosses_quote(book: ReplayBook, quote: ReplayQuote) -> bool:
    if quote.market != book.market:
        return False
    if quote.side is Side.BUY:
        return bool(book.asks and book.asks[0].price <= quote.price)
    return bool(book.bids and book.bids[0].price >= quote.price)


def _mark_crosses_quote(mark: ReplayMark, quote: ReplayQuote) -> bool:
    if quote.market != mark.market:
        return False
    if quote.side is Side.BUY:
        return mark.ask <= quote.price
    return mark.bid >= quote.price


def _topbook_crosses_quote(topbook: ReplayTopOfBook, quote: ReplayQuote) -> bool:
    if quote.market != topbook.market:
        return False
    if quote.side is Side.BUY:
        return topbook.ask.price <= quote.price
    return topbook.bid.price >= quote.price


def _active_at(state: _QuoteState, timestamp_ms: int) -> bool:
    if timestamp_ms < state.active_ts_ms or state.remaining_size <= 0:
        return False
    return (
        state.cancel_effective_ts_ms is None
        or timestamp_ms <= state.cancel_effective_ts_ms
    )


def _markout(
    fill: SimulatedFill,
    prices_by_market: dict[str, tuple[ReplayPriceEvent, ...]],
    price_times_by_market: dict[str, tuple[int, ...]],
    horizon_ms: int,
    tolerance_ms: int,
) -> Decimal | None:
    target = fill.fill_ts_ms + horizon_ms
    prices = prices_by_market.get(fill.market, ())
    times = price_times_by_market.get(fill.market, ())
    candidate_index = bisect_right(times, target) - 1
    if candidate_index < 0:
        return None
    candidate = prices[candidate_index]
    if target - candidate.timestamp_ms > tolerance_ms:
        return None
    midpoint = candidate.midpoint
    if midpoint is None:
        return None
    if fill.side is Side.BUY:
        return (midpoint - fill.price) * fill.size
    return (fill.price - midpoint) * fill.size


class ReplayEngine:
    def run(
        self,
        *,
        config: ReplayConfig,
        events: tuple[ReplayMarketEvent, ...],
        quotes: tuple[ReplayQuote, ...],
    ) -> ReplayResult:
        replay_use = {
            FillModelKind.PESSIMISTIC: ReplayUse.PESSIMISTIC_FILL_MODEL,
            FillModelKind.CENTRAL: ReplayUse.CENTRAL_FILL_MODEL,
            FillModelKind.OPTIMISTIC_TOUCH: ReplayUse.OPTIMISTIC_TOUCH,
        }[config.model]
        authorization = require_replay_use(replay_use, config.dataset_tiers)
        if len({quote.quote_id for quote in quotes}) != len(quotes):
            raise ReplayDataError("quote IDs must be unique")
        ordered_events = tuple(sorted(events, key=_event_sort_key))
        previous_event_key: tuple[int, int, str, int] | None = None
        for event in ordered_events:
            event_key = _event_sort_key(event)
            if event_key == previous_event_key:
                raise ReplayDataError("market event ordering keys must be unique")
            previous_event_key = event_key
        ordered_quotes = tuple(
            sorted(quotes, key=lambda item: (item.submitted_ts_ms, item.quote_id))
        )
        states = [
            _QuoteState(
                quote=quote,
                active_ts_ms=quote.submitted_ts_ms + config.placement_latency_ms,
                cancel_effective_ts_ms=(
                    quote.cancel_requested_ts_ms + config.cancel_latency_ms
                    if quote.cancel_requested_ts_ms is not None
                    else None
                ),
                remaining_size=quote.size,
                queue_ahead=None,
            )
            for quote in ordered_quotes
        ]
        clock = VirtualClock()
        latest_books: dict[str, ReplayBook] = {}
        latest_topbooks: dict[str, ReplayTopOfBook] = {}
        active_states: dict[str, list[_QuoteState]] = {}
        next_state_index = 0
        raw_fills: list[SimulatedFill] = []
        for event in ordered_events:
            clock.advance_to(event.timestamp_ms)
            while (
                next_state_index < len(states)
                and states[next_state_index].active_ts_ms <= event.timestamp_ms
            ):
                state = states[next_state_index]
                if _active_at(state, event.timestamp_ms):
                    active_states.setdefault(state.quote.market, []).append(state)
                next_state_index += 1
            market_states = active_states.get(event.market, [])
            if market_states:
                market_states[:] = [
                    state
                    for state in market_states
                    if _active_at(state, event.timestamp_ms)
                ]
            if isinstance(event, ReplayBook):
                self._update_queues(
                    config,
                    market_states,
                    event,
                    latest_books,
                    latest_topbooks,
                )
                latest_books[event.market] = event
                if config.model is FillModelKind.OPTIMISTIC_TOUCH:
                    for state in market_states:
                        is_active = _active_at(state, event.timestamp_ms)
                        if is_active and _book_crosses_quote(event, state.quote):
                            raw_fills.append(
                                self._fill_state(
                                    config.model,
                                    state,
                                    event.timestamp_ms,
                                    state.remaining_size,
                                )
                            )
                continue
            if isinstance(event, ReplayTopOfBook):
                self._update_queues(
                    config,
                    market_states,
                    event,
                    latest_books,
                    latest_topbooks,
                )
                latest_topbooks[event.market] = event
                if config.model is FillModelKind.OPTIMISTIC_TOUCH:
                    for state in market_states:
                        is_active = _active_at(state, event.timestamp_ms)
                        if is_active and _topbook_crosses_quote(event, state.quote):
                            raw_fills.append(
                                self._fill_state(
                                    config.model,
                                    state,
                                    event.timestamp_ms,
                                    state.remaining_size,
                                )
                            )
                continue
            if isinstance(event, ReplayMark):
                if config.model is FillModelKind.OPTIMISTIC_TOUCH:
                    for state in market_states:
                        is_active = _active_at(state, event.timestamp_ms)
                        if is_active and _mark_crosses_quote(event, state.quote):
                            raw_fills.append(
                                self._fill_state(
                                    config.model,
                                    state,
                                    event.timestamp_ms,
                                    state.remaining_size,
                                )
                            )
                continue
            self._initialize_queues(
                config,
                market_states,
                latest_books,
                latest_topbooks,
                event.timestamp_ms,
                market=event.market,
            )
            if config.model is FillModelKind.OPTIMISTIC_TOUCH:
                for state in market_states:
                    if _active_at(state, event.timestamp_ms) and _trade_reaches_quote(
                        event, state.quote
                    ):
                        raw_fills.append(
                            self._fill_state(
                                config.model,
                                state,
                                event.timestamp_ms,
                                state.remaining_size,
                            )
                        )
                continue
            available = event.size
            candidates = [
                state
                for state in market_states
                if _active_at(state, event.timestamp_ms)
                and _trade_reaches_quote(event, state.quote)
            ]
            candidates.sort(key=self._queue_priority)
            for state in candidates:
                if available <= 0:
                    break
                if state.queue_ahead is None:
                    raise ReplayDataError(
                        f"no L2 queue evidence for active quote {state.quote.quote_id}"
                    )
                queue_before = state.queue_ahead
                queue_consumed = min(state.queue_ahead, available)
                state.queue_ahead -= queue_consumed
                available -= queue_consumed
                if available <= 0 or state.queue_ahead > 0:
                    continue
                fill_size = min(state.remaining_size, available)
                raw_fills.append(
                    self._fill_state(
                        config.model,
                        state,
                        event.timestamp_ms,
                        fill_size,
                        queue_ahead_before=queue_before,
                    )
                )
                available -= fill_size

        prices_by_market: dict[str, tuple[ReplayPriceEvent, ...]] = {}
        for market in {event.market for event in ordered_events}:
            prices_by_market[market] = tuple(
                sorted(
                    (
                        event
                        for event in ordered_events
                        if isinstance(event, ReplayBook | ReplayTopOfBook | ReplayMark)
                        and event.market == market
                        and event.midpoint is not None
                    ),
                    key=lambda item: (item.timestamp_ms, item.source_sequence),
                )
            )
        price_times_by_market = {
            market: tuple(event.timestamp_ms for event in price_events)
            for market, price_events in prices_by_market.items()
        }
        fills = tuple(
            replace(
                fill,
                markout_100ms=_markout(
                    fill,
                    prices_by_market,
                    price_times_by_market,
                    100,
                    config.markout_tolerance_ms,
                ),
                markout_1s=_markout(
                    fill,
                    prices_by_market,
                    price_times_by_market,
                    1_000,
                    config.markout_tolerance_ms,
                ),
                markout_5s=_markout(
                    fill,
                    prices_by_market,
                    price_times_by_market,
                    5_000,
                    config.markout_tolerance_ms,
                ),
                markout_30s=_markout(
                    fill,
                    prices_by_market,
                    price_times_by_market,
                    30_000,
                    config.markout_tolerance_ms,
                ),
            )
            for fill in raw_fills
        )
        fees = sum((fill.fee_usd for fill in fills), Decimal(0))
        gross_markout = sum(
            (fill.markout_30s for fill in fills if fill.markout_30s is not None),
            Decimal(0),
        )
        input_hash = _replay_input_hash(ordered_events, ordered_quotes)
        filled_notional = sum((fill.price * fill.size for fill in fills), Decimal(0))
        fills_missing_markout = sum(fill.markout_30s is None for fill in fills)
        without_hash = {
            "schema_version": REPLAY_SCHEMA_VERSION,
            "run_id": config.run_id,
            "code_version": config.code_version,
            "config_sha256": config.sha256,
            "input_sha256": input_hash,
            "model": config.model,
            "evidence_label": authorization.required_label,
            "fills": fills,
            "filled_notional_usd": filled_notional,
            "fees_usd": fees,
            "gross_markout_30s_usd": gross_markout,
            "economic_pnl_30s_usd": gross_markout - fees,
            "fills_missing_30s_markout": fills_missing_markout,
        }
        return ReplayResult(
            schema_version=REPLAY_SCHEMA_VERSION,
            run_id=config.run_id,
            code_version=config.code_version,
            config_sha256=config.sha256,
            input_sha256=input_hash,
            model=config.model,
            evidence_label=authorization.required_label,
            fills=fills,
            filled_notional_usd=filled_notional,
            fees_usd=fees,
            gross_markout_30s_usd=gross_markout,
            economic_pnl_30s_usd=gross_markout - fees,
            fills_missing_30s_markout=fills_missing_markout,
            result_sha256=_hash(without_hash),
        )

    def run_stress(
        self,
        *,
        config: ReplayConfig,
        events: tuple[ReplayMarketEvent, ...],
        quotes: tuple[ReplayQuote, ...],
    ) -> StressReplayResult:
        base = self.run(config=config, events=events, quotes=quotes)
        latency_config = replace(
            config,
            run_id=f"{config.run_id}-latency-2x",
            placement_latency_ms=config.placement_latency_ms * 2,
            cancel_latency_ms=config.cancel_latency_ms * 2,
        )
        double_latency = self.run(
            config=latency_config,
            events=events,
            quotes=quotes,
        )
        fee_quotes = tuple(
            replace(quote, maker_fee_bps=quote.maker_fee_bps * 2) for quote in quotes
        )
        fee_config = replace(config, run_id=f"{config.run_id}-fees-2x")
        double_fees = self.run(
            config=fee_config,
            events=events,
            quotes=fee_quotes,
        )
        return StressReplayResult(base, double_latency, double_fees)

    def _initialize_queues(
        self,
        config: ReplayConfig,
        states: list[_QuoteState],
        latest_books: dict[str, ReplayBook],
        latest_topbooks: dict[str, ReplayTopOfBook],
        timestamp_ms: int,
        *,
        market: str,
    ) -> None:
        if config.model is FillModelKind.OPTIMISTIC_TOUCH:
            return
        for state in states:
            if (
                state.quote.market != market
                or not _active_at(state, timestamp_ms)
                or state.queue_ahead is not None
            ):
                continue
            queue = self._queue_from_latest(
                config,
                state,
                latest_books.get(state.quote.market),
                latest_topbooks.get(state.quote.market),
            )
            if queue is None:
                raise ReplayDataError(
                    "no L2 book or eligible top-of-book at activation for quote "
                    f"{state.quote.quote_id}"
                )
            state.queue_ahead = queue

    def _update_queues(
        self,
        config: ReplayConfig,
        states: list[_QuoteState],
        evidence: ReplayQueueEvent,
        latest_books: dict[str, ReplayBook],
        latest_topbooks: dict[str, ReplayTopOfBook],
    ) -> None:
        if config.model is FillModelKind.OPTIMISTIC_TOUCH:
            return
        for state in states:
            if state.quote.market == evidence.market and _active_at(
                state, evidence.timestamp_ms
            ):
                if state.queue_ahead is None:
                    current_book = (
                        evidence if isinstance(evidence, ReplayBook) else None
                    )
                    current_topbook = (
                        evidence if isinstance(evidence, ReplayTopOfBook) else None
                    )
                    queue = self._queue_from_latest(
                        config,
                        state,
                        (
                            current_book
                            if current_book is not None
                            and current_book.timestamp_ms <= state.active_ts_ms
                            else latest_books.get(evidence.market)
                        ),
                        (
                            current_topbook
                            if current_topbook is not None
                            and current_topbook.timestamp_ms <= state.active_ts_ms
                            else latest_topbooks.get(evidence.market)
                        ),
                    )
                    if queue is None:
                        raise ReplayDataError(
                            "no L2 book or eligible top-of-book at activation "
                            "for quote "
                            f"{state.quote.quote_id}"
                        )
                    state.queue_ahead = queue
                if config.model is not FillModelKind.CENTRAL:
                    continue
                visible = (
                    _visible_size(evidence, state.quote)
                    if isinstance(evidence, ReplayBook)
                    else _topbook_visible_size(evidence, state.quote)
                )
                if visible is not None:
                    state.queue_ahead = min(state.queue_ahead, visible)

    def _queue_from_latest(
        self,
        config: ReplayConfig,
        state: _QuoteState,
        book: ReplayBook | None,
        topbook: ReplayTopOfBook | None,
    ) -> Decimal | None:
        candidates: list[ReplayQueueEvent] = [
            item
            for item in (book, topbook)
            if item is not None
            and item.timestamp_ms <= state.active_ts_ms
            and item.observed_ts_ms <= state.active_ts_ms
        ]
        candidates.sort(
            key=lambda item: (item.timestamp_ms, item.source_sequence),
            reverse=True,
        )
        for evidence in candidates:
            age_ms = state.active_ts_ms - evidence.observed_ts_ms
            if age_ms > MAXIMUM_QUEUE_EVIDENCE_AGE_MS:
                continue
            visible: Decimal | None
            if isinstance(evidence, ReplayBook):
                visible = _visible_size(evidence, state.quote)
            else:
                if _topbook_crosses_quote(evidence, state.quote):
                    raise ReplayDataError(
                        f"passive quote crosses topbook: {state.quote.quote_id}"
                    )
                visible = _topbook_visible_size(evidence, state.quote)
            if visible is None:
                continue
            return (
                visible
                if config.model is FillModelKind.PESSIMISTIC
                else visible * config.central_queue_fraction
            )
        return None

    def _fill_state(
        self,
        model: FillModelKind,
        state: _QuoteState,
        timestamp_ms: int,
        size: Decimal,
        *,
        queue_ahead_before: Decimal | None = None,
    ) -> SimulatedFill:
        queue_before = (
            queue_ahead_before
            if queue_ahead_before is not None
            else state.queue_ahead or Decimal(0)
        )
        state.remaining_size -= size
        fee = state.quote.price * size * state.quote.maker_fee_bps / Decimal(10_000)
        return SimulatedFill(
            quote_id=state.quote.quote_id,
            market=state.quote.market,
            side=state.quote.side,
            fill_ts_ms=timestamp_ms,
            price=state.quote.price,
            size=size,
            fee_usd=fee,
            queue_ahead_before=queue_before,
            queue_ahead_after=state.queue_ahead or Decimal(0),
            model=model,
            markout_100ms=None,
            markout_1s=None,
            markout_5s=None,
            markout_30s=None,
        )

    def _queue_priority(self, state: _QuoteState) -> tuple[str, Decimal, int, str]:
        price_priority = (
            -state.quote.price if state.quote.side is Side.BUY else state.quote.price
        )
        return (
            state.quote.market,
            price_priority,
            state.active_ts_ms,
            state.quote.quote_id,
        )


def replay_result_payload(result: ReplayResult) -> dict[str, object]:
    encoded = _encode(result)
    if not isinstance(encoded, dict):
        raise TypeError("replay result must encode to an object")
    return cast(dict[str, object], encoded)
