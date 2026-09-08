"""External aggressive-flow event study with registered rules and local data."""

from __future__ import annotations

import argparse
import json
import runpy
from decimal import Decimal
from pathlib import Path

from hyperbot2.research.artifacts import checked_input, file_sha256, write_json
from hyperbot2.research.order_flow import FlowBar, classify_flow
from hyperbot2.research.rotation import leg_return
from hyperbot2.research.volume import VolumeBar

D = Decimal
DAY = 86400000


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    protocol = Path("reports/order_flow_2026-09-07/PROTOCOL.md")
    checked_input(protocol.parent / "registration.json")
    if json.loads((protocol.parent / "registration.json").read_text())[
        "protocol_sha256"
    ] != file_sha256(protocol):
        raise ValueError("protocol changed")
    hl_loader = Path(__file__).with_name("evaluate_alternatives.py")
    bn_loader = Path(__file__).with_name("investigate_cross_venue.py")
    stats_path = Path(__file__).with_name("investigate_volume_shocks.py")
    stats = runpy.run_path(str(stats_path))
    candles, funding, start, end, sources = runpy.run_path(str(hl_loader))[
        "load_history"
    ](Path("data/search_2026-09-06/history"))
    bn, _, bn_sources = runpy.run_path(str(bn_loader))["load_binance"](
        Path("data/cross_venue_2026-09-07/binance"), start, end
    )
    sources.update(bn_sources)
    bars = {c: [] for c in bn}
    for p in bn_sources:
        raw = json.loads(Path(p).read_text())
        if raw["route"] != "klines":
            continue
        bars[raw["coin"]].extend(
            FlowBar(VolumeBar(int(r[0]), *(D(x) for x in r[1:6])), D(r[9]))
            for r in raw["response"]
        )
    events = {name: [] for name in ("accepted_pressure", "absorbed_pressure")}
    for coin, rows in bars.items():
        rows.sort(key=lambda r: r.bar.time)
        if [r.bar for r in rows] != bn[coin]:
            raise ValueError("flow/candle alignment mismatch")
        opens = [b.open for b in candles[coin]]
        rates = [funding[coin][b.time] for b in candles[coin]]
        next_allowed = dict.fromkeys(events, 0)
        for i in range(168, len(rows) - 26):
            for name, side in classify_flow(rows, i).items():
                if i < next_allowed[name]:
                    continue
                next_allowed[name] = i + 25
                entry = i + 1
                event = {
                    "coin": coin,
                    "side": side,
                    "signal_ms": rows[i].bar.time,
                    "entry_ms": candles[coin][entry].time,
                    "imbalance": 2 * rows[i].taker_buy_volume / rows[i].bar.volume - 1,
                    "returns": {},
                }
                for hold in (1, 6, 24):
                    event["returns"][str(hold)] = {
                        s: leg_return(
                            opens, rates, entry + delay, hold, side, fee, slip, mode
                        )
                        for s, (fee, slip, delay, mode) in stats["SCENARIOS"].items()
                    }
                events[name].append(event)
    results = {}
    for name, selected in events.items():
        selected.sort(key=lambda e: (e["entry_ms"], e["coin"]))
        summary = {
            str(h): {
                s: stats["summarize"](selected, str(h), s, start + 7 * DAY, end)
                for s in stats["SCENARIOS"]
            }
            for h in (1, 6, 24)
        }
        ci = stats["interval"](selected, start + 7 * DAY, end)
        base = summary["6"]["base"]
        criteria = {
            "all_cost_scenarios_positive": all(
                (summary["6"][s]["mean_net_bps"] or 0) > 0
                for s in stats["SCENARIOS"]
                if s != "zero_cost"
            ),
            "profit_factor_above_1_2": (base["profit_factor"] or 0) > D("1.2"),
            "corrected_interval_lower_positive": ci is not None and ci["lower"] > 0,
            "four_positive_blocks": sum(v > 0 for v in base["blocks_30d_sum_bps"]) >= 4,
            "positive_without_best": (base["sum_without_best_bps"] or 0) > 0,
        }
        results[name] = {
            "horizons": summary,
            "primary_interval": ci,
            "criteria": criteria,
            "decision": "FURTHER_FREE_VALIDATION"
            if all(criteria.values())
            else "HYPOTHESIS_NOT_CONFIRMED",
        }
        write_json(args.output / f"{name}-events.json", selected)
    write_json(
        args.output / "summary.json",
        {
            "run_id": "order-flow-2026-09-07",
            "strategies": results,
            "source_hashes": sources,
            "start_ms": start,
            "end_ms_exclusive": end,
            "protocol_sha256": file_sha256(protocol),
            "code_hashes": {
                str(p): file_sha256(p)
                for p in (
                    Path(__file__),
                    hl_loader,
                    bn_loader,
                    stats_path,
                    Path("src/hyperbot2/research/order_flow.py"),
                    Path("src/hyperbot2/research/rotation.py"),
                    Path("src/hyperbot2/research/volume.py"),
                )
            },
            "incremental_data_cost_usd": 0,
            "network_calls": 0,
            "independent_holdout": False,
            "promotion_authorized": False,
            "limits": [
                "external USDC contract flow, not all Binance flow",
                "prior price history reused; local two-rule correction only",
                "no receipt-time or quote evidence; hourly-open fills hypothetical",
                "funding valued with hourly price proxy; no risk-sized portfolio",
            ],
        },
    )
    print(args.output / "summary.json")


if __name__ == "__main__":
    main()
