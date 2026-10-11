#!/usr/bin/env python3
"""Evaluate normalized scanner JSON as PASS, WARN, FAIL, or ERROR."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml

_RANK = {"UNKNOWN": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}


@dataclass(frozen=True)
class Decision:
    result: str
    scanner: str
    finding_id: str
    reason: str


def _mapping(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON/YAML object")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    return _mapping(json.loads(path.read_text(encoding="utf-8")), str(path))


def _load_exceptions(path: Path | None, today: date) -> tuple[set[tuple[str, str]], list[str]]:
    if path is None:
        return set(), []
    document = _mapping(yaml.safe_load(path.read_text(encoding="utf-8")), str(path))
    entries = document.get("exceptions", [])
    if not isinstance(entries, list):
        raise ValueError("exceptions must be a list")
    active: set[tuple[str, str]] = set()
    notes: list[str] = []
    required = {
        "finding_id",
        "scanner",
        "rationale",
        "compensating_controls",
        "owner",
        "reviewer",
        "expires",
        "scope",
    }
    for index, raw in enumerate(entries):
        item = _mapping(raw, f"exception[{index}]")
        missing = required - item.keys()
        if missing:
            raise ValueError(f"exception[{index}] misses {sorted(missing)}")
        controls = item["compensating_controls"]
        if not isinstance(controls, list) or not controls:
            raise ValueError(f"exception[{index}] requires compensating_controls")
        expires = item["expires"]
        expiry = expires if isinstance(expires, date) else date.fromisoformat(str(expires))
        key = (str(item["scanner"]), str(item["finding_id"]))
        if expiry < today:
            notes.append(f"expired exception ignored: {key[0]}/{key[1]}")
        else:
            active.add(key)
    return active, notes


def _finding_decision(scanner: str, item: dict[str, Any]) -> Decision:
    if not isinstance(item.get("id"), str) or not item["id"].strip() or "severity" not in item:
        return Decision("ERROR", scanner, "<schema>", "finding requires id and severity")
    finding_id = str(item.get("id", "<missing-id>"))
    severity = str(item.get("severity", "UNKNOWN")).upper()
    if severity not in _RANK:
        return Decision("ERROR", scanner, finding_id, f"unknown severity {severity}")
    validated = item.get("validated") is True
    confidence = str(item.get("confidence", "unknown")).lower()
    is_new = item.get("new", True) is True

    if item.get("verified_credential") is True and validated:
        return Decision("FAIL", scanner, finding_id, "validated credential exposure")
    if (
        severity == "CRITICAL"
        and validated
        and (item.get("reachable") is True or item.get("exploitable") is True)
    ):
        return Decision("FAIL", scanner, finding_id, "validated reachable/exploitable Critical")
    if severity in {"HIGH", "CRITICAL"} and validated and item.get("policy_violation") is True:
        return Decision("FAIL", scanner, finding_id, "validated high-impact policy violation")
    if severity == "HIGH" and confidence == "high" and validated and is_new:
        return Decision("FAIL", scanner, finding_id, "new validated High-confidence finding")
    if _RANK[severity] >= _RANK["MEDIUM"]:
        reason = "requires validation" if not validated else "validated non-blocking risk"
        return Decision("WARN", scanner, finding_id, reason)
    return Decision("PASS", scanner, finding_id, "below warning threshold")


def evaluate(
    reports: list[Path], exceptions_path: Path | None, today: date
) -> tuple[str, list[Decision], list[str]]:
    active_exceptions, notes = _load_exceptions(exceptions_path, today)
    if not reports:
        raise ValueError("At least one report is required")
    decisions: list[Decision] = []
    for path in reports:
        report = _load_json(path)
        scanner_meta = _mapping(report.get("scanner"), f"{path}: scanner")
        scanner = str(scanner_meta.get("name", "<missing-scanner>"))
        if not isinstance(scanner_meta.get("name"), str) or not scanner.strip():
            decisions.append(Decision("ERROR", scanner, "<schema>", "scanner name required"))
            continue
        if scanner_meta.get("status") != "success":
            decisions.append(Decision("ERROR", scanner, "<scanner>", "scanner did not complete"))
            continue
        findings = report.get("findings")
        if not isinstance(findings, list):
            decisions.append(Decision("ERROR", scanner, "<schema>", "findings is not a list"))
            continue
        for raw in findings:
            try:
                decision = _finding_decision(scanner, _mapping(raw, "finding"))
            except ValueError as error:
                decision = Decision("ERROR", scanner, "<schema>", str(error))
            if (scanner, decision.finding_id) in active_exceptions and decision.result == "FAIL":
                decision = Decision(
                    "WARN", scanner, decision.finding_id, "active reviewed exception"
                )
            decisions.append(decision)
    priority = {"PASS": 0, "WARN": 1, "FAIL": 2, "ERROR": 3}
    overall = max(
        (item.result for item in decisions),
        key=lambda result: priority[result],
        default="PASS",
    )
    return overall, decisions, notes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("reports", nargs="+", type=Path)
    parser.add_argument("--exceptions", type=Path)
    parser.add_argument("--today", type=date.fromisoformat, default=date.today())
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args(argv)
    try:
        overall, decisions, notes = evaluate(args.reports, args.exceptions, args.today)
    except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError) as error:
        print("ERROR")
        print(f"gate configuration/input error: {error}", file=sys.stderr)
        return 2
    payload = {
        "result": overall,
        "decisions": [item.__dict__ for item in decisions],
        "notes": notes,
    }
    print(overall)
    print(json.dumps(payload, indent=2, sort_keys=True))
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 2 if overall == "ERROR" else 1 if overall == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
