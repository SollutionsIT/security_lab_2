"""Publish only safe aggregate evidence, never raw tokens, logs or private paths."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from security.scripts.normalize_scanner import normalize  # noqa: E402
from security.scripts.portfolio_evidence import demo  # noqa: E402


def audit_summary(path: Path) -> dict[str, int]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    counts = raw["metadata"]["vulnerabilities"]
    keys = ("info", "low", "moderate", "high", "critical", "total")
    if not all(type(counts.get(key)) is int and counts[key] >= 0 for key in keys):
        raise ValueError("Audit counts must be non-negative integers")
    if sum(counts[key] for key in keys[:-1]) != counts["total"]:
        raise ValueError("Inconsistent audit totals")
    return {key: counts[key] for key in keys}


def suite_summary(path: Path) -> dict[str, Any]:
    cases = list(ET.parse(path).getroot().iter("testcase"))
    if not cases:
        raise ValueError("An empty test report is not verification evidence")
    suites: dict[str, dict[str, int]] = {}
    for case in cases:
        name = case.attrib.get("classname", "unknown")
        if not name.startswith("tests."):
            raise ValueError("Only known lab test modules may enter public evidence")
        counts = suites.setdefault(name, {"collected": 0, "passed": 0, "failed": 0, "skipped": 0})
        counts["collected"] += 1
        if case.find("failure") is not None or case.find("error") is not None:
            counts["failed"] += 1
        elif case.find("skipped") is not None:
            counts["skipped"] += 1
        else:
            counts["passed"] += 1
    return {
        "totals": {
            key: sum(counts[key] for counts in suites.values())
            for key in ("collected", "passed", "failed", "skipped")
        },
        "modules": suites,
    }


def build(
    root: Path = ROOT, *, demonstration: dict[str, Any], include_baseline: bool = True
) -> dict[str, Any]:
    inputs = {
        "current_full_audit": "reports/case-studies/npm-audit.json",
        "current_production_audit": "reports/case-studies/npm-audit-production.json",
        "api_junit": "reports/case-studies/api-security.xml",
        "gate_junit": "reports/case-studies/gate-tests.xml",
    }
    if include_baseline:
        inputs["retained_baseline_audit"] = "reports/portfolio/npm-audit.json"
    artifacts = {
        key: {"path": name, "sha256": hashlib.sha256((root / name).read_bytes()).hexdigest()}
        for key, name in inputs.items()
    }
    package = json.loads((root / "lab-api/package.json").read_text())
    try:
        normalize("semgrep", {})
    except ValueError:
        rejected = True
    else:
        rejected = False
    secret = normalize(
        "trivy",
        {
            "Results": [
                {"Secrets": [{"RuleID": "synthetic-evidence-canary", "Severity": "CRITICAL"}]}
            ]
        },
    )
    return {
        "schema_version": 1,
        "created_utc": datetime.now(UTC).isoformat(),
        "scope": "Synthetic loopback API; no real attacker, malware or production target",
        "python": platform.python_version(),
        "canonical_python": "3.13 (not validated by this compatibility run)",
        "baseline_note": (
            "Retained earlier audit; vulnerable dependency versions were not rerun"
            if include_baseline
            else "Historical baseline unavailable/omitted; no before-and-after comparison claimed"
        ),
        "audit": {
            "retained_baseline": (
                audit_summary(root / inputs["retained_baseline_audit"])
                if include_baseline
                else None
            ),
            "current_full": audit_summary(root / inputs["current_full_audit"]),
            "current_production": audit_summary(root / inputs["current_production_audit"]),
        },
        "versions": {
            key: package["dependencies"][key] for key in ("@nestjs/platform-express", "multer")
        },
        "api": suite_summary(root / inputs["api_junit"]),
        "gate": suite_summary(root / inputs["gate_junit"]),
        "ownership_demo": demonstration,
        "evidence_integrity_checks": {
            "missing_semgrep_collection_rejected": rejected,
            "trivy_secret_detection_retained": len(secret["findings"]) == 1,
            "note": "Synthetic parser inputs, not executed Semgrep/Trivy scans",
        },
        "artifacts": artifacts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--current-only", action="store_true", help="Explicitly omit the historical raw baseline"
    )
    args = parser.parse_args()
    try:
        data = build(demonstration=demo(), include_baseline=not args.current_only)
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        ET.ParseError,
        httpx.HTTPError,
        AssertionError,
    ) as error:
        print(f"ERROR: evidence collection failed ({type(error).__name__})", file=sys.stderr)
        return 2
    output = ROOT / "docs/evidence/case-studies-latest.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print("Sanitized case-study evidence written to docs/evidence/case-studies-latest.json")
    failed = (
        data["api"]["totals"]["failed"]
        or data["gate"]["totals"]["failed"]
        or data["api"]["totals"]["skipped"]
        or data["gate"]["totals"]["skipped"]
        or data["ownership_demo"].get("status") != "PASS"
    )
    return int(bool(failed))


if __name__ == "__main__":
    raise SystemExit(main())
