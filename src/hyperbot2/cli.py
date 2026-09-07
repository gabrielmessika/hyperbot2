"""Local-first command-line entry points for research and bounded public witnesses."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path

from hyperbot2 import __version__
from hyperbot2.models import EventContext, TimeSource
from hyperbot2.outcomes.catalog import discover_recurring
from hyperbot2.outcomes.config import load_config
from hyperbot2.outcomes.public import witness
from hyperbot2.replay.engine import FillModelKind
from hyperbot2.research.artifacts import (
    CampaignBudget,
    file_sha256,
    source_version,
    write_json,
)
from hyperbot2.research.campaign import run_campaign
from hyperbot2.research.opportunity_screen import (
    ScreenRequest,
    legacy_paper_summary,
    screen_legacy,
)
from hyperbot2.services.runtime import prepare_capture, read_health, run_service


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="HyperBot2: public research only; no live execution"
    )
    p.add_argument("--config", type=Path, default=Path("config/outcomes.toml"))
    p.add_argument("--version", action="version", version=f"HyperBot2 {__version__}")
    sub = p.add_subparsers(dest="command", required=True)
    cat = sub.add_parser("catalog", help="qualify a saved public outcomeMeta response")
    cat.add_argument("--input", type=Path, required=True)
    cat.add_argument("--observed-ms", type=int, required=True)
    cat.add_argument("--attestations", type=Path)
    cat.add_argument("--output", type=Path, required=True)
    screen = sub.add_parser(
        "screen", help="stream existing legacy snapshots, no maker fills"
    )
    screen.add_argument("--books", type=Path, required=True)
    screen.add_argument("--settlements", type=Path)
    screen.add_argument("--max-records", type=int)
    screen.add_argument("--output", type=Path, required=True)
    for name in ("replay", "shadow"):
        run = sub.add_parser(
            name, help="bounded qualified windows with the same strategy/risk"
        )
        run.add_argument("--input", type=Path, required=True)
        run.add_argument(
            "--model", choices=[x.value for x in FillModelKind], default="central"
        )
        run.add_argument("--output", type=Path, required=True)
    collect = sub.add_parser(
        "witness", help="bounded public L2 fast witness; never deploys a service"
    )
    collect.add_argument("--seconds", type=int, default=40)
    collect.add_argument("--public-network", action="store_true")
    collect.add_argument("--output", type=Path, required=True)
    service = sub.add_parser(
        "run", help="bounded public shadow service with health and graceful shutdown"
    )
    service.add_argument("--data-root", type=Path, required=True)
    service.add_argument("--seconds", type=int, default=900)
    service.add_argument("--blocked-seconds", type=int, default=300)
    service.add_argument("--public-network", action="store_true")
    service.add_argument("--attestations", type=Path)
    for command in ("health", "status"):
        status = sub.add_parser(
            command, help="read runtime state without network access"
        )
        status.add_argument("--data-root", type=Path, required=True)
    prepare = sub.add_parser(
        "prepare", help="join a recorded public capture into causal replay windows"
    )
    prepare.add_argument("--capture", type=Path, required=True)
    prepare.add_argument("--output", type=Path, required=True)
    prepare.add_argument("--references", type=Path)
    prepare.add_argument("--attestations", type=Path)
    return p


def _main() -> int:
    args = parser().parse_args()
    if args.command in ("health", "status"):
        status, healthy = read_health(args.data_root)
        print(json.dumps(status, default=str))
        return 0 if args.command == "status" or healthy else 1
    config, config_hash = load_config(args.config)
    root = Path(__file__).resolve().parents[2]
    version, source_files = source_version(root)
    run_id = f"hb2-{args.command}-{time.time_ns()}"
    context = EventContext(
        run_id,
        version,
        config_hash,
        TimeSource.EXCHANGE
        if args.command in ("witness", "run")
        else TimeSource.REPLAY,
    )
    if args.command == "run":
        if not args.public_network:
            raise ValueError("run requires --public-network")
        result = asyncio.run(
            run_service(
                root=args.data_root,
                config=config,
                context=context,
                source_files=source_files,
                seconds=args.seconds,
                blocked_seconds=args.blocked_seconds,
                attestations=args.attestations,
            )
        )
        print(
            json.dumps(
                {
                    "run_id": run_id,
                    "state": "STOPPED",
                    "verdict": result["verdict"],
                    "stop_reason": result["stop_reason"],
                }
            )
        )
        return 0
    if args.command == "prepare":
        result = prepare_capture(
            capture=args.capture,
            output=args.output,
            config=config,
            context=context,
            attestations=args.attestations,
            references=args.references,
        )
        write_json(
            args.output / "source_manifest.json",
            {"code_version": version, "files": source_files},
        )
        print(
            json.dumps(
                {
                    "run_id": run_id,
                    "verdict": result["verdict"],
                    "output": str(args.output),
                }
            )
        )
        return 2 if result["verdict"] == "DATA_BLOCKED" else 0
    if args.command in ("replay", "shadow"):
        result = run_campaign(
            source=args.input,
            output=args.output,
            config=config,
            run_id=run_id,
            code_version=version,
            config_sha256=config_hash,
            model=FillModelKind(args.model),
            shadow=args.command == "shadow",
            enforce_process=True,
        )
        write_json(
            args.output / "source_manifest.json",
            {
                "code_version": version,
                "files": source_files,
                "config_sha256": config_hash,
                "config": asdict(config),
            },
        )
        print(
            json.dumps(
                {
                    "run_id": run_id,
                    "verdict": result["verdict"],
                    "output": str(args.output),
                }
            )
        )
        return 2 if result["verdict"] == "DATA_BLOCKED" else 0
    if args.command == "witness" and not args.public_network:
        raise ValueError("public witness requires the explicit --public-network flag")
    args.output.mkdir(parents=True, exist_ok=False)
    budget = CampaignBudget(config, args.output, enforce_process=True)
    write_json(
        args.output / "source_manifest.json",
        {
            "code_version": version,
            "files": source_files,
            "config_sha256": config_hash,
            "config": asdict(config),
        },
    )
    try:
        if args.command == "catalog":
            metadata_hash = file_sha256(args.input)
            attestation_hash = (
                file_sha256(args.attestations) if args.attestations else None
            )
            metadata = json.loads(args.input.read_text())
            attestations = (
                json.loads(args.attestations.read_text()) if args.attestations else None
            )
            definitions, issues = discover_recurring(
                metadata, observed_ms=args.observed_ms, attestations=attestations
            )
            if metadata_hash != file_sha256(args.input) or (
                args.attestations and attestation_hash != file_sha256(args.attestations)
            ):
                raise ValueError("catalog inputs changed during read")
            result = {
                "run_id": run_id,
                "code_version": version,
                "config_sha256": config_hash,
                "input_sha256": metadata_hash,
                "attestations_sha256": attestation_hash,
                "definitions": [asdict(d) for d in definitions],
                "issues": issues,
                "qualification": {
                    d.market: d.reasons(args.observed_ms) for d in definitions
                },
                "verdict": "DATA_BLOCKED"
                if not definitions
                or any(d.reasons(args.observed_ms) for d in definitions)
                else "RESEARCH_ONLY",
            }
            write_json(args.output / "catalog.json", result)
        elif args.command == "screen":
            if args.max_records is not None and args.max_records <= 0:
                raise ValueError("max-records must be positive")
            result = screen_legacy(
                ScreenRequest(args.books, max_records=args.max_records), context, budget
            )
            if args.settlements:
                result["legacy_paper"] = legacy_paper_summary(args.settlements)
            write_json(args.output / "screen.json", result)
        else:
            result = asyncio.run(
                witness(
                    output=args.output,
                    context=context,
                    seconds=args.seconds,
                    budget=budget,
                )
            )
        budget.check()
        write_json(args.output / "resources.json", budget.metrics())
        print(
            json.dumps(
                {
                    "run_id": run_id,
                    "verdict": result["verdict"],
                    "output": str(args.output),
                }
            )
        )
        return 2 if result["verdict"] == "DATA_BLOCKED" else 0
    except BaseException as exc:
        write_json(
            args.output / "failure.json",
            {
                "exception": type(exc).__name__,
                "reason": str(exc),
                "run_id": run_id,
                "verdict": "DATA_BLOCKED",
                "resources": budget.metrics(),
            },
        )
        raise


def main() -> int:
    try:
        return _main()
    except (ValueError, OSError, RuntimeError) as error:
        print(
            json.dumps({"error": type(error).__name__, "reason": str(error)}),
            file=sys.stderr,
        )
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
