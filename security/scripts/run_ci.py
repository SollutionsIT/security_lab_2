"""Own the native lab lifecycle for the same verification command on both CI providers."""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import httpx
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[2]


def assert_free_port() -> None:
    try:
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 3001))
    except OSError as error:
        raise RuntimeError(
            "Loopback port 3001 is unavailable; do not reuse or stop its owner"
        ) from error


def lab_environment(environment: Mapping[str, str]) -> dict[str, str]:
    sample = dotenv_values(ROOT / "tests/security/.env.example")
    required = {
        "JWT_SECRET": "SECURITY_TEST_JWT_SECRET",
        "JWT_ISSUER": "SECURITY_TEST_JWT_ISSUER",
        "JWT_AUDIENCE": "SECURITY_TEST_JWT_AUDIENCE",
        "SYNTHETIC_WEBHOOK_SECRET": "SECURITY_TEST_WEBHOOK_SECRET",
        "LAB_TEST_KEY": "SECURITY_TEST_LAB_TEST_KEY",
    }
    result = dict(environment)
    result.update(NODE_ENV="test", HOST="127.0.0.1", PORT="3001", LAB_TEST_MODE="true")
    for key, source in required.items():
        value = sample.get(source)
        if not value:
            raise ValueError(f"Missing synthetic sample field: {source}")
        result[key] = value
    return result


def wait_ready(process: subprocess.Popen[Any], *, timeout: float = 30) -> None:
    deadline = time.monotonic() + timeout
    with httpx.Client(timeout=1, follow_redirects=False, trust_env=False) as client:
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError("Owned lab process exited before readiness")
            try:
                response = client.get("http://127.0.0.1:3001/health")
                if response.status_code == 200 and response.json() == {
                    "status": "ok",
                    "service": "company-security-lab-api",
                }:
                    return
            except (httpx.HTTPError, ValueError):
                pass
            time.sleep(0.1)
    raise RuntimeError("Owned lab readiness timed out")


def stop_owned(process: subprocess.Popen[Any]) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def main() -> int:
    process: subprocess.Popen[bytes] | None = None
    output = ROOT / "reports/ci"
    output.mkdir(parents=True, exist_ok=True)
    # Remove only the previous gate marker, never another run's raw baseline.
    marker = output / "result.txt"
    marker.unlink(missing_ok=True)
    try:
        assert_free_port()
        build = subprocess.run(
            ["npm", "--prefix", "lab-api", "run", "build"], cwd=ROOT, timeout=180, check=False
        )
        if build.returncode:
            marker.write_text("FAIL: prerequisite build\n")
            return 1
        with (output / "lab.log").open("wb") as log:
            process = subprocess.Popen(
                ["node", "dist/main.js"],
                cwd=ROOT / "lab-api",
                env=lab_environment(os.environ),
                stdout=log,
                stderr=subprocess.STDOUT,
            )
            try:
                wait_ready(process)
                result = subprocess.run(
                    [sys.executable, "security/scripts/portfolio_evidence.py", "--ci"],
                    cwd=ROOT,
                    timeout=1800,
                    check=False,
                )
                marker.write_text("PASS_OR_WARN\n" if result.returncode == 0 else "FAIL_OR_ERROR\n")
                return result.returncode
            finally:
                stop_owned(process)
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
        marker.write_text(f"ERROR: {type(error).__name__}\n")
        print(f"ERROR: CI lifecycle failed ({type(error).__name__})", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
