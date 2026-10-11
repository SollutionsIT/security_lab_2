# Data classification and handling

## Document status

| Field | Value |
|---|---|
| Phase | 1 — data classification baseline |
| Dataset policy | Synthetic data only |
| Production data | Prohibited |
| Implementation status | Synthetic data handling and log-redaction controls implemented |
| Runtime status | Native tests executed; cloud storage/SIEM handling requires runtime validation |

## Evidence summary

**CONFIRMED FROM SOURCE**

The lab models authentication, ownership-scoped resources, synthetic billing/webhooks, uploads, XML import, mocked AI and security events. All records are synthetic; no customer schema or production dataset is represented.

**SECURITY RECOMMENDATION**

The synthetic lab models only the minimum data needed to test those security boundaries. All people, objects, invoices, attachments, provider events, tokens, and logs are artificial. Data minimization applies even to synthetic values because the lab is intended to teach production-shaped handling.

**REQUIRES RUNTIME VALIDATION**

Later phases must prove that storage, responses, logs, test reports, and CI artifacts follow this policy. This document alone does not enforce retention or redaction.

## Classification model

Classification describes disclosure and handling impact. It does not grant access: authorization policy remains a separate decision.

| Class | Definition | Public repository rule | Typical lab examples |
|---|---|---|---|
| `PUBLIC` | Deliberately publishable information whose disclosure creates no material security or privacy impact | May be committed after review | Documentation, non-sensitive policy, published SBOM, public attestations |
| `INTERNAL` | Operational information intended for project contributors but not inherently secret | Commit only when it improves the public project and reveals no environment detail | Synthetic architecture metadata, non-sensitive test names, tool configuration |
| `CONFIDENTIAL` | Data that could reveal identity, ownership, business state, private content, or security evidence | Use synthetic fixtures; minimize in source and artifacts | Synthetic email, property/invoice records, attachment metadata, audit events |
| `RESTRICTED` | Credentials, authenticators, signing material, or content whose exposure can grant authority | Never commit a usable value; use runtime-generated synthetic values or unmistakable placeholders | Passwords, JWTs, reset tokens, webhook secrets/signatures, private keys |

When classification is uncertain, use the more restrictive class until the data owner decides otherwise.

## Data inventory

| Asset ID | Data element | Class | Needed for | Required handling |
|---|---|---|---|---|
| `A-IDENTITY` | Synthetic user ID | `CONFIDENTIAL` | Ownership and audit correlation | Use opaque identifiers; expose only when contract requires it |
| `A-IDENTITY` | Synthetic email or login name | `CONFIDENTIAL` | Authentication and enumeration tests | Clearly fake domain; normalize; never use a real mailbox |
| `A-SECRETS` | Password input | `RESTRICTED` | Authentication tests | Transient only; never log, persist, snapshot, or place in a URL |
| `A-SECRETS` | Password verifier/hash | `RESTRICTED` | Local authentication state | Store only a one-way verifier; never return it |
| `A-SECRETS` | JWT access token | `RESTRICTED` | Authenticated test calls | Short-lived synthetic token; redact from logs and reports |
| `A-SECRETS` | Reset or invitation token | `RESTRICTED` | Token lifecycle tests | Opaque, expiring, single-use; store a verifier where practical; never log |
| `A-AUTHZ` | Role and ownership relation | `CONFIDENTIAL` | Authorization policy | Server-controlled; clients cannot assign privileged values |
| `A-DOMAIN` | Synthetic property record | `CONFIDENTIAL` | BOLA/IDOR and mass-assignment tests | Minimize fields; filter responses; clean per test |
| `A-PAYMENT` | Synthetic invoice record | `CONFIDENTIAL` | Billing ownership and amount-binding tests | Server binds owner and amount; never accept authoritative client values |
| `A-FILES` | Attachment bytes | `CONFIDENTIAL` | Upload validation tests | Safe fixtures only; bounded size; isolated non-executable storage; delete after test |
| `A-FILES` | Original attachment name and type claim | `CONFIDENTIAL` | Mismatch and traversal tests | Treat as untrusted metadata; sanitize display; generate server-side storage name |
| `A-FILES` | XML document | `CONFIDENTIAL` | Safe-parser regression tests | Safe fixtures only; size/depth limits; no external resolution |
| `A-AI` | AI parse input and mocked output | `CONFIDENTIAL` | Prompt/output boundary tests | Minimize content; no secrets; validate output; apply quotas |
| `A-SECRETS` | Synthetic webhook secret | `RESTRICTED` | Signature verification tests | Generate/provide locally; never use a real provider secret; redact everywhere |
| `A-SECRETS` | Webhook signature and raw body | `RESTRICTED` | Integrity and replay tests | Keep only for request processing and bounded test fixtures; never emit in logs |
| `A-PAYMENT` | Webhook event ID/state | `CONFIDENTIAL` | Idempotency and replay state | Unique synthetic ID; preserve processing state atomically |
| `A-LOGS` | Security event | `INTERNAL` or `CONFIDENTIAL` | Detection and test evidence | Structured fields, opaque IDs, no raw secrets/content, bounded retention |
| `A-LOGS` | Correlation ID | `INTERNAL` | Request-to-event traceability | Server-generated or strictly validated; prevent log injection |
| `A-SOURCE` | Lab source and configuration | `PUBLIC` after review | Reusable implementation and policy | Exclude secrets, private routes, captured data, and environment-specific topology |
| `A-ARTIFACT` | Test report and scanner finding | `INTERNAL` until reviewed | Engineering evidence | Review for secrets and sensitive paths before publication |
| `A-ARTIFACT` | SBOM and public provenance | `PUBLIC` after review | Supply-chain transparency | Publish component metadata; exclude secrets and private build context |
| `A-CLUSTER` | Kubernetes configuration and metadata | `INTERNAL` until reviewed | Later hardening examples | No real endpoint, namespace, credential, or provider identifier |
| `A-AVAILABILITY` | Size, rate, time, and concurrency budgets | `INTERNAL` | Deterministic resource controls | Keep explicit and testable without publishing sensitive production thresholds |
| `A-SECRETS` | CI token, signing key, cloud credential | `RESTRICTED` | Later delivery examples | Never store in repository or ordinary artifacts; least privilege and short lifetime |

## Data by capability group

| Capability | Data entering the boundary | Data allowed to leave | Data that must not leave |
|---|---|---|---|
| Authentication | Synthetic identifier and password | Generic result; short-lived token on success | Password, verifier, detailed account-existence signal |
| Password reset | Synthetic identifier and reset token | Generic request result; bounded success/failure result | Raw token, account enumeration detail |
| Owned properties | Requested action and resource identifier | Fields permitted for the authorized actor | Another owner's protected fields or server-controlled ownership fields |
| Invoice retrieval | Resource identifier | Minimum authorized invoice view | Another user's record, internal provider or binding metadata |
| Upload | Untrusted name, claimed type, bytes | New opaque attachment ID and safe metadata | Server path, raw validation internals, unrelated stored content |
| Webhook | Signature metadata and raw synthetic event | Minimal acknowledgement | Secret, signature, raw body, internal amount/owner data |
| XML import | Bounded untrusted document | Validated import result or generic error | Parser internals, file paths, resolved external content |
| AI parse | Minimized untrusted text/file content | Validated mocked result | hidden configuration, secrets, unrestricted tool or URL output |

The final response schema for each capability is an implementation-phase decision and must be verified with positive and negative tests.

## Handling rules by lifecycle stage

### Collection

- collect only fields required for a named testable control;
- reject unexpected fields rather than silently granting meaning to them;
- prohibit real names, addresses, emails, account numbers, invoice data, and uploaded documents;
- never accept secrets in path parameters or query strings;
- bound request size before expensive parsing.

### Processing

- keep authorization decisions server-side;
- separate validation of shape from authorization to act;
- treat provider responses, XML, file metadata, and AI output as untrusted;
- allow no external resolution or egress outside explicit local stubs;
- avoid copying restricted values into exception messages.

### Storage

- persist the minimum synthetic state needed for a test;
- store password and reset-token verifiers rather than recoverable secrets where practical;
- store attachments outside executable or publicly served directories;
- use server-generated identifiers and names;
- isolate each test's data and perform idempotent cleanup;
- do not add serialized in-memory state, future runtime databases, uploaded files, tokens, or secret-bearing environment files to Git.

### Transmission

- keep lab traffic on loopback or the isolated container network;
- never send a test payload to a real provider or arbitrary host;
- use authorization-aware response filtering;
- use HTTPS and managed secret delivery when adapting the design to a shared or production environment.

### Retention and disposal

- make local test state disposable and reproducible from synthetic factories;
- clean attachments, event state, and per-test records after use;
- retain CI evidence only for a documented period and audience;
- revoke/expire runtime-generated synthetic tokens after the test window;
- review artifacts before public release;
- define legal, privacy, and incident retention separately for any real deployment.

## Logging and evidence policy

### Allowed fields

- timestamp;
- event name;
- opaque synthetic actor ID;
- resource type and opaque resource ID;
- action and result;
- validated correlation ID;
- stable error or policy reason code;
- bounded, non-sensitive request metadata such as validated content length/type category.

### Prohibited fields

- password or password verifier;
- JWT, refresh token, reset token, invitation token, API key, or private key;
- webhook secret, signature, or raw body;
- OAuth authorization code;
- raw attachment, XML, prompt, model output, or parsed document content;
- full authorization header, cookie, or environment dump;
- real personal, tenant, payment, or provider data;
- stack traces or file paths in a client response.

**SECURITY RECOMMENDATION**

Redaction must happen before serialization to the event sink. A later processor cannot reliably remove a secret that has already reached console output, a CI log, or an exception collector.

## Fixtures and public examples

- reserve a clearly non-real email domain for synthetic identities;
- use generated opaque identifiers instead of values copied from source;
- keep file and XML fixtures harmless, minimal, and purpose-specific;
- represent a secret in documentation with a placeholder such as `REPLACE_ME_WITH_LOCAL_SYNTHETIC_VALUE`;
- generate token-like values at runtime when the test needs realistic entropy;
- never paste a captured token, webhook payload, document, log, or scanner result from another environment;
- review golden snapshots because they can preserve confidential responses indefinitely.

## CI/CD and artifact handling

**SECURITY RECOMMENDATION**

- grant each workflow only the permissions it requires;
- prefer short-lived identity and environment-scoped secrets over long-lived repository secrets;
- prevent untrusted pull-request input from becoming a shell command or artifact path;
- mask restricted values, while recognizing that masking is not a substitute for avoiding output;
- exclude request bodies and environment dumps from normal test reports;
- scan repositories and relevant artifacts for accidental secrets;
- publish SBOM and provenance only after reviewing them for private paths or build metadata;
- restrict sensitive security reports to the team that can remediate them.

## Runtime validation checklist

**REQUIRES RUNTIME VALIDATION**

The working lab and CI must later demonstrate that:

1. no fixture contains real personal or provider data;
2. unexpected privileged fields are rejected and never persisted;
3. password, token, signature, raw-body, and content fields are absent from logs;
4. unauthorized responses contain neither protected fields nor existence signals beyond the chosen contract;
5. uploaded bytes and synthetic repository records are cleaned between tests;
6. test reports, traces, screenshots, and scanner artifacts contain no restricted values;
7. reset tokens expire and cannot be reused;
8. webhook event state enforces idempotency without storing the signing secret;
9. AI, XML, and URL-policy tests produce no non-local network request;
10. public SBOM and provenance output contains no secret or private build context.

No item in this checklist has been executed as part of Phase 1.

## Learning checkpoint — data classification

### What is it?

Data classification assigns handling requirements according to the impact of disclosure, modification, loss, or misuse.

### Threat

Without classification, passwords can enter logs, test fixtures can contain real data, security artifacts can become a new leak, and public documentation can expose private architecture details.

### Why it matters

Classification connects abstract confidentiality requirements to concrete decisions about collection, storage, responses, logging, retention, CI, and publication.

### Where it belongs in SDLC

Classify data during design, encode handling in requirements and schemas, test it during implementation, and reassess it when a new field, integration, artifact, or environment is introduced.

### Implementation

The lab uses four classes and permits only synthetic data. Authenticators are restricted, owned records and untrusted content are confidential, and public artifacts require review.

### How to verify locally

Later tests will inspect responses, stored state, structured events, cleanup behavior, and generated reports for prohibited fields and cross-owner disclosure.

### CI/CD integration

Secret scanning, artifact review, minimal test reporting, scoped retention, and least-privilege workflow identity enforce parts of the classification policy.

### Security gate

Block release when a usable secret, real personal data, cross-owner record, raw restricted body, or unreviewed sensitive artifact is detected. Findings still require validation and an auditable exception path.

### False positives / limitations

Pattern matching can flag harmless synthetic values and miss encoded or context-specific data. Classification needs data ownership, code review, runtime tests, and incident handling in addition to scanners.

### Real-world usage

A production classification program maps data owners, legal obligations, residency, encryption, backup, retention, deletion, monitoring, and access review to each system of record and data flow.

### Interview answer

I classify data before selecting controls. In this lab, credentials and tokens are restricted, owner-scoped records and untrusted content are confidential, and only reviewed documentation, SBOMs, and provenance are public. Then I translate the labels into response filtering, redaction, retention, cleanup, CI artifact rules, and tests for unauthorized disclosure.
