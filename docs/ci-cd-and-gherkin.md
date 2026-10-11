# CI/CD and executable Gherkin handover

## What already existed and what is now included

Four GitHub workflow configurations already existed. This extension adds the independent root `.gitlab-ci.yml`, executable Gherkin and a shared native verification entrypoint. **Configuration is not a successful remote run.** See the dated [execution ledger](../PROJECT_STATUS.md).

| Entry point | Triggers / role | Evidence and decision |
|---|---|---|
| GitHub `portfolio-native.yml` | Pull request, main push, manual | Own loopback API; core checks, API matrix, Gherkin, full/production npm audit; HTML/JSON/JUnit |
| GitHub `pr-security.yml` | Pull request / main | Quality, Gitleaks, custom Semgrep, dependency review, reporting-mode Trivy |
| GitHub `deep-security.yml` | Main, weekly, manual | CodeQL, container scan/SBOM, isolated API/ZAP jobs; prerequisites apply |
| GitHub `release.yml` | Version tag / manual | Candidate image, normalized gate, SBOM, checksum/provenance and retained artifact; no registry push |
| GitLab `native-security` | MR, branch/tag, web/schedule when a ref is present | Same `make ci-verify`; JUnit displayed by GitLab; verified build candidate packaged |
| GitLab scanner jobs / `scanner-policy` | Same pipeline | Gitleaks history/tree/canary, tested custom SAST, Trivy collection and normalization/policy |
| GitLab `release-evidence` | Protected tag only; required jobs must succeed | Check candidate SHA-256; retain build and policy evidence for review |

**Delivery meaning:** build candidates and reports retained as CI artifacts. There is no production deployment, environment promotion, registry publication or rollback automation. A production CD stage needs an authorized target, credentials, approvals, release policy and operational rollback design.

## The same native command locally and in both providers

Install dependencies first (`make install`, canonical Python 3.13, Node 24). Then, with port 3001 free:

```sh
make ci-verify
open reports/portfolio/index.html  # macOS; use a browser elsewhere
```

`security/scripts/run_ci.py` checks port availability, builds the API, starts `node dist/main.js` directly, verifies the exact health contract, runs the checks serially and stops its owned process in `finally`. It refuses to reuse/terminate an existing service. The API binds to `127.0.0.1:3001`; identities and secrets are synthetic. No Docker daemon, cloud or database is needed for the native slice.

The runner returns nonzero on failed checks/startup/timeout. `reports/ci/result.txt` records the lifecycle outcome; the JSON/HTML ledger gives individual PASS/WARN/FAIL/ERROR results. API test state is shared and reset serially—do not run these suites concurrently against one instance. Job/process timeouts bound the run; provider cancellation destroys the ephemeral runner, not a customer host.

## Gherkin: specification that actually executes

Four English feature files in `tests/bdd/features/` expand to **14 scenarios**:

- Ownership: owner read succeeds; other-user read/change is denied, with unchanged state.
- Protected fields: `ownerId`, `role`, `isVerified` are rejected without a partial update.
- Webhooks: missing/forged/stale signatures fail; valid duplicate pays only once.
- Delivery policy: PASS/WARN exit 0, FAIL exit 1, ERROR exit 2.

Example from the actual feature:

```gherkin
Scenario Outline: Reject protected fields without partially changing state
  When the owner includes the protected field "<field>" in an otherwise valid update
  Then the API returns HTTP 400
  And the original property remains unchanged
```

The full feature includes a Background and Examples. `pytest-bdd==9.0.0` binds Given/When/Then in `test_api_security_bdd.py` and `test_security_gate_bdd.py`. Existing settings/client fixtures are reused; each API Background resets the synthetic state. These are actual HTTP and CLI checks, not mocked API responses or documentation-only scenarios. The payment provider itself remains synthetic.

For a focused run, start `make lab-native` separately, then:

```sh
make bdd-test
```

`run_bdd.py` deliberately selects checked-in synthetic defaults and fixed loopback—not arbitrary environment overrides. Output: `reports/bdd/results.xml`. Gate-only scenarios can run without the API via `.venv/bin/python -m pytest tests/bdd/test_security_gate_bdd.py`.

Gherkin is a readable specification format; writing feature files alone is not proof of team-wide BDD. Scenario review with product/security stakeholders is a production adoption step. These 14 examples complement the deeper 72-case API matrix; they do not duplicate every security requirement.

## Gate policy: what blocks and what needs triage

| Check | Blocking behavior |
|---|---|
| Build/type/lint/unit/API/Gherkin/publication checks | Failure/error blocks the native job |
| npm audit | High/critical package entries block; moderate findings produce WARN; unusable output is ERROR |
| Gitleaks | Matches block; the isolated canary must produce the expected finding exit, not a clean result |
| Custom Semgrep | Rules validated/self-tested; findings in `lab-api/src` block with `--error`. Positive self-test fixtures are not application scan targets. |
| Trivy collection | Collection uses exit 0; execution/report errors still fail the job/parser |
| Normalized Trivy gate | Unvalidated medium+ detections are WARN; validated blocking risks are FAIL; invalid/missing evidence is ERROR |

A successful pipeline can contain WARN. It is not a clean vulnerability report or authorization to deploy real systems. Publisher detections are not automatically confirmed exploits. Review normalized evidence and document validation/exception decisions before production use. No `allow_failure: true` masks mandatory jobs.

## GitHub first-run checklist

1. Publish only this sanitized standalone repository after owner approval; preserve a new anonymized history and review metadata/license.
2. Enable Actions and allowed pinned third-party Actions. Run **Portfolio native evidence** manually or open a PR.
3. Inspect actual Node/Python versions, every job result and uploaded HTML/JSON/JUnit. Configure required checks on the main branch; YAML alone cannot configure branch protection.
4. Review prerequisites for dependency review, CodeQL and attestation against repository/account capabilities. Organizational Gitleaks Action use may require its upstream license; never hide that failure.
5. Keep real secrets out of fork/untrusted PR jobs. Prefer ephemeral hosted runners; do not run arbitrary fork code on a privileged shared self-hosted runner.

GitHub Actions are pinned to SHAs; native/fast checkouts disable persisted Git credentials. Read-only workflow token permissions, timeouts and finite artifact retention reduce exposure. Existing deep/release jobs need separate runtime verification and job-specific permissions. No `pull_request_target` executes PR code.

## GitLab first-run checklist

1. Publish/import the sanitized project with `.gitlab-ci.yml` at repository root. Do not copy another customer's history.
2. Use an ephemeral **Linux x86_64 Docker/container runner**, not a privileged host shell runner. No Docker-in-Docker/socket is needed for these jobs.
3. Allow pulls/downloads from the official container registry, nodejs.org, PyPI, npm and scanner databases. The Python/Gitleaks/Trivy images are digest-pinned; Node 24.12.0 is verified against a committed SHA-256 from the official release manifest. Python's direct dependencies are pinned; the complete transitive Python graph is not hash-locked.
4. Validate the YAML with GitLab **CI Lint**, run a branch/MR pipeline, inspect JUnit/JSON/artifacts, then test a known failing branch. Local YAML/contract tests are not GitLab server validation.
5. Configure protected branches/tags and review required pipeline success. The delivery job runs only for a protected tag and waits for the native, secret, SAST and scanner-policy jobs.
6. Do not grant protected variables to untrusted MR code. Avoid parent-project execution of an untrusted fork with privileged access; review runner/token permissions and artifact visibility.

MR rules avoid a duplicate push pipeline when an open MR exists. The build archive contains only compiled API output and package manifests, not `.env`, runtime data or raw logs. It still requires npm production dependency installation and secure configuration before any authorized deployment; it is not a self-contained production image. SHA-256 detects mismatched bytes, not the trustworthiness of the code or an independent attestation.

## Evidence handling and verification boundary

Reports are gitignored. Both providers retain evidence for seven days even after failed verification; the protected-tag candidate uses 14 days. Raw API process logs stay local to the runner and are not explicitly uploaded by the native job. Check logs may contain diagnostic data: review redaction/artifact access before adapting the lab to real data. No automatic public Pages/report website is created.

Local command success, syntax/contract checks, a successful remote job and actual deployed enforcement are separate evidence levels. First remote runs remain pending until repository publication and runner execution are authorized.

Official implementation references: [GitHub secure workflow use](https://docs.github.com/en/actions/reference/security/secure-use), [GitLab MR pipelines](https://docs.gitlab.com/ci/pipelines/merge_request_pipelines/), [GitLab JUnit reports](https://docs.gitlab.com/ci/testing/unit_test_reports/), [pytest-bdd](https://pytest-bdd.readthedocs.io/en/latest/), [OWASP CI/CD Security](https://cheatsheetseries.owasp.org/cheatsheets/CI_CD_Security_Cheat_Sheet.html).
