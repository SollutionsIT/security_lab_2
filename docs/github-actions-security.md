# GitHub Actions security

## Pipeline split

`pr-security.yml` gives fast feedback: reproducible install, type/lint/unit tests, Gitleaks, custom Semgrep rules, dependency review and reporting-mode Trivy filesystem/IaC scan. `deep-security.yml` runs CodeQL, builds and scans the container, executes the local-only API suite and ZAP, and retains SBOM/evidence. `release.yml` rebuilds a candidate, evaluates normalized results, generates an SBOM, attests the tarball and publishes only a GitHub Actions artifact.

`portfolio-native.yml` now invokes the shared `make ci-verify` lifecycle, including executable Gherkin and full/production npm audit. The independent `.gitlab-ci.yml` supplies the GitLab counterpart. See [CI/Gherkin handover](ci-cd-and-gherkin.md) for exact gates and prerequisites. Custom Semgrep findings in application source block; self-test fixtures are tested separately rather than included as production findings.

## Runner threat model and controls

Untrusted code executes on a runner that can influence artifacts and may see a token. Each workflow therefore starts with `contents: read`, grants `security-events`, `id-token` or `attestations` only to the job needing it, pins third-party Actions to verified commit SHAs, sets timeouts and concurrency, avoids `pull_request_target`, never evaluates PR text as shell, and limits artifact retention.

Synthetic dynamic secrets are explicit non-production values. Real publication credentials are not present. Registry publication and deployment remain disabled until environment protection, reviewers, a target registry and digest promotion are configured.

## Performance trade-off

PR jobs run independently to return useful feedback in minutes. Expensive CodeQL, image build, integration DAST and SBOM move to main/nightly/manual deep runs. This preserves developer flow while keeping deeper coverage; release repeats artifact-bound controls rather than trusting a source-only result.

## Maintenance

Dependabot proposes Action SHA/tag updates. A reviewer must compare upstream release notes and ensure the resolved commit belongs to the stated release before merging. Immutable pins prevent silent tag movement but do not prove an Action is trustworthy.

## Interview answer

I treat CI as a production system: minimize token permissions, pin executable dependencies, isolate untrusted PRs, never interpolate untrusted text into shell, set timeouts, retain evidence briefly, and bind release evidence to an artifact. I split fast and deep checks so developers get feedback without weakening the release gate.
