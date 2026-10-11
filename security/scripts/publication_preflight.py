"""Review/export Git publication candidates, never Git history or ignored runtime data."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import shutil
import struct
import subprocess
import tarfile
import tempfile
from pathlib import Path

from security.scripts.publication_check import ROOT, violations

BINARY_ALLOWLIST = {
    "docs/assets/portfolio-hero.png",
    "docs/assets/evidence-overview.png",
    "docs/assets/access-control-demo.png",
    "tests/security/fixtures/files/safe-document.pdf",
}


def git(root: Path, *arguments: str, input_bytes: bytes | None = None) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(root), *arguments],
        input=input_bytes,
        capture_output=True,
        check=True,
    )
    return result.stdout


def candidates(root: Path) -> list[str]:
    if Path(git(root, "rev-parse", "--show-toplevel").decode().strip()).resolve() != root:
        raise ValueError("Refuse to export a parent repository; initialize standalone Git first")
    names = git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z")
    return sorted({name.decode("utf-8") for name in names.split(b"\0") if name})


def png_metadata(data: bytes) -> bool:
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("Invalid PNG signature")
    offset = 8
    while offset + 12 <= len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        if offset + 12 + length > len(data):
            raise ValueError("Truncated PNG chunk")
        if kind in {b"tEXt", b"zTXt", b"iTXt", b"eXIf"}:
            return True
        offset += length + 12
        if kind == b"IEND":
            return False
    raise ValueError("Missing PNG end chunk")


def review(root: Path, names: list[str]) -> tuple[dict[str, bytes], list[str]]:
    payload: dict[str, bytes] = {}
    issues: list[str] = []
    # --no-index also detects tracked/force-added files that .gitignore cannot protect.
    ignored = subprocess.run(
        ["git", "-C", str(root), "check-ignore", "--no-index", "-z", "--stdin"],
        input=b"\0".join(name.encode() for name in names) + b"\0",
        capture_output=True,
        check=False,
    )
    if ignored.returncode not in (0, 1):
        raise RuntimeError("Cannot evaluate ignore policy")
    forbidden = {name.decode() for name in ignored.stdout.split(b"\0") if name}
    for name in names:
        path = root / name
        if name in forbidden:
            issues.append(f"{name}: tracked or force-added file violates ignore policy")
            continue
        if (
            path.is_symlink()
            or not path.is_file()
            or not path.resolve().parent.is_relative_to(root)
        ):
            issues.append(f"{name}: missing, non-regular or linked file requires review")
            continue
        data = path.read_bytes()
        try:
            content = data.decode("utf-8")
            if b"\0" in data and name not in BINARY_ALLOWLIST:
                issues.append(f"{name}: unreviewed binary asset")
        except UnicodeDecodeError:
            content = ""
            if name not in BINARY_ALLOWLIST:
                issues.append(f"{name}: unreviewed binary asset")
        issues.extend(f"{name}: {issue}" for issue in violations(name, content))
        if name.endswith(".png"):
            if name not in BINARY_ALLOWLIST:
                issues.append(f"{name}: image pixels require explicit review")
            try:
                if png_metadata(data):
                    issues.append(f"{name}: PNG text or EXIF metadata requires removal/review")
            except ValueError:
                issues.append(f"{name}: invalid PNG")
        payload[name] = data
    return payload, issues


def scan_snapshot(payload: dict[str, bytes]) -> None:
    executable = shutil.which("gitleaks")
    if executable is None:
        raise RuntimeError("Gitleaks is required; no export without a real secret scan")
    with tempfile.TemporaryDirectory(prefix="company-publication-") as temporary:
        snapshot = Path(temporary)
        for name, data in payload.items():
            target = snapshot / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        result = subprocess.run(
            [
                executable,
                "dir",
                "--no-banner",
                "--redact=100",
                "--config",
                ".gitleaks.toml",
                ".",
            ],
            cwd=snapshot,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Publication snapshot secret scan failed (exit {result.returncode})"
            )


def bundle(root: Path, payload: dict[str, bytes]) -> Path:
    destination = root / "reports/publication/company-security-lab.tar.gz"
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Refuse overwrite: previously reviewed exports remain recoverable.
    with destination.open("xb") as stream, tarfile.open(fileobj=stream, mode="w:gz") as archive:
        for name, data in sorted(payload.items()):
            member = tarfile.TarInfo(f"company-security-lab/{name}")
            member.size = len(data)
            member.mode = 0o755 if name.endswith(".sh") else 0o644
            # No original ownership, personal paths, xattrs or timestamps.
            archive.addfile(member, io.BytesIO(data))
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", action="store_true")
    args = parser.parse_args()
    try:
        names = candidates(ROOT)
        if not names:
            raise ValueError("No publication candidates")
        payload, issues = review(ROOT, names)
        if issues:
            for issue in issues:
                print(issue)
            return 1
        scan_snapshot(payload)
        manifest = {
            "scope": "current working-tree candidates, not old history or staged blob contents",
            "file_count": len(payload),
            "files": [
                {"path": name, "sha256": hashlib.sha256(data).hexdigest()}
                for name, data in payload.items()
            ],
        }
        report = ROOT / "reports/publication/manifest.json"
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(manifest, indent=2) + "\n")
        if args.bundle:
            destination = bundle(ROOT, payload)
            print(f"Export: {destination.relative_to(ROOT)}")
        print(
            f"Publication preflight: PASS ({len(payload)} working-tree files; secret scan passed)"
        )
        print(
            "Manual review of image pixels, business data and final staged diff remains required."
        )
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError):
        # Never echo Git output, secret matches or personal absolute paths.
        print("Publication preflight: ERROR; check standalone Git, Gitleaks and export destination")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
