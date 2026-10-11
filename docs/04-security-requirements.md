# Security requirements

## Evidence contract

These are design requirements for the independent synthetic lab, not claims about any customer application or proof that a control works.

- **CONFIRMED FROM SOURCE**: the lab source contains the architectural component; runtime effectiveness is a separate claim.
- **SECURITY RECOMMENDATION**: the requirement and control selected for this lab.
- **REQUIRES RUNTIME VALIDATION**: the implementation must produce the named verification evidence.

Mappings are navigation aids rather than compliance claims. OWASP ASVS 5.0.0 is used by control topic, OWASP Top 10:2025 and API Security Top 10:2023 by category, WSTG by test family, and CWE by likely weakness class. A mapped control is not a certification.

## Requirement catalogue

| Requirement | Shall statement | Threats | Verification | Standards mapping |
|---|---|---|---|---|
| `SEC-AUTH-001` | Login shall use a typed bounded DTO, a password verifier, a generic failure contract, and deterministic abuse throttling. | `T-AUTH-001` | `VER-AUTH-001`, `VER-RATE-001` | ASVS Authentication; Top 10 A07:2025; API2:2023; CWE-307 |
| `SEC-JWT-001` | Access tokens shall verify signature, expiry, exact issuer and audience, and an explicit algorithm allowlist; identity shall not imply object authority. | `T-AUTH-001`, `T-AUTHZ-001` | `VER-JWT-001`, `VER-AUTHZ-001` | ASVS Token-based Session Management; A07:2025; API2:2023; CWE-347 |
| `SEC-RESET-001` | Reset requests shall not enumerate accounts; tokens shall be opaque, random, stored as digests, short-lived, single-use, throttled, and absent from logs. | `T-RESET-001`, `T-LOG-001` | `VER-RESET-001`, `VER-LOG-002` | ASVS Credential Recovery; A07/A09:2025; API2:2023; CWE-640 |
| `SEC-INPUT-001` | JSON endpoints shall use typed operation-specific DTOs, reject unknown fields, validate nested values/ranges/URLs, require intended content types, and bound request size. | `T-INPUT-001`, `T-RESOURCE-001` | `VER-INPUT-001`, `VER-MASS-001` | ASVS Validation; A05/A10:2025; API3/API4:2023; CWE-20 |
| `SEC-AUTHZ-001` | Every protected action shall evaluate trusted actor, action, server-side owner, role, and resource state; denials shall disclose no protected data or side effect. | `T-AUTHZ-001` | `VER-AUTHZ-001` | ASVS Authorization; A01:2025; API1/API3:2023; CWE-639/863 |
| `SEC-AUTHZ-002` | Administrative functions shall deny ordinary users independently of UI visibility or JWT presence and shall create a redacted security event. | `T-AUTHZ-002` | `VER-AUTHZ-002`, `VER-LOG-001` | ASVS Authorization; A01:2025; API5:2023; CWE-862 |
| `SEC-WEBHOOK-001` | A synthetic payment event shall be authenticated over exact raw bytes, freshness checked, idempotently recorded, and server-bound to invoice, amount, and valid state transition. | `T-WEBHOOK-001` | `VER-WEBHOOK-001` | ASVS Web Services; A04/A08:2025; API10:2023; CWE-345/294 |
| `SEC-UPLOAD-001` | Uploads shall enforce byte limit, extension/MIME/magic agreement, generated storage name, non-executable storage, traversal resistance, and safe download headers. | `T-UPLOAD-001` | `VER-UPLOAD-001` | ASVS Files and Resources; A01/A02/A10:2025; API4/API8:2023; CWE-22/434 |
| `SEC-XML-001` | XML parsing shall reject DTD/entities, perform no external resolution, and bound bytes, depth, and node count. | `T-XML-001` | `VER-XML-001` | ASVS Validation; A05/A10:2025; API4/API7:2023; CWE-611/776 |
| `SEC-SSRF-001` | URL policy shall canonicalize and allowlist scheme and host, reject IP/private/loopback/link-local/metadata targets, forbid redirects, and define timeout/byte limits without making a lab network request. | `T-SSRF-001` | `VER-SSRF-001` | ASVS SSRF; A01:2025; API7:2023; CWE-918 |
| `SEC-AI-001` | The mocked AI boundary shall minimize and bound input, treat output as untrusted, validate an output schema, allowlist tools/URLs, and enforce quotas without secrets in prompts. | `T-AI-001`, `T-RESOURCE-001` | `VER-AI-001`, `VER-LOG-002` | ASVS Validation; A06/A10:2025; API4/API10:2023; CWE-20 |
| `SEC-LOG-001` | Security events shall be structured and correlated while excluding credentials, tokens, signatures, raw sensitive payloads, unnecessary PII, and attacker-controlled control characters. | `T-LOG-001` | `VER-LOG-001`, `VER-LOG-002` | ASVS Logging; A09:2025; API8:2023; CWE-117/532 |
| `SEC-SECRET-001` | Configuration shall use synthetic placeholders locally, fail production startup on placeholder/weak secrets, and scan source without storing a real credential. | `T-SECRET-001` | `VER-SECRET-001` | ASVS Configuration; A02/A04:2025; API8:2023; CWE-798 |
| `SEC-CI-001` | Workflows shall use least privilege, immutable action references, bounded execution, isolated untrusted PRs, and no PR-controlled shell interpolation. | `T-CI-001` | `VER-CI-001` | A03/A08:2025; CWE-78/829 |
| `SEC-SUPPLY-001` | Reproducible builds shall consume lockfiles, scan dependencies and images, emit an SBOM, and bind release provenance to an immutable artifact digest. | `T-SUPPLY-001`, `T-REGISTRY-001` | `VER-SUPPLY-001`, `VER-ARTIFACT-001` | A03/A08:2025; CWE-1104 |
| `SEC-K8S-001` | The hardened workload shall be non-root, drop capabilities, prevent escalation, use a read-only root filesystem, RuntimeDefault seccomp, bounded resources, restricted network and least-privilege identity. | `T-K8S-001`, `T-K8S-002` | `VER-K8S-001`, `VER-K8S-002` | A01/A02:2025; API8:2023; CWE-250/732 |

## Verification contracts

| Verification | Required evidence |
|---|---|
| `VER-AUTH-001` | Positive login and equal generic contract for unknown user/wrong password |
| `VER-JWT-001` | Rejection of expired, wrong issuer, wrong audience, invalid signature, and non-allowlisted algorithm tokens |
| `VER-RESET-001` | Equal reset-request contract plus expiry and second-use rejection |
| `VER-INPUT-001` | DTO boundary tests for type, length, range, URL, nesting, content type, and body size |
| `VER-MASS-001` | `role`, `ownerId`, and `isVerified` rejected and absent from stored effects |
| `VER-AUTHZ-001` | Parametrized actor/action/owner/state matrix with response, disclosure, pre/post state, and event assertions |
| `VER-AUTHZ-002` | Ordinary-user call to admin operation denied and audited |
| `VER-RATE-001` | Small deterministic threshold tests for login, reset, public form, and AI parse |
| `VER-WEBHOOK-001` | Missing/invalid/valid/duplicate/old/unknown/modified-body cases and invoice side effects |
| `VER-UPLOAD-001` | Valid/oversize/wrong MIME/mismatch/traversal/empty/unsupported cases plus safe download headers |
| `VER-XML-001` | Benign document accepted; DTD/entity, excessive bytes/depth/nodes rejected with no outbound call |
| `VER-SSRF-001` | Pure policy unit tests for allowed host and prohibited scheme/IP/redirect categories |
| `VER-AI-001` | Mock-only input quota, URL/tool policy and output-schema tests |
| `VER-LOG-001` | Required authorization-denial fields captured from the event sink |
| `VER-LOG-002` | Sentinels for password/token/header/reset/OAuth/webhook/payload absent from serialized events |
| `VER-SECRET-001` | Synthetic fixture detected; ordinary scan clean; production placeholder startup rejected |
| `VER-CI-001` | Workflow lint/policy review for permissions, pins, events, timeouts, concurrency and input handling |
| `VER-SUPPLY-001` | Successful lockfile build, normalized SCA status, and generated SBOM artifact |
| `VER-ARTIFACT-001` | Image digest matches provenance/attestation subject before release |
| `VER-K8S-001` | IaC policy validates pod/container identity and security context |
| `VER-K8S-002` | IaC policy validates RBAC, token mount, resources, ingress and NetworkPolicy |

## Traceability examples

| Threat | Requirement | Control | Automated verification | Gate/evidence | Residual risk |
|---|---|---|---|---|---|
| Cross-owner property mutation | `SEC-AUTHZ-001` | Server-side policy + scoped repository mutation | `VER-AUTHZ-001` | New high-confidence regression blocks; JUnit retained | Policy gaps and races outside covered states |
| Replayed signed event | `SEC-WEBHOOK-001` | Raw HMAC + time window + event ID + state machine | `VER-WEBHOOK-001` | Integration failure blocks | Provider compromise and concurrent delivery need production controls |
| Malicious upload metadata | `SEC-UPLOAD-001` | Independent size/name/type/content/storage controls | `VER-UPLOAD-001` | Regression blocks; scanner finding still reviewed | Well-formed malicious content needs sandbox/AV in production |
| Compromised build input | `SEC-CI-001`/`SEC-SUPPLY-001` | Pins, lockfiles, least privilege, SBOM/provenance | `VER-CI-001`/`VER-SUPPLY-001` | Release gate consumes normalized evidence | Trusted maintainer and platform compromise remain |

## Risk decision rule

CVSS is one technical input, never the sole priority. Validation considers evidence quality, exposure, reachability, exploitability, asset criticality, business impact, fix availability, compensating controls, and exception expiry. A tool execution failure is `ERROR`, not a clean scan and not a vulnerability.

## Learning checkpoint

### What is it?

A security requirement is a testable statement of required behavior tied to a threat and an owner.

### Threat

Tool-first programs collect findings without establishing which boundary must be protected or what evidence is sufficient.

### Why it matters

Requirements let development, testing, and release policy agree on the same security contract.

### Where it belongs in SDLC

Write requirements during design, implement them in code and configuration, verify them in PR/build/test stages, and revisit them after incidents or architecture changes.

### Implementation

The `SEC-*` catalogue links modeled threats to implementation behavior and named `VER-*` evidence.

### How to verify locally

Run the named unit/integration checks and consult `PROJECT_STATUS.md`; it records executed evidence separately from scanners and platforms that still require CI/runtime validation.

### CI/CD integration

Jobs emit evidence by verification ID; the gate reasons about normalized evidence rather than raw scanner exit codes alone.

### Security gate

Validated blocking risk fails; uncertain evidence warns; broken evidence collection errors; scoped expiring exceptions require review.

### False positives / limitations

A mapping can be incomplete or become stale. Threat review and production context remain human responsibilities.

### Real-world usage

Add accountable owners, service-specific acceptance criteria, compliance obligations, SLAs, and measurable coverage.

### Interview answer

I do not start with scanners. I connect a concrete threat to a testable requirement, implement the control at the correct trust boundary, define evidence and gate behavior, then record residual risk. That makes security reviewable and keeps a scanner severity from becoming an automatic business decision.
