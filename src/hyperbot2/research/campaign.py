"""Bounded preregistered campaigns without automatic promotion."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

from hyperbot2.models import EventContext, TimeSource
from hyperbot2.outcomes.config import OutcomeConfig
from hyperbot2.outcomes.serialization import window_from_payload
from hyperbot2.outcomes.session import OutcomeSession, stressed_config
from hyperbot2.replay.engine import FillModelKind
from hyperbot2.research.artifacts import CampaignBudget, checked_input, write_json
from hyperbot2.research.journal import ResearchVariant, VariantJournal


def run_campaign(
    *,
    source: Path,
    output: Path,
    config: OutcomeConfig,
    run_id: str,
    code_version: str,
    config_sha256: str,
    model: FillModelKind,
    shadow: bool = False,
    enforce_process: bool = False,
) -> dict[str, Any]:
    source_hash = checked_input(source)
    output.mkdir(parents=True, exist_ok=False)
    budget = CampaignBudget(config, output, enforce_process=enforce_process)
    journal = VariantJournal(output / "variants.jsonl")
    margins = (Decimal("0"), Decimal("0.005"), Decimal("0.010"))
    scenarios = ("base", "fees_x2", "latency_x2")
    models = (
        (model,)
        if model is FillModelKind.OPTIMISTIC_TOUCH
        else (FillModelKind.CENTRAL, FillModelKind.PESSIMISTIC)
    )
    specifications = []
    for margin in margins:
        for current_model in models:
            for scenario in scenarios:
                variant_config = stressed_config(
                    replace(config, additional_margin=margin), scenario
                )
                payload = {
                    "config": asdict(variant_config),
                    "model": current_model.value,
                    "scenario": scenario,
                }
                sha = hashlib.sha256(
                    json.dumps(payload, default=str, sort_keys=True).encode()
                ).hexdigest()
                variant_id = f"{run_id}-{margin}-{current_model.value}-{scenario}"
                journal.append(
                    ResearchVariant(
                        variant_id,
                        time.time_ns() // 1_000_000,
                        "Selective recurring outcome maker",
                        code_version,
                        sha,
                        "input already explored; research only",
                        "not reserved",
                        "not OOS",
                        json.dumps({"input_sha256": source_hash, "scenario": scenario}),
                    )
                )
                specifications.append(
                    (variant_id, variant_config, current_model, scenario, sha)
                )
    write_json(
        output / "preregistration.json",
        {
            "run_id": run_id,
            "code_version": code_version,
            "source": str(source),
            "input_sha256": source_hash,
            "config_sha256": config_sha256,
            "specifications": [
                {
                    "variant": i,
                    "config": asdict(c),
                    "model": m.value,
                    "scenario": s,
                    "sha256": h,
                }
                for i, c, m, s, h in specifications
            ],
            "out_of_sample": False,
        },
    )
    summaries = []
    try:
        for identity, cfg, current_model, scenario, sha in specifications:
            session = OutcomeSession(
                cfg,
                EventContext(identity, code_version, sha, TimeSource.REPLAY),
                current_model,
                shadow=shadow,
            )
            source_digest = hashlib.sha256()
            with source.open("rb") as stream:
                for index, line in enumerate(stream):
                    source_digest.update(line)
                    if index % 100 == 0:
                        budget.check()
                    window = window_from_payload(json.loads(line))
                    if scenario == "fees_x2" and window.definition.fees is not None:
                        f = window.definition.fees
                        f = replace(
                            f,
                            maker_close_rate=f.maker_close_rate * 2,
                            taker_close_rate=f.taker_close_rate * 2,
                            settlement_rate=f.settlement_rate * 2,
                        )
                        window = replace(
                            window, definition=replace(window.definition, fees=f)
                        )
                    session.process(window)
            if source_digest.hexdigest() != source_hash:
                raise ValueError("input changed during campaign")
            result = session.finish()
            write_json(output / f"{identity}.json", result)
            summaries.append(
                {
                    k: v
                    for k, v in result.items()
                    if k not in ("fills", "cycles", "lifecycle")
                }
            )
            budget.check()
        verdict = (
            "DATA_BLOCKED"
            if any(r["verdict"] == "DATA_BLOCKED" for r in summaries)
            else "INCONCLUSIVE"
        )
        summary = {
            "run_id": run_id,
            "verdict": verdict,
            "variants": summaries,
            "resources": budget.metrics(),
            "promotion_authorized": False,
            "source_sha256": source_hash,
        }
        write_json(output / "summary.json", summary)
        return summary
    except BaseException as exc:
        write_json(
            output / "failure.json",
            {
                "run_id": run_id,
                "verdict": "DATA_BLOCKED",
                "exception": type(exc).__name__,
                "reason": str(exc),
                "resources": budget.metrics(),
                "promotion_authorized": False,
            },
        )
        raise
