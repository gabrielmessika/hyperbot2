"""Descriptive uncertainty and concentration of the selected risk calibration."""

from __future__ import annotations

import argparse
import json
import math
import random
from decimal import Decimal
from pathlib import Path

from hyperbot2.research.artifacts import checked_input, file_sha256, write_json

D = Decimal


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sources, results = {}, []
    for scenario in ("base", "cost_stress", "delay", "funding_adverse"):
        for infra in ("0", "20"):
            path = args.input / f"funding72-cap-0.4-{scenario}-infra-{infra}.json"
            sources[str(path)] = checked_input(path)
            data = json.loads(path.read_text())
            daily = {}
            for row in data["curve"]:
                daily[(row["time_ms"] - 1) // 86_400_000] = D(row["equity"])
            if sorted(daily) != list(range(min(daily), max(daily) + 1)):
                raise ValueError("daily curve gap")
            returns, previous = [], D(1000)
            for day in sorted(daily):
                current = daily[day]
                if current <= 0:
                    raise ValueError("nonpositive equity")
                returns.append(float((current / previous).ln()))
                previous = current
            # Same descriptive method as the earlier metals audit: 14-day
            # moving blocks, fixed seed and 10,000 draws of daily log returns.
            rng, draws = random.Random(20260907), []
            for _ in range(10_000):
                sample = []
                while len(sample) < len(returns):
                    i = rng.randrange(len(returns) - 13)
                    sample.extend(returns[i : i + 14])
                draws.append(
                    math.expm1(30 * sum(sample[: len(returns)]) / len(returns))
                )
            draws.sort()
            pnls = [D(c["net_pnl_usd"]) for c in data["cycles"]]
            total = sum(pnls, D(0))
            cashcat = sum(
                (D(c["net_pnl_usd"]) for c in data["cycles"] if c["coin"] == "CASHCAT"),
                D(0),
            )
            results.append(
                {
                    "scenario": scenario,
                    "monthly_infra": infra,
                    "days": len(returns),
                    "observed_monthly_compound": data["summary"][
                        "equivalent_monthly_compound"
                    ],
                    "descriptive_monthly_95_interval": [draws[249], draws[9749]],
                    "block_days": 14,
                    "draws": 10_000,
                    "cashcat_share_net_trading": cashcat / total if total else None,
                    "best_cycle_usd": max(pnls) if pnls else None,
                    "accounting_net_without_best_cycle_usd": D(
                        data["summary"]["net_total_usd"]
                    )
                    - max(pnls)
                    if pnls
                    else None,
                    "distinct_entry_days": len(
                        {c["opened_ms"] // 86_400_000 for c in data["cycles"]}
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
                "52 days with overlapping blocks and selected strategy/sizing",
                "interval is not family-corrected or a prediction",
                "best-cycle subtraction does not rerun allocation or later trades",
                "bootstrap returns do not rerun the drawdown stop",
            ],
        },
    )
    print(json.dumps(results, default=str, indent=2))


if __name__ == "__main__":
    main()
