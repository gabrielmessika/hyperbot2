"""Conservative completed-block evidence, never exchange sequence qualification."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from hyperbot2.research.l4_archive import ArchiveBook


@dataclass(frozen=True, slots=True)
class ClosedState:
    book: ArchiveBook
    block: int
    exchange_ms: int
    next_exchange_ms: int
    applied_received_ms: int
    confirmed_received_ms: int


def closed_states(
    messages: Iterable[tuple[int, dict[str, Any]]],
    *,
    initial_books: dict[str, ArchiveBook] | None = None,
) -> dict[str, list[ClosedState]]:
    """Close a coin's block only when a later block is observed on that coin.

    This relies on the provider's per-coin server-order contract. It cannot
    detect omitted events or establish historical local receipt times. The
    initial snapshot envelope is never used as an exchange-time watermark.
    A local ordinal only satisfies ArchiveBook's ordered application interface;
    it is not a provider seq and must never authorize maker fills.
    """
    books: dict[str, ArchiveBook] = dict(initial_books or {})
    pending: dict[str, tuple[int, int, int]] = {}
    result: dict[str, list[ClosedState]] = {coin: [] for coin in books}
    ordinal = 0
    last_received = -1
    for received, message in messages:
        if received < last_received:
            raise ValueError("receipt clock regressed")
        last_received = received
        kind = message.get("type")
        if kind in ("gap", "gap_detected", "replay_gap", "error"):
            raise ValueError("unsafe provider control event")
        if kind not in ("l4_snapshot", "l4_batch", "subscribed", "pong"):
            raise ValueError("unrecognized provider message")
        if kind in ("subscribed", "pong"):
            continue
        coin = str(message.get("coin", message.get("symbol")))
        if kind == "l4_snapshot":
            if coin in books:
                raise ValueError("unexpected snapshot reset")
            books[coin] = ArchiveBook.snapshot(
                message["data"]
                | {"coin": coin, "last_block_number": message["last_block_number"]}
            )
            result[coin] = []
            continue
        if coin not in books:
            raise ValueError("diff before snapshot")
        for event in message["data"]:
            block, timestamp = event["bn"], event["ts"]
            if type(block) is not int or type(timestamp) is not int:
                raise ValueError("integer block and timestamp required")
            if event["coin"].lstrip("#") != coin.lstrip("#"):
                raise ValueError("batch coin mismatch")
            previous = pending.get(coin)
            if previous is not None:
                old_block, old_time, applied_at = previous
                if block < old_block or timestamp < old_time:
                    raise ValueError("provider block/time regressed")
                if block == old_block and timestamp != old_time:
                    raise ValueError("inconsistent block timestamp")
                if block > old_block:
                    if timestamp <= old_time:
                        raise ValueError("non-advancing block timestamp")
                    books[coin].validate()
                    result[coin].append(
                        ClosedState(
                            books[coin],
                            old_block,
                            old_time,
                            timestamp,
                            applied_at,
                            received,
                        )
                    )
            translated = {
                "coin": coin,
                "block_number": block,
                "seq": ordinal,
                "diff_type": event["dt"],
                "oid": event["oid"],
                "user_address": event["user"],
                "side": event["side"],
                "price": event["px"],
                "new_size": None if event["dt"] == "remove" else event["sz"],
            }
            if "insert_before" in event:
                translated["insert_before"] = event["insert_before"]
            books[coin] = books[coin].apply(translated)
            pending[coin] = (block, timestamp, received)
            ordinal += 1
    # Pending final blocks and initial snapshots have no closing witness.
    return result


def state_at(states: list[ClosedState], exchange_ms: int) -> ClosedState | None:
    """Historical comparison only; confirmation can occur after the query time."""
    return next(
        (s for s in states if s.exchange_ms <= exchange_ms < s.next_exchange_ms),
        None,
    )
