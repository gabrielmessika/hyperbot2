"""Generate synthetic software fixtures, never market or performance evidence."""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from decimal import Decimal as D
from pathlib import Path

from hyperbot2.models import BookLevel, DatasetTier, Side
from hyperbot2.outcomes.contracts import (
    FairValue,
    FeeSchedule,
    OutcomeBook,
    OutcomeDefinition,
)
from hyperbot2.outcomes.serialization import window_payload
from hyperbot2.outcomes.session import OutcomeTrade, OutcomeWindow
from hyperbot2.research.artifacts import file_sha256, write_json


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    output = parser.parse_args().output
    output.mkdir(parents=True, exist_ok=False)
    definition = OutcomeDefinition(
        1,
        "BTC",
        D("80000"),
        86_400_000,
        0,
        D("0.01"),
        D("0.1"),
        FeeSchedule(D(".001"), D(".002"), D(".003"), 0, 100_000_000, "a" * 64),
        "mark_gt_strike",
        "b" * 64,
        True,
    )
    source = output / "windows.jsonl"
    with source.open("x") as stream:
        for now in (1000, 3000, 5000, 7000):
            book = OutcomeBook(
                1,
                now,
                now,
                now,
                (BookLevel(D(".45"), D(1)), BookLevel(D(".30"), D(100))),
                (BookLevel(D(".55"), D(1)), BookLevel(D(".70"), D(100))),
                DatasetTier.A,
                True,
                True,
                True,
            )
            future = tuple(
                replace(book, exchange_ms=t, received_ms=t, sequence=t)
                for t in range(now + 300, now + 1500, 300)
            )
            trades = (
                OutcomeTrade(
                    1,
                    f"synthetic-{now}-sell",
                    0,
                    now + 700,
                    now + 700,
                    now + 700,
                    Side.SELL,
                    D(".30"),
                    D(1000),
                ),
                OutcomeTrade(
                    1,
                    f"synthetic-{now}-buy",
                    0,
                    now + 800,
                    now + 800,
                    now + 800,
                    Side.BUY,
                    D(".70"),
                    D(1000),
                ),
            )
            fair = FairValue(D(".50"), now, now, 0, D(".01"), D(".01"), "d" * 64)
            window = OutcomeWindow(now, definition, book, fair, future, trades)
            stream.write(json.dumps(window_payload(window), default=str) + "\n")
    source.with_suffix(".jsonl.sha256").write_text(file_sha256(source) + "\n")
    write_json(
        output / "manifest.json",
        {
            "kind": "SYNTHETIC_SOFTWARE_FIXTURE",
            "not_market_evidence": True,
            "qualification_flags_are_test_inputs": True,
            "source_sha256": file_sha256(source),
        },
    )


if __name__ == "__main__":
    main()
