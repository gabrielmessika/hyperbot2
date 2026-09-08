"""Descriptive moving-block uncertainty for explicit research portfolio inputs."""

from __future__ import annotations

import argparse
import json
import math
import random
from decimal import Decimal
from pathlib import Path

from hyperbot2.research.artifacts import checked_input, file_sha256, write_json

D = Decimal
DAY = 86_400_000


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    results, sources = [], {}
    for path in args.input:
        sources[str(path)] = checked_input(path)
        data = json.loads(path.read_text())
        daily = {}
        for row in data["curve"]:
            daily[(row["time_ms"] - 1) // DAY] = D(row["equity"])
        if len(daily) < 56 or sorted(daily) != list(range(min(daily), max(daily) + 1)):
            raise ValueError(
                "at least 56 continuous daily equity observations required"
            )
        returns, previous = [], D(1000)
        for day in sorted(daily):
            current = daily[day]
            if current <= 0:
                raise ValueError("nonpositive equity")
            returns.append(float((current / previous).ln()))
            previous = current
        rng, draws = random.Random(20260907), []
        for _ in range(10_000):
            sample = []
            while len(sample) < len(returns):
                i = rng.randrange(len(returns) - 13)
                sample.extend(returns[i : i + 14])
            draws.append(math.expm1(30 * sum(sample[: len(returns)]) / len(returns)))
        draws.sort()
        pnls = [D(c["net_pnl_usd"]) for c in data["cycles"]]
        results.append(
            {
                "input": str(path),
                "days": len(daily),
                "observed_monthly_compound": data["summary"][
                    "equivalent_monthly_compound"
                ],
                "descriptive_monthly_95_interval": [draws[249], draws[9749]],
                "block_days": 14,
                "draws": 10_000,
                "best_cycle_usd": max(pnls) if pnls else None,
                "accounting_net_without_best_cycle_usd": D(
                    data["summary"]["net_total_usd"]
                )
                - max(pnls)
                if pnls
                else None,
                "distinct_entry_days": len(
                    {c["opened_ms"] // DAY for c in data["cycles"]}
                ),
            }
        )
    write_json(
        args.output / "uncertainty.json",
        {
            "sources": sources,
            "script_sha256": file_sha256(Path(__file__)),
            "results": results,
            "post_selection_descriptive": True,
            "promotion_authorized": False,
            "limits": [
                "overlapping 14-day blocks from a selected strategy and sizing",
                "not corrected for the family of previous strategy searches",
                "neither a predictive interval nor a proof of expected future profit",
                "bootstrap returns do not rerun drawdown, allocations or execution",
                "best-cycle subtraction does not rerun the portfolio",
            ],
        },
    )
    print(json.dumps(results, default=str, indent=2))


if __name__ == "__main__":
    main()
