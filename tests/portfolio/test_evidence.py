import json
from pathlib import Path

import pytest

from security.scripts.portfolio_evidence import junit_counts, npm_counts, render
from security.scripts.publication_check import check, violations


def test_private_identifiers_are_denied() -> None:
    assert violations("README.md", "fy" + "lpi")
    assert violations(".private/notes.md", "safe")
    assert violations("tests/.env", "synthetic")
    assert not violations("tests/.env.example", "alice@example.test")


@pytest.mark.parametrize("path", ["/home/zap:rw", "/home/zap/.ZAP", "/ho" + "me/zap"])
def test_container_zap_home_is_not_a_personal_path(path: str) -> None:
    assert not violations("compose.yaml", path)


@pytest.mark.parametrize("path", ["/ho" + "me/person:rw", "/ho" + "me/zap-person/files"])
def test_other_home_paths_remain_private(path: str) -> None:
    assert violations("compose.yaml", path)


def test_missing_results_do_not_become_pass() -> None:
    assert "NOT RUN" in render({})
    assert "Demonstration: PASS" not in render({})


def test_report_escapes_untrusted_names() -> None:
    page = render(
        {"checks": [{"name": "<script>alert(1)</script>", "status": "ERROR", "seconds": 0}]}
    )
    assert "<script>" not in page
    assert "&lt;script&gt;" in page


def test_junit_counts_include_errors_and_skips(tmp_path: Path) -> None:
    xml = tmp_path / "suite.xml"
    xml.write_text(
        "<testsuite><testcase/><testcase><failure/></testcase>"
        "<testcase><error/></testcase><testcase><skipped/></testcase></testsuite>"
    )
    assert junit_counts(xml) == {"tests": 4, "failed": 2, "skipped": 1}
    assert junit_counts(tmp_path / "missing.xml") is None


def test_hygiene_excludes_runtime_only(tmp_path: Path) -> None:
    (tmp_path / "reports").mkdir()
    (tmp_path / "reports/local.log").write_text("fy" + "lpi")
    (tmp_path / "notes.private.md").write_text("local notes")
    assert len(check(tmp_path)) == 1


def test_npm_audit_preserves_valid_warning_counts() -> None:
    counts = {"info": 0, "low": 0, "moderate": 20, "high": 0, "critical": 0, "total": 20}
    assert npm_counts(json.dumps({"metadata": {"vulnerabilities": counts}})) == counts


@pytest.mark.parametrize(
    "counts",
    [[], {"total": 0}, {"info": 0, "low": 0, "moderate": 0, "high": 1, "critical": 0, "total": 0}],
)
def test_unusable_npm_audit_cannot_be_a_clean_result(counts: object) -> None:
    with pytest.raises(ValueError):
        npm_counts(json.dumps({"metadata": {"vulnerabilities": counts}}))
