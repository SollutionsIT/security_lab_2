import shutil
import struct
import subprocess
import tarfile
from pathlib import Path

import pytest

from security.scripts.publication_preflight import bundle, candidates, png_metadata, review

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True)
    shutil.copyfile(ROOT / ".gitignore", tmp_path / ".gitignore")
    return tmp_path


@pytest.mark.parametrize(
    "name",
    [
        ".env",
        "lab-api/.env.production",
        ".aws/credentials",
        ".ssh/id_ed25519",
        ".kube/config",
        ".docker/config.json",
        ".npmrc",
        ".netrc",
        "private/key.pem",
        "cert.pfx",
        "client.key",
        "service-account-prod.json",
        "secrets.yaml",
        "terraform.tfstate.backup",
        "production.tfvars",
        "backup.sql",
        "data.sqlite3",
        "capture.har",
        "reports/results.json",
        "screenshots/private.png",
        "notes.private.md",
        "guide.docx",
        "guide.pdf",
        "archive.zip",
        ".idea/workspace.xml",
        ".codex/history.json",
        ".venv/bin/python",
        "lab-api/node_modules/module.js",
        "lab-api/dist/main.js",
    ],
)
def test_sensitive_and_runtime_paths_are_ignored(repository: Path, name: str) -> None:
    result = subprocess.run(
        ["git", "-C", str(repository), "check-ignore", "--no-index", name],
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0


@pytest.mark.parametrize(
    "name",
    [
        ".gitignore",
        ".github/workflows/portfolio-native.yml",
        ".gitlab-ci.yml",
        "lab-api/.env.example",
        "tests/security/.env.example",
        "lab-api/package-lock.json",
        "kubernetes/base/secret.example.yaml",
        "security/fixtures/secrets/synthetic-detect.txt",
        "tests/security/fixtures/files/safe-document.pdf",
        "docs/assets/evidence-overview.png",
        "docs/15-interview-guide.md",
    ],
)
def test_required_public_files_remain_visible(repository: Path, name: str) -> None:
    result = subprocess.run(
        ["git", "-C", str(repository), "check-ignore", "--no-index", name],
        capture_output=True,
        check=False,
    )
    assert result.returncode == 1


def test_force_added_secret_is_rejected(repository: Path) -> None:
    (repository / ".env").write_text("JWT_SECRET=not-a-real-secret")
    subprocess.run(["git", "-C", str(repository), "add", "--force", ".env"], check=True)
    payload, issues = review(repository, candidates(repository))
    assert ".env" not in payload
    assert any("violates ignore policy" in issue for issue in issues)


def test_parent_git_repository_is_rejected(repository: Path) -> None:
    child = repository / "child"
    child.mkdir()
    with pytest.raises(ValueError, match="parent repository"):
        candidates(child)


def test_symlink_is_never_exported(repository: Path) -> None:
    (repository / "link.txt").symlink_to(ROOT / "README.md")
    payload, issues = review(repository, candidates(repository))
    assert "link.txt" not in payload
    assert any("linked file" in issue for issue in issues)


def test_png_metadata_and_malformed_chunks_are_detected() -> None:
    signature = b"\x89PNG\r\n\x1a\n"
    chunk = struct.pack(">I", 5) + b"tEXt" + b"test!" + bytes(4)
    assert png_metadata(signature + chunk)
    assert not png_metadata(signature + bytes(4) + b"IEND" + bytes(4))
    with pytest.raises(ValueError):
        png_metadata(signature + struct.pack(">I", 100) + b"IDAT" + bytes(4))


def test_new_binary_requires_manual_review(repository: Path) -> None:
    (repository / "asset.bin").write_bytes(b"\xff\x00")
    _, issues = review(repository, candidates(repository))
    assert any("unreviewed binary" in issue for issue in issues)


def test_bundle_strips_personal_metadata_and_refuses_overwrite(repository: Path) -> None:
    destination = bundle(repository, {"README.md": b"Synthetic lab"})
    with tarfile.open(destination) as archive:
        member = archive.getmembers()[0]
        assert member.name == "company-security-lab/README.md"
        assert member.uid == member.gid == member.mtime == 0
        assert not member.uname and not member.gname and not member.pax_headers
    with pytest.raises(FileExistsError):
        bundle(repository, {"README.md": b"Changed"})
