import json
from pathlib import Path

import pytest

from security.scripts.build_case_study_evidence import audit_summary, build, suite_summary


def test_audit_counts_are_not_unique_cve_claims(tmp_path: Path) -> None:
    report = tmp_path / "audit.json"
    report.write_text(
        json.dumps(
            {
                "metadata": {
                    "vulnerabilities": {
                        "info": 0,
                        "low": 0,
                        "moderate": 3,
                        "high": 5,
                        "critical": 2,
                        "total": 10,
                    }
                }
            }
        )
    )
    assert audit_summary(report)["total"] == 10


def test_inconsistent_audit_totals_are_rejected(tmp_path: Path) -> None:
    report = tmp_path / "audit.json"
    report.write_text(
        json.dumps(
            {
                "metadata": {
                    "vulnerabilities": {
                        "info": 0,
                        "low": 0,
                        "moderate": 0,
                        "high": 1,
                        "critical": 0,
                        "total": 0,
                    }
                }
            }
        )
    )
    with pytest.raises(ValueError):
        audit_summary(report)


def test_empty_junit_does_not_become_pass(tmp_path: Path) -> None:
    report = tmp_path / "test.xml"
    report.write_text("<testsuite/>")
    with pytest.raises(ValueError):
        suite_summary(report)


def test_junit_excludes_payloads_and_machine_paths(tmp_path: Path) -> None:
    report = tmp_path / "test.xml"
    report.write_text(
        '<testsuite><testcase classname="tests.security.test_demo" '
        'name="safe"><system-out>do not publish this</system-out></testcase>'
        '<testcase classname="tests.security.test_demo" name="failed">'
        "<failure>sensitive error content</failure></testcase></testsuite>"
    )
    summary = suite_summary(report)
    assert summary["totals"] == {"collected": 2, "passed": 1, "failed": 1, "skipped": 0}
    assert "sensitive" not in json.dumps(summary)
    assert "system-out" not in json.dumps(summary)


def test_fresh_clone_explicitly_omits_baseline(tmp_path: Path) -> None:
    reports = tmp_path / "reports/case-studies"
    reports.mkdir(parents=True)
    counts = {key: 0 for key in ("info", "low", "moderate", "high", "critical", "total")}
    audit = json.dumps({"metadata": {"vulnerabilities": counts}})
    for filename in ("npm-audit.json", "npm-audit-production.json"):
        (reports / filename).write_text(audit)
    for filename in ("api-security.xml", "gate-tests.xml"):
        (reports / filename).write_text(
            '<testsuite><testcase classname="tests.security.test_example" name="safe"/></testsuite>'
        )
    package = tmp_path / "lab-api/package.json"
    package.parent.mkdir()
    package.write_text(
        json.dumps({"dependencies": {"@nestjs/platform-express": "11.2.7", "multer": "2.4.0"}})
    )
    result = build(tmp_path, demonstration={"status": "PASS"}, include_baseline=False)
    assert result["audit"]["retained_baseline"] is None
    assert "retained_baseline_audit" not in result["artifacts"]
    assert "no before-and-after comparison" in result["baseline_note"]
    with pytest.raises(FileNotFoundError):
        build(tmp_path, demonstration={"status": "PASS"})
