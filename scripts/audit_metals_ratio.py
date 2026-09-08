"""Post-selection descriptive block uncertainty, never a promotion test."""

from __future__ import annotations

import argparse
import json
import math
import random
from decimal import Decimal
from pathlib import Path

from hyperbot2.research.artifacts import checked_input, file_sha256, write_json

D = Decimal
ROOT = Path("data/metals_ratio_2026-09-07/run1")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    sources = {}
    results = []
    for cap in ("0.5", "1"):
        for scenario in ("base", "cost_stress", "delay", "funding_adverse"):
            path = ROOT / f"cap-{cap}-{scenario}-infra-0.json"
            sources[str(path)] = checked_input(path)
            data = json.loads(path.read_text())
            daily = {}
            for row in data["curve"]:
                daily[(row["time_ms"] - 1) // 86_400_000] = D(row["equity"])
            if sorted(daily) != list(range(min(daily), max(daily) + 1)):
                raise ValueError("daily curve gap")
            previous = D(1000)
            returns = []
            for day in sorted(daily):
                current = daily[day]
                if current <= 0:
                    raise ValueError("nonpositive equity cannot use log returns")
                returns.append(float((current / previous).ln()))
                previous = current
            rng = random.Random(20260907)
            draws = []
            for _ in range(10_000):
                sampled = []
                while len(sampled) < len(returns):
                    index = rng.randrange(len(returns) - 14 + 1)
                    sampled.extend(returns[index : index + 14])
                draws.append(
                    math.expm1(30 * sum(sampled[: len(returns)]) / len(returns))
                )
            draws.sort()
            results.append(
                {
                    "gross_cap": cap,
                    "scenario": scenario,
                    "days": len(returns),
                    "observed_monthly_compound": data["summary"][
                        "equivalent_monthly_compound"
                    ],
                    "descriptive_monthly_95_interval": [draws[249], draws[9749]],
                    "positive_draw_fraction": sum(v > 0 for v in draws) / len(draws),
                }
            )
    write_json(
        args.output / "summary.json",
        {
            "run_id": "metals-ratio-descriptive-audit-20260907-v1",
            "sources": sources,
            "script_sha256": file_sha256(Path(__file__)),
            "validation_note_sha256": file_sha256(
                Path("reports/metals_ratio_2026-09-07/VALIDATION_NOTE.md")
            ),
            "results": results,
            "post_selection_descriptive": True,
            "promotion_authorized": False,
            "live_enabled": False,
        },
    )
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
