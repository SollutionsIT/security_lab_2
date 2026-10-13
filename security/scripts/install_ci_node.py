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
VERSION = "24.21.0"
ARCHIVE = f"node-v{VERSION}-linux-x64.tar.xz"
SHA256 = "fd8e59d5a511510f6a298afb548f18c7d2b1be404d8b4a27d94fbe49f56cb2d6"


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
    print(f"Installed checksum-verified Node {VERSION} in .ci-runtime/node")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
