# Local publication review — 2026-10-11

This is a review of the standalone synthetic COMPANY portfolio, not the original business application, historical customer credentials or production infrastructure. No commit, push or visibility change is implied by these results.

## Checks actually executed

| Check | Result / boundary |
|---|---|
| Fresh source and destination Git history | No commits/refs before preparation; source history was not imported |
| Intended destination | GitHub API: private, size 0; `git ls-remote`: no refs at review time |
| Publication denylist | PASS: no prohibited identities, legacy identifiers or personal filesystem paths in reviewed distributable text/names |
| Ignore-policy regression tests | 46 passed, including sensitive-path exclusion, required templates, force-added files, parent-repo rejection, links and binary/metadata review |
| Candidate snapshot Gitleaks 8.30.1 | PASS: no findings in the actual transfer candidates |
| Whole local directory Gitleaks and positive canary | Final scan: no findings; isolated non-credential canary correctly detected |
| TypeScript typecheck/build; Ruff; mypy | PASS; mypy checked 35 source files |
| Jest/Supertest | 71 passed, 0 failed/skipped |
| Python API security regressions | 72 passed, 0 failed/skipped |
| Gate/evidence/publication unit tests | 79 passed, 0 failed/skipped |
| Executable Gherkin | 14 passed, 0 failed/skipped |
| Ownership HTTP demonstration | Owner 200; cross-owner read/change 404; state unchanged and denial event retained |
| npm audit, all dependencies | WARN: 20 moderate, 0 high/critical; dev-tool advisories remain |
| npm audit, production dependencies | PASS: 0 findings in the returned audit |
| Three README PNGs | Visually reviewed; no legacy/customer/personal data observed; no PNG text/EXIF chunks |

Full local CI run recorded at `2026-10-11T15:18:42Z`, using compatibility Python 3.12.14. The canonical remote target remains Python 3.13; remote execution is not verified. The owned API process was stopped after the run. Local raw reports remain ignored under `reports/`.

## Preparation issues and their resolution

- The first snapshot scan used absolute paths, preventing the narrowly allowlisted synthetic canary path from matching. The scan now runs inside its temporary snapshot with relative paths; the canary allowlist was not broadened.
- An early manifest represented filename-to-hash pairs as JSON keys. Gitleaks raised 16 generic-key matches on SHA-256 inventory entries, not credentials. A path/hash record format removed that ambiguity; both candidate and final directory scans passed without new secret exceptions.
- A sandboxed Supertest run could not bind sockets (`EPERM`). The same verification was rerun with local socket permission and all 71 tests passed. The failed infrastructure attempt is not reported as an application defect or silently counted as PASS.
- Semgrep was not installed in the compatibility virtual environment and was not rerun. Docker/Kubernetes, Trivy/Syft, CodeQL, ZAP, remote CI and real providers were not verified during this publication pass.

## Remaining actions and limitations

Review the final staged diff and Git author before committing. Keep real identities, filled secrets and private study material outside the public tree; use only the reviewed synthetic templates. Retain the non-commercial source-available license and accurate learning-project positioning. Triage dev-dependency advisories and inspect the first actual GitHub Actions run after an explicitly approved push.

Scanning cannot guarantee the absence of all personal/business data. Any real credential historically committed/shared must be revoked or rotated separately by its owner. A fresh portfolio does not erase old repositories, clones or forks.
