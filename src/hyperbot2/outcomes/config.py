"""Strict immutable research settings; live execution cannot be enabled."""

from __future__ import annotations

import hashlib
import tomllib
from dataclasses import dataclass, fields
from decimal import Decimal
from pathlib import Path

from hyperbot2.outcomes.contracts import positive


@dataclass(frozen=True, slots=True)
class OutcomeConfig:
    live_enabled: bool = False
    shadow_only: bool = True
    public_data_only: bool = True
    equity_usd: Decimal = Decimal("1000")
    order_usd: Decimal = Decimal("10")
    minimum_probability: Decimal = Decimal("0.15")
    maximum_probability: Decimal = Decimal("0.85")
    additional_margin: Decimal = Decimal("0")
    inventory_charge: Decimal = Decimal("0.001")
    stale_ms: int = 500
    placement_ms: int = 350
    cancel_ms: int = 350
    clock_uncertainty_ms: int = 50
    ttl_ms: int = 1000
    no_entry_before_expiry_ms: int = 1_800_000
    max_cpu_seconds: int = 86400
    max_wall_seconds: int = 86400
    max_memory_bytes: int = 4 * 1024**3
    max_output_bytes: int = 10 * 1024**3
    monthly_infrastructure_usd: Decimal = Decimal("20")
    research_action_budget: int = 10_000

    def __post_init__(self) -> None:
        if self.live_enabled is not False or self.shadow_only is not True:
            raise ValueError("only shadow research is supported")
        if self.public_data_only is not True:
            raise ValueError("only public data is supported")
        for value in (self.equity_usd, self.order_usd):
            positive(value, "capital/order")
        if self.equity_usd > 1000 or self.order_usd != 10:
            raise ValueError("v0 is capped at 1000 USD with 10 USD target orders")
        if (
            not Decimal("0.15")
            <= self.minimum_probability
            < self.maximum_probability
            <= Decimal("0.85")
        ):
            raise ValueError("probability bounds cannot be loosened")
        if self.additional_margin not in (
            Decimal(0),
            Decimal("0.005"),
            Decimal("0.010"),
        ):
            raise ValueError("only three preregistered margins are permitted")
        for value in (self.inventory_charge, self.monthly_infrastructure_usd):
            positive(value, "cost", zero=True)
        if self.stale_ms != 500 or self.no_entry_before_expiry_ms < 1_800_000:
            raise ValueError("freshness/expiry gates cannot be loosened")
        for name in (
            "stale_ms",
            "ttl_ms",
            "max_cpu_seconds",
            "max_wall_seconds",
            "max_memory_bytes",
            "max_output_bytes",
            "research_action_budget",
            "no_entry_before_expiry_ms",
        ):
            if type(getattr(self, name)) is not int or getattr(self, name) <= 0:
                raise ValueError(f"invalid {name}")
        for name in ("placement_ms", "cancel_ms", "clock_uncertainty_ms"):
            if type(getattr(self, name)) is not int or getattr(self, name) < 0:
                raise ValueError(f"invalid {name}")
        if (
            self.max_cpu_seconds > 86400
            or self.max_memory_bytes > 4 * 1024**3
            or self.max_output_bytes > 10 * 1024**3
        ):
            raise ValueError("campaign budget exceeds plan")


def load_config(path: Path) -> tuple[OutcomeConfig, str]:
    raw = path.read_bytes()
    data = tomllib.loads(raw.decode())
    if set(data) != {"outcomes"} or not isinstance(data["outcomes"], dict):
        raise ValueError("one [outcomes] section is required")
    values = data["outcomes"]
    defaults = OutcomeConfig()
    known = {f.name for f in fields(defaults)}
    if set(values) - known:
        raise ValueError(f"unknown configuration keys: {set(values) - known}")
    for name, value in values.items():
        default = getattr(defaults, name)
        if isinstance(default, Decimal):
            if not isinstance(value, str):
                raise ValueError(f"{name} must be an exact decimal string")
            values[name] = Decimal(value)
        elif type(value) is not type(default):
            raise ValueError(f"invalid type for {name}")
    return OutcomeConfig(**values), hashlib.sha256(raw).hexdigest()
