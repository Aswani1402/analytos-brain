from __future__ import annotations

import importlib
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def contains(path: str, *needles: str) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    for needle in needles:
        require(needle in text, f"{path} is missing required text: {needle}")


def main() -> None:
    required_files = [
        "Dockerfile.api",
        "railway.toml",
        "scripts/start-hosted.sh",
        "omnigraph/cluster.yaml",
        "omnigraph/schema.pg",
        "omnigraph/queries/products.gq",
        "policies/analytos.cedar",
        ".github/workflows/backend-container.yml",
    ]
    for filename in required_files:
        require((ROOT / filename).exists(), f"Missing required file: {filename}")

    contains(
        "Dockerfile.api",
        "ARG OMNIGRAPH_VERSION=0.8.1",
        "ARG TARGETARCH",
        "asset_arch=\"x86_64\"",
        "asset_arch=\"arm64\"",
        "/usr/local/bin/omnigraph",
        "/usr/local/bin/omnigraph-server",
        "omnigraph-server.bin",
        "exec /usr/local/bin/omnigraph-server.bin",
        "sha256sum",
        "OMNIGRAPH_BIN",
        "version",
        "--version",
        "OMNIGRAPH_SERVER_BIN",
    )
    contains(
        "scripts/start-hosted.sh",
        "OMNIGRAPH_SERVER_BIN",
        "ANALYTOS_START_OMNIGRAPH_SERVER",
        "cluster validate",
        "cluster plan",
        "cluster apply",
        "python -m uvicorn apps.api.main:app",
    )
    contains(".dockerignore", "omnigraph/graphs", "omnigraph/__cluster__", "data")

    importlib.import_module("apps.api.main")

    bash = shutil.which("bash")
    if bash:
        try:
            subprocess.run([bash, "-n", str(ROOT / "scripts" / "start-hosted.sh")], check=True)
            print("bash syntax: ok")
        except OSError as exc:
            print(f"bash syntax: skipped; bash could not start ({exc})")
    else:
        print("bash syntax: skipped; bash not found")

    print("container static verification: ok")


if __name__ == "__main__":
    main()
