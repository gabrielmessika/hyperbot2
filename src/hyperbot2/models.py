"""Immutable domain events shared by collection, replay, and execution."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
from enum import Enum, StrEnum
from typing import TypeAlias

JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]


class Side(StrEnum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(StrEnum):
    PENDING = "pending"
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCEL_PENDING = "cancel_pending"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class OutcomeResult(StrEnum):
    YES = "yes"
    NO = "no"
    INVALID = "invalid"


class TimeSource(StrEnum):
    EXCHANGE = "exchange"
    LOCAL_MONOTONIC = "local_monotonic"
    REPLAY = "replay"


class DatasetTier(StrEnum):
    """Evidence tier attached to collected and legacy datasets."""

    A = "A"
    B = "B"
    C = "C"


class MarketKind(StrEnum):
    CORE_PERP = "core_perp"
    HIP3_PERP = "hip3_perp"
    OUTCOME = "outcome"


class MarketStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    UNKNOWN = "unknown"


class CollectorControlKind(StrEnum):
    CONNECTED = "connected"
    RECONNECTED = "reconnected"
    DISCONNECTED = "disconnected"
    GAP = "gap"
    HEARTBEAT_SENT = "heartbeat_sent"
    HEARTBEAT_ACK = "heartbeat_ack"
    SUBSCRIPTION_ACK = "subscription_ack"
    SUBSCRIPTION_REJECTED = "subscription_rejected"
    CLOCK_SKEW = "clock_skew"
    MALFORMED_MESSAGE = "malformed_message"
    UNEXPECTED_MARKET = "unexpected_market"
    QUEUE_DROP = "queue_drop"
    SHUTDOWN = "shutdown"


class ShadowQuoteStatus(StrEnum):
    STAGED = "staged"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


def _require_non_empty(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")


def _require_finite(value: Decimal, field_name: str) -> None:
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_positive(value: Decimal, field_name: str) -> None:
    _require_finite(value, field_name)
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_non_negative(value: Decimal, field_name: str) -> None:
    _require_finite(value, field_name)
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")


def _require_optional_positive(value: Decimal | None, field_name: str) -> None:
    if value is not None:
        _require_positive(value, field_name)


def _require_optional_non_negative(value: Decimal | None, field_name: str) -> None:
    if value is not None:
        _require_non_negative(value, field_name)


def _require_optional_non_empty(value: str | None, field_name: str) -> None:
    if value is not None:
        _require_non_empty(value, field_name)


@dataclass(frozen=True, slots=True)
class EventContext:
    """Reproducibility metadata carried by every domain event."""

    run_id: str
    code_version: str
    config_hash: str
    time_source: TimeSource

    def __post_init__(self) -> None:
        _require_non_empty(self.run_id, "run_id")
        _require_non_empty(self.code_version, "code_version")
        _require_non_empty(self.config_hash, "config_hash")


def _require_sha256(value: str, field_name: str) -> None:
    invalid_character = any(char not in "0123456789abcdef" for char in value)
    if len(value) != 64 or invalid_character:
        raise ValueError(f"{field_name} must be a lowercase SHA-256")


@dataclass(frozen=True, slots=True)
class MarketDefinition:
    """Versioned public market specification captured without credentials."""

    context: EventContext
    observed_at_ms: int
    catalog_version: int
    definition_version: int
    market_id: str
    market_kind: MarketKind
    dex: str
    coin: str
    display_name: str
    asset_id: int
    sz_decimals: int | None
    size_increment: Decimal | None
    max_price_decimals: int | None
    max_significant_figures: int | None
    tick_size_at_reference: Decimal | None
    minimum_order_notional_usd: Decimal
    growth_mode: str | None
    deployer_fee_scale: Decimal | None
    maker_fee_bps: Decimal | None
    taker_fee_bps: Decimal | None
    fee_basis: str
    oracle_px: Decimal | None
    mark_px: Decimal | None
    status: MarketStatus
    definition_sha256: str
    previous_definition_sha256: str | None
    quality_flags: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.observed_at_ms < 0:
            raise ValueError("observed_at_ms must be non-negative")
        if self.catalog_version <= 0 or self.definition_version <= 0:
            raise ValueError("catalog and definition versions must be positive")
        for field_name, value in (
            ("market_id", self.market_id),
            ("dex", self.dex),
            ("coin", self.coin),
            ("display_name", self.display_name),
            ("fee_basis", self.fee_basis),
        ):
            _require_non_empty(value, field_name)
        if self.asset_id < 0:
            raise ValueError("asset_id must be non-negative")
        for field_name, integer_value in (
            ("sz_decimals", self.sz_decimals),
            ("max_price_decimals", self.max_price_decimals),
            ("max_significant_figures", self.max_significant_figures),
        ):
            if integer_value is not None and integer_value < 0:
                raise ValueError(f"{field_name} must be non-negative")
        _require_optional_positive(self.size_increment, "size_increment")
        _require_optional_positive(
            self.tick_size_at_reference, "tick_size_at_reference"
        )
        _require_positive(self.minimum_order_notional_usd, "minimum_order_notional_usd")
        _require_optional_non_empty(self.growth_mode, "growth_mode")
        _require_optional_non_negative(self.deployer_fee_scale, "deployer_fee_scale")
        _require_optional_non_negative(self.maker_fee_bps, "maker_fee_bps")
        _require_optional_non_negative(self.taker_fee_bps, "taker_fee_bps")
        _require_optional_positive(self.oracle_px, "oracle_px")
        _require_optional_positive(self.mark_px, "mark_px")
        _require_sha256(self.definition_sha256, "definition_sha256")
        if self.previous_definition_sha256 is not None:
            _require_sha256(
                self.previous_definition_sha256,
                "previous_definition_sha256",
            )
        for flag in self.quality_flags:
            _require_non_empty(flag, "quality_flag")


@dataclass(frozen=True, slots=True)
class PublicMarketDataEvent:
    """Raw public WebSocket payload with all three observation clocks."""

    context: EventContext
    channel: str
    coin: str
    exchange_ts_ms: int | None
    receive_ts_ms: int
    receive_monotonic_ns: int
    local_sequence: int
    payload_json: str

    def __post_init__(self) -> None:
        if self.exchange_ts_ms is not None and self.exchange_ts_ms < 0:
            raise ValueError("exchange_ts_ms must be non-negative")
        if self.receive_ts_ms < 0 or self.receive_monotonic_ns < 0:
            raise ValueError("receive timestamps must be non-negative")
        if self.local_sequence < 0:
            raise ValueError("local_sequence must be non-negative")
        for field_name, value in (
            ("channel", self.channel),
            ("coin", self.coin),
            ("payload_json", self.payload_json),
        ):
            _require_non_empty(value, field_name)


@dataclass(frozen=True, slots=True)
class CollectorControlEvent:
    """Explicit collector lifecycle, gap, parsing, and overload signal."""

    context: EventContext
    kind: CollectorControlKind
    receive_ts_ms: int
    receive_monotonic_ns: int
    connection_attempt: int
    dropped_messages: int
    reason: str | None

    def __post_init__(self) -> None:
        if self.receive_ts_ms < 0 or self.receive_monotonic_ns < 0:
            raise ValueError("receive timestamps must be non-negative")
        if self.connection_attempt < 0 or self.dropped_messages < 0:
            raise ValueError("counters must be non-negative")
        _require_optional_non_empty(self.reason, "reason")


def _require_account_address(value: str) -> None:
    if (
        len(value) != 42
        or not value.startswith("0x")
        or any(character not in "0123456789abcdef" for character in value[2:])
    ):
        raise ValueError("account_address must be a lowercase 20-byte hex address")


@dataclass(frozen=True, slots=True)
class StrategyMarketEvidenceEvent:
    """Account-specific public market reference captured after all responses."""

    context: EventContext
    snapshot_id: str
    observed_at_ms: int
    account_address: str
    market_id: str
    market_kind: MarketKind
    market: str
    dex: str
    oracle_px: Decimal
    mark_px: Decimal
    tick_size: Decimal
    size_increment: Decimal
    maker_fee_bps: Decimal
    maker_fee_basis: str
    definition_sha256: str
    status: MarketStatus
    growth_mode: str | None
    source_payload_sha256: str

    def __post_init__(self) -> None:
        if self.observed_at_ms < 0:
            raise ValueError("observed_at_ms must be non-negative")
        _require_account_address(self.account_address)
        for name, text_value in (
            ("market_id", self.market_id),
            ("market", self.market),
            ("dex", self.dex),
            ("maker_fee_basis", self.maker_fee_basis),
        ):
            _require_non_empty(text_value, name)
        for name, decimal_value in (
            ("oracle_px", self.oracle_px),
            ("mark_px", self.mark_px),
            ("tick_size", self.tick_size),
            ("size_increment", self.size_increment),
        ):
            _require_positive(decimal_value, name)
        _require_finite(self.maker_fee_bps, "maker_fee_bps")
        if self.maker_fee_basis != "effective_observed":
            raise ValueError("maker_fee_basis must be effective_observed")
        _require_sha256(self.snapshot_id, "snapshot_id")
        _require_sha256(self.definition_sha256, "definition_sha256")
        _require_sha256(self.source_payload_sha256, "source_payload_sha256")
        _require_optional_non_empty(self.growth_mode, "growth_mode")


@dataclass(frozen=True, slots=True)
class StrategyAccountEvidenceEvent:
    """Unsigned account state and fee evidence queried through the info endpoint."""

    context: EventContext
    snapshot_id: str
    observed_at_ms: int
    account_address: str
    account_abstraction: str
    user_dex_abstraction: bool | None
    per_dex_equity_usd: tuple[tuple[str, Decimal], ...]
    exchange_positions: tuple[tuple[str, Decimal], ...]
    spot_balances: tuple[tuple[int, str, Decimal, Decimal], ...]
    token_available_after_maintenance: tuple[tuple[int, Decimal], ...]
    day_account_value_history: tuple[tuple[int, Decimal], ...]
    day_pnl_history: tuple[tuple[int, Decimal], ...]
    open_order_count: int
    user_add_rate: Decimal
    active_referral_discount: Decimal
    heartbeat_healthy: bool
    source_payload_sha256: str

    def __post_init__(self) -> None:
        if self.observed_at_ms < 0 or self.open_order_count < 0:
            raise ValueError("account evidence timestamp and counters are invalid")
        _require_account_address(self.account_address)
        _require_sha256(self.snapshot_id, "snapshot_id")
        _require_sha256(self.source_payload_sha256, "source_payload_sha256")
        if self.account_abstraction not in {"disabled", "unifiedAccount"}:
            raise ValueError("unsupported account_abstraction")
        if self.user_dex_abstraction is not None and not isinstance(
            self.user_dex_abstraction, bool
        ):
            raise ValueError("user_dex_abstraction must be boolean or null")
        if not self.per_dex_equity_usd:
            raise ValueError("account evidence requires per-DEX equity")
        for name, pairs in (
            ("per_dex_equity_usd", self.per_dex_equity_usd),
            ("exchange_positions", self.exchange_positions),
        ):
            keys = [key for key, _ in pairs]
            if len(keys) != len(set(keys)):
                raise ValueError(f"{name} keys must be unique")
            for key, value in pairs:
                _require_non_empty(key, f"{name} key")
                _require_finite(value, f"{name} value")
        if any(value < 0 for _, value in self.per_dex_equity_usd):
            raise ValueError("per-DEX equity must be non-negative")
        if not self.spot_balances:
            raise ValueError("account evidence requires spot balances")
        spot_tokens = [token for token, _, _, _ in self.spot_balances]
        spot_coins = [coin for _, coin, _, _ in self.spot_balances]
        if len(spot_tokens) != len(set(spot_tokens)) or len(spot_coins) != len(
            set(spot_coins)
        ):
            raise ValueError("spot balance tokens and coins must be unique")
        for token, coin, total, hold in self.spot_balances:
            if token < 0:
                raise ValueError("spot balance token must be non-negative")
            _require_non_empty(coin, "spot balance coin")
            _require_non_negative(total, "spot balance total")
            _require_non_negative(hold, "spot balance hold")
            if hold > total:
                raise ValueError("spot balance hold must not exceed total")
        available_tokens = [
            token for token, _ in self.token_available_after_maintenance
        ]
        if len(available_tokens) != len(set(available_tokens)):
            raise ValueError("available-after-maintenance tokens must be unique")
        for token, available in self.token_available_after_maintenance:
            if token < 0:
                raise ValueError("available token must be non-negative")
            _require_non_negative(available, "available after maintenance")
        for name, history in (
            ("day_account_value_history", self.day_account_value_history),
            ("day_pnl_history", self.day_pnl_history),
        ):
            if not history:
                raise ValueError(f"{name} must not be empty")
            timestamps = [timestamp_ms for timestamp_ms, _ in history]
            if timestamps != sorted(timestamps) or len(timestamps) != len(
                set(timestamps)
            ):
                raise ValueError(f"{name} timestamps must be unique and ordered")
            for timestamp_ms, value in history:
                if timestamp_ms < 0:
                    raise ValueError(f"{name} timestamps must be non-negative")
                _require_finite(value, f"{name} value")
        if any(value < 0 for _, value in self.day_account_value_history):
            raise ValueError("day account values must be non-negative")
        _require_finite(self.user_add_rate, "user_add_rate")
        _require_non_negative(self.active_referral_discount, "active_referral_discount")
        if self.active_referral_discount >= 1:
            raise ValueError("active_referral_discount must be below one")


@dataclass(frozen=True, slots=True)
class StrategyEvidenceHealthEvent:
    """Fail-closed health for one synchronized evidence sampling attempt."""

    context: EventContext
    snapshot_id: str
    observed_at_ms: int
    account_address: str
    collector_healthy: bool
    market_data_healthy: bool
    catalog_healthy: bool
    account_healthy: bool
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.observed_at_ms < 0:
            raise ValueError("observed_at_ms must be non-negative")
        _require_account_address(self.account_address)
        _require_sha256(self.snapshot_id, "snapshot_id")
        healthy = (
            self.collector_healthy
            and self.market_data_healthy
            and self.catalog_healthy
            and self.account_healthy
        )
        if healthy and self.reason_codes:
            raise ValueError("healthy evidence must not carry reason codes")
        if not healthy and not self.reason_codes:
            raise ValueError("unhealthy evidence requires reason codes")
        for reason in self.reason_codes:
            _require_non_empty(reason, "reason_code")


@dataclass(frozen=True, slots=True)
class RiskAuditEvent:
    context: EventContext
    decision_ts_ms: int
    intent_id: str
    approved: bool
    approved_size: Decimal | None
    action: str
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.decision_ts_ms < 0:
            raise ValueError("decision_ts_ms must be non-negative")
        _require_non_empty(self.intent_id, "intent_id")
        _require_non_empty(self.action, "action")
        _require_optional_positive(self.approved_size, "approved_size")
        if self.approved != (self.approved_size is not None):
            raise ValueError("approved flag and size are inconsistent")
        if not self.reason_codes:
            raise ValueError("risk audit requires reason codes")
        for reason in self.reason_codes:
            _require_non_empty(reason, "reason_code")


@dataclass(frozen=True, slots=True)
class ShadowQuoteEvent:
    context: EventContext
    decision_id: str
    intent_id: str
    market: str
    side: Side
    price: Decimal
    size: Decimal
    staged_ts_ms: int
    expires_ts_ms: int
    status: ShadowQuoteStatus
    shadow_only: bool

    def __post_init__(self) -> None:
        for field_name, value in (
            ("decision_id", self.decision_id),
            ("intent_id", self.intent_id),
            ("market", self.market),
        ):
            _require_non_empty(value, field_name)
        _require_positive(self.price, "price")
        _require_positive(self.size, "size")
        if self.staged_ts_ms < 0 or self.expires_ts_ms <= self.staged_ts_ms:
            raise ValueError("shadow quote timestamps are invalid")
        if not self.shadow_only:
            raise ValueError("shadow quote events must remain shadow-only")


@dataclass(frozen=True, slots=True)
class ShadowFillEvaluationEvent:
    context: EventContext
    evaluation_ts_ms: int
    replay_result_sha256: str
    quote_id: str
    model: str
    predicted_fill: bool
    filled_size: Decimal
    markout_100ms: Decimal | None
    markout_1s: Decimal | None
    markout_5s: Decimal | None
    markout_30s: Decimal | None

    def __post_init__(self) -> None:
        if self.evaluation_ts_ms < 0:
            raise ValueError("evaluation_ts_ms must be non-negative")
        _require_sha256(self.replay_result_sha256, "replay_result_sha256")
        _require_non_empty(self.quote_id, "quote_id")
        _require_non_empty(self.model, "model")
        _require_non_negative(self.filled_size, "filled_size")
        if self.predicted_fill != (self.filled_size > 0):
            raise ValueError("predicted_fill and filled_size are inconsistent")
        for field_name, value in (
            ("markout_100ms", self.markout_100ms),
            ("markout_1s", self.markout_1s),
            ("markout_5s", self.markout_5s),
            ("markout_30s", self.markout_30s),
        ):
            if value is not None:
                _require_finite(value, field_name)


@dataclass(frozen=True, slots=True)
class BookLevel:
    price: Decimal
    size: Decimal
    order_count: int | None = None

    def __post_init__(self) -> None:
        _require_positive(self.price, "price")
        _require_positive(self.size, "size")
        if self.order_count is not None and self.order_count < 0:
            raise ValueError("order_count must be non-negative")


@dataclass(frozen=True, slots=True)
class BookEvent:
    context: EventContext
    exchange_ts_ms: int
    receive_ts_ms: int
    dex: str
    asset: str
    sequence: int
    bids: tuple[BookLevel, ...]
    asks: tuple[BookLevel, ...]
    oracle_px: Decimal | None
    mark_px: Decimal | None

    def __post_init__(self) -> None:
        if self.exchange_ts_ms < 0 or self.receive_ts_ms < 0:
            raise ValueError("timestamps must be non-negative")
        if self.sequence < 0:
            raise ValueError("sequence must be non-negative")
        _require_non_empty(self.dex, "dex")
        _require_non_empty(self.asset, "asset")
        if self.oracle_px is not None:
            _require_positive(self.oracle_px, "oracle_px")
        if self.mark_px is not None:
            _require_positive(self.mark_px, "mark_px")


@dataclass(frozen=True, slots=True)
class QuoteIntent:
    context: EventContext
    intent_id: str
    strategy: str
    market: str
    side: Side
    price: Decimal
    size: Decimal
    ttl_ms: int
    fair_value: Decimal
    min_edge_bps: Decimal
    inventory_before: Decimal
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_non_empty(self.intent_id, "intent_id")
        _require_non_empty(self.strategy, "strategy")
        _require_non_empty(self.market, "market")
        _require_positive(self.price, "price")
        _require_positive(self.size, "size")
        _require_positive(self.fair_value, "fair_value")
        _require_non_negative(self.min_edge_bps, "min_edge_bps")
        _require_finite(self.inventory_before, "inventory_before")
        if self.ttl_ms <= 0:
            raise ValueError("ttl_ms must be positive")
        if not self.reason_codes:
            raise ValueError("reason_codes must not be empty")
        for reason_code in self.reason_codes:
            _require_non_empty(reason_code, "reason_code")


@dataclass(frozen=True, slots=True)
class OrderLifecycle:
    context: EventContext
    client_order_id: str
    exchange_order_id: str | None
    intent_id: str
    sent_ts_ms: int
    ack_ts_ms: int | None
    cancel_ts_ms: int | None
    status: OrderStatus
    reject_reason: str | None

    def __post_init__(self) -> None:
        _require_non_empty(self.client_order_id, "client_order_id")
        _require_non_empty(self.intent_id, "intent_id")
        if self.exchange_order_id is not None:
            _require_non_empty(self.exchange_order_id, "exchange_order_id")
        for field_name, value in (
            ("sent_ts_ms", self.sent_ts_ms),
            ("ack_ts_ms", self.ack_ts_ms),
            ("cancel_ts_ms", self.cancel_ts_ms),
        ):
            if value is not None and value < 0:
                raise ValueError(f"{field_name} must be non-negative")
        if self.status is OrderStatus.REJECTED and not self.reject_reason:
            raise ValueError("a rejected order requires reject_reason")


@dataclass(frozen=True, slots=True)
class FillAttribution:
    context: EventContext
    order_id: str
    fill_ts_ms: int
    price: Decimal
    size: Decimal
    fee_usd: Decimal
    estimated_queue_ahead: Decimal
    markout_100ms: Decimal | None
    markout_1s: Decimal | None
    markout_5s: Decimal | None
    markout_30s: Decimal | None

    def __post_init__(self) -> None:
        _require_non_empty(self.order_id, "order_id")
        if self.fill_ts_ms < 0:
            raise ValueError("fill_ts_ms must be non-negative")
        _require_positive(self.price, "price")
        _require_positive(self.size, "size")
        _require_finite(self.fee_usd, "fee_usd")
        _require_non_negative(self.estimated_queue_ahead, "estimated_queue_ahead")
        for field_name, value in (
            ("markout_100ms", self.markout_100ms),
            ("markout_1s", self.markout_1s),
            ("markout_5s", self.markout_5s),
            ("markout_30s", self.markout_30s),
        ):
            if value is not None:
                _require_finite(value, field_name)


@dataclass(frozen=True, slots=True)
class OutcomeSettlement:
    context: EventContext
    market: str
    expiry_ts_ms: int
    strike: Decimal
    result: OutcomeResult
    payout_usd: Decimal
    settlement_fee_usd: Decimal

    def __post_init__(self) -> None:
        _require_non_empty(self.market, "market")
        if self.expiry_ts_ms < 0:
            raise ValueError("expiry_ts_ms must be non-negative")
        _require_positive(self.strike, "strike")
        _require_non_negative(self.payout_usd, "payout_usd")
        _require_non_negative(self.settlement_fee_usd, "settlement_fee_usd")


@dataclass(frozen=True, slots=True)
class LegacyProvenance:
    """Verifiable origin attached to every normalized legacy event."""

    dataset_tier: DatasetTier
    source_path: str
    source_sha256: str
    source_record_number: int
    source_record_sha256: str
    source_record_hash_kind: str
    subrecord_index: int
    adapter_name: str
    adapter_version: str
    quality_flags: tuple[str, ...]
    legacy_research_only: bool

    def __post_init__(self) -> None:
        _require_non_empty(self.source_path, "source_path")
        _require_non_empty(self.adapter_name, "adapter_name")
        _require_non_empty(self.adapter_version, "adapter_version")
        if self.source_record_hash_kind not in {
            "raw_line_sha256",
            "canonical_json_sha256",
        }:
            raise ValueError("unsupported source_record_hash_kind")
        for field_name, value in (
            ("source_sha256", self.source_sha256),
            ("source_record_sha256", self.source_record_sha256),
        ):
            invalid_character = any(char not in "0123456789abcdef" for char in value)
            if len(value) != 64 or invalid_character:
                raise ValueError(f"{field_name} must be a lowercase SHA-256")
        if self.source_record_number <= 0:
            raise ValueError("source_record_number must be positive")
        if self.subrecord_index < 0:
            raise ValueError("subrecord_index must be non-negative")
        if not self.legacy_research_only:
            raise ValueError("legacy provenance must remain research-only")
        if "legacy_research_only" not in self.quality_flags:
            raise ValueError("quality_flags must include legacy_research_only")
        for flag in self.quality_flags:
            _require_non_empty(flag, "quality_flag")


@dataclass(frozen=True, slots=True)
class LegacyBookObservation:
    """Partial BBO/depth observation that never implies a full L2 book."""

    context: EventContext
    provenance: LegacyProvenance
    exchange_ts_ms: int
    dex: str
    asset: str
    market_id: str | None
    outcome_side: str | None
    best_bid: Decimal | None
    best_ask: Decimal | None
    bid_size: Decimal | None
    ask_size: Decimal | None
    bid_depth: Decimal | None
    ask_depth: Decimal | None

    def __post_init__(self) -> None:
        if self.exchange_ts_ms < 0:
            raise ValueError("exchange_ts_ms must be non-negative")
        _require_non_empty(self.dex, "dex")
        _require_non_empty(self.asset, "asset")
        _require_optional_non_empty(self.market_id, "market_id")
        _require_optional_non_empty(self.outcome_side, "outcome_side")
        _require_optional_positive(self.best_bid, "best_bid")
        _require_optional_positive(self.best_ask, "best_ask")
        for field_name, value in (
            ("bid_size", self.bid_size),
            ("ask_size", self.ask_size),
            ("bid_depth", self.bid_depth),
            ("ask_depth", self.ask_depth),
        ):
            _require_optional_non_negative(value, field_name)
        if (
            self.best_bid is not None
            and self.best_ask is not None
            and self.best_bid > self.best_ask
        ):
            raise ValueError("best_bid cannot exceed best_ask")


@dataclass(frozen=True, slots=True)
class LegacyTradeObservation:
    """Normalized trade with explicit units for every available quantity."""

    context: EventContext
    provenance: LegacyProvenance
    exchange_ts_ms: int
    dex: str
    asset: str
    market_id: str | None
    side: Side | None
    price: Decimal
    base_size: Decimal | None
    token_size: Decimal | None
    notional_usd: Decimal | None

    def __post_init__(self) -> None:
        if self.exchange_ts_ms < 0:
            raise ValueError("exchange_ts_ms must be non-negative")
        _require_non_empty(self.dex, "dex")
        _require_non_empty(self.asset, "asset")
        _require_optional_non_empty(self.market_id, "market_id")
        _require_positive(self.price, "price")
        for field_name, value in (
            ("base_size", self.base_size),
            ("token_size", self.token_size),
            ("notional_usd", self.notional_usd),
        ):
            _require_optional_positive(value, field_name)
        quantities = (self.base_size, self.token_size, self.notional_usd)
        if all(value is None for value in quantities):
            raise ValueError("a trade requires at least one explicit quantity")


@dataclass(frozen=True, slots=True)
class LegacyQuoteObservation:
    """Historical paper/shadow quote observation, never an executable intent."""

    context: EventContext
    provenance: LegacyProvenance
    exchange_ts_ms: int
    market_id: str
    asset: str | None
    side_label: str
    decision_approved: bool | None
    would_quote: bool | None
    bid: Decimal | None
    ask: Decimal | None
    maker_price: Decimal | None
    quote_size_usd: Decimal | None
    model_probability: Decimal | None
    reference_price: Decimal | None
    strike: Decimal | None
    seconds_left: int | None

    def __post_init__(self) -> None:
        if self.exchange_ts_ms < 0:
            raise ValueError("exchange_ts_ms must be non-negative")
        _require_non_empty(self.market_id, "market_id")
        _require_optional_non_empty(self.asset, "asset")
        _require_non_empty(self.side_label, "side_label")
        for field_name, value in (
            ("bid", self.bid),
            ("ask", self.ask),
            ("maker_price", self.maker_price),
            ("quote_size_usd", self.quote_size_usd),
            ("reference_price", self.reference_price),
            ("strike", self.strike),
        ):
            _require_optional_positive(value, field_name)
        if self.bid is not None and self.ask is not None and self.bid > self.ask:
            raise ValueError("bid cannot exceed ask")
        if self.model_probability is not None:
            _require_finite(self.model_probability, "model_probability")
            if not Decimal("0") <= self.model_probability <= Decimal("1"):
                raise ValueError("model_probability must be between zero and one")
        if self.seconds_left is not None and self.seconds_left < 0:
            raise ValueError("seconds_left must be non-negative")


@dataclass(frozen=True, slots=True)
class LegacySettlementObservation:
    """Historical outcome settlement with no reconstructed missing strike."""

    context: EventContext
    provenance: LegacyProvenance
    exchange_ts_ms: int
    market_id: str
    asset: str | None
    side_label: str | None
    result_label: str
    payout_usd: Decimal | None
    fee_usd: Decimal | None
    net_pnl_usd: Decimal | None

    def __post_init__(self) -> None:
        if self.exchange_ts_ms < 0:
            raise ValueError("exchange_ts_ms must be non-negative")
        _require_non_empty(self.market_id, "market_id")
        _require_optional_non_empty(self.asset, "asset")
        _require_optional_non_empty(self.side_label, "side_label")
        _require_non_empty(self.result_label, "result_label")
        _require_optional_non_negative(self.payout_usd, "payout_usd")
        _require_optional_non_negative(self.fee_usd, "fee_usd")
        if self.net_pnl_usd is not None:
            _require_finite(self.net_pnl_usd, "net_pnl_usd")


@dataclass(frozen=True, slots=True)
class LegacyFeatureObservation:
    """One symbol extracted from an aggregated TRIDENT feature snapshot."""

    context: EventContext
    provenance: LegacyProvenance
    exchange_ts_ms: int
    asset: str
    source_label: str | None
    price: Decimal | None
    best_bid: Decimal | None
    best_ask: Decimal | None
    bid_size: Decimal | None
    ask_size: Decimal | None
    bid_depth: Decimal | None
    ask_depth: Decimal | None
    oracle_px: Decimal | None
    mark_px: Decimal | None
    spread_bps: Decimal | None

    def __post_init__(self) -> None:
        if self.exchange_ts_ms < 0:
            raise ValueError("exchange_ts_ms must be non-negative")
        _require_non_empty(self.asset, "asset")
        _require_optional_non_empty(self.source_label, "source_label")
        for field_name, value in (
            ("price", self.price),
            ("best_bid", self.best_bid),
            ("best_ask", self.best_ask),
            ("oracle_px", self.oracle_px),
            ("mark_px", self.mark_px),
        ):
            _require_optional_positive(value, field_name)
        for field_name, value in (
            ("bid_size", self.bid_size),
            ("ask_size", self.ask_size),
            ("bid_depth", self.bid_depth),
            ("ask_depth", self.ask_depth),
            ("spread_bps", self.spread_bps),
        ):
            _require_optional_non_negative(value, field_name)
        if (
            self.best_bid is not None
            and self.best_ask is not None
            and self.best_bid > self.best_ask
        ):
            raise ValueError("best_bid cannot exceed best_ask")


DomainEvent: TypeAlias = (
    MarketDefinition
    | PublicMarketDataEvent
    | CollectorControlEvent
    | StrategyMarketEvidenceEvent
    | StrategyAccountEvidenceEvent
    | StrategyEvidenceHealthEvent
    | RiskAuditEvent
    | ShadowQuoteEvent
    | ShadowFillEvaluationEvent
    | BookEvent
    | QuoteIntent
    | OrderLifecycle
    | FillAttribution
    | OutcomeSettlement
    | LegacyBookObservation
    | LegacyTradeObservation
    | LegacyQuoteObservation
    | LegacySettlementObservation
    | LegacyFeatureObservation
)


def _encode_json(value: object) -> JsonValue:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Enum):
        return str(value.value)
    if isinstance(value, tuple | list):
        return [_encode_json(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _encode_json(item) for key, item in value.items()}
    if value is None or isinstance(value, str | int | float | bool):
        return value
    raise TypeError(f"unsupported event payload value: {type(value).__name__}")


def event_payload(event: DomainEvent) -> dict[str, JsonValue]:
    """Return a deterministic JSON-compatible payload for an event."""

    encoded = _encode_json(asdict(event))
    if not isinstance(encoded, dict):
        raise TypeError("domain event must encode to a JSON object")
    return encoded


def event_type(event: DomainEvent) -> str:
    """Return the stable on-disk event type identifier."""

    return type(event).__name__
