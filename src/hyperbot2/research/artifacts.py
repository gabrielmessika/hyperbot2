"""Immutable artifacts, source fingerprints and enforced process budgets."""

from __future__ import annotations

import hashlib
import json
import os
import resource
import signal
import time
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path
from typing import Any

from hyperbot2.outcomes.config import OutcomeConfig


def file_sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def checked_input(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise ValueError("input must be a regular, non-symlink file")
    expected = path.with_suffix(path.suffix + ".sha256").read_text().split()[0]
    actual = file_sha256(path)
    if expected != actual:
        raise ValueError(f"source checksum mismatch: {path}")
    return actual


def source_version(root: Path) -> tuple[str, dict[str, str]]:
    source_root = root / "src"
    if not (source_root / "hyperbot2").is_dir():
        source_root = Path(__file__).resolve().parents[2]
    files = {
        str(Path("src") / p.relative_to(source_root)): file_sha256(p)
        for p in sorted((source_root / "hyperbot2").rglob("*.py"))
    }
    if (root / "pyproject.toml").is_file():
        files["pyproject.toml"] = file_sha256(root / "pyproject.toml")
    else:
        files["installed_distribution_version"] = hashlib.sha256(
            version("hyperbot2").encode()
        ).hexdigest()
    value = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
    return f"source-sha256:{value}", files


def write_json(path: Path, value: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(value, default=str, indent=2, sort_keys=True) + "\n").encode()
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    checksum = hashlib.sha256(raw).hexdigest()
    with path.with_suffix(path.suffix + ".sha256").open("x") as stream:
        stream.write(f"{checksum}  {path.name}\n")
        stream.flush()
        os.fsync(stream.fileno())
    return checksum


class BudgetExceeded(RuntimeError):
    pass


class CampaignBudget:
    def __init__(
        self, config: OutcomeConfig, output: Path, *, enforce_process: bool = False
    ) -> None:
        self.config, self.output = config, output
        self.wall_start, self.cpu_start = time.monotonic(), time.process_time()
        if enforce_process:

            def expired(signum: int, frame: object) -> None:
                raise BudgetExceeded("wall/CPU budget exceeded")

            signal.signal(signal.SIGALRM, expired)
            signal.signal(signal.SIGXCPU, expired)
            signal.alarm(config.max_wall_seconds)
            soft = int(time.process_time()) + config.max_cpu_seconds
            resource.setrlimit(resource.RLIMIT_CPU, (soft, soft + 1))
            resource.setrlimit(
                resource.RLIMIT_AS, (config.max_memory_bytes, config.max_memory_bytes)
            )
            resource.setrlimit(
                resource.RLIMIT_FSIZE,
                (config.max_output_bytes, config.max_output_bytes),
            )

    def check(self) -> None:
        if time.monotonic() - self.wall_start > self.config.max_wall_seconds:
            raise BudgetExceeded("wall budget exceeded")
        if time.process_time() - self.cpu_start > self.config.max_cpu_seconds:
            raise BudgetExceeded("CPU budget exceeded")
        if (
            resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
            > self.config.max_memory_bytes
        ):
            raise BudgetExceeded("RSS budget exceeded")
        if (
            sum(p.stat().st_size for p in self.output.rglob("*") if p.is_file())
            > self.config.max_output_bytes
        ):
            raise BudgetExceeded("aggregate output budget exceeded")

    def metrics(self) -> dict[str, Any]:
        return {
            "cpu_seconds": time.process_time() - self.cpu_start,
            "wall_seconds": time.monotonic() - self.wall_start,
            "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
            "limits": asdict(self.config),
        }
