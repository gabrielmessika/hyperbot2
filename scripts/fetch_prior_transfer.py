"""Checksum-verified, bounded public Binance monthly archive acquisition."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path

from qualify_prior_transfer import BASE, REPORT
from qualify_prior_transfer import DATA as QUALIFICATION

from hyperbot2.research.artifacts import checked_input, file_sha256, write_json
from hyperbot2.research.binance_archives import year_bounds


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--year", type=int, choices=(2024, 2025), default=2025)
    parser.add_argument(
        "--qualification", type=Path, default=REPORT / "qualification.json"
    )
    parser.add_argument("--reuse", type=Path, default=QUALIFICATION)
    args = parser.parse_args()
    checked_input(args.qualification)
    qualification = json.loads(args.qualification.read_text())
    start, end = year_bounds(args.year)
    coins = [r["coin"] for r in qualification["selected_by_metadata"]]
    if (
        len(coins) != (15 if args.year == 2025 else 11)
        or qualification.get("year", 2025) != args.year
        or any(r["onboard_ms"] > start for r in qualification["selected_by_metadata"])
    ):
        raise ValueError("qualified cohort changed")
    args.output.mkdir(parents=True, exist_ok=False)
    requests: list[dict] = []
    archives: list[dict] = []
    total_bytes = 0

    def request(url: str, name: str) -> Path:
        nonlocal total_bytes
        if len(requests) >= 864 or total_bytes >= 50_000_000:
            raise ValueError("free archive budget exceeded")
        path = args.output / name
        sent = time.time_ns() // 1_000_000
        result = subprocess.run(
            [
                "curl",
                "--fail-with-body",
                "--max-time",
                "20",
                "--max-filesize",
                "2000000",
                "-sS",
                url,
            ],
            capture_output=True,
            timeout=25,
            check=False,
        )
        with path.open("xb") as stream:
            stream.write(result.stdout)
        sha = file_sha256(path)
        path.with_suffix(path.suffix + ".sha256").write_text(f"{sha}  {path.name}\n")
        total_bytes += len(result.stdout)
        requests.append(
            {
                "url": url,
                "path": str(path),
                "sha256": sha,
                "returncode": result.returncode,
                "bytes": len(result.stdout),
                "sent_ms": sent,
                "received_ms": time.time_ns() // 1_000_000,
            }
        )
        write_json(args.output / f"index-{len(requests):03d}.json", requests[-1])
        if result.returncode or total_bytes > 50_000_000:
            raise ValueError(f"archive acquisition failed: {name}")
        time.sleep(0.25)
        return path

    try:
        for c in coins:
            for month in range(1, 13):
                for route in ("klines", "fundingRate"):
                    frequency = "1h" if route == "klines" else "fundingRate"
                    name = f"{c}USDT-{frequency}-{args.year}-{month:02d}.zip"
                    url = (
                        f"{BASE}/{route}/{c}USDT/"
                        + ("1h/" if route == "klines" else "")
                        + name
                    )
                    if c == "ARB" and month == 1:
                        path, check = (
                            args.reuse / name,
                            args.reuse / (name + ".CHECKSUM"),
                        )
                        checked_input(path)
                        checked_input(check)
                    else:
                        path = request(url, name)
                        check = request(url + ".CHECKSUM", name + ".CHECKSUM")
                    if (
                        hashlib.sha256(path.read_bytes()).hexdigest()
                        != check.read_text().split()[0]
                    ):
                        raise ValueError("provider checksum mismatch")
                    archives.append(
                        {
                            "coin": c,
                            "month": month,
                            "route": route,
                            "path": str(path),
                            "sha256": checked_input(path),
                            "provider_checksum_path": str(check),
                            "provider_checksum_sha256": checked_input(check),
                        }
                    )
            print(
                c,
                "24 monthly archives checked",
                len(requests),
                "new requests",
                flush=True,
            )
    finally:
        write_json(
            args.output / "manifest.json",
            {
                "requests": requests,
                "archives": archives,
                "response_bytes": total_bytes,
                "script_sha256": file_sha256(Path(__file__)),
                "data_cost_usd": 0,
                "complete": len(archives) == len(coins) * 24,
                "coins": coins,
                "start_ms": start,
                "end_ms_exclusive": end,
            },
        )


if __name__ == "__main__":
    main()
