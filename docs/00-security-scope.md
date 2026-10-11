# Security scope and evidence contract

COMPANY is fictional. This standalone educational lab models common application-security failures using synthetic identities, resources and provider messages. It does not represent a customer architecture, production audit or penetration test.

Reasoning chain: **threat → requirement → control → negative test → evidence → triage → residual risk**.

## Authorized targets

Only the lab on loopback or its isolated container network. Tests reject non-lab targets and do not follow redirects. Do not scan public sites, metadata services, private networks or unrelated local services. Real payments, cloud accounts, email, OAuth and LLM providers are out of scope.

## Evidence vocabulary

- **Source-inspected**: implementation/configuration is present; not proof it works.
- **Local verified**: the specified command ran against synthetic data and produced retained evidence.
- **Configured / not executed**: files exist, but the integration was not run.
- **Recommendation**: production adaptation, not implemented effectiveness.
- **Modeled threat**: a scenario requiring analysis, not a discovered vulnerability.

The current execution ledger is [PROJECT_STATUS.md](../PROJECT_STATUS.md). Scanner findings require validation. Missing tools, invalid reports and parser failures must not silently become PASS.

## Working scope

Authentication; owner/role/state authorization; DTO input validation; rate limits; signed synthetic webhooks; bounded uploads/XML; pure SSRF policy checks without fetching; mocked AI boundary; redacted correlation events; Python security regressions; normalized policy gates; publication hygiene and local evidence reporting.

Infrastructure workflows and manifests are examples until separately executed. No managed cluster, cloud IAM, service mesh, production incident response or organizational compliance is claimed.

## Publication boundary

Only original synthetic implementation and reviewable public references. Exclude customer source, identities, private environment topology, real endpoints, credentials, internal screenshots and private interview notes. Synthetic credentials are deliberately local-only—not safe production defaults. All screenshots must be reviewed for visible data and metadata before publishing.

Test mode exposes reset/state helpers. Bind it to the isolated lab only and disable it in any production adaptation. Shared state requires serial API execution; xdist isolation is not implemented here.

## Residual risk

Passing tests cover defined cases, not every attack. Production requires persistence/transactions, distributed rate limiting, TLS, real secrets lifecycle, monitoring, explicit risk owners and tested operational recovery. Security tools cannot substitute for authorization logic or human review.
