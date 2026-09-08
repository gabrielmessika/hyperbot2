"""Descriptive market and same-asset controls; never a new validation gate."""

from __future__ import annotations

import argparse
import json
from decimal import Decimal
from pathlib import Path

from investigate_funding_normalization import END, OLD, ROOT, START, load, registered

from hyperbot2.research.artifacts import checked_input, file_sha256, write_json
from hyperbot2.research.funding_normalization import event_return
from hyperbot2.research.rotation import HOUR

D = Decimal


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    protocol, coins = registered()
    event_sha = checked_input(args.events)
    events = json.loads(args.events.read_text())
    if any(e["coin"] not in coins or not START < e["entry_ms"] < END for e in events):
        raise ValueError("unexpected event cohort")
    bars, payments, _, quality = load(
        [OLD / "history", OLD / "cashcat_hedge", ROOT / "history"], coins, START, END
    )
    opens = {c: [b.open for b in rows] for c, rows in bars.items()}

    def net(c: str, i: int, h: int, side: int) -> Decimal:
        return event_return(
            opens[c],
            START,
            payments[c],
            i,
            h,
            side,
            D("0.00045"),
            D("0.0002"),
            "signed",
        )["net_bps"]

    controls = {}
    for horizon in (24, 72):
        rows = []
        asset_baselines = {}
        for c in coins:
            for side in (-1, 1):
                values = [
                    net(c, i, horizon, side) for i in range(12, len(opens[c]) - 73, 73)
                ]
                asset_baselines[c, side] = sum(values, D(0)) / len(values)
        for e in events:
            c, side = e["coin"], e["side"]
            i = (e["entry_ms"] - START - 60_000) // HOUR
            actual = net(c, i, horizon, side)
            if actual != D(e["returns"][str(horizon)]["base"]["net_bps"]):
                raise ValueError("event accounting mismatch")
            market = sum(
                (net(other, i, horizon, side) for other in coins if other != c), D(0)
            ) / (len(coins) - 1)
            rows.append(
                {
                    "coin": c,
                    "entry_ms": e["entry_ms"],
                    "side": side,
                    "actual_net_bps": actual,
                    "same_time_other_assets_mean_bps": market,
                    "excess_same_time_bps": actual - market,
                    "same_asset_fixed_grid_mean_bps": asset_baselines[c, side],
                    "excess_same_asset_bps": actual - asset_baselines[c, side],
                }
            )
        fields = [k for k in rows[0] if k.endswith("bps")]
        controls[str(horizon)] = {
            "events": len(rows),
            "means_bps": {
                k: sum((r[k] for r in rows), D(0)) / len(rows) for k in fields
            },
            "without_cashcat": {
                "events": sum(r["coin"] != "CASHCAT" for r in rows),
                "means_bps": {
                    k: sum((r[k] for r in rows if r["coin"] != "CASHCAT"), D(0))
                    / sum(r["coin"] != "CASHCAT" for r in rows)
                    for k in fields
                },
            },
            "rows": rows,
        }
    write_json(
        args.output / "controls.json",
        {
            "protocol_sha256": protocol,
            "event_sha256": event_sha,
            "script_sha256": file_sha256(Path(__file__)),
            "sources": quality["sources"],
            "controls": controls,
            "promotion_authorized": False,
            "limits": [
                "post-result descriptive audit, not a registered strategy",
                "market baseline ignores beta and is not a hedge portfolio",
                "fixed-grid phase chosen arbitrarily; not a randomized test",
                "removing CASHCAT measures concentration, not a new selected universe",
            ],
        },
    )


if __name__ == "__main__":
    main()
