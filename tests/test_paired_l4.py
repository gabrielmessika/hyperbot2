"""Block completion must not turn a fresh envelope into causal market evidence."""

from decimal import Decimal

import pytest

from hyperbot2.research.l4_archive import ArchiveBook
from hyperbot2.research.paired_l4 import closed_states, state_at


def snapshot() -> dict:
    return {
        "type": "l4_snapshot",
        "coin": "#10",
        "timestamp": 999999,
        "last_block_number": 100,
        "data": {"bids": [], "asks": [], "bid_count": 0, "ask_count": 0},
    }


def batch(block: int, timestamp: int, oid: int) -> dict:
    return {
        "type": "l4_batch",
        "coin": "#10",
        "data": [
            {
                "bn": block,
                "ts": timestamp,
                "coin": "#10",
                "dt": "new",
                "oid": oid,
                "user": "fixture",
                "side": "B",
                "px": Decimal("0.4"),
                "sz": Decimal(1),
            }
        ],
    }


def test_next_block_closes_previous_without_using_snapshot_envelope_time() -> None:
    states = closed_states(
        [(2000, snapshot()), (2100, batch(101, 1000, 1)), (2200, batch(105, 1500, 2))]
    )["#10"]
    assert len(states) == 1
    assert states[0].exchange_ms == 1000
    assert states[0].applied_received_ms == 2100
    assert states[0].confirmed_received_ms == 2200
    assert [o.oid for o in states[0].book.orders] == [1]
    assert state_at(states, 1200) == states[0]
    assert state_at(states, 1500) is None
    assert state_at(states, 999) is None


def test_multiple_messages_in_one_block_are_not_prematurely_closed() -> None:
    states = closed_states(
        [
            (2000, snapshot()),
            (2100, batch(101, 1000, 1)),
            (2150, batch(101, 1000, 2)),
            (2200, batch(102, 1500, 3)),
        ]
    )["#10"]
    assert len(states) == 1
    assert [o.oid for o in states[0].book.orders] == [1, 2]
    assert states[0].applied_received_ms == 2150


def test_remove_has_no_size_field_and_only_removes_the_identified_order() -> None:
    removal = batch(102, 1500, 1)
    removal["data"][0]["dt"] = "remove"
    del removal["data"][0]["sz"]
    states = closed_states(
        [
            (2000, snapshot()),
            (2100, batch(101, 1000, 1)),
            (2200, removal),
            (2300, batch(103, 2000, 2)),
        ]
    )["#10"]
    assert len(states) == 2
    assert not states[1].book.orders


def test_rest_seed_is_not_mutated_and_unknown_order_is_never_ignored() -> None:
    seed = ArchiveBook("#10", 100, ())
    states = closed_states(
        [(2100, batch(101, 1000, 1)), (2200, batch(102, 1500, 2))],
        initial_books={"#10": seed},
    )
    assert len(states["#10"]) == 1
    assert seed.orders == ()
    removal = batch(101, 1000, 999)
    removal["data"][0]["dt"] = "remove"
    with pytest.raises(ValueError, match="unknown resting order"):
        closed_states([(2100, removal)], initial_books={"#10": seed})


@pytest.mark.parametrize(
    "message",
    [
        {"type": "gap_detected"},
        batch(99, 900, 2),
        batch(101, 1001, 2),
    ],
)
def test_gap_regression_or_inconsistent_block_time_stops_reconstruction(
    message,
) -> None:
    with pytest.raises(ValueError):
        closed_states(
            [(2000, snapshot()), (2100, batch(101, 1000, 1)), (2200, message)]
        )
