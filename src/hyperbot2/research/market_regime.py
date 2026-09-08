"""Past-only collective trend and strict joining of contiguous hourly panels."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal
from statistics import median

from hyperbot2.research.rotation import HOUR
from hyperbot2.research.volume import VolumeBar


def collective_trend(closes: Mapping[str, Sequence[Decimal]], index: int) -> Decimal:
    if len(closes) < 6 or index < 721 or any(index > len(v) for v in closes.values()):
        raise ValueError("six assets and thirty completed days required")
    returns = []
    for values in closes.values():
        before, latest = values[index - 721], values[index - 1]
        if not before.is_finite() or not latest.is_finite() or min(before, latest) <= 0:
            raise ValueError("finite positive historical closes required")
        returns.append(latest / before - 1)
    return median(returns)


def join_panels(
    left: Mapping[str, Sequence[VolumeBar]],
    left_payments: Mapping[str, Mapping[int, Decimal]],
    right: Mapping[str, Sequence[VolumeBar]],
    right_payments: Mapping[str, Mapping[int, Decimal]],
) -> tuple[dict[str, list[VolumeBar]], dict[str, dict[int, Decimal]]]:
    coins = set(left)
    if not coins or any(
        set(v) != coins for v in (right, left_payments, right_payments)
    ):
        raise ValueError("identical nonempty cohorts required")
    bars, payments = {}, {}
    reference: list[int] | None = None
    for c in sorted(coins):
        if not left[c] or not right[c] or left[c][-1].time + HOUR != right[c][0].time:
            raise ValueError("contiguous hourly boundary required")
        rows = [*left[c], *right[c]]
        times = [b.time for b in rows]
        if any(b - a != HOUR for a, b in zip(times, times[1:], strict=False)):
            raise ValueError("hourly history gap or overlap")
        if reference is not None and times != reference:
            raise ValueError("aligned panels required")
        reference = times
        if set(left_payments[c]) & set(right_payments[c]):
            raise ValueError("overlapping funding timestamps")
        for historical, funding in (
            (left[c], left_payments[c]),
            (right[c], right_payments[c]),
        ):
            if (
                len(funding) != len(historical)
                or {at // HOUR * HOUR for at in funding} != {b.time for b in historical}
                or any(
                    not rate.is_finite() or at % HOUR > 60_000
                    for at, rate in funding.items()
                )
            ):
                raise ValueError("qualified hourly funding coverage required")
        bars[c], payments[c] = rows, {**left_payments[c], **right_payments[c]}
    return bars, payments
