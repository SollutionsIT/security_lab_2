"""Run Gherkin checks against the explicit synthetic lab, never an external target."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    values = dotenv_values(ROOT / "tests/security/.env.example")
    environment = os.environ | {key: value for key, value in values.items() if value is not None}
    # Fixed project defaults deliberately override external target/identity overrides.
    environment["SECURITY_TEST_BASE_URL"] = "http://127.0.0.1:3001"
    environment.pop("PYTEST_ADDOPTS", None)
    report = ROOT / "reports/bdd/results.xml"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.unlink(missing_ok=True)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/bdd", f"--junitxml={report}"],
        cwd=ROOT,
        env=environment,
        timeout=300,
        check=False,
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
