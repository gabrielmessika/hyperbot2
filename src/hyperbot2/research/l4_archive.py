"""Strict offline L4 checkpoint reconciliation, without maker qualification."""

from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal
from typing import Any


def _number(value: object) -> Decimal:
    if isinstance(value, float):
        raise ValueError("parse provider JSON using parse_float=Decimal")
    result = Decimal(str(value))
    if not result.is_finite() or result <= 0:
        raise ValueError("non-positive/non-finite order field")
    return result


def _integer(value: object) -> int:
    if type(value) is not int or value < 0:
        raise ValueError("nonnegative integer required")
    return value


@dataclass(frozen=True, slots=True)
class L4Order:
    oid: int
    user: str
    side: str
    price: Decimal
    size: Decimal


@dataclass(frozen=True, slots=True)
class ArchiveBook:
    coin: str
    block: int
    orders: tuple[L4Order, ...]
    last_event: tuple[int, int] | None = None

    @classmethod
    def snapshot(cls, payload: dict[str, Any]) -> ArchiveBook:
        if payload.get("is_crossed") is True:
            raise ValueError("crossed provider reconstruction")
        orders = []
        for key, side in (("bids", "B"), ("asks", "A")):
            rows = payload[key]
            count_key = "bid_count" if side == "B" else "ask_count"
            if _integer(payload[count_key]) != len(rows):
                raise ValueError("truncated checkpoint")
            for row in rows:
                if row["side"] != side or not row["user_address"]:
                    raise ValueError("order side/owner missing")
                orders.append(
                    L4Order(
                        _integer(row["oid"]),
                        str(row["user_address"]),
                        side,
                        _number(row["price"]),
                        _number(row["size"]),
                    )
                )
        book = cls(
            str(payload["coin"]), _integer(payload["last_block_number"]), tuple(orders)
        )
        book.validate()
        return book

    def validate(self) -> None:
        if len({o.oid for o in self.orders}) != len(self.orders):
            raise ValueError("duplicate resting order")
        bids = [o.price for o in self.orders if o.side == "B"]
        asks = [o.price for o in self.orders if o.side == "A"]
        if bids != sorted(bids, reverse=True) or asks != sorted(asks):
            raise ValueError("snapshot price order invalid")
        if bids and asks and bids[0] >= asks[0]:
            raise ValueError("crossed book")

    def apply(self, event: dict[str, Any]) -> ArchiveBook:
        key = (_integer(event["block_number"]), _integer(event["seq"]))
        if event["coin"].lstrip("#") != self.coin.lstrip("#"):
            raise ValueError("diff coin mismatch")
        if key[0] <= self.block or (
            self.last_event is not None and key <= self.last_event
        ):
            raise ValueError("duplicate/out-of-order diff or snapshot overlap")
        oid = _integer(event["oid"])
        orders = list(self.orders)
        found = next((i for i, o in enumerate(orders) if o.oid == oid), None)
        kind = event["diff_type"]
        if kind == "new":
            if found is not None or event["side"] not in ("A", "B"):
                raise ValueError("duplicate/new order side invalid")
            if not event.get("user_address"):
                raise ValueError("new order owner missing")
            order = L4Order(
                oid,
                str(event["user_address"]),
                str(event["side"]),
                _number(event["price"]),
                _number(event["new_size"]),
            )
            before = event.get("insert_before")
            index = len(orders)
            if before is not None:
                before = _integer(before)
                index = next((i for i, o in enumerate(orders) if o.oid == before), -1)
                if index < 0 or (orders[index].side, orders[index].price) != (
                    order.side,
                    order.price,
                ):
                    raise ValueError("priority insertion target missing/mismatched")
            orders.insert(index, order)
            # Stable sorting preserves the authoritative queue within a price.
            orders.sort(
                key=lambda o: (o.side != "B", -o.price if o.side == "B" else o.price)
            )
        elif kind in ("update", "remove"):
            if found is None:
                raise ValueError("update/remove of an unknown resting order")
            old = orders[found]
            if (event["side"], _number(event["price"]), event["user_address"]) != (
                old.side,
                old.price,
                old.user,
            ):
                raise ValueError("resting order identity changed without replacement")
            if kind == "remove":
                orders.pop(found)
            else:
                size = _number(event["new_size"])
                if size > old.size:
                    raise ValueError("size increase priority requires qualification")
                orders[found] = replace(old, size=size)
        else:
            raise ValueError("unknown diff type")
        result = replace(self, orders=tuple(orders), last_event=key)
        # Diffs within a block may transiently cross; validate at checkpoints.
        return result

    def reconcile(self, target: ArchiveBook) -> bool:
        self.validate()
        return (
            self.coin.lstrip("#") == target.coin.lstrip("#")
            and self.orders == target.orders
            and self.block <= target.block
            and (self.last_event is None or self.last_event[0] <= target.block)
        )
