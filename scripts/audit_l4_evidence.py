"""Reproduce the September 7 L4 diagnosis offline from checksummed evidence."""

from __future__ import annotations

import argparse
import json
import runpy
from decimal import Decimal
from pathlib import Path
from urllib.parse import quote, urlencode

from hyperbot2.event_store import JsonlEventStore
from hyperbot2.models import BookLevel
from hyperbot2.research.artifacts import checked_input, file_sha256, write_json
from hyperbot2.research.l4_archive import ArchiveBook, canonical_yes_levels

SCRIPTS = Path(__file__).resolve().parent
PROBE = runpy.run_path(str(SCRIPTS / "probe_l4_archive.py"))["ArchiveProbe"]
distribution = runpy.run_path(str(SCRIPTS / "diagnose_feasibility.py"))["distribution"]


class RecordedProbe(PROBE):
    """Use the production reconciliation path without allowing network access."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory
        checked_input(directory / "report.json")
        self.recorded = iter(
            json.loads((directory / "report.json").read_text())["requests"]
        )
        self.inputs: dict[str, str] = {}

    def get(self, coin: str, suffix: str, parameters: dict) -> dict:
        request = next(self.recorded)
        expected = (
            "https://api.0xarchive.io/v1/hyperliquid/hip4/orderbook/"
            + quote(coin, safe="")
            + "/l4"
            + suffix
            + "?"
            + urlencode(parameters)
        )
        if request["url"] != expected or request["http_status"] != "200":
            raise ValueError("recorded request differs from replay request")
        path = self.directory / Path(request["path"]).name
        digest = checked_input(path)
        if digest != request["sha256"]:
            raise ValueError("response differs from request manifest")
        self.inputs[str(path)] = digest
        return json.loads(path.read_text(), parse_float=Decimal)


def audit(root: Path, native_path: Path) -> dict:
    inputs = {str(native_path): file_sha256(native_path)}
    reconstructed = []
    for outcome in (1715, 1716, 1717, 1718):
        probe = RecordedProbe(root / f"reconstruction-{outcome}")
        for side in (0, 1):
            result = probe.reconcile(
                f"#{outcome * 10 + side}", 1788710400000, 1788710460000
            )
            if not result["checkpoint_matched"]:
                raise ValueError("historical checkpoint mismatch")
            reconstructed.append(result)
        if next(probe.recorded, None) is not None:
            raise ValueError("unexpected trailing requests")
        inputs.update(probe.inputs)
    native = [
        record["payload"]
        for record in JsonlEventStore(native_path.parent).iter_records(native_path.stem)
        if record["payload"]["channel"] == "l2Book"
        and record["payload"]["coin"] == "#17150"
    ]
    cross = RecordedProbe(root / "cross-source")
    comparisons = []
    for index in (0, 50, 100):
        payload = native[index]
        timestamp = payload["exchange_ts_ms"]
        snapshots = [
            ArchiveBook.snapshot(cross.get(coin, "", {"timestamp": timestamp})["data"])
            for coin in ("#17150", "#17151")
        ]
        merged = canonical_yes_levels(*snapshots)
        expected = json.loads(payload["payload_json"])["levels"]
        for actual, levels in zip(merged, expected, strict=True):
            if actual[:5] != tuple(
                BookLevel(Decimal(v["px"]), Decimal(v["sz"]), v["n"]) for v in levels
            ):
                raise ValueError("independent native depth mismatch")
        comparisons.append(
            {"native_index": index, "exchange_ms": timestamp, "matched": True}
        )
    inputs.update(cross.inputs)
    witnesses = []
    for directory, report_name in (
        ("ws-local", "ws-local/report.json"),
        ("ws-server-diffs", "server-diffs-report.json"),
        ("ws-server-orders", "server-orders-report.json"),
    ):
        report_path = root / report_name
        checked_input(report_path)
        report = json.loads(report_path.read_text())
        raw_path = root / directory / "raw/archive-l4.jsonl"
        digest = file_sha256(raw_path)
        if digest != report["raw_sha256"]:
            raise ValueError("witness checksum mismatch")
        inputs[str(raw_path)] = digest
        ages = []
        for sequence, record in enumerate(
            JsonlEventStore(raw_path.parent).iter_records(raw_path.stem)
        ):
            payload = record["payload"]
            if payload["local_sequence"] != sequence:
                raise ValueError("local witness sequence gap")
            message = json.loads(payload["payload_json"], parse_float=Decimal)
            if message.get("type") == "l4_batch":
                ages.extend(
                    payload["receive_ts_ms"] - event["ts"] for event in message["data"]
                )
        stats = distribution(ages)
        fresh = sum(0 <= age <= 100 for age in ages)
        if (
            stats != report["diff_event_age_ms"]
            or fresh != report["diff_events_with_age_0_to_100_ms"]
        ):
            raise ValueError("witness statistics mismatch")
        witnesses.append(
            {"source": directory, "event_age_ms": stats, "admissible_100_ms": fresh}
        )
    return {
        "run_id": "l4-evidence-offline-2026-09-07",
        "script_sha256": file_sha256(Path(__file__)),
        "reconstructor_sha256": file_sha256(
            SCRIPTS.parent / "src/hyperbot2/research/l4_archive.py"
        ),
        "probe_sha256": file_sha256(SCRIPTS / "probe_l4_archive.py"),
        "inputs": inputs,
        "reconstructions": reconstructed,
        "native_depth_checks": comparisons,
        "witnesses": witnesses,
        "historical_reconstruction": "CHECKPOINTS_MATCHED_RESEARCH_ONLY",
        "execution_status": "DATA_BLOCKED",
        "queue_qualified": False,
        "promotion_authorized": False,
        "limits": [
            "bounded sampled evidence; no economic backtest or fill validation",
            "local sequence is not an exchange completeness watermark",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--native", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_json(args.output, audit(args.data, args.native))
    print(args.output)


if __name__ == "__main__":
    main()
