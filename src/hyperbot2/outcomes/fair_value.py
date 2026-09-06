"""Causal fair values using the copied digital benchmark and isotonic calibration."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from decimal import Decimal

from hyperbot2.outcomes.contracts import FairValue, OutcomeDefinition, digest
from hyperbot2.research.outcomes import (
    DigitalOutcomeBenchmark,
    IsotonicCalibrator,
    OutcomeSample,
    empirical_volatility,
)


@dataclass(frozen=True, slots=True)
class ReferencePrice:
    exchange_ms: int
    received_ms: int
    price: Decimal


class CausalFairValueModel:
    def __init__(
        self,
        *,
        interval_ms: int = 60_000,
        window_size: int = 120,
        uncertainty: Decimal = Decimal("0.02"),
        adverse_selection: Decimal = Decimal("0.01"),
        calibrator: IsotonicCalibrator | None = None,
        calibration_end_ms: int = 0,
    ) -> None:
        if interval_ms <= 0 or window_size < 3 or calibration_end_ms < 0:
            raise ValueError("invalid fair-value window")
        for value in (uncertainty, adverse_selection):
            if not value.is_finite() or value < 0:
                raise ValueError("invalid uncertainty")
        self.interval_ms = interval_ms
        self.prices: deque[ReferencePrice] = deque(maxlen=window_size)
        self.uncertainty = uncertainty
        self.adverse_selection = adverse_selection
        self.calibrator = calibrator
        self.calibration_end_ms = calibration_end_ms
        self.latest: ReferencePrice | None = None

    def observe(self, price: ReferencePrice) -> None:
        if not price.price.is_finite() or price.price <= 0:
            raise ValueError("invalid reference")
        if not 0 <= price.exchange_ms <= price.received_ms:
            raise ValueError("reference timestamps invalid")
        if self.latest and (
            price.received_ms < self.latest.received_ms
            or price.exchange_ms < self.latest.exchange_ms
        ):
            raise ValueError("reference ordering invalid")
        self.latest = price
        if (
            not self.prices
            or price.exchange_ms - self.prices[-1].exchange_ms >= self.interval_ms
        ):
            if (
                self.prices
                and price.exchange_ms - self.prices[-1].exchange_ms
                > 2 * self.interval_ms
            ):
                self.prices.clear()
            self.prices.append(price)

    def predict(self, definition: OutcomeDefinition, now_ms: int) -> FairValue | None:
        latest = self.latest
        if latest is None or latest.received_ms > now_ms or len(self.prices) < 3:
            return None
        if self.calibration_end_ms > now_ms or now_ms >= definition.expiry_ms:
            return None
        volatility = empirical_volatility(
            tuple(p.price for p in self.prices),
            periods_per_year=int(365.25 * 86400000 / self.interval_ms),
        )
        if volatility <= 0:
            return None
        # Labels are placeholders; probability() reads only causal features.
        sample = OutcomeSample(
            "prediction",
            now_ms,
            definition.expiry_ms,
            definition.market,
            definition.underlying,
            latest.price,
            definition.strike,
            volatility,
            0,
            Decimal(0),
            Decimal(0),
            "unclassified",
            "recurring",
        )
        probability = DigitalOutcomeBenchmark().probability(sample)
        if self.calibrator is not None:
            probability = self.calibrator.predict(probability)
        if not 0 < probability < 1:
            return None
        return FairValue(
            probability,
            now_ms,
            latest.exchange_ms,
            self.calibration_end_ms,
            self.uncertainty,
            self.adverse_selection,
            digest(
                {
                    "prices": [
                        (p.exchange_ms, p.received_ms, str(p.price))
                        for p in self.prices
                    ],
                    "calibrator": self.calibrator,
                    "calibration_end_ms": self.calibration_end_ms,
                    "interval_ms": self.interval_ms,
                }
            ),
        )
