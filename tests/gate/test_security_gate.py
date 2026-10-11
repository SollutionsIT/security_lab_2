from __future__ import annotations

from datetime import date
from pathlib import Path

from security.scripts.evaluate_security_gate import evaluate

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "security/fixtures/gate"


def test_gate_states_are_distinct() -> None:
    for name, expected in (
        ("pass", "PASS"),
        ("warn", "WARN"),
        ("fail", "FAIL"),
        ("error", "ERROR"),
    ):
        result, _, _ = evaluate([FIXTURES / f"{name}.json"], None, date(2026, 8, 16))
        assert result == expected


def test_active_exception_downgrades_fail_but_expired_exception_does_not(
    tmp_path: Path,
) -> None:
    report = FIXTURES / "fail.json"
    exception = tmp_path / "exceptions.yaml"
    exception.write_text(
        """version: 1
exceptions:
  - finding_id: SYNTH-SECRET-001
    scanner: gitleaks
    rationale: Synthetic gate-unit-test exception.
    compensating_controls: [Repository access is restricted during the test.]
    owner: owner@example.test
    reviewer: reviewer@example.test
    expires: 2026-09-30
    scope: synthetic fixture only
""",
        encoding="utf-8",
    )
    active, _, _ = evaluate([report], exception, date(2026, 8, 16))
    expired, _, notes = evaluate([report], exception, date(2026, 10, 1))
    assert active == "WARN"
    assert expired == "FAIL"
    assert notes == ["expired exception ignored: gitleaks/SYNTH-SECRET-001"]
