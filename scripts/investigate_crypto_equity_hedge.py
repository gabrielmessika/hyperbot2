"""Registered crypto-equity residual screen, entirely offline and non-executable."""

from __future__ import annotations

import argparse
import importlib.util
import json
import random
from collections import Counter
from dataclasses import asdict
from datetime import UTC, date, datetime, time, timedelta
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
from hyperbot2.research.equity_weekend import HOLIDAYS, NY
from hyperbot2.research.hip3_fees import taker_fee
from hyperbot2.research.return_hedge import fit_return_hedge, hedged_return
from hyperbot2.research.rotation import HOUR

D = Decimal
COINS = ("xyz:COIN", "xyz:MSTR")
REPORT = Path("reports/crypto_equity_hedge_2026-09-07")
SPLIT = date(2026, 7, 1)
SCENARIOS = ("base", "cost_stress", "delay", "funding_adverse", "zero_cost")


def session(day: date) -> bool:
    return day.weekday() < 5 and day not in HOLIDAYS


def instant(day: date, hour: int) -> int:
    return int(datetime.combine(day, time(hour), NY).timestamp() * 1000)


def equities() -> tuple:
    # Reuse the already verified native loader with an isolated universe, like
    # the existing weekend replication adapter. No legacy runtime dependency.
    path = Path("scripts/investigate_weekend_repricing.py")
    spec = importlib.util.spec_from_file_location("crypto_equity_native_history", path)
    if spec is None or spec.loader is None:
        raise ValueError("native loader unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.COINS = COINS
    return module.load(Path("data/weekend_repricing_2026-09-07/replication_history"))


def interval(events: list[dict], start: int, end: int) -> list[float] | None:
    if not events:
        return None
    first = datetime.fromtimestamp(start / 1000, UTC).date()
    monday = first - timedelta(days=first.weekday())
    last = datetime.fromtimestamp((end - 1) / 1000, UTC).date()
    weeks: list[list[float]] = [[] for _ in range((last - monday).days // 7 + 1)]
    for e in events:
        weeks[(date.fromisoformat(e["date"]) - monday).days // 7].append(
            float(e["returns"]["base"]["basket"]["net_bps"])
        )
    rng, draws = random.Random(20260907), []
    for _ in range(10_000):
        sampled = []
        while len(sampled) < len(weeks):
            i = rng.randrange(len(weeks) - 2)
            sampled.extend(weeks[i : i + 3])
        values = [v for w in sampled[: len(weeks)] for v in w]
        if values:
            draws.append(sum(values) / len(values))
    if len(draws) < 9500:
        return None
    draws.sort()
    return [draws[int(len(draws) * 0.0125)], draws[int(len(draws) * 0.9875)]]


def describe(events: list[dict], start: int, end: int) -> dict:
    days = D(end - start) / (24 * HOUR)
    result = {}
    for scenario in SCENARIOS:
        filled = [e for e in events if e["returns"][scenario] is not None]
        values = [e["returns"][scenario]["basket"]["net_bps"] for e in filled]
        total = sum(values, D(0))
        gains = sum((max(D(0), v) for v in values), D(0))
        losses = -sum((min(D(0), v) for v in values), D(0))
        realized, peak, drawdown = D(0), D(0), D(0)
        for value in values:
            realized += value / 10  # 1,000 USD total notional.
            peak = max(peak, realized)
            drawdown = max(drawdown, peak - realized)
        result[scenario] = {
            "fills": len(values),
            "rejected": len(events) - len(values),
            "mean_net_bps": total / len(values) if values else None,
            "profit_factor": gains / losses if losses else None,
            "constant_notional_proxy_usd": total / 10,
            "monthly_after_20_infra": total / 10 * 30 / days - 20,
            "realized_only_drawdown_usd": drawdown,
            "worst_trade_usd": min(values) / 10 if values else None,
            "without_best_proxy_usd": (total - max(values)) / 10 if values else None,
        }
    central = [e for e in events if e["returns"]["base"] is not None]
    return {
        "signals": len(events),
        "calendar_days": days,
        "scenarios": result,
        "bootstrap_97_5_mean_bps": interval(central, start, end),
        "by_asset": {
            coin: {
                "fills": sum(e["coin"] == coin for e in central),
                "proxy_usd": sum(
                    (
                        e["returns"]["base"]["basket"]["net_bps"] / 10
                        for e in central
                        if e["coin"] == coin
                    ),
                    D(0),
                ),
            }
            for coin in COINS
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    checked_input(REPORT / "registration.json")
    protocol = file_sha256(REPORT / "PROTOCOL.md")
    if (
        json.loads((REPORT / "registration.json").read_text())["protocol_sha256"]
        != protocol
    ):
        raise ValueError("registered protocol changed")
    cs, fs, a, b, sources = equities()
    meta_path = Path("data/weekend_repricing_2026-09-07/xyz_meta.json")
    sources[str(meta_path)] = checked_input(meta_path)
    meta = json.loads(meta_path.read_text())["response"][0]["universe"]
    asset_fees = {
        r["name"]: taker_fee(
            deployer_fee_scale=D(r["deployerFeeScale"]),
            growth_mode=r.get("growthMode"),
        )
        for r in meta
        if r["name"] in COINS
    }
    if asset_fees != {"xyz:COIN": D("0.00009"), "xyz:MSTR": D("0.0009")}:
        raise ValueError("metadata fees differ from registered fee scenario")
    btc, btc_funding, c, d, hashes = load_history(
        Path("data/search_2026-09-06/history")
    )
    sources.update(hashes)
    start, end = max(a, c), min(b, d)
    cs["BTC"], fs["BTC"] = btc["BTC"], btc_funding["BTC"]
    rows = {
        coin: {bar.time: bar for bar in bars if start <= bar.time < end}
        for coin, bars in cs.items()
    }
    times = list(range(start, end, HOUR))
    for coin in (*COINS, "BTC"):
        if sorted(rows[coin]) != times or any(t not in fs[coin] for t in times):
            raise ValueError("shared native time series gap")
    opens = {coin: [rows[coin][t].open for t in times] for coin in rows}
    rates = {coin: [fs[coin][t] for t in times] for coin in rows}
    observations: dict[str, list[dict]] = {coin: [] for coin in COINS}
    decisions = []
    events: dict[str, list[dict]] = {"fade": [], "continuation": []}
    day = datetime.fromtimestamp(start / 1000, UTC).date()
    last = datetime.fromtimestamp((end - 1) / 1000, UTC).date()
    while day <= last:
        if not session(day):
            day += timedelta(days=1)
            continue
        begin, point, finish = (
            instant(day, 10),
            instant(day, 14),
            instant(day + timedelta(days=1), 14),
        )
        session_times = list(range(begin, point, HOUR))
        if any(t not in rows["BTC"] for t in session_times):
            day += timedelta(days=1)
            continue
        x = (rows["BTC"][point - HOUR].close / rows["BTC"][begin].open).ln()
        eligible = (
            day.weekday() < 4
            and session(day + timedelta(days=1))
            and finish + HOUR < end
        )
        candidates = []
        for coin in COINS:
            valid = all(rows[coin][t].volume > 0 for t in session_times)
            y = (rows[coin][point - HOUR].close / rows[coin][begin].open).ln()
            prior = observations[coin][-20:]
            item: dict[str, Any] = {
                "date": day.isoformat(),
                "coin": coin,
                "decision_ms": point,
                "eligible_calendar": eligible,
                "x": x,
                "y": y,
            }
            if not valid or len(prior) < 20 or not all(r["valid"] for r in prior):
                item["status"] = "INVALID_SESSION_OR_WARMUP"
            else:
                model = fit_return_hedge(
                    [r["y"] for r in prior], [r["x"] for r in prior]
                )
                if (
                    model is None
                    or not D("0.25") <= model.beta <= 4
                    or model.correlation < D("0.5")
                    or model.sigma < D("0.001")
                ):
                    item["status"] = "HEDGE_MODEL_REJECTED"
                else:
                    z = model.score(y, x)
                    item.update(
                        {
                            "model": asdict(model),
                            "z": z,
                            "status": "SIGNAL"
                            if abs(z) >= 2 and eligible
                            else "NO_SIGNAL",
                        }
                    )
                    if item["status"] == "SIGNAL":
                        candidates.append(item)
            observations[coin].append(
                {"date": day.isoformat(), "x": x, "y": y, "valid": valid}
            )
            decisions.append(item)
        if candidates:
            chosen = sorted(candidates, key=lambda r: (-abs(r["z"]), r["coin"]))[0]
            coin, beta = chosen["coin"], chosen["model"]["beta"]
            for direction in events:
                side = -1 if chosen["z"] > 0 else 1
                if direction == "continuation":
                    side = -side
                event = {
                    **chosen,
                    "entry_ms": point,
                    "exit_ms": finish,
                    "side": side,
                    "returns": {},
                }
                for scenario in SCENARIOS:
                    lag = HOUR if scenario == "delay" else 0
                    entry, exit_at = point + lag, finish + lag
                    if rows[coin][entry].volume <= 0 or rows[coin][exit_at].volume <= 0:
                        event["returns"][scenario] = None
                        continue
                    multiplier = 2 if scenario == "cost_stress" else 1
                    asset_fee = asset_fees[coin]
                    hedge_fee = D("0.00045")
                    asset_slip = (
                        D("0.0005") if scenario == "cost_stress" else D("0.0002")
                    )
                    hedge_slip = (
                        D("0.0003") if scenario == "cost_stress" else D("0.0001")
                    )
                    funding_mode = (
                        "adverse" if scenario == "funding_adverse" else "signed"
                    )
                    if scenario == "zero_cost":
                        asset_fee = hedge_fee = asset_slip = hedge_slip = D(0)
                        funding_mode = "zero"
                    event["returns"][scenario] = hedged_return(
                        opens[coin],
                        opens["BTC"],
                        rates[coin],
                        rates["BTC"],
                        index=(entry - start) // HOUR,
                        horizon=(exit_at - entry) // HOUR,
                        side=side,
                        beta=beta,
                        asset_fee=asset_fee * multiplier,
                        hedge_fee=hedge_fee * multiplier,
                        asset_slip=asset_slip,
                        hedge_slip=hedge_slip,
                        funding_mode=funding_mode,
                    )
                events[direction].append(event)
        day += timedelta(days=1)
    split = int(datetime.combine(SPLIT, time(), UTC).timestamp() * 1000)
    summaries = {}
    for direction, es in events.items():
        all_stats = describe(es, start, end)
        old = describe([e for e in es if e["entry_ms"] < split], start, split)
        recent = describe([e for e in es if e["entry_ms"] >= split], split, end)
        ci = all_stats["bootstrap_97_5_mean_bps"]
        base = all_stats["scenarios"]["base"]
        gates = {
            "20_dates_each_segment": all(
                s["scenarios"]["base"]["fills"] >= 20 for s in (old, recent)
            ),
            "all_paid_scenarios_positive_each_segment": all(
                s["scenarios"][k]["constant_notional_proxy_usd"] > 0
                for s in (old, recent)
                for k in SCENARIOS
                if k != "zero_cost"
            ),
            "bootstrap_lower_positive": ci is not None and ci[0] > 0,
            "profit_factor_ge_1_2": base["profit_factor"] is not None
            and base["profit_factor"] >= D("1.2"),
            "monthly_research_filter_ge_30": base["monthly_after_20_infra"] >= 30,
        }
        summaries[direction] = {
            "all": all_stats,
            "old": old,
            "recent": recent,
            "gates": gates,
            "decision": "RESEARCH_CANDIDATE_RISK_UNQUALIFIED"
            if all(gates.values())
            else "HYPOTHESIS_NOT_CONFIRMED",
        }
    summary = {
        "run_id": "crypto-equity-return-hedge-20260907-v1",
        "protocol_sha256": protocol,
        "sources": sources,
        "code_version": source_version(Path.cwd())[0],
        "scripts": {
            str(p): file_sha256(p)
            for p in (
                Path(__file__),
                Path("scripts/evaluate_alternatives.py"),
                Path("scripts/investigate_weekend_repricing.py"),
            )
        },
        "start_ms": start,
        "end_ms_exclusive": end,
        "decision_counts": dict(Counter(r["status"] for r in decisions)),
        "results": summaries,
        "live_enabled": False,
        "promotion_authorized": False,
        "limitations": [
            "prior exploration of these periods",
            "fractional unverified fills",
            "no depth, min-size, or liquidation qualification",
            "constant notional proxy without stop execution",
            "fee timeline incomplete",
        ],
    }
    write_json(args.output / "decisions.json", decisions)
    for direction, es in events.items():
        write_json(args.output / f"{direction}-events.json", es)
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
