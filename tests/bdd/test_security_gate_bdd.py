from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from pytest_bdd import given, parsers, scenarios, then, when

ROOT = Path(__file__).resolve().parents[2]
scenarios("features/security_gate.feature")


@given(parsers.parse('the normalized "{fixture}" policy report'), target_fixture="report")
def policy_report(fixture: str) -> Path:
    assert fixture in {"pass", "warn", "fail", "error"}
    return ROOT / "security/fixtures/gate" / f"{fixture}.json"


@when("the security gate evaluates the report", target_fixture="decision")
def evaluate_report(report: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "security/scripts/evaluate_security_gate.py", str(report)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=10,
        check=False,
    )


@then(parsers.parse('the gate result is "{result}" with exit code {exit_code:d}'))
def gate_result(decision: subprocess.CompletedProcess[str], result: str, exit_code: int) -> None:
    assert decision.returncode == exit_code
    assert decision.stdout.splitlines()[0] == result
