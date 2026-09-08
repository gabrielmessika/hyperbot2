"""Frozen daily binary-price hypothesis against native official settlements."""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from dataclasses import asdict, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

from evaluate_alternatives import HOUR, load_history

from hyperbot2.research.artifacts import (
    checked_input,
    file_sha256,
    source_version,
    write_json,
)
from hyperbot2.research.outcome_taker import (
    TakerBook,
    execution_price,
    select_intent,
    settlement_pnl,
)
from hyperbot2.research.outcomes import (
    DigitalOutcomeBenchmark,
    OutcomeSample,
    empirical_volatility,
)

D = Decimal
ROOT = Path("data/outcome_taker_2026-09-07")
REPORT = Path("reports/outcome_taker_2026-09-07")
SPLIT = 1_781_481_600_000  # 2026-06-15 00:00 UTC


def book(row: dict[str, Any] | None) -> TakerBook | None:
    if row is None or row["raw"]["best_ask"] is None:
        return None
    return TakerBook(
        row["event_ms"],
        row["received_ms"],
        D(str(row["raw"]["best_ask"])),
        D(str(row["raw"]["ask_size"])),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--extract", type=Path, default=ROOT / "extract")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    checked_input(REPORT / "registration.json")
    protocol_hash = file_sha256(REPORT / "PROTOCOL.md")
    if (
        json.loads((REPORT / "registration.json").read_text())["protocol_sha256"]
        != protocol_hash
    ):
        raise ValueError("protocol changed after registration")
    sources: dict[str, str] = {}

    def read(path: Path) -> Any:
        sources[str(path)] = checked_input(path)
        return json.loads(path.read_text())

    extraction = read(args.extract / "manifest.json")
    markets = read(args.extract / "markets.json")
    rows = read(args.extract / "books.json")
    for name in ("books", "markets"):
        if sources[str(args.extract / f"{name}.json")] != extraction[f"{name}_sha256"]:
            raise ValueError("extraction manifest mismatch")
    books = {(r["market"], r["side"], r["stage"]): r for r in rows}
    if len(books) != len(rows):
        raise ValueError("duplicate selected book")
    label_manifest = read(ROOT / "labels/manifest.json")
    if label_manifest["markets_sha256"] != sources[str(args.extract / "markets.json")]:
        raise ValueError("label universe differs from extracted markets")
    labels = {}
    for record in label_manifest["requests"]:
        path = Path(record["path"])
        response = read(path)
        if sources[str(path)] != record["sha256"] or response["returncode"]:
            raise ValueError("label manifest mismatch")
        labels[response["request"]["outcome"]] = response["response"]
    candles, _, _, _, history_sources = load_history(
        Path("data/search_2026-09-06/history")
    )
    sources.update(history_sources)
    indices = {
        coin: {c.time: i for i, c in enumerate(cs)} for coin, cs in candles.items()
    }
    results = []
    model = DigitalOutcomeBenchmark()
    for market, meta in sorted(markets.items()):
        item: dict[str, Any] = {"market": market, **meta}
        results.append(item)
        if meta["outcome"] in {111, 762, 1715}:
            item["status"] = "PROBE_LABEL_ALREADY_SEEN"
            continue
        label = labels.get(meta["outcome"])
        if not label:
            item["status"] = "OFFICIAL_LABEL_MISSING"
            continue
        spec = label["spec"]
        fields = dict(part.split(":", 1) for part in spec["description"].split("|"))
        parts = market.split("_")
        if (
            spec["outcome"] != meta["outcome"]
            or fields["underlying"] != meta["underlying"]
            or D(fields["targetPrice"]) != D(meta["strike"])
            or fields["expiry"] != parts[3] + "-" + parts[4]
            or fields["period"] != "1d"
            or fields["class"] != "priceBinary"
            or spec["quoteToken"] != "USDC"
            or [s["name"] for s in spec["sideSpecs"]] != ["Yes", "No"]
        ):
            raise ValueError("official contract identity differs from legacy book")
        fraction = D(label["settleFraction"])
        if fraction not in (D(0), D(1)):
            item["status"] = "NON_BINARY_SETTLEMENT"
            continue
        coin, decision = meta["underlying"], meta["decision_ms"]
        index = indices[coin].get(decision // HOUR * HOUR - HOUR)
        if index is None or index < 168:
            item["status"] = "REFERENCE_HISTORY_MISSING"
            continue
        history = candles[coin][index - 168 : index + 1]
        if any(
            b.time - a.time != HOUR for a, b in zip(history, history[1:], strict=False)
        ):
            raise ValueError("reference history gap")
        volatility = empirical_volatility(
            tuple(c.close for c in history), periods_per_year=8766
        )
        sample = OutcomeSample(
            market,
            decision,
            meta["expiry_ms"],
            market,
            coin,
            history[-1].close,
            D(meta["strike"]),
            volatility,
            0,
            D(0),
            D(0),
            "unfitted",
            "18h",
        )
        probabilities = tuple(
            model.probability(
                replace(sample, realized_volatility_annualized=volatility * scale)
            )
            for scale in (D("0.75"), D(1), D("1.25"))
        )
        available = {}
        diagnostics = {}
        for side in ("YES", "NO"):
            candidate = book(books.get((market, side, "decision")))
            if candidate is None:
                diagnostics[side] = {"status": "MISSING_OR_EMPTY"}
                continue
            if not candidate.fresh(decision):
                diagnostics[side] = {"status": "STALE_OR_INVALID"}
                continue
            if not D("0.15") <= candidate.ask <= D("0.85"):
                diagnostics[side] = {"status": "OUTSIDE_PRICE_BAND"}
            else:
                ps = (
                    probabilities
                    if side == "YES"
                    else tuple(1 - p for p in probabilities)
                )
                robust_edge = (
                    max(D(0), min(ps) - D("0.03")) * D("0.998") - candidate.ask
                )
                diagnostics[side] = {
                    "status": "SMALL_EDGE" if robust_edge < D("0.05") else "EDGE_PASS",
                    "robust_edge": robust_edge,
                    "ask": candidate.ask,
                    "ask_size": candidate.ask_size,
                }
            if candidate is not None:
                available[side] = candidate
        item["decision_diagnostics"] = diagnostics
        intent = select_intent(decision, probabilities, available)
        item.update(
            {
                "spot_proxy": history[-1].close,
                "volatility": volatility,
                "probabilities": probabilities,
            }
        )
        if intent is None:
            item["status"] = "NO_ELIGIBLE_INTENT"
            continue
        item["intent"] = asdict(intent)
        item["fraction"] = fraction
        item["segment"] = "old" if meta["expiry_ms"] < SPLIT else "validation"
        executed = execution_price(
            intent, book(books.get((market, intent.side, "execution")))
        )
        delayed = execution_price(
            intent, book(books.get((market, intent.side, "delay"))), delay=True
        )
        item.update(
            {
                "status": "EXPLORATORY_FILL"
                if executed is not None
                else "EXECUTION_REJECTED",
                "price": executed,
                "delay_price": delayed,
                "pnl": settlement_pnl(intent, executed, fraction)
                if executed is not None
                else D(0),
                "stress_pnl": settlement_pnl(intent, executed, fraction, stress=True)
                if executed is not None
                else D(0),
                "delay_pnl": settlement_pnl(intent, delayed, fraction)
                if delayed is not None
                else D(0),
            }
        )
    traded = [r for r in results if r["status"] == "EXPLORATORY_FILL"]
    intents = [r for r in results if "intent" in r]
    by_day: dict[int, Decimal] = defaultdict(Decimal)
    for row in traded:
        by_day[row["expiry_ms"] // (24 * HOUR)] += row["pnl"]
    totals = {
        key: sum((r[key] for r in intents), D(0))
        for key in ("pnl", "stress_pnl", "delay_pnl")
    }
    interval = None
    if by_day:
        rng = random.Random(1709)
        values = list(by_day.values())
        draws = sorted(
            sum(rng.choices(values, k=len(values)), D(0)) for _ in range(10_000)
        )
        interval = [draws[49], draws[9949]]
    by_coin = {
        coin: sum((r["pnl"] for r in traded if r["underlying"] == coin), D(0))
        for coin in candles
    }
    segments = {
        segment: sum((r["pnl"] for r in traded if r["segment"] == segment), D(0))
        for segment in ("old", "validation")
    }
    period_days = (
        max(m["expiry_ms"] for m in markets.values())
        - min(m["expiry_ms"] for m in markets.values())
    ) // (24 * HOUR) + 1
    monthly = totals["pnl"] * 30 / period_days - 20
    positive_coin_profits = sum((max(D(0), v) for v in by_coin.values()), D(0))
    concentration = (
        max(by_coin.values()) / positive_coin_profits
        if positive_coin_profits > 0
        else None
    )
    gates = {
        "30_trade_dates": len(by_day) >= 30,
        "both_segments_positive": all(v > 0 for v in segments.values()),
        "stress_positive": totals["stress_pnl"] > 0,
        "delay_positive": totals["delay_pnl"] > 0,
        "bootstrap_99_lower_positive": interval is not None and interval[0] > 0,
        "coin_concentration_le_half": concentration is not None
        and concentration <= D("0.5"),
        "monthly_after_infra_ge_30": monthly >= 30,
    }
    summary = {
        "run_id": "outcome-taker-fixed-20260907-v1",
        "config_hash": protocol_hash,
        "code_version": source_version(Path.cwd())[0],
        "scripts": {
            str(p): file_sha256(p)
            for p in (Path(__file__), Path("scripts/evaluate_alternatives.py"))
        },
        "sources": sources,
        "period_start_expiry_ms": min(m["expiry_ms"] for m in markets.values()),
        "period_end_expiry_ms": max(m["expiry_ms"] for m in markets.values()),
        "period_days": period_days,
        "counts": dict(Counter(r["status"] for r in results)),
        "side_diagnostic_counts": dict(
            Counter(
                d["status"]
                for r in results
                for d in r.get("decision_diagnostics", {}).values()
            )
        ),
        "maximum_robust_edge": max(
            (
                d["robust_edge"]
                for r in results
                for d in r.get("decision_diagnostics", {}).values()
                if "robust_edge" in d
            ),
            default=None,
        ),
        "independent_trade_dates": len(by_day),
        "pnl_usd": totals,
        "base_pnl_by_coin": by_coin,
        "base_pnl_by_segment": segments,
        "bootstrap_99_total_usd": interval,
        "monthly_proxy_after_20_usd_infra": monthly,
        "positive_profit_coin_concentration": concentration,
        "gates": gates,
        "verdict": "REPLICATION_CANDIDATE"
        if all(gates.values())
        else "HYPOTHESIS_NOT_CONFIRMED",
        "execution_evidence": (
            "legacy B exploratory sampled asks, no actual fills; "
            "reference availability assumed +5s"
        ),
        "fees": (
            "opening zero; payout 7bps base /20bps stress; "
            "stress buy price +0.01 absolute"
        ),
        "latency": (
            "received decision book; subsequent book at +1..60s; delay +60..120s"
        ),
        "live_enabled": False,
        "shadow_only": True,
        "public_data_only": True,
    }
    write_json(args.output / "events.json", results)
    write_json(args.output / "summary.json", summary)
    print(
        json.dumps(
            {k: v for k, v in summary.items() if k not in {"sources", "scripts"}},
            default=str,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
