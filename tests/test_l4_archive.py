from decimal import Decimal

import pytest

from hyperbot2.research.l4_archive import ArchiveBook


def snapshot() -> dict:
    return {
        "coin": "#10",
        "last_block_number": 100,
        "bid_count": 2,
        "ask_count": 0,
        "bids": [
            {
                "oid": i,
                "user_address": f"u{i}",
                "side": "B",
                "price": Decimal("0.4"),
                "size": Decimal(10),
            }
            for i in (1, 2)
        ],
        "asks": [],
    }


def diff(**kwargs: object) -> dict:
    return {
        "coin": "#10",
        "block_number": 101,
        "seq": 0,
        "oid": 3,
        "user_address": "u3",
        "side": "B",
        "price": Decimal("0.4"),
        "new_size": Decimal(5),
        "diff_type": "new",
        **kwargs,
    }


def test_priority_insert_is_not_timestamp_order_and_input_is_immutable() -> None:
    initial = ArchiveBook.snapshot(snapshot())
    inserted = initial.apply(diff(insert_before=1))
    assert [o.oid for o in inserted.orders] == [3, 1, 2]
    assert [o.oid for o in initial.orders] == [1, 2]
    appended = initial.apply(diff())
    assert [o.oid for o in appended.orders] == [1, 2, 3]
    assert not inserted.reconcile(appended)


def test_unknown_priority_target_and_duplicate_event_fail_closed() -> None:
    initial = ArchiveBook.snapshot(snapshot())
    with pytest.raises(ValueError, match="target"):
        initial.apply(diff(insert_before=999))
    inserted = initial.apply(diff())
    with pytest.raises(ValueError, match="out-of-order"):
        inserted.apply(diff())


def test_snapshot_truncation_and_float_conversion_rejected() -> None:
    truncated = snapshot() | {"bid_count": 3}
    with pytest.raises(ValueError, match="truncated"):
        ArchiveBook.snapshot(truncated)
    floats = snapshot()
    floats["bids"][0]["price"] = 0.4
    with pytest.raises(ValueError, match="parse_float"):
        ArchiveBook.snapshot(floats)


def test_reductions_removals_and_priority_ambiguity() -> None:
    initial = ArchiveBook.snapshot(snapshot())
    reduced = initial.apply(diff(oid=1, user_address="u1", diff_type="update"))
    assert reduced.orders[0].size == 5
    removed = reduced.apply(diff(oid=1, user_address="u1", diff_type="remove", seq=1))
    assert [o.oid for o in removed.orders] == [2]
    with pytest.raises(ValueError, match="increase"):
        reduced.apply(
            diff(
                oid=1,
                user_address="u1",
                diff_type="update",
                seq=1,
                new_size=Decimal(20),
            )
        )
