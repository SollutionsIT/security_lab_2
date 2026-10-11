# Synthetic lab architecture

## Document status

| Field | Value |
|---|---|
| Phase | 1 — target architecture |
| Architecture type | Independent synthetic security lab |
| Implementation status | Working in-memory lab implemented in Phases 4–7 |
| Runtime status | Native build/unit/integration execution recorded in `PROJECT_STATUS.md`; container/platform remains unexecuted |
| Network policy | Loopback or isolated local container network only |

## Evidence summary

**CONFIRMED FROM SOURCE**

The lab contains a NestJS REST API, in-memory persistence, JWT identity, owned resources, synthetic webhook behavior, uploads, XML import and a mocked AI boundary. Source inspection shows implementation structure; runtime effectiveness needs the verification ledger.

**SECURITY RECOMMENDATION**

This deliberately small fictional application demonstrates common security problem classes. Names below describe its synthetic contract, not a customer environment.

**REQUIRES RUNTIME VALIDATION**

The in-memory components and core controls are implemented and tested as recorded in `PROJECT_STATUS.md`. PostgreSQL, cloud services and production deployment remain target architecture requiring runtime validation.

## Architectural goals

- keep the system small enough that every trust decision is reviewable;
- make identity, ownership, role, and resource state explicit inputs to authorization;
- isolate untrusted upload, XML, webhook, and AI-processing boundaries;
- replace every external integration with a deterministic local adapter or stub;
- make side effects and security events observable to tests;
- prevent test-only convenience from bypassing the production-shaped API contract;
- support a fast local vertical slice before adding supply-chain and Kubernetes examples.

## Target component model

| Component | Responsibility | Data handled | Principal security concerns |
|---|---|---|---|
| Synthetic user client | Conceptual browser or HTTP caller for ordinary user flows; no separate UI is required for the working slice | Credentials, bearer token, request data | Untrusted input, token handling, owner isolation |
| Synthetic admin client | Conceptual caller for explicitly authorized administrative flows; no private admin UI is copied | Admin bearer token and bounded requests | BFLA, excessive privilege, auditability |
| Security test runner | Drives deterministic negative and positive cases through the public contract | Synthetic fixtures and expected state | Isolation, repeatability, no privileged shortcut |
| NestJS lab API | Authentication, authorization, validation, orchestration, audit events | All request metadata and domain data | Deny by default, validation, rate/resource limits, redaction |
| Authorization policy layer | Evaluates actor, action, owner, role, and resource state | Identity claims and minimal resource metadata | BOLA/IDOR, BFLA, confused-deputy behavior |
| Repository port | Gives domain and policy code a storage-independent contract | Users, resources, ownership and event state | Scoped operations, state integrity, deterministic replacement |
| Deterministic in-memory repository | Working-lab persistence for Phases 0–8 | Synthetic records, verifiers, ownership and idempotency keys | Per-test isolation, atomic behavior, cleanup, no external dependency |
| Content boundary | Validates and processes attachments, XML, and AI parse requests | Untrusted bytes and text | Type confusion, traversal, XXE, SSRF, injection, exhaustion |
| Local provider adapters | Simulate payment, storage, identity, email, and AI dependencies | Synthetic provider requests and responses | Signature trust, egress control, untrusted output |
| Structured event sink | Captures security-relevant events for local verification | Actor/resource IDs, action, result, correlation ID | Sensitive-data leakage, injection, retention |

No port numbers, credentials, database names, or deployment addresses are defined here. Those values belong to explicit local configuration and must remain synthetic.

## Logical service topology

```text
Synthetic user client -----\
Synthetic admin client -----+--> NestJS synthetic API
Security test runner -------/       |       |        |
                                    |       |        +--> structured local security events
                                    |       |
                                    |       +--> local-only provider adapters and stubs
                                    |
                                    +--> repository port --> deterministic in-memory repository
                                    |
                                    +--> bounded attachment / XML / AI content processing
```

All arrows terminate inside the developer-controlled lab. The topology deliberately has no production or Internet dependency.

**SECURITY RECOMMENDATION** — a production adaptation may replace the in-memory implementation behind the repository port with Prisma/PostgreSQL. That would introduce network identity, credentials, migrations, database authorization, transaction, backup, and tenant-isolation requirements. It is not a dependency of the working lab and is not claimed as implemented here.

## Synthetic domain model

| Entity | Minimal purpose | Security invariant |
|---|---|---|
| `User` | Represents a synthetic identity and role | Credentials and tokens never authorize object access by themselves |
| `Property` | Represents an owner-scoped resource | Read and mutation decisions use server-side ownership and action policy |
| `Invoice` | Represents a user-scoped billing record | Amount, subject, and owner are server-bound and cannot be selected by client claim |
| `Attachment` | Represents metadata for bounded untrusted content | Server controls name, validated type, storage location, and download behavior |
| `WebhookEvent` | Represents a signed event and idempotency state | Signature, freshness, event identity, and processing state are verified before effects |

The entities contain only the fields needed to exercise a security rule. They are not intended to model a real estate or billing product.

## Actors and authorization context

| Actor | Intended capability class | Explicit limit |
|---|---|---|
| `anonymous` | Enter authentication and password-reset flows | No implicit access to owned resources |
| `user` | Perform authenticated operations allowed by policy | Authentication alone grants no cross-object access |
| `owner` | Act on a resource that the server confirms is owned by that user | Client-supplied owner identifiers are not trusted |
| `admin` | Perform explicitly enumerated administrative actions | Admin behavior remains deny-by-default and auditable |
| Local provider stub | Submit a correctly signed synthetic provider event | Not a human role and not a general API principal |

An `owner` is a relationship between a user and an object, not a stronger authentication credential. The same authenticated user may be the owner of one object and a non-owner of another.

## High-level API capability groups

The exact synthetic contract is implemented later. At a high level, the lab will expose only these capability groups:

| Capability group | Minimal operations | Security focus |
|---|---|---|
| Authentication | Login and password reset | Typed input, generic errors, token lifecycle, throttling |
| Owned properties | Retrieve, update, and delete by synthetic identifier | BOLA/IDOR, mass assignment, state and side-effect assertions |
| Invoices | Retrieve a synthetic invoice by identifier | Owner isolation and sensitive-field minimization |
| Attachments | Submit bounded content | Size, type, content, name, storage, and traversal controls |
| Payment events | Receive a synthetic signed event | Raw-body signature, freshness, replay, idempotency, server-side binding |
| XML imports | Submit a bounded XML document | DTD/entity prohibition, no network resolution, depth and size limits |
| AI parsing | Submit content to a mocked parser/model | Prompt boundary, output validation, tool/URL allowlist, quotas and redaction |

These are newly defined lab capabilities. No private endpoint inventory is reproduced.

## Trust boundaries

### TB-01 — Untrusted client to API

Every header, path value, query value, body field, byte sequence, and claimed identifier is untrusted. The API authenticates when required, validates the request contract, authorizes the requested action, applies size/rate limits, and emits a bounded response.

Primary threats: spoofing, mass assignment, injection, enumeration, BOLA/IDOR, BFLA, and resource exhaustion.

### Identity-to-authorization decision point inside TB-01

A valid JWT establishes an authenticated subject under defined algorithm, issuer, audience, and expiry rules. It does not prove that the subject may act on a particular object or function. Server-side policy combines the subject with action, resource ownership, role, and resource state.

Primary threats: token confusion, stale or malformed claims, privilege escalation, and authorization based only on token presence.

### TB-02 — API to data store

The application crosses from request-driven logic into authoritative stored state. In the working lab, this is a conceptual boundary at the repository port: the deterministic in-memory implementation remains in-process but still owns authoritative state and isolation behavior. Data-access operations must preserve owner scoping, atomic updates, idempotency, and state transitions. Tests must inspect state after denied and repeated requests, not only HTTP status.

**SECURITY RECOMMENDATION** — in a production adaptation, this becomes a process and network boundary to a database such as PostgreSQL through a data-access layer such as Prisma. Database identity, least privilege, encrypted transport, migrations, tenant scoping, transactions, backups, and monitoring would then require separate controls and evidence.

Primary threats: cross-owner access, time-of-check/time-of-use errors, partial updates, replay, and orphaned test data.

### Untrusted content processing boundary inside the API

Attachments, XML, and AI inputs remain hostile after authentication. Validation, content inspection, parser configuration, generated names, bounded storage, quotas, and safe output handling are separate defenses.

Primary threats: content-type confusion, path traversal, XXE, unsafe URL fetches, prompt injection, malicious model output, sensitive logging, and resource exhaustion.

### TB-03 — API to local integration mocks

The adapter represents an external trust boundary without contacting a real provider. Payment events require synthetic signature and replay controls; AI and other provider responses are treated as untrusted input. Egress is deny-by-default except for an explicit local stub destination.

Primary threats: forged events, replay, insecure trust in provider fields, SSRF, and compromised third-party output.

### Logging and evidence handling boundary

Security events cross from live processing into diagnostics and retained evidence. Event schemas use stable synthetic identifiers and correlation IDs while excluding secrets, credentials, raw sensitive bodies, and content.

Primary threats: credential or PII disclosure, log injection, excessive retention, and misleading evidence.

### TB-04 — Repository to CI/CD execution

Later phases introduce automation that can execute code, read tokens, publish artifacts, and make release decisions. Workflows therefore require least-privilege permissions, pinned dependencies, trusted input handling, timeouts, concurrency controls, and explicit evidence retention.

Primary threats: workflow injection, dependency compromise, secret exposure, artifact substitution, and unreviewed release bypass.

### TB-05 — CI/CD to artifact registry

Later phases may build and attest synthetic artifacts. The registry boundary changes a local build output into a retained or distributable artifact, so identity, digest, provenance, access, and publication policy must be explicit.

Primary threats: artifact substitution, unauthorized publication, tag mutability, credential exposure, and untrusted build metadata.

### TB-06 — Delivery system to cluster

Kubernetes material is a later security example, not part of the initial working vertical slice. Crossing this boundary would grant a delivery identity authority over platform resources and therefore requires environment protection, least-privilege RBAC, admission policy, immutable artifact identity, and auditable approval.

Primary threats: excessive deployment privilege, confused-deputy behavior, policy bypass, untrusted image deployment, and unintended administrative exposure.

## Security invariants

**SECURITY RECOMMENDATION**

1. Authentication is never treated as authorization.
2. The server derives actor identity and object ownership; a client cannot assign `role`, `owner`, or verification state.
3. A denied request produces no protected state change and no protected-data disclosure.
4. Administrative functions are explicitly allowlisted and audited.
5. Password-reset tokens are opaque, expiring, single-use, and absent from logs.
6. JWT validation uses an algorithm allowlist plus issuer, audience, signature, and expiry checks.
7. Webhook effects occur only after signature, freshness, event identity, and server-side resource binding checks.
8. Client MIME type and filename are metadata, not proof of content safety.
9. XML parsing performs no external entity or network resolution.
10. AI input and output are untrusted; tools, URLs, size, time, and output schema are bounded.
11. Sensitive values never become log or CI artifact content.
12. Every dynamic request remains inside the synthetic local lab.

## Local deployment constraint

**SECURITY RECOMMENDATION**

The working lab must bind only to loopback or an isolated container network. Its authoritative domain state uses the deterministic in-memory repository; local stubs and content storage must not be published beyond what the test runner needs. No adapter may silently fall back to a real external service. Configuration should fail closed when a provider URL, credential, or DAST target violates the lab allowlist.

Kubernetes manifests and supply-chain workflows are later portfolio layers, not a reason to expose this application publicly. Production adaptation requires a separate threat model, platform controls, ownership, monitoring, and approval process.

## Runtime validation backlog

**REQUIRES RUNTIME VALIDATION**

Later phases must provide evidence that:

- the API starts from documented local commands and creates isolated deterministic repository state;
- each actor is denied outside its intended action/object boundary;
- denied and repeated requests leave protected state unchanged;
- parser, size, rate, token, and replay limits are deterministic;
- adapters cannot reach non-local destinations;
- structured events are produced without prohibited fields;
- tests are isolated and repeatable;
- CI uses the same security contract without trusting pull-request-controlled shell input.

## Learning checkpoint — architecture and trust boundaries

### What is it?

A trust boundary is a point where data or authority changes owner, validation level, execution context, or protection assumptions.

### Threat

If a design treats client claims, tokens, stored state, provider responses, parsers, or logs as equally trusted, one compromised boundary can silently grant authority elsewhere.

### Why it matters

Security controls belong at the boundary where trust changes. This makes requirements testable and prevents a single control, such as JWT validation, from being asked to solve unrelated problems.

### Where it belongs in SDLC

Identify components and boundaries during design, refine them in threat modeling, encode them in requirements, and regression-test their invariants throughout delivery.

### Implementation

The target architecture separates request validation, identity, authorization policy, persistence, untrusted content, provider adapters, and security evidence.

### How to verify locally

Later tests will cross each boundary with valid and invalid inputs, compare state before and after, inspect emitted events, and confirm that all dependencies remain local.

### CI/CD integration

Architecture invariants become unit, integration, and security jobs. CI should retain machine-readable results while preventing logs and artifacts from containing restricted data.

### Security gate

A change should not pass when it removes a required authorization check, permits non-local egress, weakens a parser or token invariant, or makes a critical boundary untestable without an approved exception.

### False positives / limitations

A diagram cannot prove enforcement, and a passing test proves only the cases and environment exercised. Concurrency, deployment, and operational controls require separate evidence.

### Real-world usage

In a production system, each boundary would have an owner, data classification, identity mechanism, network policy, telemetry, abuse cases, and documented failure mode.

### Interview answer

I start architecture review by marking where untrusted data or authority changes context. Here, JWT validation proves identity, while a separate policy layer checks action, ownership, role, and state. Files, XML, model output, provider events, persistence, and logs are distinct boundaries, so each gets a focused control and a testable invariant.
