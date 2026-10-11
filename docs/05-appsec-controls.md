# AppSec controls handbook

Each control follows the same learning path. “Working” refers only to this synthetic lab.

## 1. Authentication and reset

### What is it?
Identity proof using scrypt passwords, bounded JWTs and an opaque reset flow.
### Threat
Credential enumeration, token confusion/replay and reset-token theft.
### Why it matters
Authentication establishes the subject; every later authorization decision depends on its integrity.
### Where it belongs in SDLC
Abuse requirements, protocol design, implementation tests, PR review and runtime detection.
### Implementation
Generic errors, dummy hash, HS256 allowlist, exact issuer/audience/expiry, random token digest, TTL and atomic single use.
### How to verify locally
`npm --prefix lab-api test` and `make security-test` cover wrong credentials, tamper, algorithm/claim/expiry and reset replay.
### CI/CD integration
Unit tests run on PR; integration behavior runs deep.
### Security gate
Regression failure blocks; anomalous login telemetry warns/alerts at runtime.
### False positives / limitations
The lab has no MFA, federation, key rotation or distributed token store.
### Real-world usage
Use asymmetric signing or managed identity where trust domains multiply; rotate and protect signing keys.
### Interview answer
Authentication answers who the actor is, not what they may do. I validate the complete JWT contract and make reset tokens opaque, short-lived and single-use while returning generic responses to prevent enumeration.

## 2. Input validation and authorization

### What is it?
Validation constrains input shape; authorization decides whether this actor may perform this action on this object in this state.
### Threat
Mass assignment, BOLA/IDOR and BFLA.
### Why it matters
A perfectly valid `ownerId` is still unauthorized when supplied by a client.
### Where it belongs in SDLC
DTO/API design, domain policy, code review, regression matrix and audit monitoring.
### Implementation
Strict DTO whitelist plus server-derived owner relationship, admin role and archived-state rules; concealed 404 for object denial.
### How to verify locally
The parametrized matrix asserts status, response equivalence, state and a unique denial event.
### CI/CD integration
Jest on PR and Python matrix in deep CI.
### Security gate
Any allowed cross-owner mutation blocks release.
### False positives / limitations
In-memory policy cannot prove every production query includes tenant scoping.
### Real-world usage
Centralize policy and enforce ownership in repository queries/transactions, not only controllers.
### Interview answer
Validation and authorization solve different problems. I reject unknown fields, but I also derive ownership server-side and test actor × action × owner × state, including side effects and audit evidence.

## 3. Webhook integrity

### What is it?
Authentication and safe processing of asynchronous provider events.
### Threat
Forgery, raw-body mutation, replay, duplicates, reordering and attacker-controlled amount/resource binding.
### Why it matters
A valid signature alone does not make a business state transition correct.
### Where it belongs in SDLC
Integration design, transaction implementation, contract tests and operational replay monitoring.
### Implementation
Synthetic raw-body HMAC, timestamp tolerance, atomic event claim and server-side order/amount/currency lookup.
### How to verify locally
Run webhook unit/Python tests; no real Stripe call occurs.
### CI/CD integration
Unit on PR, full cases deep.
### Security gate
Forgery/replay/binding regression fails.
### False positives / limitations
The mock does not prove Stripe SDK semantics or distributed transaction isolation.
### Real-world usage
Use provider libraries, durable event IDs and a transaction/outbox strategy.
### Interview answer
I verify the exact raw bytes and timestamp, claim the event ID atomically, and bind every financial value to server-side state. Idempotency and business binding are separate from signature validity.

## 4. File upload

### What is it?
Treat files and metadata as hostile while keeping storage and retrieval least-privileged.
### Threat
Traversal, polyglots/type spoofing, resource exhaustion and cross-owner disclosure.
### Why it matters
Client MIME and filename are claims, not evidence.
### Where it belongs in SDLC
API/storage design, limits, authorization, content processing and safe delivery.
### Implementation
1 MiB limit, MIME/extension/magic agreement, UUID name, OS-temp confinement, 0600 mode, owner binding and attachment headers.
### How to verify locally
Seven negative classes plus owner/admin/anonymous retrieval tests.
### CI/CD integration
Unit and deep integration.
### Security gate
Traversal, type bypass or BOLA regression fails.
### False positives / limitations
No malware scanning or real object-store ACL is modeled.
### Real-world usage
Quarantine, asynchronous scanning, immutable buckets and signed short-lived download authorization.
### Interview answer
I validate size, extension, declared MIME and magic independently, generate the storage key, store outside static roots, bind ownership server-side and serve with download/nosniff headers.

## 5. XML, SSRF and AI boundaries

### What is it?
Bounded parsing plus explicit policies around network/model trust boundaries.
### Threat
XXE, parser exhaustion, SSRF, prompt injection, unsafe tools and untrusted model output.
### Why it matters
Parsers and models can turn data into computation or external actions.
### Where it belongs in SDLC
Integration design, allowlists, resource budgets, unit policy tests and telemetry.
### Implementation
Reject DTD/entities, cap bytes/depth/nodes, never resolve network; pure HTTPS/host/IP/redirect policy; mock model, allowed tools, output schema and quotas.
### How to verify locally
Safe fixtures and policy tests execute without outbound requests.
### CI/CD integration
PR unit and deep API checks.
### Security gate
External-resolution/tool-bypass regression fails.
### False positives / limitations
DNS rebinding and provider model behavior require production-grade resolver/gateway testing.
### Real-world usage
Resolve and pin allowed destinations, revalidate redirects, sandbox tools and minimize prompt data.
### Interview answer
I treat XML, URLs and model output as untrusted. The lab tests the policy without attacking metadata services: no DTD/network resolution, exact host rules, no redirects, resource quotas and an allowlisted mock tool boundary.

## 6. Security logging

### What is it?
Structured events designed for detection without becoming a secret/PII leak.
### Threat
Invisible abuse, log injection and credential exposure in telemetry.
### Why it matters
Prevention fails; response needs trustworthy, correlatable evidence.
### Where it belongs in SDLC
Event schema design, implementation redaction, tests, collector/SIEM configuration and response runbooks.
### Implementation
Bounded event buffer, stable fields/correlation ID and recursive redaction of secret-shaped keys.
### How to verify locally
`test_log_redaction.py` and redaction unit tests inspect retained events.
### CI/CD integration
Schema/redaction regressions run automatically; SIEM delivery is a production recommendation.
### Security gate
Known credential material in logs is immediate fail after validation.
### False positives / limitations
Key-name redaction cannot understand every sensitive free-text value.
### Real-world usage
Data classification, field allowlists, transport integrity, retention/access control and sampled detection tests.
### Interview answer
I log decisions and identifiers, not credentials or full payloads. Stable structured events with correlation IDs support detection, while automated redaction tests stop logs becoming a second data breach.

## 7. CI, container and Kubernetes

### What is it?
Protect the path from commit to artifact and contain the running workload.
### Threat
Malicious dependencies/Actions, runner credential theft, artifact replacement, privilege escalation and lateral movement.
### Why it matters
Compromising delivery can bypass every application control.
### Where it belongs in SDLC
PR, build, release, deploy and runtime policy.
### Implementation
Exact dependencies/lockfile, Action SHAs, least permissions, digest-pinned base, non-root/read-only runtime, no workload token and NetworkPolicy.
### How to verify locally
Make targets run config/image scans when tools exist; CI retains reports/SBOM/provenance.
### CI/CD integration
Fast PR, deep and release workflows are separated.
### Security gate
Validated credential, reachable Critical or excessive production privilege fails; scanner failure is `ERROR`.
### False positives / limitations
IaC scan cannot prove admission, CNI, registry or runtime enforcement.
### Real-world usage
Protected environments, OIDC federation, digest promotion, admission policy and runtime detection.
### Interview answer
I secure both build identity and runtime containment: pin executable inputs, minimize CI permissions, scan the exact artifact, attach SBOM/provenance, deploy by digest and run with the least Kubernetes identity and privileges.
