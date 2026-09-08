"""Bounded native price-only ceiling for the existing weekly long basket."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from decimal import Decimal as D
from pathlib import Path

from investigate_breakout_extension import DATA, START
from investigate_funding_normalization import END, OLD, ROOT, load
from investigate_funding_transfer import DATA as TRANSFER
from investigate_pairs import bootstrap_ratio

from hyperbot2.research.artifacts import (
    checked_input,
    file_sha256,
    source_version,
    write_json,
)
from hyperbot2.research.rotation import HOUR, leg_return

REPORT = Path("reports/native_price_ceiling_2026-09-07")
QUALIFICATION = Path("reports/native_2025_qualification_2026-09-07")
STEP = 4 * HOUR
SCENARIOS = {
    "central_ceiling": (D(".00045"), D(".0002"), 0),
    "cost_ceiling": (D(".0009"), D(".0005"), 0),
    "delay_4h_ceiling": (D(".00045"), D(".0002"), 1),
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    checked_input(REPORT / "registration.json")
    reg = json.loads((REPORT / "registration.json").read_text())
    version, script_sha = source_version(Path.cwd())[0], file_sha256(Path(__file__))
    if (
        reg["code_version"] != version
        or reg["script_sha256"] != script_sha
        or reg["protocol_sha256"] != file_sha256(REPORT / "PROTOCOL.md")
    ):
        raise ValueError("registered study changed")
    for filename, sha in reg["inputs"].items():
        if checked_input(Path(filename)) != sha:
            raise ValueError("registered source changed")
    q = json.loads((QUALIFICATION / "cohort_qualification.json").read_text())
    coins = [
        r["coin"]
        for r in q["results"]
        if r.get("complete_ordered_buckets")
        and r.get("schema_values_valid")
        and r.get("zero_volume_candles") == 0
    ]
    if coins != reg["coins"] or len(coins) != 9:
        raise ValueError("fixed availability cohort changed")
    args.output.mkdir(parents=True, exist_ok=False)
    for panel in ("native_2025", "native_2026"):
        bars = {}
        if panel == "native_2025":
            sources = {}
            for filename in reg["candle_sources"]:
                p = Path(filename)
                x = json.loads(p.read_text())
                coin = x["request"]["req"]["coin"]
                if coin in coins:
                    sources[str(p)] = checked_input(p)
                    bars[coin] = [
                        {"time": int(r["t"]), "open": D(r["o"]), "close": D(r["c"])}
                        for r in x["response"]
                    ]
            quality = {
                "sources": sources,
                "interval_hours": 4,
                "qualification": str(QUALIFICATION / "cohort_qualification.json"),
            }
        else:
            folders = (
                [DATA / "history"]
                + [TRANSFER / "history" / f"batch-{b}" for b in range(2)]
                + [ROOT / "history", ROOT / "replication_history", OLD / "history"]
            )
            hourly, _, _, quality = load(folders, coins, START, END)
            for c, rows in hourly.items():
                if len(rows) % 4 or rows[0].time % STEP:
                    raise ValueError("complete four-hour aggregation required")
                bars[c] = [
                    {
                        "time": rows[i].time,
                        "open": rows[i].open,
                        "close": rows[i + 3].close,
                    }
                    for i in range(0, len(rows), 4)
                ]
            quality["aggregation"] = (
                "four consecutive qualified hourly bars, no interpolation"
            )
        times = [b["time"] for b in bars[coins[0]]]
        if set(bars) != set(coins) or any(
            [b["time"] for b in bars[c]] != times for c in coins
        ):
            raise ValueError("aligned cohort required")
        if any(t % STEP for t in times) or any(
            b - a != STEP for a, b in zip(times, times[1:], strict=False)
        ):
            raise ValueError("four-hour coverage gap")
        opens = {c: [b["open"] for b in bars[c]] for c in coins}
        selections, events = [], []
        ledger_checks = 0
        for i in range(181, len(times) - 43):
            date = datetime.fromtimestamp(times[i] / 1000, UTC)
            if date.weekday() != 0 or date.hour:
                continue
            scores = {}
            for c in coins:
                prices = [bars[c][i - 1 - 6 * j]["close"] for j in range(31)]
                returns = [(prices[j] / prices[j + 1]).ln() for j in range(30)]
                mean = sum(returns, D(0)) / 30
                scores[c] = (sum(((r - mean) ** 2 for r in returns), D(0)) / 29).sqrt()
            ordered = sorted(coins, key=lambda c: (scores[c], c))
            tied = (
                scores[ordered[2]] == scores[ordered[3]]
                or scores[ordered[-4]] == scores[ordered[-3]]
            )
            selected = [] if tied else ordered[:3] + ordered[-3:]
            selections.append(
                {
                    "time_ms": times[i],
                    "index": i,
                    "scores": scores,
                    "selected": selected,
                }
            )
            if not selected:
                continue
            legs = {}
            for c in coins:
                legs[c] = {}
                for name, (fee, slip, delay) in SCENARIOS.items():
                    at = i + delay
                    r = leg_return(opens[c], (), at, 42, 1, fee, slip, "zero")
                    entry, exit_price = (
                        opens[c][at] * (1 + slip),
                        opens[c][at + 42] * (1 - slip),
                    )
                    quantity = D(1) / entry
                    ledger = -quantity * entry * (1 + fee) + quantity * exit_price * (
                        1 - fee
                    )
                    if abs(ledger * 10000 - r["net_bps"]) > D("1e-18"):
                        raise ValueError("independent price ledger mismatch")
                    ledger_checks += 1
                    legs[c][name] = r
            averages = {
                rule: {
                    scenario: sum((legs[c][scenario]["net_bps"] for c in members), D(0))
                    / len(members)
                    for scenario in SCENARIOS
                }
                for rule, members in (
                    ("volatility_extremes", selected),
                    ("all_assets_control", coins),
                )
            }
            events.append(
                {
                    "time_ms": times[i],
                    "selected": selected,
                    "legs": legs,
                    "basket_returns_net_bps": averages,
                }
            )
        results = {}
        evaluation_start = times[181]
        for rule in ("volatility_extremes", "all_assets_control"):
            results[rule] = {}
            for scenario in SCENARIOS:
                daily = {
                    d: [0.0, 0]
                    for d in range(
                        evaluation_start // (24 * HOUR),
                        (times[-1] + STEP) // (24 * HOUR),
                    )
                }
                values = []
                for e in events:
                    v = e["basket_returns_net_bps"][rule][scenario]
                    values.append(v)
                    daily[e["time_ms"] // (24 * HOUR)] = [float(v), 1]
                results[rule][scenario] = {
                    "mean_net_bps": sum(values, D(0)) / len(values) if values else None,
                    "worst_basket_bps": min(values) if values else None,
                    "positive_baskets": sum(v > 0 for v in values),
                    "mean_bootstrap": bootstrap_ratio(list(daily.values())),
                }
        primary = results["volatility_extremes"]
        criteria = {
            "twenty_baskets": len(events) >= 20,
            "positive_price_ceilings": all(
                r["mean_net_bps"] is not None and r["mean_net_bps"] > 0
                for r in primary.values()
            ),
            "positive_central_lower_bound": (
                primary["central_ceiling"]["mean_bootstrap"]["lower_95"] or 0
            )
            > 0,
        }
        out = args.output / panel
        out.mkdir()
        write_json(out / "quality.json", quality)
        write_json(out / "selections.json", selections)
        write_json(out / "events.json", events)
        write_json(
            out / "summary.json",
            {
                "run_id": f"native-price-ceiling-20260907-v1-{panel}",
                "panel": panel,
                "code_version": version,
                "script_sha256": script_sha,
                "protocol_sha256": reg["protocol_sha256"],
                "coins": coins,
                "baskets": len(events),
                "results": results,
                "criteria": criteria,
                "price_ledger_checks": ledger_checks,
                "scenario_config": SCENARIOS,
                "start_ms": times[0],
                "end_ms_exclusive": times[-1] + STEP,
                "network_data_calls": 0,
                "funding_included": False,
                "portfolio_simulated": False,
                "live_enabled": False,
                "promotion_authorized": False,
            },
        )
        print(
            panel,
            "baskets",
            len(events),
            "primary",
            primary,
            "criteria",
            criteria,
            flush=True,
        )
    if (
        source_version(Path.cwd())[0] != version
        or file_sha256(Path(__file__)) != script_sha
    ):
        raise ValueError("code changed during run")


if __name__ == "__main__":
    main()
