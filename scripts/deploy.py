"""Build and install an immutable public-only release without starting any bot."""

from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import subprocess
import tarfile
from pathlib import Path


def run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess:
    return subprocess.run(args, check=True, **kwargs)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="trident-hetzner")
    parser.add_argument("--user", default="trident-deploy")
    parser.add_argument(
        "--identity", type=Path, default=Path.home() / ".ssh/trident_hetzner_ed25519"
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    run(["uv", "build"], cwd=root)
    run(
        [
            "uv",
            "export",
            "--frozen",
            "--no-dev",
            "--no-emit-project",
            "-o",
            "requirements.lock",
        ],
        cwd=root,
        stdout=subprocess.DEVNULL,
    )
    names = [
        "Dockerfile",
        "requirements.lock",
        "dist/hyperbot2-0.2.0-py3-none-any.whl",
        "config/outcomes.toml",
        "bin/hyperbot2",
        "bin/hyperbot2-server",
    ]
    checksums = {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in names
    }
    release = hashlib.sha256(
        json.dumps(checksums, sort_keys=True).encode()
    ).hexdigest()[:16]
    output = root / "tmp" / f"deploy-{release}"
    output.mkdir(parents=True, exist_ok=True)
    manifest = output / "deployment-manifest.json"
    manifest.write_text(
        json.dumps(
            {"release": release, "files": checksums, "live_enabled": False}, indent=2
        )
        + "\n"
    )
    archive = output / "release.tar"
    with tarfile.open(archive, "w") as tar:
        for name in names:
            if (root / name).is_symlink():
                raise ValueError("release inputs cannot be symlinks")
            tar.add(root / name, arcname=name)
        tar.add(manifest, arcname="deployment-manifest.json")
    ssh = [
        "ssh",
        "-i",
        str(args.identity),
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=10",
        f"{args.user}@{args.host}",
    ]

    def remote(command: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        return run([*ssh, shlex.join(command)], **kwargs)

    install = "/opt/hyperbot2"
    destination = f"{install}/releases/{release}"
    # Create only this new service directory through the already authorized Docker host.
    remote(
        [
            "docker",
            "run",
            "--rm",
            "--entrypoint",
            "sh",
            "-v",
            "/opt:/host-opt",
            "python:3.12.13-slim",
            "-c",
            "mkdir -p /host-opt/hyperbot2 && chown 1000:1000 /host-opt/hyperbot2",
        ]
    )
    remote(["mkdir", "-p", f"{install}/releases", f"{install}/shared/data"])
    exists = subprocess.run(
        [*ssh, shlex.join(["test", "-e", destination])], check=False
    )
    if exists.returncode == 0:
        raise RuntimeError("release already exists; refusing overwrite")
    if exists.returncode != 1:
        raise RuntimeError("remote preflight failed")
    remote(["mkdir", destination])
    with archive.open("rb") as stream:
        remote(["tar", "-xf", "-", "-C", destination], stdin=stream)
    verify = (
        "import json,hashlib,pathlib; r=pathlib.Path('.'); "
        "m=json.loads((r/'deployment-manifest.json').read_text()); "
        "assert all(hashlib.sha256((r/n).read_bytes()).hexdigest()==h "
        "for n,h in m['files'].items())"
    )
    remote(
        [
            "sh",
            "-c",
            f"cd {shlex.quote(destination)} && python3 -c {shlex.quote(verify)}",
        ]
    )
    image = f"hyperbot2:{release}"
    remote(
        [
            "docker",
            "build",
            "--label",
            f"hyperbot2.release={release}",
            "-t",
            image,
            destination,
        ]
    )
    remote(["docker", "run", "--rm", "--network=none", image, "--version"])
    remote(
        [
            "chmod",
            "755",
            f"{destination}/bin/hyperbot2",
            f"{destination}/bin/hyperbot2-server",
        ]
    )
    remote(
        [
            "sh",
            "-c",
            f"printf '%s\\n' {shlex.quote(image)} > "
            f"{shlex.quote(destination)}/image.txt",
        ]
    )
    # Activation changes only the CLI symlink; no container is started by deployment.
    remote(["ln", "-sfn", destination, f"{install}/current.next"])
    remote(["mv", "-Tf", f"{install}/current.next", f"{install}/current"])
    print(
        json.dumps(
            {"release": release, "image": image, "install": install, "started": False}
        )
    )


if __name__ == "__main__":
    main()
