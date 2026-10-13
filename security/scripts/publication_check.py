"""Portfolio hygiene; complements secret scanning and manual image review."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXCLUDED = {
    ".git",
    ".venv",
    ".ci-runtime",
    "node_modules",
    "dist",
    "reports",
    "artifacts",
    "coverage",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".lab",
}
PRIVATE = {".private", "private", "interview-private"}
DENIED = ("fy" + "lpi", "soli" + "annikov", "vlad" + "yslav")
LOCAL_PATH = re.compile(
    r"(?:/Us" + r"ers/|/ho" + r"me/(?!zap(?:/|:|$))|[A-Z]:\\Us" + r"ers\\)", re.I
)


def violations(name: str, content: str) -> list[str]:
    issues: list[str] = []
    if any(word in (name + content).casefold() for word in DENIED):
        issues.append("prohibited identity or legacy identifier")
    if LOCAL_PATH.search(content):
        issues.append("personal filesystem path")
    if any(part in PRIVATE for part in Path(name).parts) or name.endswith(".private.md"):
        issues.append("private study document")
    if Path(name).name.startswith(".env") and Path(name).name != ".env.example":
        issues.append("local environment file")
    return issues


def check(root: Path = ROOT) -> list[str]:
    issues: list[str] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in EXCLUDED for part in relative.parts):
            continue
        if path.is_symlink():
            issues.append(f"{relative}: symlink requires publication review")
            continue
        if not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = ""  # pixels / binary metadata need separate manual review
        issues.extend(f"{relative}: {issue}" for issue in violations(str(relative), content))
    return issues


def main() -> int:
    issues = check()
    for issue in issues:
        print(issue)  # do not echo matched sensitive text
    print(f"Publication hygiene: {'FAIL' if issues else 'PASS'} ({len(issues)} issues)")
    print("Scope: distributable text/names; runtime exclusions and images need manual review.")
    return int(bool(issues))


if __name__ == "__main__":
    raise SystemExit(main())
