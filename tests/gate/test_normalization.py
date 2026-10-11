import json
from datetime import date
from pathlib import Path

import pytest

from security.scripts.evaluate_security_gate import evaluate
from security.scripts.normalize_scanner import normalize


@pytest.mark.parametrize("scanner", ["semgrep", "trivy", "zap"])
def test_missing_scanner_collection_is_not_clean(scanner: str) -> None:
    with pytest.raises(ValueError):
        normalize(scanner, {})


def test_trivy_secret_findings_are_not_dropped() -> None:
    report = normalize(
        "trivy",
        {"Results": [{"Secrets": [{"RuleID": "synthetic-secret", "Severity": "CRITICAL"}]}]},
    )
    assert report["findings"][0]["id"] == "synthetic-secret"
    assert report["findings"][0]["validated"] is False


def test_semgrep_partial_error_is_failed_scan() -> None:
    report = normalize("semgrep", {"results": [], "errors": [{"type": "ParseError"}]})
    assert report["scanner"]["status"] == "failed"


@pytest.mark.parametrize(
    "report",
    [
        {"scanner": {"name": "test", "status": "success"}},
        {"scanner": {"status": "success"}, "findings": []},
        {"scanner": {"name": "test", "status": "success"}, "findings": [{}]},
    ],
)
def test_incomplete_gate_schema_is_error(tmp_path: Path, report: dict[str, object]) -> None:
    path = tmp_path / "report.json"
    path.write_text(json.dumps(report))
    assert evaluate([path], None, date(2026, 10, 11))[0] == "ERROR"


def test_empty_report_set_is_rejected() -> None:
    with pytest.raises(ValueError):
        evaluate([], None, date(2026, 10, 11))
