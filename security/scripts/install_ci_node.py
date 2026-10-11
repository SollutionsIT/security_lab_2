"""Install the checksum-pinned official Node runtime for Linux x86_64 GitLab jobs."""

from __future__ import annotations

import hashlib
import platform
import shutil
import tarfile
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERSION = "24.12.0"
ARCHIVE = f"node-v{VERSION}-linux-x64.tar.xz"
SHA256 = "bdebee276e58d0ef5448f3d5ac12c67daa963dd5e0a9bb621a53d1cefbc852fd"


def main() -> int:
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        raise RuntimeError("This GitLab bootstrap requires a Linux x86_64 container runner")
    destination = ROOT / ".ci-runtime/node"
    if destination.exists():
        raise RuntimeError("Refusing to overwrite an existing CI Node runtime")
    with tempfile.TemporaryDirectory(prefix="company-ci-node-") as temporary:
        directory = Path(temporary)
        archive = directory / ARCHIVE
        with urllib.request.urlopen(
            f"https://nodejs.org/dist/v{VERSION}/{ARCHIVE}", timeout=60
        ) as response:
            with archive.open("wb") as output:
                shutil.copyfileobj(response, output)
        if hashlib.sha256(archive.read_bytes()).hexdigest() != SHA256:
            raise ValueError("Official Node archive checksum mismatch")
        with tarfile.open(archive) as package:
            package.extractall(directory, filter="data")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(directory / f"node-v{VERSION}-linux-x64"), destination)
    print("Installed checksum-verified Node 24.12.0 in .ci-runtime/node")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
