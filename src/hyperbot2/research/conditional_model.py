"""Small fixed ridge model with explicit feature and label availability."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from statistics import median

from hyperbot2.research.rotation import HOUR
from hyperbot2.research.volume import VolumeBar

DAY = 24 * HOUR


def clipped(value: float) -> float:
    if not math.isfinite(value):
        raise ValueError("finite model input required")
    return max(-5.0, min(5.0, value))


@dataclass(frozen=True, slots=True)
class Observation:
    coin: str
    index: int
    time_ms: int
    label_known_ms: int
    features: tuple[float, ...]
    scale: float
    label: float


@dataclass(frozen=True, slots=True)
class RidgeModel:
    means: tuple[float, ...]
    scales: tuple[float, ...]
    coefficients: tuple[float, ...]
    intercept: float

    def predict(self, features: Sequence[float]) -> float:
        if len(features) != len(self.means) or any(
            not math.isfinite(x) for x in features
        ):
            raise ValueError("invalid prediction features")
        return self.intercept + sum(
            b * (x - m) / s
            for x, m, s, b in zip(
                features, self.means, self.scales, self.coefficients, strict=True
            )
        )


def fit_ridge(xs: Sequence[Sequence[float]], ys: Sequence[float]) -> RidgeModel:
    n = len(xs)
    if n < 2 or n != len(ys) or not xs[0]:
        raise ValueError("aligned nonempty training data required")
    p = len(xs[0])
    if any(len(x) != p or any(not math.isfinite(v) for v in x) for x in xs) or any(
        not math.isfinite(y) for y in ys
    ):
        raise ValueError("invalid training values")
    means = tuple(sum(x[j] for x in xs) / n for j in range(p))
    scales = tuple(
        max(1e-12, math.sqrt(sum((x[j] - means[j]) ** 2 for x in xs) / n))
        for j in range(p)
    )
    target = [clipped(y) for y in ys]
    intercept = sum(target) / n
    matrix = [[0.0] * (p + 1) for _ in range(p)]
    for x, y in zip(xs, target, strict=True):
        z = [(x[j] - means[j]) / scales[j] for j in range(p)]
        for j in range(p):
            matrix[j][p] += z[j] * (y - intercept) / n
            for k in range(p):
                matrix[j][k] += z[j] * z[k] / n
    for j in range(p):
        matrix[j][j] += 1.0
    for j in range(p):
        pivot = max((abs(matrix[k][j]), k) for k in range(j, p))[1]
        matrix[j], matrix[pivot] = matrix[pivot], matrix[j]
        divisor = matrix[j][j]
        if abs(divisor) < 1e-12:
            raise ValueError("singular ridge system")
        matrix[j] = [v / divisor for v in matrix[j]]
        for k in range(p):
            if k != j:
                factor = matrix[k][j]
                matrix[k] = [
                    a - factor * b for a, b in zip(matrix[k], matrix[j], strict=True)
                ]
    return RidgeModel(means, scales, tuple(matrix[j][p] for j in range(p)), intercept)


def fit_before(
    observations: Sequence[Observation], now_ms: int, minimum: int = 1000
) -> tuple[RidgeModel, int, int] | None:
    if minimum < 2:
        raise ValueError("at least two training rows required")
    eligible = [
        o
        for o in observations
        if now_ms - 90 * DAY <= o.time_ms < now_ms and o.label_known_ms <= now_ms - HOUR
    ]
    if len(eligible) < minimum:
        return None
    model = fit_ridge([o.features for o in eligible], [o.label for o in eligible])
    return model, len(eligible), max(o.label_known_ms for o in eligible)


@dataclass(frozen=True, slots=True)
class MonthlyFit:
    time_ms: int
    training_rows: int
    last_label_known_ms: int
    model: RidgeModel


@dataclass(frozen=True, slots=True)
class Prediction:
    observation: Observation
    trained_ms: int
    predicted: float
    intercept_only: float


def chronological_predictions(
    observations: Sequence[Observation], start_ms: int, minimum: int = 1000
) -> tuple[list[Prediction], list[MonthlyFit]]:
    """Freeze each fit at its UTC month boundary; purge unavailable labels."""
    predictions: list[Prediction] = []
    fits: list[MonthlyFit] = []
    previous_month = -1
    current: MonthlyFit | None = None
    for o in sorted(observations, key=lambda row: (row.time_ms, row.coin)):
        date = datetime.fromtimestamp(o.time_ms / 1000, UTC)
        month = int(datetime(date.year, date.month, 1, tzinfo=UTC).timestamp() * 1000)
        if month != previous_month:
            previous_month, current = month, None
            if month >= start_ms + 90 * DAY:
                fitted = fit_before(observations, month, minimum)
                if fitted is not None:
                    model, count, known = fitted
                    current = MonthlyFit(month, count, known, model)
                    fits.append(current)
        if current is not None:
            predictions.append(
                Prediction(
                    o,
                    current.time_ms,
                    current.model.predict(o.features),
                    current.model.intercept,
                )
            )
    return predictions, fits


def features_at(
    bars: Mapping[str, Sequence[VolumeBar]],
    funding: Mapping[str, Sequence[float]],
    i: int,
) -> dict[str, tuple[tuple[float, ...], float]]:
    if (
        i < 169
        or not bars
        or any(i > len(rows) or len(funding[c]) < i for c, rows in bars.items())
    ):
        raise ValueError("169 completed hourly bars required")
    relative = {
        c: math.log(float(rows[i - 1].close / rows[i - 25].close))
        for c, rows in bars.items()
    }
    center = median(relative.values())
    result = {}
    for c, rows in bars.items():
        returns = [
            math.log(float(rows[j].close / rows[j - 1].close))
            for j in range(i - 168, i)
        ]
        mean = sum(returns) / 168
        sigma = max(0.001, math.sqrt(sum((r - mean) ** 2 for r in returns) / 167))
        momentum = [
            math.log(float(rows[i - 1].close / rows[i - 1 - h].close))
            / (sigma * math.sqrt(h))
            for h in (1, 6, 24, 168)
        ]
        typical_volume = float(median(r.volume for r in rows[i - 168 : i]))
        recent_volume = sum(float(r.volume) for r in rows[i - 6 : i]) / 6
        if typical_volume <= 0 or recent_volume <= 0:
            raise ValueError("positive historical volume required")
        volume = clipped(math.log(recent_volume / typical_volume))
        values = [
            *map(clipped, momentum),
            volume,
            clipped(sum(funding[c][i - 24 : i]) / 0.001),
            clipped((relative[c] - center) / (sigma * math.sqrt(24))),
            clipped(clipped(momentum[0]) * volume / 5),
        ]
        result[c] = (tuple(values), sigma * math.sqrt(6))
    return result
