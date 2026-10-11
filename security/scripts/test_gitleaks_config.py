#!/usr/bin/env python3
"""Fail unless Gitleaks detects the deliberately synthetic canary."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path


def main() -> int:
    executable = shutil.which("gitleaks")
    if executable is None:
        print("ERROR: gitleaks is not installed")
        return 2
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="gitleaks-self-test-") as temporary:
        report = Path(temporary) / "report.json"
        result = subprocess.run(
            [
                executable,
                "dir",
                "--no-banner",
                "--redact=100",
                "--config",
                str(root / "security/gitleaks-fixture.toml"),
                "--report-format",
                "json",
                "--report-path",
                str(report),
                str(root / "security/fixtures/secrets"),
            ],
            check=False,
        )
        if result.returncode != 1 or not report.exists():
            print(f"ERROR: expected finding exit 1, received {result.returncode}")
            return 2
        findings = json.loads(report.read_text(encoding="utf-8"))
        if not any(item.get("RuleID") == "synthetic-lab-api-key" for item in findings):
            print("ERROR: synthetic-lab-api-key finding was not reported")
            return 2
    print("PASS: Gitleaks detected the isolated synthetic canary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
