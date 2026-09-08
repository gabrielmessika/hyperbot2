"""Preregistered BTC/ETH hypothesis screen using existing hourly archives."""

from __future__ import annotations

import argparse
import json
import math
import random
import runpy
from dataclasses import asdict
from decimal import ROUND_DOWN, Decimal
from pathlib import Path

from hyperbot2.research.artifacts import checked_input, file_sha256, write_json
from hyperbot2.research.pairs import model_at

D = Decimal
HOUR, DAY = 3_600_000, 86_400_000
COINS = ("BTC", "ETH")
SCENARIOS = {
    "base": (D("0.00045"), D("0.0002"), 0),
    "cost_stress": (D("0.0009"), D("0.0005"), 0),
    "delay_stress": (D("0.00045"), D("0.0002"), 1),
    "zero_cost_control": (D(0), D(0), 0),
}


def pnl(quantities: dict, sides: dict, entries: dict, exits: dict) -> Decimal:
    return sum(
        (sides[c] * quantities[c] * (exits[c] - entries[c]) for c in COINS), D(0)
    )


def bootstrap_ratio(daily: list[tuple[float, int]]) -> dict:
    """Resample sums and event counts jointly; retain zero-event days."""
    rng = random.Random(20260907)
    estimates = []
    for _ in range(5000):
        sample = []
        while len(sample) < len(daily):
            start = rng.randrange(len(daily) - 7 + 1)
            sample.extend(daily[start : start + 7])
        sample = sample[: len(daily)]
        count = sum(n for _, n in sample)
        if count:
            estimates.append(sum(v for v, _ in sample) / count)
    estimates.sort()
    return {
        "replicates": len(estimates),
        "block_days": 7,
        "seed": 20260907,
        "lower_95": estimates[int(len(estimates) * 0.025)] if estimates else None,
        "upper_95": estimates[min(len(estimates) - 1, int(len(estimates) * 0.975))]
        if estimates
        else None,
    }


def features(candles: dict) -> tuple[list[dict], list[dict]]:
    logs = {c: [math.log(float(b.close)) for b in candles[c]] for c in COINS}
    rows, events = [], []
    next_signal = 720
    for i in range(720, len(logs["BTC"]) - 25):
        try:
            model = model_at(logs["BTC"], logs["ETH"], i)
        except ValueError:
            continue
        z = model.z(logs["BTC"][i], logs["ETH"][i])
        rows.append(
            {"index": i, "time": candles["BTC"][i].time, **asdict(model), "z": z}
        )
        if i < next_signal or not (2 <= abs(z) < 4 and 0.25 <= model.beta <= 4):
            continue
        event = {"index": i, "model": model, "z": z, "eth_side": -1 if z > 0 else 1}
        events.append(event)
        next_signal = i + 25
    return rows, events


def event_study(candles: dict, events: list[dict], start: int, end: int) -> dict:
    results = []
    for e in events:
        entry = e["index"] + 1
        model, side = e["model"], e["eth_side"]
        beta = D(str(model.beta))
        notionals = {"ETH": D(1) / (1 + beta), "BTC": beta / (1 + beta)}
        prices = {c: candles[c][entry].open for c in COINS}
        entry_z = model.z(
            math.log(float(prices["BTC"])), math.log(float(prices["ETH"]))
        )
        quantities = {c: notionals[c] / prices[c] for c in COINS}
        sides = {"ETH": side, "BTC": -side}
        row = {
            "signal_ms": candles["BTC"][e["index"]].time + HOUR,
            "entry_ms": candles["BTC"][entry].time,
            "signal_z": e["z"],
            "beta": model.beta,
            "eth_side": side,
            "horizons": {},
        }
        for horizon in (1, 6, 24):
            exits = {c: candles[c][entry + horizon].open for c in COINS}
            gross = pnl(quantities, sides, prices, exits)
            costs = D("0.00065") * (1 + sum(quantities[c] * exits[c] for c in COINS))
            future_z = model.z(
                math.log(float(exits["BTC"])), math.log(float(exits["ETH"]))
            )
            row["horizons"][str(horizon)] = {
                "gross_bps": gross * 10000,
                "net_bps_before_funding": (gross - costs) * 10000,
                "future_frozen_z": future_z,
                "absolute_gap_reduced": abs(future_z) < abs(entry_z),
            }
        results.append(row)
    summary = {}
    for horizon in (1, 6, 24):
        observations = [r["horizons"][str(horizon)] for r in results]
        daily = {day: [0.0, 0] for day in range(start // DAY, end // DAY)}
        for row in results:
            daily[row["entry_ms"] // DAY][0] += float(
                row["horizons"][str(horizon)]["net_bps_before_funding"]
            )
            daily[row["entry_ms"] // DAY][1] += 1
        summary[str(horizon)] = {
            "n": len(observations),
            "mean_gross_bps": sum((r["gross_bps"] for r in observations), D(0))
            / len(observations)
            if observations
            else None,
            "mean_net_bps_before_funding": sum(
                (r["net_bps_before_funding"] for r in observations), D(0)
            )
            / len(observations)
            if observations
            else None,
            "gap_reduction_fraction": sum(
                r["absolute_gap_reduced"] for r in observations
            )
            / len(observations)
            if observations
            else None,
            "positive_net_fraction": sum(
                r["net_bps_before_funding"] > 0 for r in observations
            )
            / len(observations)
            if observations
            else None,
            "bootstrap_net_mean_bps": bootstrap_ratio(list(daily.values())),
        }
    return {"events": results, "horizons": summary, "primary_horizon_hours": 6}


def simulate(
    candles: dict,
    funding: dict,
    events: list[dict],
    start: int,
    end: int,
    scenario: str,
    decimals: dict,
) -> dict:
    fee, slip, delay = SCENARIOS[scenario]
    scheduled = {e["index"] + 1 + delay: e for e in events}
    cash = peak = month_peak = D(1000)
    drawdown = D(0)
    position = None
    cycles, daily, skipped = [], {}, []
    blocked_day = None
    last_day = None
    day_open = cash
    hard_stop = False

    def close(prices: dict, at: int, reason: str) -> None:
        nonlocal cash, position
        p = position
        executions = {c: prices[c] * (1 - p["sides"][c] * slip) for c in COINS}
        gross = pnl(p["quantities"], p["sides"], p["entries"], executions)
        exit_fee = sum(p["quantities"][c] * executions[c] * fee for c in COINS)
        cash += gross - exit_fee
        cycles.append(
            {
                "opened_ms": p["opened"],
                "closed_ms": at,
                "reason": reason,
                "eth_side": p["sides"]["ETH"],
                "beta": p["model"].beta,
                "entry_z": p["z"],
                "quantities": p["quantities"],
                "entries": p["entries"],
                "exits": executions,
                "entry_gross_notional": p["notional"],
                "gross_pnl_after_slippage": gross,
                "fees": p["entry_fee"] + exit_fee,
                "funding_adverse": p["funding"],
                "funding_signed_proxy": p["signed_funding"],
                "net_pnl": gross - p["entry_fee"] - exit_fee - p["funding"],
            }
        )
        position = None

    for i, anchor in enumerate(candles["BTC"]):
        at = anchor.time
        if not start <= at < end:
            continue
        opening = {c: candles[c][i].open for c in COINS}
        closing = {c: candles[c][i].close for c in COINS}
        equity_open = cash + (
            pnl(position["quantities"], position["sides"], position["entries"], opening)
            if position
            else 0
        )
        if at // DAY != last_day:
            day_open, last_day = equity_open, at // DAY
        if position:
            adverse = (
                sum(
                    position["quantities"][c] * opening[c] * abs(funding[c][at])
                    for c in COINS
                )
                if scenario != "zero_cost_control"
                else D(0)
            )
            signed = (
                sum(
                    position["sides"][c]
                    * position["quantities"][c]
                    * opening[c]
                    * funding[c][at]
                    for c in COINS
                )
                if scenario != "zero_cost_control"
                else D(0)
            )
            cash -= adverse
            position["funding"] += adverse
            position["signed_funding"] += signed
            reason = position["exit_reason"] or (
                "time" if at - position["opened"] >= 24 * HOUR else None
            )
            if reason:
                close(opening, at, reason)
        event = scheduled.get(i)
        if event and position is None and not hard_stop and blocked_day != at // DAY:
            model, z, side = event["model"], event["z"], event["eth_side"]
            beta, sigma = D(str(model.beta)), D(str(model.sigma))
            eth_notional = min(
                D(50), D(50) / beta, D("2.5") / (sigma * (4 - D(str(abs(z)))))
            )
            if month_peak - equity_open >= 80:
                eth_notional /= 2
            notionals = {"ETH": eth_notional, "BTC": beta * eth_notional}
            sides = {"ETH": side, "BTC": -side}
            entries = {c: opening[c] * (1 + sides[c] * slip) for c in COINS}
            quantities = {
                c: (notionals[c] / entries[c]).quantize(
                    D(1).scaleb(-decimals[c]), rounding=ROUND_DOWN
                )
                for c in COINS
            }
            actual = {c: quantities[c] * entries[c] for c in COINS}
            if min(actual.values()) < 10:
                skipped.append({"at": at, "reason": "minimum_order"})
            else:
                entry_fee = sum(actual.values()) * fee
                cash -= entry_fee
                position = {
                    "model": model,
                    "z": z,
                    "sides": sides,
                    "entries": entries,
                    "quantities": quantities,
                    "opened": at,
                    "entry_fee": entry_fee,
                    "notional": sum(actual.values()),
                    "funding": D(0),
                    "signed_funding": D(0),
                    "exit_reason": None,
                }
        unrealized = (
            pnl(position["quantities"], position["sides"], position["entries"], closing)
            if position
            else D(0)
        )
        equity = cash + unrealized
        peak, month_peak = max(peak, equity), max(month_peak, equity)
        drawdown = max(drawdown, peak - equity)
        if position:
            znow = position["model"].z(
                math.log(float(closing["BTC"])), math.log(float(closing["ETH"]))
            )
            exit_fee_estimate = sum(
                position["quantities"][c] * closing[c] * fee for c in COINS
            )
            net_mark = (
                unrealized
                - position["entry_fee"]
                - position["funding"]
                - exit_fee_estimate
            )
            if abs(znow) >= 4 or net_mark <= D("-2.5"):
                position["exit_reason"] = "risk_at_hourly_close"
            elif abs(znow) <= 0.5 or znow * position["z"] <= 0:
                position["exit_reason"] = "convergence"
        if day_open - equity >= 15 or peak - equity >= 120:
            blocked_day = at // DAY
            hard_stop |= peak - equity >= 120
            if position:
                position["exit_reason"] = "portfolio_stop"
        if at + HOUR == end and position:
            close(closing, end, "fold_terminal")
            equity = cash
        drawdown = max(drawdown, peak - equity)
        daily[at // DAY] = equity
    if position is not None or abs(
        cash - 1000 - sum((c["net_pnl"] for c in cycles), D(0))
    ) > D("1e-20"):
        raise ValueError("pair accounting did not reconcile")
    gains = sum((max(c["net_pnl"], D(0)) for c in cycles), D(0))
    losses = -sum((min(c["net_pnl"], D(0)) for c in cycles), D(0))
    return {
        "scenario": scenario,
        "start_ms": start,
        "end_ms_exclusive": end,
        "cycles": cycles,
        "daily_equity": daily,
        "round_trips": len(cycles),
        "net_trading_usd": cash - 1000,
        "infrastructure_usd": D(20),
        "net_after_infra_usd": cash - 1020,
        "profit_factor": gains / losses if losses else None,
        "max_hourly_drawdown_usd": drawdown,
        "hard_stop": hard_stop,
        "skipped": skipped,
        "promotion_authorized": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    loader = runpy.run_path(str(Path(__file__).with_name("evaluate_alternatives.py")))[
        "load_history"
    ]
    candles, funding, start, end, provenance = loader(args.history)
    checked_input(args.metadata)
    meta = json.loads(args.metadata.read_text())["response"][0]["universe"]
    decimals = {m["name"]: m["szDecimals"] for m in meta if m["name"] in COINS}
    rows, events = features(candles)
    write_json(args.output / "features.json", rows)
    study = event_study(candles, events, start + 30 * DAY, end)
    write_json(args.output / "events.json", study)
    simulations = []
    summaries = {}
    for scenario in SCENARIOS:
        scenario_runs = []
        for block in range(1, 6):
            result = simulate(
                candles,
                funding,
                events,
                start + block * 30 * DAY,
                start + (block + 1) * 30 * DAY,
                scenario,
                decimals,
            )
            path = args.output / f"{scenario}-{block}.json"
            digest = write_json(path, result)
            simulations.append(
                {
                    k: v
                    for k, v in result.items()
                    if k not in ("cycles", "daily_equity", "skipped")
                }
                | {"block": block, "path": str(path), "sha256": digest}
            )
            scenario_runs.append(result)
        cycles = [c for r in scenario_runs for c in r["cycles"]]
        gains = sum((max(c["net_pnl"], D(0)) for c in cycles), D(0))
        losses = -sum((min(c["net_pnl"], D(0)) for c in cycles), D(0))
        daily_pnl = []
        for result in scenario_runs:
            previous = D(1000)
            for equity in result["daily_equity"].values():
                daily_pnl.append((float(equity - previous - D(20) / 30), 1))
                previous = equity
        summaries[scenario] = {
            "net_trading_usd": sum((r["net_trading_usd"] for r in scenario_runs), D(0)),
            "net_after_infra_usd": sum(
                (r["net_after_infra_usd"] for r in scenario_runs), D(0)
            ),
            "round_trips": len(cycles),
            "profit_factor": gains / losses if losses else None,
            "positive_blocks_after_infra": sum(
                r["net_after_infra_usd"] > 0 for r in scenario_runs
            ),
            "fees_usd": sum((c["fees"] for c in cycles), D(0)),
            "funding_adverse_usd": sum((c["funding_adverse"] for c in cycles), D(0)),
            "funding_signed_proxy_usd": sum(
                (c["funding_signed_proxy"] for c in cycles), D(0)
            ),
            "mean_daily_net_usd_bootstrap": bootstrap_ratio(daily_pnl),
        }
    base, primary = summaries["base"], study["horizons"]["6"]
    criteria = {
        "at_least_30_events": primary["n"] >= 30,
        "primary_net_lower_95_positive": (
            primary["bootstrap_net_mean_bps"]["lower_95"] or 0
        )
        > 0,
        "base_after_infra_positive": base["net_after_infra_usd"] > 0,
        "four_positive_blocks": base["positive_blocks_after_infra"] >= 4,
        "profit_factor_above_1_2": base["profit_factor"] is not None
        and base["profit_factor"] > D("1.2"),
    }
    write_json(
        args.output / "summary.json",
        {
            "run_id": "btc-eth-pairs-2026-09-07",
            "script_sha256": file_sha256(Path(__file__)),
            "feature_code_sha256": file_sha256(
                Path(__file__).resolve().parents[1] / "src/hyperbot2/research/pairs.py"
            ),
            "source_hashes": provenance,
            "metadata_sha256": file_sha256(args.metadata),
            "history_start_ms": start,
            "history_end_ms_exclusive": end,
            "feature_rows": len(rows),
            "event_study": study["horizons"],
            "simulations": simulations,
            "scenario_summaries": summaries,
            "criteria": criteria,
            "decision": "FRESH_VALIDATION_CANDIDATE"
            if all(criteria.values())
            else "HYPOTHESIS_NOT_CONFIRMED",
            "independent_holdout": False,
            "promotion_authorized": False,
            "limits": [
                "previously consulted history, exploratory only",
                "hourly OHLC cannot prove simultaneous fills or intrabar risk",
                "current size precision, historical precision not verified",
                "funding oracle approximated with hourly open",
                "fitted residual persistence is not a cointegration test",
                "no trading client or live configuration change",
            ],
        },
    )
    print(args.output / "summary.json")


if __name__ == "__main__":
    main()
