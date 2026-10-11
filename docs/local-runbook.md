# Local checks, tools and CI integration

Run all commands from the repository root. Never target a system you do not own and have permission to test.

## 1. Install and start

Required: Node 24, npm 11+, Python 3.13. `make install` installs pinned npm/Python dependencies (including Semgrep and pre-commit). Security scanners also need network/database access. Gitleaks, Docker, Trivy and Syft are separate binaries.

```sh
make install
npm --prefix lab-api run build
make lab-native
```

Leave the last command running in terminal 1. It starts only `127.0.0.1:3001`, with synthetic test values. Use `Ctrl+C` to stop. The Docker alternative is `make lab-up`; stop only this lab using `make lab-down` (deletes its synthetic volumes).

Configuration: `lab-api/src/config/`, `compose.yaml`, `Makefile`; Python settings in `tests/security/config.py` and `tests/security/.env.example`. Copy the example only to a gitignored `.env` when customizing. JWT issuer/audience, signing value and test key must match both sides. The supplied example matches native lab defaults. Test mode is prohibited in production.

## 2. Verify the code and controls

```sh
make lint unit security-test gate publication-check
make portfolio-evidence
```

The evidence command runs build/typecheck/Jest, Ruff/mypy, gate/evidence unit tests, API regressions, gate decision fixtures, publication hygiene and a two-user ownership demo. It continues after failed checks to retain results and exits nonzero if a check/demo fails. The lab must already be running. It resets synthetic state, so do not run another suite concurrently.

For installed Gitleaks and npm audit in the same report: `.venv/bin/python security/scripts/portfolio_evidence.py --extended`. npm requires network. The audit check uses a high-severity blocking threshold; remaining lower-severity advisories appear as WARN, not an all-clear. Errors remain nonzero.

Outputs (gitignored): `reports/portfolio/index.html`, `summary.json`, JUnit XML, Jest JSON and per-check logs. Open the HTML in a browser. `make evidence-report` only re-renders saved results; it does not validate the current code. Unknown or missing evidence is never a fresh PASS. Screenshots in the README are fixed snapshots, not live badges.

Refresh screenshots only after real execution: `cd lab-api && npx playwright install chromium && node scripts/capture-evidence.cjs`. With Chrome already installed, use `BROWSER_CHANNEL=chrome node scripts/capture-evidence.cjs` instead of downloading Chromium. Manually inspect images and metadata. The script checks horizontal overflow, not sensitive pixels.

Local compatibility execution may use Python 3.12 when explicitly recorded; it does not replace canonical Python 3.13 CI validation. See the exact current ledger.

## 3. Scanner toolbox

| Command | Tool / purpose | Interpretation |
|---|---|---|
| `make secrets` | Gitleaks repository scan + synthetic detection canary | Secret-pattern detection; review allowlist and history separately |
| `make sast` | Custom Semgrep rule validation, rule tests, scan | Findings require triage; installation failure is ERROR |
| `npm --prefix lab-api audit --audit-level=high` | npm dependency advisories | Time-sensitive dependency findings, not exploit proof |
| `make sca` | npm audit + Trivy dependency JSON | Requires Trivy and updated database |
| `make iac-scan` | Trivy configuration scan | Static Docker/Kubernetes/workflow findings |
| `make container-scan` | Build image and Trivy scan | Requires Docker + Trivy |
| `make sbom` | Syft CycloneDX inventory | Component inventory, not a clean bill of health |
| `make dast` | ZAP baseline against local container `/health` | Limited unauthenticated coverage; not a full API assessment |

For normalized policy decisions use `security/scripts/normalize_scanner.py --help` and `evaluate_security_gate.py --help`. Collection commands intentionally allow findings without failing; only the selected policy gate enforces delivery decisions. Review unsupported fields/adapters and triage status. A parser error or absent report must not be called PASS.

## 4. GitHub Actions

Existing workflows: `pr-security.yml` (quality, hygiene, secrets, SAST, dependencies/IaC), `deep-security.yml` (local integration/DAST and deeper checks), `release.yml` (local artifact verification). They do not imply deployment. Action references are pinned; scheduled external databases/images still need review. Dependabot is configured separately.

`portfolio-native.yml` adds the native vertical slice under canonical Python 3.13, with local health readiness, cleanup, retained HTML/JUnit evidence and an npm high/critical gate. Its configuration was inspected locally; execution still requires the first GitHub run. The HTML report distinguishes the checks it runs itself from separate scanner jobs.

Publish only the sanitized directory with new history. Enable Actions and inspect the first run, tool versions, artifacts and denied-release cases. Set branch rules requiring the appropriate jobs; uploading a report is not itself a security gate. Use minimal token permissions; no production secrets in untrusted PR jobs. Remote CI has not run merely because these files exist.

## 5. GitLab CI counterpart and executable Gherkin

The root `.gitlab-ci.yml` now replaces the earlier documentation-only template. It defines native verification, secret scanning, custom SAST, Trivy/policy and protected-tag build delivery. Its native job uses the same `make ci-verify` command as GitHub. JUnit includes the API matrix, unit policy checks and executable Gherkin scenarios.

After installation, `make ci-verify` builds, owns and cleans up its loopback API—do not start `make lab-native` concurrently. For a focused Gherkin run against an already running native lab, use `make bdd-test`. The 14 Gherkin scenarios use synthetic default settings and real HTTP/policy CLI actions.

See [CI/Gherkin handover](ci-cd-and-gherkin.md) for provider setup, pinned images, exact gates, artifacts, protected tags and first-run checks. GitLab requires an ephemeral Linux x86_64 container runner. Remote jobs still require publication, GitLab CI Lint and actual execution; no deployment or successful remote result is implied by the configuration.

## 6. Reproduce threat case-study evidence

Follow the exact commands in [case studies](security-case-studies.md#reproduce-the-current-evidence-safely). They collect fresh audits and JUnit reports separately from the portfolio screenshot snapshots. The API must be running, and the two-user demonstration resets only synthetic lab state.

`make case-study-evidence` reads those local reports and performs the ownership demonstration. On a fresh clone use `make case-study-evidence CASE_STUDY_FLAGS=--current-only`: historical raw audit data is intentionally not shipped. The exporter explicitly records a missing baseline instead of inventing a before/after comparison.

The reviewed public JSON contains module-level counts, synthetic observations, dependency versions and raw-artifact SHA-256 hashes—not tokens, test stdout, stack traces or machine paths. Its timestamp marks export time, not an independently attested time for every input; keep fresh raw reports locally and review the snapshot before publishing. Remote CI is not automatically proven by this local export.
