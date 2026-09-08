"""Registered paired price/funding screens on freely accessible native history."""

from __future__ import annotations

import argparse
import json
import runpy
from decimal import Decimal
from pathlib import Path
from statistics import median

from hyperbot2.research.artifacts import checked_input, file_sha256, write_json
from hyperbot2.research.cross_venue import paired_return
from hyperbot2.research.volume import VolumeBar

D = Decimal
HOUR, DAY = 3600000, 86400000
COINS = ("BTC", "ETH", "SOL")
SCENARIOS = {
    "base": (D("0.00045"), D("0.0005"), D("0.0002"), 0, "signed"),
    "cost_stress": (D("0.0009"), D("0.001"), D("0.0005"), 0, "signed"),
    "delay_stress": (D("0.00045"), D("0.0005"), D("0.0002"), 1, "signed"),
    "funding_adverse": (D("0.00045"), D("0.0005"), D("0.0002"), 0, "adverse"),
    "zero_cost": (D(0), D(0), D(0), 0, "zero"),
}


def load_binance(root: Path, start: int, end: int) -> tuple[dict, dict, dict]:
    checked_input(root / "manifest.json")
    manifest = json.loads((root / "manifest.json").read_text())
    if (manifest["start_ms"], manifest["end_ms_exclusive"]) != (start, end):
        raise ValueError("Binance requested coverage mismatch")
    candles, payments, sources = {c: [] for c in COINS}, {c: {} for c in COINS}, {}
    for record in manifest["requests"]:
        path = Path(record["path"])
        sources[str(path)] = checked_input(path)
        if sources[str(path)] != record["sha256"]:
            raise ValueError("Binance manifest hash mismatch")
        raw = json.loads(path.read_text())
        coin = raw["coin"]
        if raw["returncode"] or raw["query"]["symbol"] != coin + "USDC":
            raise ValueError("wrong currency or failed request")
        if raw["route"] == "klines":
            if raw["query"]["interval"] != "1h":
                raise ValueError("incorrect kline interval")
            for row in raw["response"]:
                if row[6] != row[0] + HOUR - 1:
                    raise ValueError("candle duration mismatch")
                candles[coin].append(VolumeBar(int(row[0]), *(D(x) for x in row[1:6])))
        elif raw["route"] == "fundingRate":
            for row in raw["response"]:
                time = int(row["fundingTime"])
                if (
                    row["symbol"] != coin + "USDC"
                    or time in payments[coin]
                    or not start <= time < end
                ):
                    raise ValueError("funding identity/duplicate/coverage error")
                rate, mark = D(row["fundingRate"]), D(row["markPrice"])
                if not rate.is_finite() or not mark.is_finite() or mark <= 0:
                    raise ValueError("invalid funding economics")
                payments[coin][time] = (rate, mark)
        else:
            raise ValueError("unrecognized public data route")
    for coin in COINS:
        candles[coin].sort(key=lambda b: b.time)
        if [b.time for b in candles[coin]] != list(range(start, end, HOUR)):
            raise ValueError("kline gap/duplicate")
        if sorted(t // (8 * HOUR) * (8 * HOUR) for t in payments[coin]) != list(
            range(start, end, 8 * HOUR)
        ) or any(t % (8 * HOUR) >= 1000 for t in payments[coin]):
            raise ValueError("funding does not match complete eight-hour schedule")
        payments[coin] = {t - start: pair for t, pair in payments[coin].items()}
    return candles, payments, sources


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    protocol = Path("reports/cross_venue_2026-09-07/PROTOCOL.md")
    checked_input(protocol.parent / "registration.json")
    if json.loads((protocol.parent / "registration.json").read_text())[
        "protocol_sha256"
    ] != file_sha256(protocol):
        raise ValueError("protocol changed")
    loader_path = Path(__file__).with_name("evaluate_alternatives.py")
    stats_path = Path(__file__).with_name("investigate_volume_shocks.py")
    stats = runpy.run_path(str(stats_path))
    hl, funding, start, end, sources = runpy.run_path(str(loader_path))["load_history"](
        Path("data/search_2026-09-06/history")
    )
    bn, payments, bn_sources = load_binance(
        Path("data/cross_venue_2026-09-07/binance"), start, end
    )
    sources.update(bn_sources)
    events = {"basis_reversion": [], "funding_differential": []}
    coverage = {}
    for coin in COINS:
        h_open, b_open = [b.open for b in hl[coin]], [b.open for b in bn[coin]]
        rates = [funding[coin][b.time] for b in hl[coin]]
        basis = [a.close / b.close - 1 for a, b in zip(hl[coin], bn[coin], strict=True)]
        next_allowed = dict.fromkeys(events, 0)
        deviations = []
        for i in range(168, len(basis) - 74):
            deviation = basis[i] - median(basis[i - 168 : i])
            deviations.append(abs(deviation) * 10000)
            # At the next open, only completed funding hours through i are known.
            diff = sum(rates[i - 23 : i + 1], D(0)) - sum(
                (
                    value[0]
                    for t, value in payments[coin].items()
                    if (i - 23) * HOUR <= t < (i + 1) * HOUR
                ),
                D(0),
            )
            candidates = {}
            if abs(deviation) >= D("0.003"):
                candidates["basis_reversion"] = (
                    -1 if deviation > 0 else 1,
                    (1, 6, 24),
                    25,
                )
            if abs(diff) >= D("0.001") and abs(deviation) < D("0.002"):
                candidates["funding_differential"] = (-1 if diff > 0 else 1, (72,), 73)
            for name, (side, horizons, spacing) in candidates.items():
                if i < next_allowed[name]:
                    continue
                next_allowed[name] = i + spacing
                entry = i + 1
                event = {
                    "coin": coin,
                    "side": side,
                    "signal_ms": hl[coin][i].time,
                    "entry_ms": hl[coin][entry].time,
                    "basis_deviation_bps": deviation * 10000,
                    "past_24h_funding_differential_bps": diff * 10000,
                    "returns": {},
                }
                for hold in horizons:
                    event["returns"][str(hold)] = {
                        s: paired_return(
                            h_open,
                            b_open,
                            rates,
                            payments[coin],
                            entry + delay,
                            hold,
                            side,
                            fh,
                            fb,
                            slip,
                            mode,
                        )
                        for s, (fh, fb, slip, delay, mode) in SCENARIOS.items()
                    }
                events[name].append(event)
        deviations.sort()
        coverage[coin] = {
            "candles_per_venue": len(basis),
            "binance_funding_payments": len(payments[coin]),
            "abs_basis_deviation_p99_bps": deviations[int(0.99 * len(deviations))],
            "abs_basis_deviation_max_bps": max(deviations),
        }
    results = {}
    for name, selected in events.items():
        selected.sort(key=lambda e: (e["entry_ms"], e["coin"]))
        primary = "6" if name == "basis_reversion" else "72"
        horizons = ("1", "6", "24") if primary == "6" else ("72",)
        summary = {
            h: {
                s: stats["summarize"](selected, h, s, start + 7 * DAY, end)
                for s in SCENARIOS
            }
            for h in horizons
        }
        ci = stats["interval"](selected, start + 7 * DAY, end, primary)
        base = summary[primary]["base"]
        criteria = {
            "all_cost_scenarios_positive": all(
                (summary[primary][s]["mean_net_bps"] or 0) > 0
                for s in SCENARIOS
                if s != "zero_cost"
            ),
            "profit_factor_above_1_2": (base["profit_factor"] or 0) > D("1.2"),
            "corrected_interval_lower_positive": ci is not None and ci["lower"] > 0,
            "four_positive_blocks": sum(v > 0 for v in base["blocks_30d_sum_bps"]) >= 4,
            "positive_without_best": (base["sum_without_best_bps"] or 0) > 0,
        }
        results[name] = {
            "primary_horizon_hours": int(primary),
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
            "run_id": "cross-venue-2026-09-07",
            "strategies": results,
            "coverage": coverage,
            "source_hashes": sources,
            "start_ms": start,
            "end_ms_exclusive": end,
            "protocol_sha256": file_sha256(protocol),
            "code_hashes": {
                str(p): file_sha256(p)
                for p in (
                    Path(__file__),
                    loader_path,
                    stats_path,
                    Path("src/hyperbot2/research/cross_venue.py"),
                    Path("src/hyperbot2/research/volume.py"),
                )
            },
            "data_cost_usd": 0,
            "independent_holdout": False,
            "promotion_authorized": False,
            "limits": [
                "asynchronous historical traded prices, no simultaneous fill proof",
                "HL funding valued with hourly open proxy, Binance with native mark",
                "eight-hour Binance schedule complete on this dataset only",
                "research fee assumptions, not account-qualified historical tiers",
                "no transfer costs, exchange counterparty, margin or ADL simulation",
                "equal quantities without lot rounding; bps of gross notional",
                "last 74 hours excluded for common eligibility across rules",
            ],
        },
    )
    print(args.output / "summary.json")


if __name__ == "__main__":
    main()
