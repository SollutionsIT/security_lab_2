"""Run real Semgrep positive/negative rule tests using its supported sibling layout."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def materialize(root: Path, directory: Path) -> set[str]:
    policy = root / "semgrep.yml"
    rules = yaml.safe_load(policy.read_text())["rules"]
    identifiers = {rule["id"] for rule in rules}
    fixtures = "\n\n".join(
        path.read_text() for path in sorted((root / "security/semgrep").glob("*.ts"))
    )
    for identifier in identifiers:
        if f"// ruleid: {identifier}" not in fixtures or f"// ok: {identifier}" not in fixtures:
            raise ValueError("Every Semgrep rule needs positive and negative annotations")
    if not identifiers:
        raise ValueError("No Semgrep rule tests")
    # Semgrep --test expects configuration and target files with the same stem.
    (directory / "cases.yml").write_bytes(policy.read_bytes())
    (directory / "cases.ts").write_text(fixtures + "\n")
    return identifiers


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--semgrep", default="semgrep")
    args = parser.parse_args()
    executable = shutil.which(args.semgrep)
    if executable is None:
        raise RuntimeError("Semgrep is required")
    with tempfile.TemporaryDirectory(prefix="company-semgrep-tests-") as temporary:
        directory = Path(temporary)
        identifiers = materialize(ROOT, directory)
        result = subprocess.run(
            [executable, "--test", "--metrics=off", str(directory)],
            capture_output=True,
            text=True,
            check=False,
        )
        print(result.stdout, end="")
        print(result.stderr, end="")
    if result.returncode != 0:
        return result.returncode
    summary = re.search(r"(\d+)/(\d+):[^\n]*All tests passed", result.stdout + result.stderr)
    if summary is None or tuple(map(int, summary.groups())) != (len(identifiers), len(identifiers)):
        raise RuntimeError("Semgrep did not confirm execution of every rule test")
    print(f"PASS: real positive/negative fixtures exercised for {len(identifiers)} Semgrep rules")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
