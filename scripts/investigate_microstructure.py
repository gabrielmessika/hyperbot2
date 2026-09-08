"""Evaluate preregistered flow/book hypotheses from causal existing data."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import random
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path
from typing import Any

from evaluate_alternatives import load_history

from hyperbot2.research.artifacts import (
    checked_input,
    file_sha256,
    source_version,
    write_json,
)
from hyperbot2.research.microstructure import MicroQuote, micro_signal, taker_return

D = Decimal
REPORT = Path("reports/microstructure_2026-09-07")
COINS = ("BTC", "ETH", "HYPE")
RULES = ("continuation", "absorption")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    checked_input(REPORT / "registration.json")
    checked_input(REPORT / "adapter_registration.json")
    protocol = file_sha256(REPORT / "PROTOCOL.md")
    adapter = file_sha256(REPORT / "ADAPTER.md")
    if (
        json.loads((REPORT / "registration.json").read_text())["protocol_sha256"]
        != protocol
    ):
        raise ValueError("registered protocol changed")
    if (
        json.loads((REPORT / "adapter_registration.json").read_text())["adapter_sha256"]
        != adapter
    ):
        raise ValueError("registered adapter changed")
    candles, funding, _, _, history_sources = load_history(
        Path("data/search_2026-09-06/history")
    )
    payments = {
        coin: tuple((b.time, funding[coin][b.time], b.open) for b in candles[coin])
        for coin in COINS
    }
    sources = dict(history_sources)
    results: list[dict[str, Any]] = []
    days = []
    for manifest_path in sorted(args.input.glob("*/manifest.json")):
        root = manifest_path.parent
        sources[str(manifest_path)] = checked_input(manifest_path)
        manifest = json.loads(manifest_path.read_text())
        if (
            manifest["protocol_sha256"] != protocol
            or manifest["adapter_sha256"] != adapter
        ):
            raise ValueError("extraction protocol or adapter mismatch")
        path = root / "seconds.csv.gz"
        sources[str(path)] = checked_input(path)
        if sources[str(path)] != manifest["seconds_sha256"]:
            raise ValueError("seconds checksum differs from manifest")
        if (
            checked_input(root / "source_manifest.json")
            != manifest["source_manifest_sha256"]
        ):
            raise ValueError("source inventory checksum mismatch")
        days.append(manifest["day"])
        quotes: dict[tuple[str, int], MicroQuote] = {}
        signals = []
        last = defaultdict(lambda: -(10**20))
        with gzip.open(path, "rt") as stream:
            for row in csv.DictReader(stream):
                coin, time = row["coin"], int(row["time"])
                if row["bid"]:
                    quote = MicroQuote(
                        time,
                        *(D(row[k]) for k in ("bid", "ask", "bid_size", "ask_size")),
                    )
                    if (coin, time) in quotes:
                        raise ValueError("duplicate second")
                    quotes[coin, time] = quote
                if row["valid"] != "1":
                    continue
                kwargs = {
                    "coin": coin,
                    "valid": True,
                    "flow": D(row["flow"]),
                    "notional": D(row["notional"]),
                    "count": int(row["count"]),
                    "imbalance": D(row["imbalance"]),
                    "return_bps": D(row["return_bps"]),
                    "spread_bps": D(row["spread_bps"]),
                }
                for rule in RULES:
                    if time < last[coin, rule] + 1_800_000:
                        continue
                    side = micro_signal(rule=rule, **kwargs)
                    if side:
                        last[coin, rule] = time
                        signals.append(
                            {
                                "coin": coin,
                                "rule": rule,
                                "decision_ms": time,
                                "side": side,
                                "day": manifest["day"],
                                "features": kwargs,
                            }
                        )
        for signal in signals:
            coin, time, side = signal["coin"], signal["decision_ms"], signal["side"]
            for horizon in (300, 1800):
                for delay in (1, 2):
                    item = dict(signal, horizon_seconds=horizon, delay_seconds=delay)
                    results.append(item)
                    entry = quotes.get((coin, time + delay * 1000))
                    exit = quotes.get((coin, time + (horizon + delay) * 1000))
                    if entry is None or exit is None:
                        item["status"] = (
                            "ENTRY_QUOTE_MISSING"
                            if entry is None
                            else "EXIT_QUOTE_MISSING"
                        )
                        continue
                    item["mid_markout_bps"] = (
                        side
                        * ((exit.bid + exit.ask) / (entry.bid + entry.ask) - 1)
                        * 10_000
                    )
                    base = taker_return(coin, side, entry, exit, payments[coin])
                    stressed = taker_return(
                        coin, side, entry, exit, payments[coin], stress=True
                    )
                    if base is None or stressed is None:
                        item["status"] = "DEPTH_INSUFFICIENT"
                        continue
                    item.update(
                        {"status": "EXPLORATORY_FILL", "base": base, "stress": stressed}
                    )
        print(
            manifest["day"],
            "signals",
            dict(Counter(s["rule"] for s in signals)),
            flush=True,
        )
    summary: dict[str, Any] = {
        "run_id": "microstructure-fixed-20260907-v1",
        "config_hash": protocol,
        "adapter_hash": adapter,
        "code_version": source_version(Path.cwd())[0],
        "script_sha256": file_sha256(Path(__file__)),
        "loader_sha256": file_sha256(Path("scripts/evaluate_alternatives.py")),
        "sources": sources,
        "days": days,
        "groups": [],
        "live_enabled": False,
        "shadow_only": True,
        "public_data_only": True,
        "execution_model": "causal received BBO at +1s; alternative +2s; 10% depth cap",
        "cost_model": (
            "4.5bps fees and 1bp slippage per side; stress 7bps/3bps; "
            "signed funding with hourly perp open as oracle proxy"
        ),
    }
    for rule in RULES:
        for horizon in (300, 1800):
            for delay in (1, 2):
                events = [
                    r
                    for r in results
                    if r["rule"] == rule
                    and r["horizon_seconds"] == horizon
                    and r["delay_seconds"] == delay
                ]
                fills = [r for r in events if r["status"] == "EXPLORATORY_FILL"]
                markouts = [
                    r["mid_markout_bps"] for r in events if "mid_markout_bps" in r
                ]
                base = sum((r["base"]["pnl_usd"] for r in fills), D(0))
                stress = sum((r["stress"]["pnl_usd"] for r in fills), D(0))
                by_day = {
                    day: sum(
                        (r["base"]["pnl_usd"] for r in fills if r["day"] == day), D(0)
                    )
                    for day in days
                }
                by_coin = {
                    coin: sum(
                        (r["base"]["pnl_usd"] for r in fills if r["coin"] == coin), D(0)
                    )
                    for coin in COINS
                }
                interval = None
                gains = sum((max(D(0), r["base"]["pnl_usd"]) for r in fills), D(0))
                losses = sum((min(D(0), r["base"]["pnl_usd"]) for r in fills), D(0))
                if len(days) >= 5:
                    rng = random.Random(709)
                    values = list(by_day.values())
                    draws = sorted(
                        sum(rng.choices(values, k=len(values)), D(0))
                        for _ in range(10_000)
                    )
                    interval = [draws[49], draws[9949]]
                summary["groups"].append(
                    {
                        "rule": rule,
                        "horizon_seconds": horizon,
                        "delay_seconds": delay,
                        "signals": len(events),
                        "fills": len(fills),
                        "status_counts": dict(Counter(r["status"] for r in events)),
                        "mean_mid_markout_bps": sum(markouts, D(0)) / len(markouts)
                        if markouts
                        else None,
                        "mean_net_bps": sum((r["base"]["net_bps"] for r in fills), D(0))
                        / len(fills)
                        if fills
                        else None,
                        "mean_stress_bps": sum(
                            (r["stress"]["net_bps"] for r in fills), D(0)
                        )
                        / len(fills)
                        if fills
                        else None,
                        "base_pnl_usd": base,
                        "stress_pnl_usd": stress,
                        "winning_fills": sum(r["base"]["pnl_usd"] > 0 for r in fills),
                        "gross_positive_pnl_usd": gains,
                        "gross_negative_pnl_usd": losses,
                        "profit_factor": gains / abs(losses) if losses < 0 else None,
                        "evaluable_fraction": D(len(fills)) / len(events)
                        if events
                        else None,
                        "base_by_day": by_day,
                        "base_by_coin": by_coin,
                        "bootstrap_99_usd": interval,
                        "monthly_proxy_after_infra": base * 30 / len(days) - 20
                        if days
                        else None,
                    }
                )
    principal = [
        g
        for g in summary["groups"]
        if g["horizon_seconds"] == 300 and g["delay_seconds"] == 1
    ]
    stop = all(
        g["mean_mid_markout_bps"] is not None and g["mean_mid_markout_bps"] < 0
        for g in principal
    )
    summary["pilot_stop_rule_triggered"] = stop
    summary["verdict"] = "HYPOTHESIS_NOT_CONFIRMED"
    write_json(args.output / "events.json", results)
    write_json(args.output / "summary.json", summary)
    print(json.dumps(principal, default=str, indent=2))


if __name__ == "__main__":
    main()
