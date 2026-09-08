"""Descriptive covariance of selected mechanisms, never a combined-account backtest."""

from __future__ import annotations

import argparse
import json
from decimal import Decimal
from itertools import combinations
from pathlib import Path

from hyperbot2.research.artifacts import checked_input, file_sha256, write_json

D = Decimal
DAY = 86_400_000
REPORT = Path("reports/diversification_2026-09-07")


def correlation(a: list[Decimal], b: list[Decimal]) -> Decimal | None:
    ma, mb = sum(a, D(0)) / len(a), sum(b, D(0)) / len(b)
    x, y = [v - ma for v in a], [v - mb for v in b]
    xx, yy = sum((v * v for v in x), D(0)), sum((v * v for v in y), D(0))
    return (
        sum((u * v for u, v in zip(x, y, strict=True)), D(0)) / (xx * yy).sqrt()
        if xx and yy
        else None
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    checked_input(REPORT / "registration.json")
    protocol = file_sha256(REPORT / "PROTOCOL.md")
    if (
        json.loads((REPORT / "registration.json").read_text())["protocol_sha256"]
        != protocol
    ):
        raise ValueError("registered covariance qualification changed")
    sources, results = {}, {}
    for scenario in ("base", "cost_stress", "delay", "funding_adverse"):
        paths = {
            "breakout": Path("data/compression_breakout_2026-09-07/run1")
            / f"no_compression_control-cap-0.5-{scenario}-infra-0.json",
            "weekly": Path("data/weekly_relative_2026-09-07/run1")
            / f"weekly_relative-cap-0.5-{scenario}-infra-0.json",
            "passive_control": Path("data/weekly_relative_2026-09-07/run1")
            / f"hold_equal-cap-0.5-{scenario}-infra-0.json",
        }
        returns, timelines = {}, {}
        for name, path in paths.items():
            sources[str(path)] = checked_input(path)
            data = json.loads(path.read_text())
            if data["summary"]["halted"]:
                raise ValueError("halted path cannot support this covariance screen")
            daily = {}
            for row in data["curve"]:
                daily[(row["time_ms"] - 1) // DAY] = D(row["equity"])
            if len(daily) != 180 or sorted(daily) != list(
                range(min(daily), max(daily) + 1)
            ):
                raise ValueError("expected 180 aligned daily marks")
            timelines[name] = sorted(daily)
            previous, returns[name] = D(1000), []
            for day in timelines[name]:
                current = daily[day]
                returns[name].append((current / previous).ln())
                previous = current
        if any(t != timelines["breakout"] for t in timelines.values()):
            raise ValueError("unaligned portfolio dates")
        pairs = {}
        for a, b in combinations(returns, 2):
            x, y = returns[a], returns[b]
            downside = [(u, v) for u, v in zip(x, y, strict=True) if u < 0 or v < 0]
            pairs[f"{a}/{b}"] = {
                "correlation": correlation(x, y),
                "both_red_days": sum(
                    u < 0 and v < 0 for u, v in zip(x, y, strict=True)
                ),
                "either_red_days": len(downside),
                "downside_subset_correlation": correlation(
                    [p[0] for p in downside], [p[1] for p in downside]
                ),
                "a_red_days": sum(u < 0 for u in x),
                "b_red_days": sum(v < 0 for v in y),
            }
        results[scenario] = pairs
    passed = all(
        r["breakout/weekly"]["correlation"] is not None
        and abs(r["breakout/weekly"]["correlation"]) < D("0.5")
        for r in results.values()
    )
    write_json(
        args.output / "summary.json",
        {
            "run_id": "diversification-20260907-v1",
            "protocol_sha256": protocol,
            "script_sha256": file_sha256(Path(__file__)),
            "sources": sources,
            "results": results,
            "decision": "DIVERSIFICATION_WORTH_PORTFOLIO_TEST"
            if passed
            else "COVARIANCE_NOT_COMPELLING",
            "combined_account_pnl_computed": False,
            "live_enabled": False,
            "promotion_authorized": False,
        },
    )
    print(json.dumps(results, default=str, indent=2))


if __name__ == "__main__":
    main()
