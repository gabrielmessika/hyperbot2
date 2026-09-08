"""Compare archived liquidation rows with captured, public native fills offline."""

from __future__ import annotations

import argparse
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

from hyperbot2.research.artifacts import checked_input, file_sha256, write_json
from hyperbot2.research.liquidations import timestamp


def compare(archived: dict, envelope: dict) -> dict:
    query, response = envelope["request"], envelope["response"]
    if (
        envelope["http_status"] != "200"
        or query.get("type") != "userFillsByTime"
        or query.get("user") != archived["liquidated_user"]
        or not isinstance(response, list)
    ):
        raise ValueError("native response identity mismatch")
    matches = [r for r in response if r.get("tid") == archived["trade_id"]]
    if len(matches) != 1:
        return {"verified": False, "reason": "missing_or_duplicate_native_trade"}
    native = matches[0]
    liquidation = native.get("liquidation") or {}
    checks = {
        "coin": native.get("coin") == archived["coin"],
        "time": native.get("time") == timestamp(archived["timestamp"]),
        "transaction": native.get("hash") == archived["tx_hash"],
        "side": native.get("side") == archived["side"],
        "direction": native.get("dir") == archived["direction"],
        "forced_close_owner": liquidation.get("liquidatedUser")
        == archived["liquidated_user"],
        "method": liquidation.get("method") in ("market", "backstop"),
    }
    for source_key, native_value in (
        ("price", native.get("px")),
        ("size", native.get("sz")),
        ("mark_price", liquidation.get("markPx")),
        ("closed_pnl", native.get("closedPnl")),
    ):
        try:
            a, b = Decimal(str(archived[source_key])), Decimal(str(native_value))
            checks[source_key] = a.is_finite() and b.is_finite() and a == b
        except InvalidOperation:
            checks[source_key] = False
    return {
        "verified": all(checks.values()),
        "checks": checks,
        "method": liquidation.get("method"),
        "native_response_rows": len(response),
        "liquidator_identity_validated": False,
        "coverage_validated": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    inputs, rows = {}, []
    original = Path("data/liquidations_2026-09-07")
    for folder in ("event_raw", "event_raw_continued"):
        manifest = original / folder / "manifest.json"
        inputs[str(manifest)] = checked_input(manifest)
        for request in json.loads(manifest.read_text())["requests"]:
            p = Path(request["path"])
            inputs[str(p)] = checked_input(p)
            if inputs[str(p)] != request["sha256"]:
                raise ValueError("archive manifest mismatch")
            rows.extend(json.loads(p.read_text())["data"])
    root = Path("data/liquidation_history_2026-09-07/native_checks")
    registration = root / "registration.json"
    inputs[str(registration)] = checked_input(registration)
    results = []
    for index in json.loads(registration.read_text())["indices"]:
        p = root / f"row-{index}.json"
        inputs[str(p)] = checked_input(p)
        results.append(
            {"source_index": index, **compare(rows[index], json.loads(p.read_text()))}
        )
    write_json(
        args.output,
        {
            "run_id": "native-liquidation-audit-2026-09-07",
            "script_sha256": file_sha256(Path(__file__)),
            "inputs": inputs,
            "results": results,
            "verified": sum(r["verified"] for r in results),
            "sample_size": len(results),
            "total_event_rows": len(rows),
            "coverage_validated": False,
            "promotion_authorized": False,
            "note": "Decimal comparisons supersede exploratory string-format equality",
        },
    )
    print(args.output)


if __name__ == "__main__":
    main()
