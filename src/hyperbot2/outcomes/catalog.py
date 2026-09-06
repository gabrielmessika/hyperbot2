"""Strict recurring metadata discovery separated from economic qualification."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from hyperbot2.outcomes.contracts import UNIVERSE, FeeSchedule, OutcomeDefinition


def discover_recurring(
    payload: dict[str, Any],
    *,
    observed_ms: int,
    attestations: dict[str, Any] | None = None,
) -> tuple[tuple[OutcomeDefinition, ...], tuple[str, ...]]:
    definitions: list[OutcomeDefinition] = []
    issues: list[str] = []
    seen: set[int] = set()
    for row in payload.get("outcomes", []):
        if row.get("name") != "Recurring":
            continue
        try:
            parts = str(row["description"]).split("|")
            fields = dict(x.split(":", 1) for x in parts)
            if len(fields) != len(parts):
                raise ValueError("duplicate descriptor key")
            if fields.get("class") != "priceBinary" or fields.get("period") != "1d":
                raise ValueError("unsupported recurring contract")
            if fields.get("underlying") not in UNIVERSE:
                raise ValueError("underlying outside universe")
            if [s["name"] for s in row["sideSpecs"]] != ["Yes", "No"]:
                raise ValueError("side ordering must be Yes/No")
            if row.get("quoteToken") != "USDC":
                raise ValueError("unsupported collateral")
            outcome_id = int(row["outcome"])
            if outcome_id in seen:
                raise ValueError("duplicate outcome id")
            expiry = int(
                datetime.strptime(fields["expiry"], "%Y%m%d-%H%M")
                .replace(tzinfo=UTC)
                .timestamp()
                * 1000
            )
            att = (attestations or {}).get(str(outcome_id), {})
            if att and not (
                int(att["observed_ms"]) <= observed_ms < int(att["valid_until_ms"])
            ):
                raise ValueError("attestation unavailable or expired")
            fees = None
            if att.get("fees"):
                f = att["fees"]
                fees = FeeSchedule(
                    Decimal(f["maker_close_rate"]),
                    Decimal(f["taker_close_rate"]),
                    Decimal(f["settlement_rate"]),
                    int(att["observed_ms"]),
                    int(att["valid_until_ms"]),
                    f["source_sha256"],
                )
            definitions.append(
                OutcomeDefinition(
                    outcome_id,
                    fields["underlying"],
                    Decimal(fields["targetPrice"]),
                    expiry,
                    observed_ms,
                    tick=Decimal(att["tick"]) if "tick" in att else None,
                    size_increment=Decimal(att["size_increment"])
                    if "size_increment" in att
                    else None,
                    fees=fees,
                    settlement_rule=att.get("settlement_rule"),
                    specification_sha256=att.get("specification_sha256"),
                    active=att.get("active") is True,
                    fee_scale=payload.get("feeScale"),
                    deployer_fee_scale=row.get("deployerFeeScale"),
                )
            )
            seen.add(outcome_id)
        except (KeyError, ValueError, TypeError, ArithmeticError) as exc:
            issues.append(f"outcome:{row.get('outcome', '?')}:{exc}")
    return tuple(sorted(definitions, key=lambda d: d.outcome_id)), tuple(issues)
