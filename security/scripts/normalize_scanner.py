#!/usr/bin/env python3
"""Normalize supported scanner JSON without upgrading detections to confirmed issues."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _semgrep(data: dict[str, Any]) -> list[dict[str, Any]]:
    severity = {"ERROR": "HIGH", "WARNING": "MEDIUM", "INFO": "LOW"}
    return [
        {
            "id": item.get("check_id", "semgrep-unknown"),
            "severity": severity.get(item.get("extra", {}).get("severity"), "UNKNOWN"),
            "confidence": item.get("extra", {}).get("metadata", {}).get("confidence", "medium"),
            "validated": False,
            "new": True,
        }
        for item in data.get("results", [])
    ]


def _trivy(data: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for result in data.get("Results", []):
        for item in result.get("Vulnerabilities") or []:
            findings.append(
                {
                    "id": item.get("VulnerabilityID", "trivy-vulnerability-unknown"),
                    "severity": item.get("Severity", "UNKNOWN"),
                    "confidence": "medium",
                    "validated": False,
                    "reachable": False,
                    "fix_available": bool(item.get("FixedVersion")),
                    "new": True,
                }
            )
        for item in result.get("Misconfigurations") or []:
            findings.append(
                {
                    "id": item.get("ID", "trivy-misconfiguration-unknown"),
                    "severity": item.get("Severity", "UNKNOWN"),
                    "confidence": "medium",
                    "validated": False,
                    "policy_violation": False,
                    "new": True,
                }
            )
        for item in result.get("Secrets") or []:
            findings.append(
                {
                    "id": item.get("RuleID", "trivy-secret-unknown"),
                    "severity": item.get("Severity", "UNKNOWN"),
                    "confidence": "medium",
                    "validated": False,
                    "verified_credential": False,
                    "new": True,
                }
            )
    return findings


def _gitleaks(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": item.get("RuleID", "gitleaks-unknown"),
            "severity": "CRITICAL",
            "confidence": "medium",
            "validated": False,
            "verified_credential": False,
            "new": True,
        }
        for item in data
    ]


def _zap(data: dict[str, Any]) -> list[dict[str, Any]]:
    severity = {"0": "UNKNOWN", "1": "LOW", "2": "MEDIUM", "3": "HIGH"}
    findings: list[dict[str, Any]] = []
    for site in data.get("site", []):
        for item in site.get("alerts", []):
            findings.append(
                {
                    "id": f"ZAP-{item.get('pluginid', 'unknown')}",
                    "severity": severity.get(str(item.get("riskcode", "0")), "UNKNOWN"),
                    "confidence": "medium",
                    "validated": False,
                    "new": True,
                }
            )
    return findings


def normalize(scanner: str, raw: object, *, scanner_failed: bool = False) -> dict[str, Any]:
    if scanner == "gitleaks":
        if not isinstance(raw, list) or not all(isinstance(item, dict) for item in raw):
            raise ValueError("Gitleaks report must be a list of objects")
        findings = _gitleaks(raw)
    else:
        if not isinstance(raw, dict):
            raise ValueError("Scanner report must be an object")
        field = {"semgrep": "results", "trivy": "Results", "zap": "site"}.get(scanner)
        if field is None:
            raise ValueError("Unsupported scanner")
        if field not in raw or not isinstance(raw[field], list):
            raise ValueError(f"Scanner report requires a {field} list")
        if not all(isinstance(item, dict) for item in raw[field]):
            raise ValueError("Scanner entries must be objects")
        if scanner == "semgrep" and raw.get("errors"):
            scanner_failed = True
        findings = {"semgrep": _semgrep, "trivy": _trivy, "zap": _zap}[scanner](raw)
    return {
        "scanner": {"name": scanner, "status": "failed" if scanner_failed else "success"},
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("scanner", choices=["semgrep", "trivy", "gitleaks", "zap"])
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--scanner-failed", action="store_true")
    args = parser.parse_args()
    try:
        raw: object = json.loads(args.input.read_text(encoding="utf-8"))
        normalized = normalize(args.scanner, raw, scanner_failed=args.scanner_failed)
    except (OSError, ValueError, TypeError, AttributeError, KeyError) as error:
        print(f"ERROR: normalization failed ({type(error).__name__})", file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(normalized, indent=2) + "\n", encoding="utf-8")
    return 2 if normalized["scanner"]["status"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
