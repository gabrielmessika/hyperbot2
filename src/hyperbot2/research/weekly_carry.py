"""Past-settlement carry baskets with a fixed transaction-cost hurdle."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from hyperbot2.research.rotation import HOUR

D = Decimal
HURDLE = D("0.0013")


@dataclass(frozen=True, slots=True)
class CarryBasket:
    index: int
    time_ms: int
    sides: tuple[tuple[str, int], ...]
    past_week_rates: tuple[tuple[str, Decimal], ...]
    expected_receipt: Decimal
    eligible: bool


def carry_selection(
    rates: Mapping[str, Sequence[Decimal]], index: int
) -> tuple[dict[str, int], dict[str, Decimal], Decimal]:
    """Rank completed weekly sums, independent of funding settlement frequency."""
    if len(rates) < 6 or index < 168 or any(index > len(v) for v in rates.values()):
        raise ValueError("six assets and 168 completed funding buckets required")
    scores = {}
    for coin, rows in rates.items():
        past = rows[index - 168 : index]
        if any(not v.is_finite() for v in past):
            raise ValueError("finite historical funding required")
        scores[coin] = sum(past, D(0))
    ordered = sorted(scores, key=lambda c: (scores[c], c))
    if (
        scores[ordered[2]] == scores[ordered[3]]
        or scores[ordered[-4]] == scores[ordered[-3]]
    ):
        return {}, scores, D(0)
    sides = {**dict.fromkeys(ordered[:3], 1), **dict.fromkeys(ordered[-3:], -1)}
    receipt = -sum((scores[c] * side for c, side in sides.items()), D(0)) / 6
    return sides, scores, receipt


def carry_baskets(
    payments: Mapping[str, Mapping[int, Decimal]], times: Sequence[int]
) -> list[CarryBasket]:
    """Consume complete loader-validated hourly buckets, retaining timestamp checks."""
    if not times or len(payments) < 6:
        raise ValueError("nonempty hourly panel and six assets required")
    if any(t % HOUR for t in times) or any(
        b - a != HOUR for a, b in zip(times, times[1:], strict=False)
    ):
        raise ValueError("regular UTC hourly panel required")
    rates = {}
    for coin, rows in payments.items():
        ordered = sorted(rows.items())
        if len(ordered) != len(times) or any(
            at // HOUR * HOUR != expected
            or not 0 <= at - expected <= 60_000
            or not value.is_finite()
            for (at, value), expected in zip(ordered, times, strict=False)
        ):
            raise ValueError(
                "complete finite funding buckets with qualified offsets required"
            )
        rates[coin] = [v for _, v in ordered]
    records = []
    for i, at in enumerate(times):
        date = datetime.fromtimestamp(at / 1000, UTC)
        if i < 168 or i + 169 >= len(times) or date.weekday() != 0 or date.hour:
            continue
        sides, scores, receipt = carry_selection(rates, i)
        records.append(
            CarryBasket(
                i,
                at,
                tuple(sorted(sides.items())),
                tuple(sorted(scores.items())),
                receipt,
                bool(sides) and receipt > HURDLE,
            )
        )
    return records
