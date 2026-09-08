"""Strict monthly futures archive adapter; absent payments need schedule proof."""

from __future__ import annotations

import csv
import io
import json
import zipfile
from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from hyperbot2.research.archive_overlay import load_october_rest, overlay_october
from hyperbot2.research.artifacts import checked_input
from hyperbot2.research.rotation import HOUR
from hyperbot2.research.volume import VolumeBar

D = Decimal
START, END = 1735689600000, 1767225600000


def year_bounds(year: int) -> tuple[int, int]:
    if year not in (2024, 2025):
        raise ValueError("qualified archive year must be 2024 or 2025")
    start = int(datetime(year, 1, 1, tzinfo=UTC).timestamp() * 1000)
    end = int(datetime(year + 1, 1, 1, tzinfo=UTC).timestamp() * 1000)
    return start, end


def hourly_payments(
    rows: Sequence[tuple[int, int, Decimal]], start: int, end: int
) -> dict[int, Decimal]:
    """Prove complete interval coverage before inserting non-payment zero hours."""
    if not rows or start % HOUR or end % HOUR or end <= start:
        raise ValueError("nonempty funding schedule required")
    buckets = [at // HOUR * HOUR for at, _, _ in rows]
    if buckets != sorted(set(buckets)) or buckets[0] != start:
        raise ValueError("funding start/order/duplicate failure")
    for i, (at, interval, rate) in enumerate(rows):
        if (
            not start <= at < end
            or not 0 <= at % HOUR <= 60_000
            or interval not in (1, 2, 4, 8)
            or not rate.is_finite()
        ):
            raise ValueError("invalid funding record")
        if i and buckets[i] - buckets[i - 1] != interval * HOUR:
            raise ValueError("unexplained funding gap or interval change")
    if buckets[-1] + rows[-1][1] * HOUR != end:
        raise ValueError("unproven final funding interval")
    output = {at: D(0) for at in range(start, end, HOUR)}
    for at, _, rate in rows:
        del output[at // HOUR * HOUR]
        output[at] = rate
    return output


def load_archives(
    root: Path,
    coins: Sequence[str],
    *,
    year: int = 2025,
    october_2024_rest: Path | None = None,
) -> tuple[dict[str, list[VolumeBar]], dict[str, dict[int, Decimal]], dict[str, Any]]:
    start, end = year_bounds(year)
    if october_2024_rest is not None and year != 2024:
        raise ValueError("October correction only applies to 2024")
    manifest_path = root / "manifest.json"
    manifest_sha = checked_input(manifest_path)
    manifest = json.loads(manifest_path.read_text())
    if (
        not manifest["complete"]
        or set(manifest["coins"]) != set(coins)
        or manifest["start_ms"] != start
        or manifest["end_ms_exclusive"] != end
    ):
        raise ValueError("incomplete or different registered acquisition")
    by_key = {}
    sources = {str(manifest_path): manifest_sha}
    rest: dict[str, list[VolumeBar]] = {}
    if october_2024_rest is not None:
        rest, correction_sources = load_october_rest(october_2024_rest, coins)
        sources.update(correction_sources)
    for row in manifest["archives"]:
        key = (row["coin"], row["month"], row["route"])
        if key in by_key:
            raise ValueError("duplicate source archive")
        by_key[key] = row
    if set(by_key) != {
        (c, m, route)
        for c in coins
        for m in range(1, 13)
        for route in ("klines", "fundingRate")
    }:
        raise ValueError("registered monthly archive coverage differs")
    bars: dict[str, list[VolumeBar]] = {}
    payments: dict[str, dict[int, Decimal]] = {}
    assets = {}
    for c in coins:
        bars[c] = []
        funding_rows: list[tuple[int, int, Decimal]] = []
        for month in range(1, 13):
            for route in ("klines", "fundingRate"):
                row = by_key[c, month, route]
                path, checksum = Path(row["path"]), Path(row["provider_checksum_path"])
                sha, check_sha = checked_input(path), checked_input(checksum)
                if (
                    sha != row["sha256"]
                    or check_sha != row["provider_checksum_sha256"]
                    or checksum.read_text().split()[0] != sha
                ):
                    raise ValueError("provider/source checksum differs")
                sources[str(path)], sources[str(checksum)] = sha, check_sha
                with zipfile.ZipFile(path) as archive:
                    infos = archive.infolist()
                    if (
                        len(infos) != 1
                        or infos[0].filename != path.with_suffix(".csv").name
                        or infos[0].file_size > 2_000_000
                        or archive.testzip() is not None
                    ):
                        raise ValueError("invalid bounded archive")
                    reader = csv.DictReader(
                        io.StringIO(archive.read(infos[0]).decode())
                    )
                    if route == "klines":
                        for record in reader:
                            at = int(record["open_time"])
                            if int(record["close_time"]) != at + HOUR - 1:
                                raise ValueError("invalid kline duration/unit")
                            bars[c].append(
                                VolumeBar(
                                    at,
                                    *(
                                        D(record[k])
                                        for k in (
                                            "open",
                                            "high",
                                            "low",
                                            "close",
                                            "volume",
                                        )
                                    ),
                                )
                            )
                    else:
                        funding_rows.extend(
                            (
                                int(r["calc_time"]),
                                int(r["funding_interval_hours"]),
                                D(r["last_funding_rate"]),
                            )
                            for r in reader
                        )
        if [b.time for b in bars[c]] != list(range(start, end, HOUR)):
            raise ValueError(f"hourly price coverage failure: {c}")
        payments[c] = hourly_payments(funding_rows, start, end)
        if october_2024_rest is not None:
            bars[c] = overlay_october(bars[c], rest[c])
        zero_volume = sum(b.volume == 0 for b in bars[c])
        if zero_volume:
            raise ValueError(f"zero-volume transfer asset: {c}")
        assets[c] = {
            "hours": len(bars[c]),
            "funding_payments": len(funding_rows),
            "zero_volume_hours": zero_volume,
            "funding_intervals": sorted({r[1] for r in funding_rows}),
            "max_funding_offset_ms": max(at % HOUR for at, _, _ in funding_rows),
        }
    return (
        bars,
        payments,
        {
            "sources": sources,
            "assets": assets,
            "source_venue": "Binance USDT perpetual futures",
            "data_class": "C",
            "adapter_version": "binance-monthly-v1+october2024-rest-v1"
            if october_2024_rest is not None
            else "binance-monthly-v1",
            **(
                {
                    "source_correction": {
                        "priority": (
                            "current official REST over original archive "
                            "for two audited hours"
                        ),
                        "times_ms": [1730145600000, 1730149200000],
                        "corrected_bars": 2 * len(coins),
                        "unchanged_october_bars": 742 * len(coins),
                        "raw_archives_unchanged": True,
                    }
                }
                if october_2024_rest is not None
                else {}
            ),
            "start_ms": start,
            "end_ms_exclusive": end,
            "inserted_zero_hours": (
                "only non-payment hours after full funding-interval validation"
            ),
            "native_hyperliquid_history": False,
        },
    )
