"""Independently reconcile native equity via a signed inventory cash ledger."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

from investigate_breakout_extension import DATA, START
from investigate_funding_normalization import END, OLD, ROOT, load
from investigate_funding_transfer import DATA as TRANSFER

from hyperbot2.research.artifacts import checked_input, file_sha256, write_json
from hyperbot2.research.binance_archives import load_archives
from hyperbot2.research.market_regime import join_panels
from hyperbot2.research.rotation import HOUR

D = Decimal


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--capital-diagnostic", action="store_true")
    args = parser.parse_args()
    checked_input(args.input / "summary.json")
    study = json.loads((args.input / "summary.json").read_text())
    if args.capital_diagnostic:
        coins = study["coins"]
    else:
        selection = Path("reports/funding_transfer_2026-09-07/selection.json")
        checked_input(selection)
        coins = json.loads(selection.read_text())["eligible"]
    folders = (
        [DATA / "history"]
        + [TRANSFER / "history" / f"batch-{b}" for b in range(2)]
        + [ROOT / "history", ROOT / "replication_history", OLD / "history"]
    )
    if args.capital_diagnostic and study["panel"] == "continuous_2024_2025":
        root = Path("data/volatility_long_2024_2026-09-07")
        left, left_payments, _ = load_archives(
            root / "archives",
            coins,
            year=2024,
            october_2024_rest=root / "october_api_audit",
        )
        selection = Path("reports/prior_transfer_2026-09-07/qualification.json")
        checked_input(selection)
        full = [
            r["coin"] for r in json.loads(selection.read_text())["selected_by_metadata"]
        ]
        right, right_payments, _ = load_archives(
            Path("data/prior_transfer_2026-09-07/archives"), full
        )
        right, right_payments = (
            {c: rows[c] for c in coins} for rows in (right, right_payments)
        )
        bars, payments = join_panels(left, left_payments, right, right_payments)
    elif args.capital_diagnostic and study["panel"] == "transfer_2024":
        root = Path("data/volatility_long_2024_2026-09-07")
        bars, payments, _ = load_archives(
            root / "archives",
            coins,
            year=2024,
            october_2024_rest=root / "october_api_audit",
        )
    elif args.capital_diagnostic and study["panel"] == "transfer_2025":
        selection = Path("reports/prior_transfer_2026-09-07/qualification.json")
        checked_input(selection)
        full = [
            r["coin"] for r in json.loads(selection.read_text())["selected_by_metadata"]
        ]
        bars, payments, _ = load_archives(
            Path("data/prior_transfer_2026-09-07/archives"), full
        )
        bars, payments = ({c: rows[c] for c in coins} for rows in (bars, payments))
    else:
        bars, payments, _, _ = load(folders, coins, START, END)
    start, end = bars[coins[0]][0].time, bars[coins[0]][-1].time + HOUR
    checked_input(OLD / "meta.json")
    decimals = {
        m["name"]: m["szDecimals"]
        for m in json.loads((OLD / "meta.json").read_text())["response"][0]["universe"]
        if m["name"] in coins
    }
    rates = {c: {at // HOUR * HOUR: r for at, r in payments[c].items()} for c in coins}
    results = []
    for row in study["results"]:
        path = args.input / row["artifact"]
        sha = checked_input(path)
        if sha != row["sha256"]:
            raise ValueError("study artifact identity differs")
        result = json.loads(path.read_text())
        s = result["summary"]
        fee = (
            D(0)
            if s["scenario"] == "zero_cost"
            else D("0.0009")
            if s["scenario"] == "cost_stress"
            else D("0.00045")
        )
        by_hour: dict[int, list[dict]] = defaultdict(list)
        for order in result["orders"]:
            if order["time_ms"] % HOUR != 60_000 or not start <= order["time_ms"] < end:
                raise ValueError("order outside execution grid")
            by_hour[order["time_ms"] // HOUR * HOUR].append(order)
        inventory = dict.fromkeys(coins, D(0))
        ledger = peak = D(1000)
        max_dd = D(0)
        halted = False
        total_fees = total_funding = D(0)
        for i, at in enumerate(range(start, end, HOUR)):
            prices = {c: bars[c][i].open for c in coins}
            value = ledger + sum((inventory[c] * prices[c] for c in coins), D(0))
            peak = max(peak, value)
            max_dd = max(max_dd, 1 - value / peak)
            halted |= max_dd >= D(s["drawdown_limit"])
            ledger -= D(s["monthly_infra"]) / 720
            charge = (
                sum(
                    (
                        prices[c]
                        * (
                            abs(inventory[c]) * abs(rates[c][at])
                            if s["scenario"] == "funding_adverse"
                            else inventory[c] * rates[c][at]
                        )
                        for c in coins
                    ),
                    D(0),
                )
                if s["scenario"] != "zero_cost"
                else D(0)
            )
            ledger -= charge
            total_funding += charge
            value = ledger + sum((inventory[c] * prices[c] for c in coins), D(0))
            peak = max(peak, value)
            max_dd = max(max_dd, 1 - value / peak)
            halted |= max_dd >= D(s["drawdown_limit"])
            for o in by_hour[at]:
                c, q, price = o["coin"], D(o["delta"]), D(o["price"])
                if q == 0 or abs(q) % (D(10) ** -decimals[c]) or abs(q) * price < 10:
                    raise ValueError("invalid order minimum/quantity")
                normalized = price.normalize().as_tuple()
                if price != price.to_integral_value() and (
                    len(normalized.digits) > 5
                    or -int(normalized.exponent) > 6 - decimals[c]
                ):
                    raise ValueError("invalid order price precision")
                old = inventory[c]
                if D(o["before"]) != old or D(o["after"]) != old + q:
                    raise ValueError("inventory transition differs")
                inventory[c] += q
                reducing = old * inventory[c] >= 0 and abs(inventory[c]) < abs(old)
                if halted and not reducing:
                    raise ValueError("risk-increasing fill after halt")
                paid = abs(q) * price * fee
                if paid != D(o["fee_usd"]):
                    raise ValueError("fee differs")
                total_fees += paid
                ledger -= q * price + paid
                value = ledger + sum((inventory[n] * prices[n] for n in coins), D(0))
                gross = sum((abs(inventory[n]) * prices[n] for n in coins), D(0))
                if not reducing and (
                    gross > D(s["gross_cap_at_entry"]) * value + D("1e-18")
                    or gross / 2 > value
                ):
                    raise ValueError("entry exceeds actual native capital")
                peak = max(peak, value)
                max_dd = max(max_dd, 1 - value / peak)
                halted |= max_dd >= D(s["drawdown_limit"])
            value = ledger + sum((inventory[c] * bars[c][i].close for c in coins), D(0))
            peak = max(peak, value)
            max_dd = max(max_dd, 1 - value / peak)
            halted |= max_dd >= D(s["drawdown_limit"])
            expected = result["curve"][i]
            if (
                expected["time_ms"] != at + HOUR
                or abs(value - D(expected["equity"])) > D("1e-18")
                or inventory
                != {c: D(v) for c, v in expected["native_quantities"].items()}
            ):
                raise ValueError("independent hourly inventory/equity differs")
        if (
            abs(max_dd - D(s["max_hourly_drawdown"])) > D("1e-18")
            or abs(total_funding - D(s["funding_cost_usd"])) > D("1e-18")
            or total_fees != D(s["fees_usd"])
        ):
            raise ValueError("risk or cost summary differs")
        results.append(
            {
                "source": str(path),
                "sha256": sha,
                "hours": len(result["curve"]),
                "orders": len(result["orders"]),
                "independent_equity_passed": True,
                "minimums_lots_ticks_passed": True,
                "entry_capital_and_halt_passed": True,
                "funding_and_fees_passed": True,
            }
        )
    write_json(
        args.output / "ledger_audit.json",
        {
            "results": results,
            "script_sha256": file_sha256(Path(__file__)),
            "network_data_calls": 0,
            "live_enabled": False,
            "promotion_authorized": False,
        },
    )
    print(f"{len(results)} portfolios independently reconciled")


if __name__ == "__main__":
    main()
