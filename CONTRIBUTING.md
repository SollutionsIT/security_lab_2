# Contributing

Contributions must preserve the repository's safety boundary and traceability model.

## Change workflow

1. Describe the threat or failure mode.
2. Add or update a security requirement.
3. Implement the smallest control that satisfies it.
4. Add a deterministic automated verification.
5. Define the CI policy and evidence produced.
6. Document limitations, false-positive handling, and residual risk.

Core changes require tests. Scanner suppressions require a scoped, owned, reviewed, and expiring exception; permanent blanket suppressions are not accepted.

## Prohibited content

- Proprietary COMPANY source, data models, assets, routes, or copied configuration.
- Real credentials, tokens, personal data, production URLs, internal hostnames, or customer data.
- Dynamic test targets other than the synthetic local lab.
- Invented CVEs, scanner output, test output, or performance claims.

## Reproducibility

- Commit lockfiles.
- Use `npm ci` in reproducible builds.
- Pin CI actions immutably.
- Keep generated evidence out of Git unless it is a deliberately reviewed synthetic fixture.
