"""Bound end-of-expiry economics with explicit perfect foresight and no orders."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path
from typing import Any

from fetch_outcome_taker import EXPECTED, SOURCE, timestamp

from hyperbot2.research.artifacts import checked_input, file_sha256, write_json
from hyperbot2.research.expiry_bound import WinningOffer, oracle_allocation, parse_offer

D = Decimal
REPORT = Path("reports/expiry_bound_2026-09-07")
PREVIOUS = Path("data/outcome_taker_2026-09-07")


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
        raise ValueError("registered protocol changed")
    markets = read(PREVIOUS / "extract_verified/markets.json")
    manifest = read(PREVIOUS / "labels/manifest.json")
    labels = {}
    for record in manifest["requests"]:
        path = Path(record["path"])
        response = read(path)
        if sources[str(path)] != record["sha256"]:
            raise ValueError("label checksum mismatch")
        labels[response["request"]["outcome"]] = response["response"]
    for outcome in (111, 762):
        response = read(PREVIOUS / f"native-probe-{outcome}.json")
        labels[outcome] = response["response"]
    for market, meta in markets.items():
        label = labels[meta["outcome"]]
        spec = label["spec"]
        fields = dict(s.split(":", 1) for s in spec["description"].split("|"))
        parts = market.split("_")
        if (
            spec["outcome"] != meta["outcome"]
            or fields["underlying"] != meta["underlying"]
            or D(fields["targetPrice"]) != D(meta["strike"])
            or fields["expiry"] != parts[3] + "-" + parts[4]
            or [s["name"] for s in spec["sideSpecs"]] != ["Yes", "No"]
            or spec["quoteToken"] != "USDC"
        ):
            raise ValueError("official contract differs from book mapping")
        fraction = D(label["settleFraction"])
        if fraction not in (D(0), D(1)):
            raise ValueError("non-binary payout cannot use this bound")
        meta["winning_side"] = "YES" if fraction else "NO"
    sources[str(SOURCE)] = file_sha256(SOURCE)
    if sources[str(SOURCE)] != EXPECTED:
        raise ValueError("legacy source changed")
    fixed, best = {}, {}
    counts: Counter[str] = Counter()
    for number, line in enumerate(SOURCE.open(), 1):
        row = json.loads(line)
        market = row.get("market_id")
        if market not in markets:
            continue
        meta = markets[market]
        if row["side_name"].upper() != meta["winning_side"]:
            continue
        expiry = meta["expiry_ms"]
        received, event = timestamp(row["ts_init"]), timestamp(row["ts_event"])
        point = expiry - 300_000
        selected = {
            "market": market,
            "event_ms": event,
            "received_ms": received,
            "source_line": number,
            "raw": row,
        }
        if point - 60_000 <= received <= point and (
            market not in fixed or fixed[market]["received_ms"] < received
        ):
            # Preserve empty latest observations instead of backfilling older asks.
            fixed[market] = selected
        if not expiry - 360_000 <= received <= expiry - 1000:
            continue
        counts["winning_side_window_observations"] += 1
        if not 0 <= received - event <= 60_000:
            counts["stale_window_observations"] += 1
            continue
        observed = parse_offer(row, market)
        if observed is None:
            counts["empty_or_invalid_window_ask"] += 1
            continue
        if market not in best or observed.ask < D(str(best[market]["raw"]["best_ask"])):
            best[market] = selected
    if file_sha256(SOURCE) != EXPECTED:
        raise ValueError("source changed while reading")
    fixed_offers, best_offers = {}, {}
    records = []
    for market, meta in sorted(markets.items()):
        point = meta["expiry_ms"] - 300_000
        a, b = fixed.get(market), best.get(market)
        status = "NO_FIXED_OBSERVATION"
        if a is not None:
            raw = a["raw"]
            if (
                not 0 <= point - a["event_ms"] <= 60_000
                or a["event_ms"] > a["received_ms"]
            ):
                status = "STALE_FIXED_OBSERVATION"
            elif parse_offer(raw, market) is None:
                status = "EMPTY_FIXED_WINNING_ASK"
            else:
                status = "FIXED_WINNING_ASK_AVAILABLE"
                fixed_offers[market] = WinningOffer(
                    market, D(str(raw["best_ask"])), D(str(raw["ask_size"]))
                )
        if b is not None:
            best_offers[market] = WinningOffer(
                market, D(str(b["raw"]["best_ask"])), D(str(b["raw"]["ask_size"]))
            )
        records.append(
            {
                "market": market,
                "meta": meta,
                "fixed_status": status,
                "fixed": a,
                "best_window": b,
            }
        )
        counts[status] += 1
    days = sorted({m["expiry_ms"] for m in markets.values()})
    envelope_days = D(days[-1] - days[0]) / 86_400_000 + 1
    summaries, daily = {}, []
    for name, offers, share in (
        ("fixed_full_depth", fixed_offers, D(1)),
        ("fixed_tenth_depth", fixed_offers, D("0.1")),
        ("window_unlimited_depth", best_offers, None),
    ):
        for fee in (D(0), D("0.0007")):
            key = name + ("_zero_fee" if fee == 0 else "_payout_7bps")
            total = D(0)
            max_allocation = D(0)
            for date in days:
                available = tuple(
                    o
                    for market, o in offers.items()
                    if markets[market]["expiry_ms"] == date
                )
                allocation = oracle_allocation(
                    available, capital=D(1000), payout_fee=fee, depth_fraction=share
                )
                total += D(str(allocation["oracle_gain_usd"]))
                max_allocation = max(
                    max_allocation,
                    *(D(str(a["oracle_gain"])) for a in allocation["allocations"]),
                    D(0),
                )
                daily.append({"scenario": key, "expiry_ms": date, **allocation})
            summaries[key] = {
                "oracle_gain_usd": total,
                "oracle_monthly_before_infra": total * 30 / envelope_days,
                "oracle_monthly_after_20_infra": total * 30 / envelope_days - 20,
                "best_single_allocation_gain_usd": max_allocation,
                "best_allocation_profit_fraction": max_allocation / total
                if total
                else None,
                "oracle_monthly_excluding_best_after_infra": (total - max_allocation)
                * 30
                / envelope_days
                - 20,
            }
    summary = {
        "run_id": "expiry-oracle-bound-20260907-v1",
        "protocol_sha256": protocol,
        "sources": sources,
        "source_rows": number,
        "markets": len(markets),
        "dates": len(days),
        "calendar_envelope_days": envelope_days,
        "start_expiry_ms": days[0],
        "end_expiry_ms": days[-1],
        "quality_counts": dict(counts),
        "markets_with_window_ask": len(best_offers),
        "scenarios": summaries,
        "decision": "BOUND_TOO_LOW"
        if summaries["window_unlimited_depth_zero_fee"]["oracle_monthly_after_20_infra"]
        < 150
        else "BOUND_CANNOT_REJECT_REAL_SIGNAL_UNPROVEN",
        "code_hashes": {
            str(p): file_sha256(p)
            for p in (
                Path(__file__),
                Path("scripts/fetch_outcome_taker.py"),
                Path("src/hyperbot2/research/expiry_bound.py"),
            )
        },
        "perfect_foresight": True,
        "live_enabled": False,
        "promotion_authorized": False,
        "limits": [
            "future winner deliberately known",
            "window bound selects best time retrospectively",
            "conditional on observed asks, missing periods not bounded",
            "fractional units and no minimum notional",
            "no latency, queue or fill proof",
            "not a strategy PnL",
        ],
    }
    write_json(args.output / "selected_books.json", records)
    write_json(args.output / "daily_bounds.json", daily)
    write_json(args.output / "summary.json", summary)
    print(
        json.dumps(
            {k: v for k, v in summary.items() if k not in {"sources", "code_hashes"}},
            default=str,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
