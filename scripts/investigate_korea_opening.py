"""Fixed Korean premarket residual screen using already qualified native data."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from fetch_research_history import END, START
from investigate_funding_normalization import load

from hyperbot2.research.artifacts import (
    checked_input,
    file_sha256,
    source_version,
    write_json,
)
from hyperbot2.research.funding_normalization import event_return
from hyperbot2.research.hip3_fees import taker_fee
from hyperbot2.research.return_hedge import fit_return_hedge
from hyperbot2.research.rotation import HOUR

D = Decimal
REPORT = Path("reports/korea_opening_2026-09-07")
COINS = ("xyz:SKHX", "xyz:NVDA")
# Published 2026 full closures within the registered native period.
US_CLOSED = {date(2026, 4, 3), date(2026, 5, 25), date(2026, 6, 19), date(2026, 7, 3)}
KR_CLOSED = {
    date(2026, 5, 1),
    date(2026, 5, 5),
    date(2026, 5, 25),
    date(2026, 6, 3),
    date(2026, 7, 17),
    date(2026, 8, 17),
}
SPLIT = date(2026, 7, 16)
SCENARIOS = {
    "base": (D("0.00009"), D("0.0002"), 0, "signed"),
    "cost_stress": (D("0.0009"), D("0.0005"), 0, "signed"),
    "delay": (D("0.00009"), D("0.0002"), 1, "signed"),
    "funding_adverse": (D("0.00009"), D("0.0002"), 0, "adverse"),
    "zero_cost": (D(0), D(0), 0, "zero"),
}


def eligible(day: date) -> bool:
    return (
        day.weekday() < 4
        and day not in US_CLOSED
        and day + timedelta(days=1) not in KR_CLOSED
    )


def summarize(events: list[dict], days: int) -> dict:
    results = {}
    for scenario in SCENARIOS:
        filled = [e for e in events if e["returns"][scenario] is not None]
        values = [e["returns"][scenario]["basket"]["net_bps"] for e in filled]
        total = sum(values, D(0))
        gains = sum((max(v, D(0)) for v in values), D(0))
        losses = -sum((min(v, D(0)) for v in values), D(0))
        monthly: dict[str, Decimal] = {}
        for e in filled:
            month = e["date"][:7]
            monthly[month] = (
                monthly.get(month, D(0))
                + e["returns"][scenario]["basket"]["net_bps"] / 10
            )
        results[scenario] = {
            "events": len(values),
            "execution_data_exclusions": len(events) - len(values),
            "mean_net_bps": total / len(values) if values else None,
            "profit_factor": gains / losses if losses else None,
            "constant_1000_gross_notional_proxy_usd": total / 10,
            "monthly_proxy_before_infra_usd": total / 10 * 30 / days,
            "monthly_proxy_after_20_infra_usd": total / 10 * 30 / days - 20,
            "without_best_proxy_usd": (total - max(values)) / 10 if values else None,
            "worst_event_proxy_usd": min(values) / 10 if values else None,
            "months_proxy_usd": monthly,
        }
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    checked_input(REPORT / "registration.json")
    protocol = file_sha256(REPORT / "PROTOCOL.md")
    reg = json.loads((REPORT / "registration.json").read_text())
    if reg["protocol_sha256"] != protocol:
        raise ValueError("registered opening study changed")
    args.output.mkdir(parents=True, exist_ok=False)
    bars, payments, _, quality = load(
        [
            Path("data/korea_opening_2026-09-07/history"),
            Path("data/weekend_repricing_2026-09-07/history"),
        ],
        list(COINS),
        START,
        END,
    )
    meta_path = Path("data/weekend_repricing_2026-09-07/xyz_meta.json")
    quality["sources"][str(meta_path)] = checked_input(meta_path)
    meta = json.loads(meta_path.read_text())["response"][0]["universe"]
    fees = {
        row["name"]: taker_fee(
            deployer_fee_scale=D(row["deployerFeeScale"]),
            growth_mode=row.get("growthMode"),
        )
        for row in meta
        if row["name"] in COINS
    }
    if fees != dict.fromkeys(COINS, D("0.00009")):
        raise ValueError("registered native fee assumptions changed")
    opens = {coin: [b.open for b in rows] for coin, rows in bars.items()}
    observations, events, decisions = [], [], []
    exclusions: Counter[str] = Counter()
    for day_offset in range(180):
        day = datetime.fromtimestamp(START / 1000, UTC).date() + timedelta(
            days=day_offset
        )
        if not eligible(day):
            exclusions["calendar"] += 1
            continue
        i = day_offset * 24 + 22
        if i + 4 >= len(bars[COINS[0]]):
            exclusions["terminal"] += 1
            continue
        if any(b.volume == 0 for c in COINS for b in bars[c][i - 11 : i]):
            exclusions["signal_zero_volume"] += 1
            continue
        y, x = ((bars[c][i - 1].close / bars[c][i - 11].open).ln() for c in COINS)
        previous = observations[-20:]
        model = (
            fit_return_hedge([r[0] for r in previous], [r[1] for r in previous])
            if len(previous) == 20
            else None
        )
        # Append only after fitting, so today's return cannot train its own model.
        observations.append((y, x))
        if model is None:
            exclusions["warmup_or_degenerate"] += 1
            continue
        residual = y - model.alpha - model.beta * x
        z = residual / model.sigma
        valid_model = (
            D("0.25") <= model.beta <= 4
            and model.correlation >= D("0.3")
            and model.sigma >= D("0.003")
        )
        signal = valid_model and 2 <= abs(z) < 6 and abs(residual) >= D("0.01")
        decisions.append(
            {
                "date": day.isoformat(),
                "model": asdict(model),
                "residual": residual,
                "z": z,
                "signal": signal,
            }
        )
        if not signal:
            exclusions["model_or_threshold"] += 1
            continue
        side = -1 if residual > 0 else 1
        weights = (1 / (1 + model.beta), model.beta / (1 + model.beta))
        returns = {}
        for scenario, (fee, slip, delay, funding) in SCENARIOS.items():
            entry = i + delay
            if any(b.volume == 0 for c in COINS for b in bars[c][entry : entry + 4]):
                returns[scenario] = None
                continue
            legs = {
                c: event_return(
                    opens[c],
                    START,
                    payments[c],
                    entry,
                    3,
                    side if k == 0 else -side,
                    fee,
                    slip,
                    funding,
                )
                for k, c in enumerate(COINS)
            }
            returns[scenario] = {
                "legs": legs,
                "basket": {
                    key: sum(
                        (weights[k] * legs[c][key] for k, c in enumerate(COINS)), D(0)
                    )
                    for key in legs[COINS[0]]
                },
            }
        events.append(
            {
                "date": day.isoformat(),
                "entry_ms": START + i * HOUR + 60_000,
                "side": side,
                "beta": model.beta,
                "weights": weights,
                "residual": residual,
                "z": z,
                "returns": returns,
            }
        )
    results = summarize(events, 180)
    passed = bool(events) and all(
        results[s]["constant_1000_gross_notional_proxy_usd"] > 0
        and results[s]["execution_data_exclusions"] == 0
        for s in SCENARIOS
        if s != "zero_cost"
    )
    write_json(args.output / "quality.json", quality)
    write_json(args.output / "events.json", events)
    write_json(args.output / "decisions.json", decisions)
    write_json(
        args.output / "summary.json",
        {
            "run_id": "korea-opening-20260907-v1",
            "protocol_sha256": protocol,
            "code_version": source_version(Path.cwd())[0],
            "script_sha256": file_sha256(Path(__file__)),
            "scenarios": results,
            "exclusions": dict(exclusions),
            "signals": len(events),
            "older": summarize(
                [e for e in events if date.fromisoformat(e["date"]) < SPLIT], 128
            ),
            "recent": summarize(
                [e for e in events if date.fromisoformat(e["date"]) >= SPLIT], 52
            ),
            "decision": "POSITIVE_EVENT_SCREEN_UNQUALIFIED"
            if passed
            else "HYPOTHESIS_NOT_CONFIRMED",
            "live_enabled": False,
            "promotion_authorized": False,
            "portfolio_drawdown_qualified": False,
            "new_network_calls": 0,
        },
    )
    print("signals", len(events), "passed", passed, flush=True)
    for scenario, result in results.items():
        print(
            scenario,
            result["mean_net_bps"],
            result["constant_1000_gross_notional_proxy_usd"],
            flush=True,
        )


if __name__ == "__main__":
    main()
