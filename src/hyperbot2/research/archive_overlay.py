"""Explicit, narrow REST source overlay for the audited October 2024 discrepancy."""

from __future__ import annotations

import json
from collections.abc import Sequence
from decimal import Decimal
from pathlib import Path

from hyperbot2.research.artifacts import checked_input
from hyperbot2.research.rotation import HOUR
from hyperbot2.research.volume import VolumeBar

OCTOBER_START = 1727740800000
OCTOBER_END = 1730419200000
DISPUTED = (1730145600000, 1730149200000)


def load_october_rest(
    root: Path, coins: Sequence[str]
) -> tuple[dict[str, list[VolumeBar]], dict[str, str]]:
    manifest = root / "manifest.json"
    sources = {str(manifest): checked_input(manifest)}
    requests = json.loads(manifest.read_text())["requests"]
    if len(requests) != len(coins) or {r["coin"] for r in requests} != set(coins):
        raise ValueError("exact REST correction cohort required")
    output = {}
    for r in requests:
        path = Path(r["path"])
        sha = checked_input(path)
        if r["returncode"] != 0 or sha != r["sha256"]:
            raise ValueError("REST correction source failed")
        sources[str(path)] = sha
        bars = []
        for row in json.loads(path.read_text()):
            if len(row) != 12 or row[6] != row[0] + HOUR - 1:
                raise ValueError("invalid REST candle schema or duration")
            bars.append(VolumeBar(row[0], *(Decimal(row[j]) for j in (1, 2, 3, 4, 5))))
        if [b.time for b in bars] != list(range(OCTOBER_START, OCTOBER_END, HOUR)):
            raise ValueError("complete ordered October REST history required")
        if any(b.volume <= 0 for b in bars):
            raise ValueError("positive REST correction volume required")
        output[r["coin"]] = bars
    return output, sources


def overlay_october(
    original: Sequence[VolumeBar], rest: Sequence[VolumeBar]
) -> list[VolumeBar]:
    """Check all 744 overlapping bars; replace only the two registered disagreements."""
    expected = list(range(OCTOBER_START, OCTOBER_END, HOUR))
    old = [b for b in original if OCTOBER_START <= b.time < OCTOBER_END]
    if [b.time for b in old] != expected or [b.time for b in rest] != expected:
        raise ValueError("complete October overlap required")
    if any(b.volume <= 0 for b in rest):
        raise ValueError("positive REST correction volume required")
    different = [a.time for a, b in zip(old, rest, strict=True) if a != b]
    if (
        tuple(different) != DISPUTED
        or next(b for b in old if b.time == DISPUTED[0]).volume != 0
    ):
        raise ValueError("correction differs from the registered two-hour scope")
    replacement = {b.time: b for b in rest if b.time in DISPUTED}
    return [replacement.get(b.time, b) for b in original]
