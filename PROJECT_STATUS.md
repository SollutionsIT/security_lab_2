# Execution ledger — 2026-10-11

This ledger concerns the sanitized standalone lab. It does not inherit an unverified result from another checkout. Primary evidence is generated locally under gitignored `reports/portfolio/`; README screenshots are reviewed snapshots, not remote CI results.

## Actually executed

Environment: macOS, Node 24.12.0, npm 11.6.2, Python 3.12.14, Gitleaks 8.30.1. Canonical project/CI Python target remains 3.13. The current Python run is compatibility evidence only.

Command: `.venv/bin/python security/scripts/portfolio_evidence.py --extended`, with the synthetic API bound to `127.0.0.1:3001`. Final evidence timestamp: `2026-10-11T12:18:01Z`.

| Check | Result | Evidence |
|---|---|---|
| TypeScript typecheck + NestJS build | PASS | `check-0.log`, `check-1.log` |
| Jest / Supertest | PASS: 71/71, no skips | `jest.json`, `check-2.log` |
| Ruff / mypy | PASS | `check-3.log`, `check-4.log` |
| Gate, normalization, evidence/hygiene unit tests | PASS: 16/16, no skips | `gate.xml`, `check-5.log` |
| Python API security regressions | PASS: 72/72, no skips | `api.xml`, `check-6.log` |
| PASS / WARN / FAIL / ERROR gate fixtures | PASS: expected outcomes/exit codes | `check-7.log` |
| Publication denylist hygiene | PASS in distributable text/names | `check-8.log`; not a comprehensive data-leak detector |
| Gitleaks distributable scan | PASS: no findings under configured exclusions | `check-10.log` |
| Gitleaks isolated synthetic canary | PASS: expected detection | `check-11.log` |
| npm audit, high blocking threshold | WARN: 0 high, 0 critical; 20 moderate entries | `check-9.log`; time-sensitive database result |
| Separate npm production-only audit | PASS: 0 reported entries | `npm-audit-production.json`; not proof of no runtime risk |
| Reproducible updated Node install | PASS | Fresh `npm ci --ignore-scripts --no-fund --no-audit` completed |
| Two-user local ownership demonstration | PASS: 200/404/404; unchanged state; correlated denial | `summary.json`, HTML demo section |

The moderate npm entries are a propagated development-tool dependency chain involving `sprintf-js` / `argparse` / legacy `js-yaml` / Istanbul / Jest. Twenty reported package entries do not mean twenty independently exploitable application vulnerabilities. They remain unresolved and require dev/build-context triage; do not describe this as a clean dependency audit.

## Changes made after a real dependency finding

Initial npm audit reported 10 affected dependency entries: 2 critical, 5 high, 3 moderate. A compatible transitive lockfile refresh plus NestJS packages `11.2.1 → 11.2.7` and Multer `2.2.0 → 2.4.0` removed the reported high/critical entries in the final audit. Application and API tests were rerun after the update. No forced major downgrade was used to hide the remaining development dependency findings.

The first local attempt hit sandbox socket restrictions, not an application failure. The demonstration initially used an invalid DTO field and the wrong log-field spelling; these were corrected to the actual contract (`title`, `correlation_id`) and rerun. Final evidence is from the corrected run.

## Configured, not executed here

Semgrep / CodeQL, Trivy, Docker/container runtime, Kubernetes enforcement, ZAP, Syft SBOM and remote GitHub/GitLab pipelines. Their configurations are included, but they have no current local/remote execution claim. DAST targets only the local health endpoint baseline; this is not full authenticated API coverage.

Four GitHub workflows are provided, including the canonical native evidence workflow. YAML loading and immutable-reference syntax were checked locally; workflow files are not successful remote runs. The later CI/Gherkin extension below replaces the GitLab documentation-only example with a root configuration; remote execution remains unverified.

No production system, real payment provider, LLM, managed cloud, Vault, Istio, organizational ISMS or customer dataset was tested. ISO/IEC 27001 is a management reference, not certification. AI-related checks use a mocked boundary; SSRF tests exercise pure policy without fetching.

## Review boundaries

The prohibited legacy identifier and personal-name denylist did not match distributable text/file names. Public images require manual pixel/metadata review; automatic text scanning does not prove complete anonymization. Runtime dependencies, caches, raw reports and private study material are excluded from publication. The source-available license is custom and requires legal review for commercial enforcement.

## Next verification

1. Run canonical Python 3.13 and first remote CI; record actual artifacts and job results.
2. Triage remaining dev-tool advisories by reachability/build input; upgrade the chain when a compatible fix exists.
3. Execute external scanners in an authorized isolated environment and retain versions/databases/reports.
4. Validate real workload/admission/network enforcement before claiming Kubernetes controls work.
5. Review tracked files and Git metadata before approving any public upload.

## Threat case-study extension — fresh local verification, 11 October 2026

This later run is separate from the earlier 16-test portfolio screenshot snapshot. Its public aggregates are in `docs/evidence/case-studies-latest.json`; raw inputs remain in gitignored `reports/case-studies/`.

- API security regressions: 72/72 passed, no skips; real HTTP requests against the synthetic loopback API.
- Gate/normalization/evidence unit regressions: 21/21 passed, no skips, including explicit fresh-clone baseline omission and rejection of empty/inconsistent reports.
- Fresh full npm audit: 0 critical, 0 high, 20 moderate package entries; WARN remains. Fresh production-only audit: 0 reported entries.
- Ownership demonstration: owner GET 200, other-user GET/PATCH 404, unchanged state and correlated denial event.
- Ruff/mypy: PASS; publication text/name check: PASS; configured Gitleaks scan: no findings; isolated synthetic canary: detected as expected. These are scoped checks, not a comprehensive privacy guarantee.
- Added six case studies, an observed dependency finding record, first-person risk prioritization, precise ATT&CK/CWE mappings, current primary-source context and unpublished LinkedIn drafts.

The baseline audit is retained historical evidence, not a new run of vulnerable software. Jest's 71/71 result above is also retained, not rerun for the documentation extension. These cases do not demonstrate a production intrusion, BOLA exploit, malicious package execution, live Semgrep/Trivy detection or legal compliance. Current-report publication dates and their observation periods are documented separately.

## CI/Gherkin extension — local equivalent verified, 11 October 2026

Command: `make ci-verify`. Final core-report timestamp: `2026-10-11T13:40:47Z` (15:40 Warsaw). Same Node/npm and Python 3.12.14 compatibility environment as above; canonical Python 3.13 and Linux/container jobs remain pending remote verification.

| Check | Fresh result | Local evidence |
|---|---|---|
| TypeScript typecheck / NestJS build | PASS | `reports/portfolio/check-0.log`, `check-1.log` |
| Jest / Supertest | 71/71 PASS, no pending | `reports/portfolio/jest.json` |
| API security regression matrix | 72/72 PASS, no skips | `reports/portfolio/api.xml` |
| Gate/evidence/CI lifecycle and YAML contracts | 33/33 PASS, no skips | `reports/portfolio/gate.xml` |
| Executable Gherkin | 14/14 PASS, no skips | `reports/bdd/results.xml` |
| Ruff / mypy | PASS, including new scripts/step definitions | `check-3.log`, `check-4.log` |
| Ownership HTTP/state/event demonstration | PASS | `reports/portfolio/summary.json` |
| Fresh full npm audit | WARN: 20 moderate; 0 high/critical | `npm-audit-current.json` |
| Fresh production-only npm audit | 0 reported entries | `npm-audit-production-current.json` |

The first CI-equivalent attempt correctly failed on a Ruff line-length issue; it was fixed and the full command was rerun. The wrapper starts and terminates only its own loopback Node process; occupied-port refusal and cleanup branches are additionally covered by isolated unit tests. These unit tests use mocked process objects, not a production-process claim.

The four `.feature` files bind to pytest-bdd 9.0.0 and real HTTP/policy CLI steps. GitHub native verification now calls the shared lifecycle; `.gitlab-ci.yml` defines native, secret, custom-SAST, Trivy/policy and protected-tag artifact delivery. Image digests and the committed Node archive SHA-256 were read from publisher registries/release data. This does not prove those container jobs have run.

All four GitHub workflow files passed local actionlint 1.7.12 (ShellCheck disabled); GitLab YAML and repository-specific contracts passed locally. No GitLab server CI Lint, remote GitHub/GitLab execution, production deployment or cloud/runtime scanner execution is claimed. Build delivery is an artifact, not production CD. Previous README images and case-study JSON remain explicitly dated snapshots rather than inheriting these new counts.

## Publication preparation — 13 October 2026

The reviewed synthetic `docs/evidence/` files and this ledger are retained in the public portfolio by explicit owner choice. Raw reports, credentials, private documents and IDE/dependency data remain ignored. A readable `gitignore_example` is included; `.gitignore` is the active policy.

The later retained [publication review](docs/evidence/publication-review.md) records the 11 October native run at `15:18:42Z`: 71 Jest, 72 API, 14 Gherkin and 79 gate/evidence/publication tests passed. These are dated local results, not a new 13 October integration run. Earlier 16/21/33-test snapshots above remain historical and do not silently inherit later counts.

On 13 October, the working-tree Gitleaks scan found no leaks and the publication text/name hygiene check passed. These scoped checks are not a complete privacy or licensing guarantee. Remote CI, canonical Python 3.13 execution and platform/external-scanner validation still require the actual authorized runs. The project is publishable as a working reference lab with these limitations, not a production-readiness or compliance claim.
