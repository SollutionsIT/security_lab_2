"""Run local checks and render escaped, screenshot-ready factual evidence."""

from __future__ import annotations

import argparse
import html
import json
import os
import platform
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "reports" / "portfolio"


def junit_counts(path: Path) -> dict[str, int] | None:
    if not path.exists():
        return None
    cases = list(ET.parse(path).getroot().iter("testcase"))
    return {
        "tests": len(cases),
        "failed": sum(c.find("failure") is not None or c.find("error") is not None for c in cases),
        "skipped": sum(c.find("skipped") is not None for c in cases),
    }


def demo() -> dict[str, Any]:
    sys.path.insert(0, str(ROOT))
    from dotenv import dotenv_values

    from tests.security.clients.lab_api import LabApiClient
    from tests.security.config import SecurityTestSettings
    from tests.security.fixtures.identities import IdentityCatalog
    from tests.security.fixtures.state import SeedResources, event_list, property_from_state

    values = dotenv_values(ROOT / "tests/security/.env.example")
    previous = {key: os.environ.get(key) for key in values}
    os.environ.update({key: value for key, value in values.items() if value is not None})
    try:
        settings = SecurityTestSettings()  # type: ignore[call-arg]
        identities = IdentityCatalog.from_settings(settings)
        with LabApiClient(settings) as api:
            api.reset()
            resource = SeedResources.from_state(api.state()).user_a.property_id
            user_a, user_b = api.login(identities.user_a), api.login(identities.user_b)
            before = property_from_state(api.state(), str(resource))
            own = api.request("GET", f"/properties/{resource}", token=user_a)
            cross = api.request("GET", f"/properties/{resource}", token=user_b)
            change = api.request(
                "PATCH",
                f"/properties/{resource}",
                token=user_b,
                headers={"X-Correlation-ID": "portfolio-denied-change"},
                json={"title": "Unauthorized change"},
            )
            unchanged = before == property_from_state(api.state(), str(resource))
            correlated = any(
                e.get("correlation_id") == "portfolio-denied-change" for e in event_list(api.logs())
            )
            rows = [
                {"action": "Owner reads own resource", "actual": own.status_code, "expected": 200},
                {
                    "action": "Other user reads resource",
                    "actual": cross.status_code,
                    "expected": 404,
                },
                {
                    "action": "Other user changes resource",
                    "actual": change.status_code,
                    "expected": 404,
                },
                {"action": "Original state unchanged", "actual": unchanged, "expected": True},
                {
                    "action": "Correlated denial event retained",
                    "actual": correlated,
                    "expected": True,
                },
            ]
            return {
                "status": "PASS" if all(r["actual"] == r["expected"] for r in rows) else "FAIL",
                "checks": rows,
            }
    finally:
        for key, old in previous.items():
            if old is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old


def npm_counts(stdout: str) -> dict[str, int]:
    counts = json.loads(stdout)["metadata"]["vulnerabilities"]
    keys = ("info", "low", "moderate", "high", "critical", "total")
    if not isinstance(counts, dict):
        raise ValueError("Invalid npm audit counts collection")
    if not all(type(counts.get(key)) is int and counts[key] >= 0 for key in keys):
        raise ValueError("Invalid npm audit counts")
    if sum(counts[key] for key in keys[:-1]) != counts["total"]:
        raise ValueError("Inconsistent npm audit totals")
    return {key: counts[key] for key in keys}


def run_checks(*, extended: bool = False, ci: bool = False) -> dict[str, Any]:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    commands = [
        ("TypeScript typecheck", ["npm", "--prefix", "lab-api", "run", "typecheck"]),
        ("NestJS build", ["npm", "--prefix", "lab-api", "run", "build"]),
        (
            "Jest / Supertest",
            [
                "npm",
                "--prefix",
                "lab-api",
                "test",
                "--",
                "--runInBand",
                "--json",
                "--outputFile=../reports/portfolio/jest.json",
            ],
        ),
        (
            "Python lint",
            [
                sys.executable,
                "-m",
                "ruff",
                "check",
                "tests/security",
                "tests/gate",
                "tests/portfolio",
                "tests/bdd",
                "security/scripts",
            ],
        ),
        (
            "Python typecheck",
            [sys.executable, "-m", "mypy", "tests/security", "tests/bdd", "security/scripts"],
        ),
        (
            "Gate and evidence tests",
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/gate",
                "tests/portfolio",
                "--junitxml=reports/portfolio/gate.xml",
            ],
        ),
        (
            "API security regressions",
            [
                "env",
                "PYTEST_ADDOPTS=--junitxml=reports/portfolio/api.xml",
                "make",
                "security-test",
                "PY=.venv/bin/python",
            ],
        ),
        ("Gate decision contract", ["make", "gate", "PY=.venv/bin/python"]),
        ("Publication hygiene", [sys.executable, "security/scripts/publication_check.py"]),
    ]
    if ci:
        commands.extend(
            [
                ("Gherkin acceptance scenarios", [sys.executable, "security/scripts/run_bdd.py"]),
                (
                    "npm audit (high threshold)",
                    ["npm", "--prefix", "lab-api", "audit", "--audit-level=high", "--json"],
                ),
                (
                    "npm audit production (high threshold)",
                    [
                        "npm",
                        "--prefix",
                        "lab-api",
                        "audit",
                        "--omit=dev",
                        "--audit-level=high",
                        "--json",
                    ],
                ),
            ]
        )
    if extended:
        commands.extend(
            [
                (
                    "npm audit (high threshold)",
                    ["npm", "--prefix", "lab-api", "audit", "--audit-level=high", "--json"],
                ),
                (
                    "Gitleaks distributable tree",
                    [
                        "gitleaks",
                        "dir",
                        "--no-banner",
                        "--redact",
                        "--config",
                        ".gitleaks.toml",
                        ".",
                    ],
                ),
                (
                    "Gitleaks synthetic detection canary",
                    [sys.executable, "security/scripts/test_gitleaks_config.py"],
                ),
            ]
        )
    audit_counts: dict[str, Any] | None = None
    production_counts: dict[str, Any] | None = None
    checks: list[dict[str, Any]] = []
    for index, (label, command) in enumerate(commands):
        start = time.monotonic()
        print(f"Running: {label}", flush=True)
        try:
            completed = subprocess.run(
                command, cwd=ROOT, capture_output=True, text=True, timeout=240, check=False
            )
            log = completed.stdout + completed.stderr
            status = "PASS" if completed.returncode == 0 else "FAIL"
            code: int | None = completed.returncode
            if label.startswith("npm audit"):
                try:
                    counts = npm_counts(completed.stdout)
                    if label.startswith("npm audit production"):
                        production_counts = counts
                        name = "npm-audit-production-current.json"
                    else:
                        audit_counts = counts
                        name = "npm-audit-current.json"
                    (OUTPUT / name).write_text(completed.stdout, encoding="utf-8")
                    if completed.returncode not in {0, 1}:
                        status = "ERROR"
                    elif counts["high"] or counts["critical"]:
                        status = "FAIL"
                    elif completed.returncode != 0:
                        status = "ERROR"
                    elif counts["total"]:
                        status = "WARN"
                except (ValueError, KeyError, TypeError):
                    status = "ERROR"
        except (OSError, subprocess.TimeoutExpired) as error:
            status, code, log = "ERROR", None, type(error).__name__
        log = log.replace(str(ROOT), "<repo>").replace(str(Path.home()), "<home>")
        (OUTPUT / f"check-{index}.log").write_text(log, encoding="utf-8")
        checks.append(
            {
                "name": label,
                "status": status,
                "exit_code": code,
                "seconds": round(time.monotonic() - start, 2),
            }
        )
        print(f"{label}: {status}", flush=True)
    try:
        demonstration = demo()
    except Exception as error:
        demonstration = {"status": "ERROR", "error": type(error).__name__, "checks": []}
    data: dict[str, Any] = {
        "created_utc": datetime.now(UTC).isoformat(),
        "python": platform.python_version(),
        "checks": checks,
        "demo": demonstration,
        "api_tests": junit_counts(OUTPUT / "api.xml"),
        "gate_tests": junit_counts(OUTPUT / "gate.xml"),
        "npm_audit": audit_counts,
        "npm_audit_production": production_counts,
        "bdd_tests": junit_counts(ROOT / "reports/bdd/results.xml") if ci else None,
        "jest": None,
        "not_executed": (
            ["Gitleaks (separate CI job)"]
            if ci and not extended
            else ["npm audit / Gitleaks"]
            if not extended
            else []
        )
        + [
            "Docker / Kubernetes runtime",
            "Trivy / Syft",
            "Semgrep / CodeQL",
            "ZAP",
            "Remote CI",
            "Production / real providers",
        ],
    }
    if (OUTPUT / "jest.json").exists():
        parsed = json.loads((OUTPUT / "jest.json").read_text())
        data["jest"] = {
            key: parsed.get(key)
            for key in ("numTotalTests", "numPassedTests", "numFailedTests", "numPendingTests")
        }
    (OUTPUT / "summary.json").write_text(json.dumps(data, indent=2) + "\n")
    return data


def render(data: dict[str, Any]) -> str:
    def escape(value: object) -> str:
        return html.escape(str(value), quote=True)

    rows = "".join(
        f"<tr><td>{escape(c['name'])}</td><td>{escape(c['status'])}</td>"
        f"<td>{escape(c['seconds'])}s</td></tr>"
        for c in data.get("checks", [])
    )
    d = data.get("demo", {})
    demo_rows = "".join(
        f"<tr><td>{escape(r['action'])}</td><td>{escape(r['expected'])}</td>"
        f"<td>{escape(r['actual'])}</td></tr>"
        for r in d.get("checks", [])
    )

    def stats(key: str) -> str:
        counts = data.get(key)
        if not counts:
            return "NOT RUN / evidence unavailable"
        if key == "jest":
            total = counts.get("numTotalTests", 0)
            failed = counts.get("numFailedTests", 0)
            skipped = counts.get("numPendingTests", 0)
        else:
            total, failed, skipped = counts["tests"], counts["failed"], counts["skipped"]
        return (
            f"{total - failed - skipped} passed / {total} collected\n"
            f"{failed} failed · {skipped} skipped"
        )

    cards = "".join(
        f"<div class='card'><h3>{escape(label)}</h3><pre>{escape(stats(key))}</pre></div>"
        for label, key in [
            ("Jest / Supertest", "jest"),
            ("API regressions", "api_tests"),
            ("Gate + evidence", "gate_tests"),
        ]
    )
    audit = ("npm advisory counts: " + escape(data["npm_audit"])) if data.get("npm_audit") else ""
    return f"""<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>COMPANY Security Lab — local evidence</title><style>
*{{box-sizing:border-box}}body{{margin:0;color:#eef1ff;font:17px/1.5 system-ui;
padding:44px;background:#080e27;background-image:radial-gradient(ellipse at 0 0,
#4e2b8760,transparent 65%),radial-gradient(ellipse at 100% 40%,#195ccf55,transparent 55%)}}
main{{max-width:1180px;margin:auto}}h1{{font-size:40px;margin:6px 0 8px}}h2{{font-size:27px}}
h3{{margin-top:0}}.eyebrow{{color:#aeb6ff;letter-spacing:3px}}.glass,.card{{background:#ffffff09;
border:1px solid #98a9ff36;border-radius:22px;padding:26px;
backdrop-filter:blur(15px);margin:24px 0}}
.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}}.card{{margin:0;padding:20px}}
table{{border-collapse:collapse;width:100%}}td,th{{text-align:left;padding:10px;
border-bottom:1px solid #ffffff16}}th{{color:#aebcff}}
pre{{white-space:pre-wrap;font:14px/1.6 monospace}}
.note{{color:#b9c1dd;font-size:15px}}.badge{{display:inline-block;border:1px solid #949cff77;
border-radius:40px;padding:5px 15px;color:#ccd6ff}}footer{{font-size:14px;color:#aeb7d8}}
</style><main><section id="overview"><div class="eyebrow">SOLLUTIONS / ENGINEERING EVIDENCE</div>
<h1>COMPANY Security Lab</h1><p>From a security assumption to a tested control.</p>
<span class="badge">Actual local execution · synthetic data only</span>
<p class="note">UTC: {escape(data.get("created_utc", "unknown"))} · Python
{escape(data.get("python", "unknown"))}. Canonical CI target: Python 3.13.
This run does not certify production readiness.</p><div class="grid">{cards}</div>
<div class="glass"><h2>Verification ledger</h2><table><tr><th>Check</th><th>Result</th>
<th>Elapsed</th></tr>{rows}</table><p class="note">{audit}</p></div></section>
<div class="glass"><h2>Gherkin acceptance evidence</h2>
<pre>{escape(data.get("bdd_tests") or "NOT RUN")}</pre>
<p class="note">Business-readable scenarios execute real local HTTP and the policy CLI.
They complement—not replace—the full API regression matrix.</p></div>
<section class="glass" id="demo"><div class="eyebrow">BUSINESS RISK / ACCESS CONTROL</div>
<h2>Can one customer change another customer's data?</h2>
<p>Two synthetic users, one owned resource, real local HTTP requests.</p>
<p class="badge">Demonstration: {escape(d.get("status", "NOT RUN"))}</p>
<table><tr><th>Action / observation</th><th>Expected</th><th>Actual</th></tr>{demo_rows}</table>
<p class="note">404 conceals resource existence. Verify both denial and unchanged state.
Correlation IDs link the denial to a redacted event. No tokens or credentials are displayed.</p>
</section><div class="glass"><h2>Scope and limitations</h2><p>Not executed by this runner:
{escape(", ".join(data.get("not_executed", [])))}</p><p class="note">Scanners and cloud/CI
deployment need separate evidence. No customer data, financial savings or certification claim.</p>
</div><footer>Source-available · non-commercial evaluation · Sollutions</footer></main></html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render-only", action="store_true")
    parser.add_argument(
        "--ci",
        action="store_true",
        help="Also execute Gherkin and full/production dependency gates",
    )
    parser.add_argument(
        "--extended",
        action="store_true",
        help="Also run installed Gitleaks and npm audit (requires network)",
    )
    args = parser.parse_args()
    if args.render_only:
        data = json.loads((OUTPUT / "summary.json").read_text())
    else:
        OUTPUT.mkdir(parents=True, exist_ok=True)
        for name in (
            "api.xml",
            "gate.xml",
            "jest.json",
            "summary.json",
            "index.html",
            "npm-audit-current.json",
            "npm-audit-production-current.json",
        ):
            (OUTPUT / name).unlink(missing_ok=True)
        data = run_checks(extended=args.extended, ci=args.ci)
    (OUTPUT / "index.html").write_text(render(data), encoding="utf-8")
    print("Evidence written to reports/portfolio/index.html")
    return int(
        any(c["status"] not in {"PASS", "WARN"} for c in data.get("checks", []))
        or data.get("demo", {}).get("status") != "PASS"
    )


if __name__ == "__main__":
    raise SystemExit(main())
