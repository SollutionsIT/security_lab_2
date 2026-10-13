import hashlib
import io
import tarfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from security.scripts.install_ci_scanner import SCANNERS, binary_from_archive, install
from security.scripts.test_semgrep_config import materialize

ROOT = Path(__file__).resolve().parents[2]


def package(*, symlink: bool = False) -> bytes:
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w:gz") as archive:
        member = tarfile.TarInfo("gitleaks")
        if symlink:
            member.type = tarfile.SYMTYPE
            member.linkname = "../../outside"
            archive.addfile(member)
        else:
            member.size = 6
            archive.addfile(member, io.BytesIO(b"binary"))
    return stream.getvalue()


def test_checksum_is_required_before_using_archive() -> None:
    with pytest.raises(ValueError, match="checksum"):
        binary_from_archive(b"untrusted", "0" * 64, "gitleaks")


def test_only_the_named_regular_binary_is_returned() -> None:
    data = package()
    assert binary_from_archive(data, hashlib.sha256(data).hexdigest(), "gitleaks") == b"binary"


def test_linked_archive_members_are_rejected() -> None:
    data = package(symlink=True)
    with pytest.raises(ValueError, match="regular"):
        binary_from_archive(data, hashlib.sha256(data).hexdigest(), "gitleaks")


def test_bootstrap_rejects_wrong_platform_before_network(tmp_path: Path) -> None:
    with patch("security.scripts.install_ci_scanner.platform.system", return_value="Darwin"):
        with patch("security.scripts.install_ci_scanner.urllib.request.urlopen") as download:
            with pytest.raises(RuntimeError, match="Linux"):
                install("gitleaks", tmp_path)
            download.assert_not_called()


def test_bootstrap_does_not_overwrite_runtime(tmp_path: Path) -> None:
    (tmp_path / ".ci-runtime/gitleaks").mkdir(parents=True)
    with patch("security.scripts.install_ci_scanner.platform.system", return_value="Linux"):
        with patch("security.scripts.install_ci_scanner.platform.machine", return_value="x86_64"):
            with pytest.raises(RuntimeError, match="existing"):
                install("gitleaks", tmp_path)


def test_publisher_release_digests_are_explicit() -> None:
    for name, (version, url, digest) in SCANNERS.items():
        assert url.startswith("https://github.com/")
        assert f"/v{version}/" in url
        assert name in url
        assert len(digest) == 64 and set(digest) <= set("0123456789abcdef")


def test_zap_has_bounded_writable_home_without_writable_root() -> None:
    zap = yaml.safe_load((ROOT / "compose.yaml").read_text())["services"]["zap"]
    assert zap["read_only"] is True
    assert zap["cap_drop"] == ["ALL"]
    assert zap["user"] == "${ZAP_UID:-1000}:${ZAP_GID:-1000}"
    assert zap["mem_limit"] == "3g"
    assert zap["environment"]["JAVA_TOOL_OPTIONS"] == "-Xmx1024m -Duser.home=/home/zap"
    assert any(
        mount.startswith("/home/zap:rw,") and "uid=${ZAP_UID:-1000}" in mount
        for mount in zap["tmpfs"]
    )


def test_runtime_removes_unused_npm_without_modifying_build_stage() -> None:
    dockerfile = (ROOT / "lab-api/Dockerfile").read_text()
    build, runtime = dockerfile.split(" AS runtime", 1)
    assert "npm ci --ignore-scripts" in build
    assert "rm -r /usr/local/lib/node_modules/npm" in runtime
    assert "USER 1000:1000" in runtime
    assert 'CMD ["node", "dist/main.js"]' in runtime


def test_scanner_workflows_do_not_hide_failures() -> None:
    pr = yaml.safe_load((ROOT / ".github/workflows/pr-security.yml").read_text())
    for name in ("secrets", "sast", "iac-and-filesystem"):
        job = pr["jobs"][name]
        assert not job.get("continue-on-error", False)
        assert not any(step.get("continue-on-error", False) for step in job["steps"])
    secret_steps = pr["jobs"]["secrets"]["steps"]
    assert any("--log-opts=--all" in step.get("run", "") for step in secret_steps)
    assert any("test_gitleaks_config.py" in step.get("run", "") for step in secret_steps)
    sast_steps = pr["jobs"]["sast"]["steps"]
    assert any("--error" in step.get("run", "") for step in sast_steps)
    deep = yaml.safe_load((ROOT / ".github/workflows/deep-security.yml").read_text())
    assert deep["jobs"]["codeql"]["permissions"]["actions"] == "read"
    assert deep["jobs"]["codeql"]["if"] == "github.event.repository.private == false"


def test_semgrep_fixture_layout_covers_every_rule(tmp_path: Path) -> None:
    identifiers = materialize(ROOT, tmp_path)
    assert len(identifiers) == 4
    assert (tmp_path / "cases.yml").read_bytes() == (ROOT / "semgrep.yml").read_bytes()
    source = (tmp_path / "cases.ts").read_text()
    assert all(
        f"// ruleid: {rule}" in source and f"// ok: {rule}" in source for rule in identifiers
    )


def test_semgrep_fixture_layout_rejects_missing_negative_case(tmp_path: Path) -> None:
    root = tmp_path / "source"
    (root / "security/semgrep").mkdir(parents=True)
    (root / "semgrep.yml").write_text("rules:\n  - id: missing-negative\n")
    (root / "security/semgrep/case.ts").write_text("// ruleid: missing-negative\nunsafe();\n")
    with pytest.raises(ValueError, match="positive and negative"):
        materialize(root, tmp_path)
