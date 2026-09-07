"""Read-only, non-atomic basket price screen; no executable arbitrage claim."""

from __future__ import annotations

import argparse
import json
import runpy
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from typing import Any

from hyperbot2.research.artifacts import checked_input, file_sha256, write_json

D = Decimal


def fields(description: str) -> dict[str, str]:
    return dict(part.split(":", 1) for part in description.split("|") if ":" in part)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    metadata_hash = checked_input(args.metadata)
    metadata = json.loads(args.metadata.read_text())["response"]
    args.output.mkdir(parents=True, exist_ok=False)
    client_class = runpy.run_path(
        str(Path(__file__).with_name("fetch_research_history.py"))
    )["PublicResearchClient"]
    client = client_class(args.output / "raw")
    candidates: list[dict[str, Any]] = []
    for question in metadata["questions"]:
        if (
            question["name"] == "Recurring"
            and "class:priceBucket" in question["description"]
        ):
            ids = [*question["namedOutcomes"], question["fallbackOutcome"]]
            if question["settledNamedOutcomes"]:
                continue
            candidates.append(
                {
                    "kind": "complete_yes_basket",
                    "question": question,
                    "coins": [f"#{i * 10}" for i in ids],
                }
            )
    groups: dict[str, list[tuple[Decimal, int]]] = defaultdict(list)
    for outcome in metadata["outcomes"]:
        if outcome["name"] != "template:binaryPrice":
            continue
        spec = fields(outcome["description"])
        if "threshold" not in spec:
            continue
        threshold = D(spec.pop("threshold"))
        key = json.dumps(
            {
                "spec": spec,
                "venue": outcome.get("venue"),
                "quote": outcome.get("quoteToken"),
            },
            sort_keys=True,
        )
        groups[key].append((threshold, outcome["outcome"]))
    for key, values in sorted(groups.items()):
        values.sort()
        for i, (low, low_id) in enumerate(values):
            for high, high_id in values[i + 1 :]:
                if low == high:
                    continue
                candidates.append(
                    {
                        "kind": "nested_binary_cover",
                        "spec": json.loads(key),
                        "thresholds": [low, high],
                        "coins": [f"#{low_id * 10}", f"#{high_id * 10 + 1}"],
                    }
                )
    coins = sorted({c for x in candidates for c in x["coins"]})
    if len(coins) > 46:
        raise ValueError("basket request budget exceeded before any book reads")
    books = {coin: client.info({"type": "l2Book", "coin": coin}) for coin in coins}
    rows = []
    for candidate in candidates:
        observed = [books[c] for c in candidate["coins"]]
        row = dict(candidate)
        if any(b is None or not b.get("levels", [[], []])[1] for b in observed):
            row["verdict"] = "MISSING_LEG_LIQUIDITY"
        else:
            asks = [D(b["levels"][1][0]["px"]) for b in observed]
            sizes = [D(b["levels"][1][0]["sz"]) for b in observed]
            row.update(
                {
                    "sum_best_asks": sum(asks),
                    "zero_fee_margin_per_bundle": 1 - sum(asks),
                    "max_exchange_timestamp_skew_ms": max(b["time"] for b in observed)
                    - min(b["time"] for b in observed),
                    "max_quantity_at_top_and_50_usd_per_leg": min(
                        min(sizes), *(D(50) / p for p in asks)
                    ),
                    "min_quantity_for_10_usd_each_leg": max(D(10) / p for p in asks),
                    "verdict": "PRICE_ANOMALY_TO_INVESTIGATE"
                    if sum(asks) < 1
                    else "NO_VISIBLE_BUY_BASKET_EDGE",
                }
            )
        rows.append(row)
    write_json(
        args.output / "summary.json",
        {
            "metadata_path": str(args.metadata),
            "metadata_sha256": metadata_hash,
            "script_sha256": file_sha256(Path(__file__)),
            "requests": client.records,
            "candidates": rows,
            "book_requests": len(coins),
            "verdict": "EXPLORATORY_ONLY",
            "promotion_authorized": False,
            "limits": [
                "sequential REST snapshots are not atomic",
                "fees set to zero",
                "payoff/settlement descriptions require independent qualification",
                "no queue or actual execution proof",
                "no short/split strategy tested",
            ],
        },
    )
    print(args.output / "summary.json")


if __name__ == "__main__":
    main()
