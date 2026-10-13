"""Install official, checksum-pinned scanner binaries on Linux x86_64 CI runners."""

from __future__ import annotations

import argparse
import hashlib
import io
import platform
import tarfile
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# Publisher GitHub release asset digests inspected on 2026-10-13.
SCANNERS = {
    "gitleaks": (
        "8.30.1",
        "https://github.com/gitleaks/gitleaks/releases/download/v8.30.1/"
        "gitleaks_8.30.1_linux_x64.tar.gz",
        "551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb",
    ),
    "trivy": (
        "0.75.0",
        "https://github.com/aquasecurity/trivy/releases/download/v0.75.0/"
        "trivy_0.75.0_Linux-64bit.tar.gz",
        "c6e65abddb348e25f10549df887045629cf28cc72453cd1c63acb717316b3f3f",
    ),
}
MAX_ARCHIVE_BYTES = 128 * 1024 * 1024
MAX_BINARY_BYTES = 512 * 1024 * 1024


def binary_from_archive(data: bytes, checksum: str, name: str) -> bytes:
    if hashlib.sha256(data).hexdigest() != checksum:
        raise ValueError("Publisher archive checksum mismatch")
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        member = archive.getmember(name)
        if not member.isfile() or member.size > MAX_BINARY_BYTES:
            raise ValueError("Scanner must be a bounded regular archive member")
        stream = archive.extractfile(member)
        if stream is None:
            raise ValueError("Scanner archive member missing")
        return stream.read()


def install(name: str, root: Path = ROOT) -> Path:
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        raise RuntimeError("Scanner bootstrap requires Linux x86_64")
    version, url, checksum = SCANNERS[name]
    runtime = root / ".ci-runtime"
    destination = runtime / name
    if runtime.is_symlink() or destination.exists() or destination.is_symlink():
        raise RuntimeError("Refusing linked or existing scanner runtime")
    request = urllib.request.Request(url, headers={"User-Agent": "COMPANY-security-lab-CI"})
    with urllib.request.urlopen(request, timeout=60) as response:
        data = response.read(MAX_ARCHIVE_BYTES + 1)
    if len(data) > MAX_ARCHIVE_BYTES:
        raise ValueError("Scanner archive exceeds the size limit")
    binary = binary_from_archive(data, checksum, name)
    runtime.mkdir(exist_ok=True)
    # Create privately, then move the complete binary into its final location.
    with tempfile.TemporaryDirectory(prefix=f".{name}-", dir=runtime) as temporary:
        candidate = Path(temporary) / name
        candidate.write_bytes(binary)
        candidate.chmod(0o755)
        Path(temporary).rename(destination)
    print(f"Installed checksum-verified {name} {version}")
    return destination / name


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scanner", choices=SCANNERS)
    args = parser.parse_args()
    install(args.scanner)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
