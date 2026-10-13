# GitHub verification — 13 October 2026

This is a real hosted-runner verification of the synthetic reference lab, not a customer or production audit. Raw scanner/JUnit reports are retained as workflow artifacts; this page contains reviewed public aggregates. Scan databases and advisory counts are time-sensitive.

## Reproducible native evidence

Commit: `8ac4cbefb6e7afe21a5c78daed598ff67d7d9377`.

[Native run](https://github.com/SollutionsIT/security_lab_2/actions/runs/38406660665): **SUCCESS**, Python 3.13.16, Node 24.21.0 / npm 11.19.0 on Ubuntu 24.04. The command was `make ci-verify`; the wrapper owned and cleaned up its loopback API.

- 71 Jest/Supertest, 72 API security, 95 gate/evidence tests and 14 executable Gherkin scenarios passed; no skipped cases.
- TypeScript build/typecheck, Ruff, mypy, publication hygiene and the ownership/state/event demonstration passed.
- Full npm audit: 20 moderate package entries, no high/critical; **WARN** remains. Production-only audit: zero reported entries.
- README screenshots are captured from this run's actual HTML artifact. “Local” in that report means runner loopback, not a laptop or production service.

## Independent security jobs

[Fast security run](https://github.com/SollutionsIT/security_lab_2/actions/runs/38406661002): **SUCCESS**.

- Gitleaks 8.30.1: no matches in the entire Git history or distributable tree under the reviewed configuration. The isolated synthetic canary was detected as expected.
- Semgrep 1.173.0: four custom rule self-tests passed; source scan produced zero findings and zero scan errors. Intentional positive fixtures are tested separately, not mislabeled application vulnerabilities.
- Trivy 0.75.0 filesystem scan: zero dependency vulnerabilities and secrets; two LOW Kubernetes configuration findings (`KSV-0020`, `KSV-0021`: UID/GID 1000). Non-root execution is configured; using a dedicated UID/GID above 10000 is an additional hardening option requiring workload/volume compatibility verification.
- Scanner archive SHA-256 checks precede binary extraction. Workflow Actions remain immutable-SHA pinned.

[Successful isolated API/ZAP run](https://github.com/SollutionsIT/security_lab_2/actions/runs/38406258828): the API regressions and non-root, read-only ZAP job passed. ZAP 2.17.0 baseline observed one informational “Storable and Cacheable Content” alert on the local `/health` target. It does not test authenticated API coverage or demonstrate active penetration testing.

[Updated container and SBOM run](https://github.com/SollutionsIT/security_lab_2/actions/runs/38406660990): the container/SBOM job passed. Trivy reported zero CRITICAL/HIGH, one MEDIUM OS package entry (`CVE-2026-85091`, zlib 1.3.2-r0; database fixed version 1.3.2-r1) and zero secrets. Gate: **WARN**, not a clean scan. CycloneDX SBOM contains 366 components.

## Failures investigated rather than hidden

1. Gitleaks' former Action bundled a version too old for the configured allowlist syntax. The pinned official CLI now reads the configuration; history/tree scans and a positive canary verify behavior.
2. Semgrep's direct rule-test file/directory combination failed. A checked helper materializes sibling rule/fixture files, requires all four positive/negative cases and checks the exact nonzero test count.
3. The old Node/Alpine image produced 3 CRITICAL and 49 HIGH package entries. Updating the publisher-pinned base reduced them to 8 HIGH, all in the bundled npm toolchain. Removing unused npm from the **runtime stage only** reduced the final image to 0 CRITICAL/HIGH and 1 MEDIUM. Build-stage `npm ci --ignore-scripts` is retained; no scanner suppression was added.
4. New npm rejected missing optional dependency lock entries. The lock was regenerated with npm 11.19.0 in a fresh directory and validated with strict `npm ci --ignore-scripts`, without force/legacy-peer overrides.
5. ZAP failed on a read-only home, report-directory ownership, temporary storage and an arbitrary runner UID's JVM home. Bounded tmpfs, matching non-root UID/GID and explicit JVM home fixed startup; diagnostic logs and failure exit codes are retained. Capabilities remain dropped and the root filesystem read-only.
6. Publication hygiene rejected ambiguous home-path notation. Explicit container directory notation passed the existing strict check; its denylist was not relaxed to permit personal paths.

Historical failed runs remain visible. Successful checks do not erase earlier failures or unresolved risks.

## Public integration phase

Repository visibility was changed to public with the owner's explicit approval after the private-phase checks passed.

- [First public deep run](https://github.com/SollutionsIT/security_lab_2/actions/runs/38407384264): **SUCCESS**, including actual CodeQL analysis/SARIF upload, container/SBOM and isolated API/ZAP. CodeQL found three source warnings; successful execution was not treated as zero findings.
- CodeQL triage: `js/polynomial-redos` identified repeated rescanning by the XML tag regex. The scanner now excludes nested opening delimiters; the existing 32 KiB input cap remains. Two `js/path-injection` alerts identified request-name flows into download filesystem operations. Strict UUID/extension validation and confinement already existed; no traversal exploit was demonstrated. Download now resolves the server-owned repository key and reads one `O_NOFOLLOW` file handle with size/type checks, avoiding the lstat/read symlink race. No rule suppression or source exclusion was added to hide these findings.
- [CodeQL reanalysis](https://github.com/SollutionsIT/security_lab_2/actions/runs/38408100980) on commit `b8c01b1a24d970b78e7482a5d10801cc189f8625`: the CodeQL job passed and downloaded SARIF contains **zero findings**. Two regression tests cover maximum-size malformed XML delimiters and replacement upload symlinks.
- [Fresh native verification](https://github.com/SollutionsIT/security_lab_2/actions/runs/38408109348): **SUCCESS**, 73 Jest, 72 API, 95 gate/evidence and 14 Gherkin cases; no skips. The full local command also passed after these code changes. README screenshots use this later actual artifact; the earlier 71-case record above remains historical.
- [Release evidence](https://github.com/SollutionsIT/security_lab_2/actions/runs/38407388676): **SUCCESS**. Built a Docker candidate, scanned/gated it, generated an actual image CycloneDX SBOM, retained tar/checksum and created GitHub build-provenance attestation. Downloaded tar checksum passed and `gh attestation verify ... --repo SollutionsIT/security_lab_2` exited successfully. This run attests the pre-CodeQL-fix commit `8ac4cbefb6e7afe21a5c78daed598ff67d7d9377`, not later source; no registry push or production deployment occurred.
- Pull Requests were initially disabled by the repository owner, preventing API creation. They were enabled with explicit owner approval; [PR #11](https://github.com/SollutionsIT/security_lab_2/pull/11) exercises the real PR workflow. Dependency review initially failed because Dependency graph was disabled. After enabling that prerequisite, the current PR dependency-review job passed. This diff contains no dependency upgrades, so it demonstrates integration execution, not detection of a deliberately introduced vulnerable package.

## Prioritization and next actions

I treated exposed runtime dependency findings first: update the base, remove unnecessary runtime tooling, rebuild, then rescan and retest. This reduces the delivered attack surface without pretending every package advisory is an exploitable endpoint. The remaining zlib MEDIUM should receive a compatible publisher/package update and a fresh build/scan. The 20 moderate npm development-chain entries require build-input reachability triage and a compatible toolchain update, not a forced downgrade.

For a real company pilot, require an owner and deadline for remaining findings, dependency-update cadence, branch rules, least-privilege secrets and authenticated API coverage. Validate Kubernetes admission/network controls in an authorized cluster before making enforcement claims. These actions align with least privilege and OWASP/NIST SSDF dependency verification; they are not ISO certification or a compliance assessment.

GitLab CI YAML and local contract checks are included, but no GitLab server pipeline was executed. No production deployment, cloud account, Kubernetes cluster, customer data, payment provider or LLM was used.
