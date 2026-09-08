"""Bounded public metadata and checksum-verified Binance archive qualification."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import subprocess
import time
import zipfile
from pathlib import Path

from hyperbot2.research.artifacts import checked_input, file_sha256, write_json
from hyperbot2.research.binance_archives import year_bounds

REPORT = Path("reports/prior_transfer_2026-09-07")
DATA = Path("data/prior_transfer_2026-09-07/qualification")
BASE = "https://data.binance.vision/data/futures/um/monthly"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, choices=(2024, 2025), default=2025)
    parser.add_argument("--report", type=Path, default=REPORT)
    parser.add_argument("--output", type=Path, default=DATA)
    args = parser.parse_args()
    checked_input(args.report / "qualification_registration.json")
    reg = json.loads((args.report / "qualification_registration.json").read_text())
    if reg["protocol_sha256"] != file_sha256(args.report / "QUALIFICATION_PROTOCOL.md"):
        raise ValueError("registered protocol changed")
    start, end = year_bounds(args.year)
    selection = Path("reports/funding_transfer_2026-09-07/selection.json")
    checked_input(selection)
    coins = json.loads(selection.read_text())["eligible"]
    args.output.mkdir(parents=True, exist_ok=False)
    records: list[dict] = []
    total_bytes = 0

    def request(url: str, filename: str) -> bytes:
        nonlocal total_bytes
        if len(records) >= 5 or total_bytes >= 5_000_000:
            raise ValueError("qualification acquisition budget exceeded")
        sent = time.time_ns() // 1_000_000
        response = subprocess.run(
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
        total_bytes += len(response.stdout)
        path = args.output / filename
        with path.open("xb") as stream:
            stream.write(response.stdout)
        sha = file_sha256(path)
        path.with_suffix(path.suffix + ".sha256").write_text(f"{sha}  {path.name}\n")
        records.append(
            {
                "url": url,
                "path": str(path),
                "sha256": sha,
                "bytes": len(response.stdout),
                "returncode": response.returncode,
                "sent_ms": sent,
                "received_ms": time.time_ns() // 1_000_000,
            }
        )
        write_json(args.output / f"index-{len(records)}.json", records)
        if response.returncode or total_bytes > 5_000_000:
            raise ValueError("public qualification request failed")
        return response.stdout

    try:
        if args.year == 2024:
            meta_path = DATA / "exchangeInfo.json"
            if checked_input(meta_path) != reg["metadata_sha256"]:
                raise ValueError("registered metadata changed")
            meta = json.loads(meta_path.read_text())
        else:
            meta = json.loads(
                request(
                    "https://fapi.binance.com/fapi/v1/exchangeInfo", "exchangeInfo.json"
                )
            )
        by_symbol = {s["symbol"]: s for s in meta["symbols"]}
        selected, excluded = [], []
        for coin in coins:
            symbol = coin + "USDT"
            s = by_symbol.get(symbol)
            reason = (
                "missing_symbol"
                if s is None
                else "contract_mismatch"
                if s["baseAsset"] != coin
                or s["quoteAsset"] != "USDT"
                or s["contractType"] != "PERPETUAL"
                else f"contract_begins_after_{args.year}_start"
                if s["onboardDate"] > start
                else None
            )
            item = {
                "coin": coin,
                "symbol": symbol,
                "onboard_ms": s["onboardDate"] if s else None,
                "status": s["status"] if s else None,
            }
            if reason:
                excluded.append({**item, "reason": reason})
            else:
                selected.append(item)
        schemas = {}
        for route in ("klines", "fundingRate"):
            name = (
                f"ARBUSDT-1h-{args.year}-01.zip"
                if route == "klines"
                else f"ARBUSDT-fundingRate-{args.year}-01.zip"
            )
            url = (
                f"{BASE}/{route}/ARBUSDT/" + ("1h/" if route == "klines" else "") + name
            )
            raw = request(url, name)
            checksum = (
                request(url + ".CHECKSUM", name + ".CHECKSUM").decode().split()[0]
            )
            if hashlib.sha256(raw).hexdigest() != checksum:
                raise ValueError("provider checksum failed")
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                if (
                    len(archive.infolist()) != 1
                    or archive.infolist()[0].file_size > 2_000_000
                    or archive.testzip() is not None
                ):
                    raise ValueError("invalid bounded archive")
                lines = archive.read(archive.namelist()[0]).decode().splitlines()
            schemas[route] = {
                "archive": name,
                "rows_including_header": len(lines),
                "header": lines[0],
                "first_row": lines[1],
                "last_row": lines[-1],
                "provider_checksum_passed": True,
            }
        write_json(
            args.report / "qualification.json",
            {
                "selected_by_metadata": selected,
                "year": args.year,
                "start_ms": start,
                "end_ms_exclusive": end,
                "excluded": excluded,
                "schemas": schemas,
                "financial_results_computed": False,
                "coverage_qualified": False,
                "promotion_authorized": False,
            },
        )
        print(
            json.dumps(
                {"selected": selected, "excluded": excluded, "schemas": schemas},
                indent=2,
            )
        )
    finally:
        write_json(
            args.output / "manifest.json",
            {
                "requests": records,
                "response_bytes": total_bytes,
                "script_sha256": file_sha256(Path(__file__)),
                "data_cost_usd": 0,
            },
        )


if __name__ == "__main__":
    main()
