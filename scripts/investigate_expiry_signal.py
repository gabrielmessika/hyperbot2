"""Exploratory causal near-expiry benchmark using qualified archived references."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict, replace
from decimal import ROUND_CEILING, Decimal
from pathlib import Path
from typing import Any

from evaluate_alternatives import HOUR, load_history
from fetch_outcome_taker import EXPECTED, SOURCE, timestamp

from hyperbot2.research.artifacts import (
    checked_input,
    file_sha256,
    source_version,
    write_json,
)
from hyperbot2.research.expiry_bound import parse_offer
from hyperbot2.research.expiry_reference import okx_usdt_midpoint
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
REPORT = Path("reports/expiry_signal_2026-09-07")
PREVIOUS = Path("data/expiry_bound_2026-09-07")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    sources = {}

    def read(path: Path) -> Any:
        sources[str(path)] = checked_input(path)
        return json.loads(path.read_text())

    protocol = file_sha256(REPORT / "PROTOCOL.md")
    if read(REPORT / "registration.json")["protocol_sha256"] != protocol:
        raise ValueError("protocol changed")
    bound = read(PREVIOUS / "final/selected_books.json")
    bound_summary = read(PREVIOUS / "final/summary.json")
    for path, expected in bound_summary["sources"].items():
        if file_sha256(Path(path)) != expected:
            raise ValueError("bound source changed")
        sources[path] = expected
    markets = {r["market"]: r["meta"] for r in bound}
    references = {
        r["market"]: r
        for r in read(PREVIOUS / "reference_audit_final/selected_references.json")
    }
    selected = {}
    if file_sha256(SOURCE) != EXPECTED:
        raise ValueError("legacy source changed")
    for number, line in enumerate(SOURCE.open(), 1):
        raw = json.loads(line)
        market = raw.get("market_id")
        if market not in markets:
            continue
        side = raw["side_name"].upper()
        encoding = int(raw["coin"].lstrip("#"))
        if side not in {"YES", "NO"} or encoding != 10 * markets[market]["outcome"] + (
            side == "NO"
        ):
            raise ValueError("book identity mismatch")
        received = timestamp(raw["ts_init"])
        point = markets[market]["expiry_ms"] - 300_000
        for stage, low, high in (
            ("decision", -60_000, 0),
            ("execution", 1000, 60_000),
            ("delay", 60_000, 120_000),
        ):
            if not point + low <= received <= point + high:
                continue
            key = market, side, stage
            old = selected.get(key)
            if old and (
                (stage == "decision" and old["received_ms"] >= received)
                or (stage != "decision" and old["received_ms"] <= received)
            ):
                continue
            selected[key] = {
                "market": market,
                "side": side,
                "stage": stage,
                "received_ms": received,
                "event_ms": timestamp(raw["ts_event"]),
                "source_line": number,
                "raw": raw,
            }
    if file_sha256(SOURCE) != EXPECTED:
        raise ValueError("source changed during extraction")
    sources[str(SOURCE)] = EXPECTED

    def book(market: str, side: str, stage: str) -> TakerBook | None:
        row = selected.get((market, side, stage))
        offer = parse_offer(row["raw"], market) if row else None
        if row is None or offer is None:
            return None
        return TakerBook(row["event_ms"], row["received_ms"], offer.ask, offer.size)

    candles, _, _, _, hashes = load_history(Path("data/search_2026-09-06/history"))
    sources.update(hashes)
    indices = {
        coin: {c.time: i for i, c in enumerate(cs)} for coin, cs in candles.items()
    }
    model = DigitalOutcomeBenchmark()
    results = []
    for market, meta in sorted(markets.items()):
        item: dict[str, Any] = {
            "market": market,
            "underlying": meta["underlying"],
            "expiry_ms": meta["expiry_ms"],
        }
        results.append(item)
        coin, point = meta["underlying"], meta["expiry_ms"] - 300_000
        reference = references.get(market)
        midpoint = (
            okx_usdt_midpoint(reference, underlying=coin, decision_ms=point)
            if reference
            else None
        )
        if midpoint is None:
            item["status"] = "REFERENCE_UNQUALIFIED"
            continue
        index = indices[coin].get(point // HOUR * HOUR - HOUR)
        if index is None or index < 168:
            item["status"] = "VOLATILITY_HISTORY_MISSING"
            continue
        history = candles[coin][index - 168 : index + 1]
        if any(
            b.time - a.time != HOUR for a, b in zip(history, history[1:], strict=False)
        ):
            raise ValueError("hourly history gap")
        volatility = empirical_volatility(
            tuple(c.close for c in history), periods_per_year=8766
        )
        sample = OutcomeSample(
            market,
            point,
            meta["expiry_ms"],
            market,
            coin,
            midpoint,
            D(meta["strike"]),
            volatility,
            0,
            D(0),
            D(0),
            "unfitted",
            "5m",
        )
        probabilities = tuple(
            model.probability(
                replace(
                    sample,
                    spot=midpoint * factor,
                    realized_volatility_annualized=volatility * scale,
                )
            )
            for factor in (D("0.9985"), D("1.0015"))
            for scale in (D("0.75"), D(1), D("1.25"))
        )
        available = {
            side: b
            for side in ("YES", "NO")
            if (b := book(market, side, "decision")) is not None
        }
        item.update(
            {
                "reference_midpoint": midpoint,
                "volatility": volatility,
                "probabilities": probabilities,
                "books": {s: asdict(b) for s, b in available.items()},
            }
        )
        diagnostics = {}
        for side in ("YES", "NO"):
            observed = available.get(side)
            if observed is None or not observed.fresh(point):
                diagnostics[side] = {"status": "MISSING_STALE_OR_INVALID_BOOK"}
                continue
            if not D("0.15") <= observed.ask <= D("0.85"):
                diagnostics[side] = {"status": "OUTSIDE_PRICE_BAND"}
                continue
            ps = probabilities if side == "YES" else tuple(1 - p for p in probabilities)
            edge = max(D(0), min(ps) - D("0.03")) * D("0.998") - observed.ask
            quantity = (D(10) / observed.ask).to_integral_value(rounding=ROUND_CEILING)
            diagnostics[side] = {
                "status": "EDGE_TOO_SMALL" if edge < D("0.05") else "EDGE_PASS",
                "robust_edge": edge,
                "capacity_pass": quantity <= observed.ask_size * D("0.1")
                and quantity * observed.ask <= 11,
            }
        item["diagnostics"] = diagnostics
        intent = select_intent(point, probabilities, available)
        if intent is None:
            item["status"] = "NO_ELIGIBLE_INTENT"
            continue
        item["intent"] = asdict(intent)
        price = execution_price(intent, book(market, intent.side, "execution"))
        delay_price = execution_price(
            intent, book(market, intent.side, "delay"), delay=True
        )
        # Resolution is only used after causal selection and execution qualification.
        fraction = D(markets[market]["winning_side"] == "YES")
        item.update(
            {
                "price": price,
                "delay_price": delay_price,
                "fraction": fraction,
                "status": "EXPLORATORY_FILL"
                if price is not None
                else "EXECUTION_REJECTED",
                "pnl": settlement_pnl(intent, price, fraction)
                if price is not None
                else D(0),
                "stress_pnl": settlement_pnl(intent, price, fraction, stress=True)
                if price is not None
                else D(0),
                "delay_pnl": settlement_pnl(intent, delay_price, fraction)
                if delay_price is not None
                else D(0),
            }
        )
    dates = sorted({m["expiry_ms"] for m in markets.values()})
    if max(Counter(m["expiry_ms"] for m in markets.values()).values()) > 4:
        raise ValueError("registered universe allows at most four contracts per expiry")
    days = D(dates[-1] - dates[0]) / (24 * HOUR) + 1
    totals = {
        k: sum((r.get(k, D(0)) for r in results), D(0))
        for k in ("pnl", "stress_pnl", "delay_pnl")
    }
    summary = {
        "run_id": "expiry-signal-exploratory-20260907-v1",
        "protocol_sha256": protocol,
        "sources": sources,
        "code_version": source_version(Path.cwd())[0],
        "script_hashes": {
            str(p): file_sha256(p)
            for p in (
                Path(__file__),
                Path("scripts/evaluate_alternatives.py"),
                Path("scripts/fetch_outcome_taker.py"),
            )
        },
        "source_rows": number,
        "markets": len(markets),
        "calendar_days": days,
        "status_counts": dict(Counter(r["status"] for r in results)),
        "side_diagnostics": dict(
            Counter(
                d["status"] for r in results for d in r.get("diagnostics", {}).values()
            )
        ),
        "best_robust_edge_in_price_band": max(
            (
                d["robust_edge"]
                for r in results
                for d in r.get("diagnostics", {}).values()
                if "robust_edge" in d
            ),
            default=None,
        ),
        "totals": totals,
        "monthly_after_20_infra": {k: v * 30 / days - 20 for k, v in totals.items()},
        "labels_previously_seen": True,
        "native_reference_qualified": False,
        "decision": "EXPLORATORY_ONLY_NO_GO",
        "live_enabled": False,
    }
    write_json(
        args.output / "selected_books.json", [selected[k] for k in sorted(selected)]
    )
    write_json(args.output / "events.json", results)
    write_json(args.output / "summary.json", summary)
    print(
        json.dumps(
            {k: v for k, v in summary.items() if k not in {"sources", "script_hashes"}},
            default=str,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
