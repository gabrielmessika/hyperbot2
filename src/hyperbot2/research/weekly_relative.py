"""Past-only weekly relative-strength ranking with a one-day skip."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from decimal import Decimal

D = Decimal


def weekly_selection(
    closes: Mapping[str, Sequence[Decimal]], entry_index: int
) -> tuple[dict[str, int], dict[str, Decimal]]:
    if len(closes) < 6 or entry_index < 193:
        raise ValueError("six assets and eight completed days required")
    scores = {
        c: rows[entry_index - 25] / rows[entry_index - 193] - 1
        for c, rows in closes.items()
    }
    ordered = sorted(scores, key=lambda c: (scores[c], c))
    shorts, longs = ordered[:3], ordered[-3:]
    if min(scores[c] for c in longs) <= max(scores[c] for c in shorts):
        return {}, scores
    return {**dict.fromkeys(shorts, -1), **dict.fromkeys(longs, 1)}, scores


def weekly_entries(
    closes: Mapping[str, Sequence[Decimal]], times: Sequence[int]
) -> tuple[dict[str, tuple[int, ...]], list[dict[str, object]]]:
    if any(len(rows) != len(times) for rows in closes.values()):
        raise ValueError("aligned closes and timestamps required")
    entries = {c: [0] * len(times) for c in closes}
    records: list[dict[str, object]] = []
    for i, at in enumerate(times):
        dt = datetime.fromtimestamp(at / 1000, UTC)
        if i < 193 or i + 169 >= len(times) or dt.weekday() != 0 or dt.hour != 0:
            continue
        sides, scores = weekly_selection(closes, i)
        for c, side in sides.items():
            entries[c][i] = side
        records.append({"index": i, "time_ms": at, "scores": scores, "sides": sides})
    return {c: tuple(rows) for c, rows in entries.items()}, records
