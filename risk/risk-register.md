# Risk register

## Method

This register uses qualitative NIST-style reasoning. Priority is based on likelihood and impact plus exposure, reachability, exploitability, asset criticality, evidence confidence, fix availability, and compensating controls. CVSS may be added to a validated technical finding, but it never replaces business context.

The rows below are **MODELED SCENARIOS / INHERENT DESIGN PRIORITIES**, not a list of open confirmed vulnerabilities. Likelihood labels are qualitative design judgments, not calibrated probabilities or percentages derived from industry reports. Several controls have local verification evidence; that does not exhaust the scenario or validate production residual risk. See [observed cases](../docs/security-case-studies.md), [my prioritization decisions](../docs/my-security-prioritization.md) and [current threat context](../docs/threat-intelligence-2026.md). Scanner-detected dependency advisories are tracked separately in [OBS-001](findings/OBS-001-dependency-advisories.md).

| Risk | Scenario | Likelihood | Impact | Contextual priority | Planned treatment / evidence | Residual risk |
|---|---|---|---|---|---|---|
| `R-001` | Account attacks and enumeration | Medium | High | P1: public and automatable identity boundary | `SEC-AUTH-001`, `SEC-RESET-001`; auth/reset/rate tests | Distributed attempts and channel compromise |
| `R-002` | Invalid JWT accepted | Medium | High | P1: token is an identity root | `SEC-JWT-001`; issuer/audience/expiry/algorithm tests | Signing-secret compromise |
| `R-003` | BOLA/IDOR across properties/invoices | High | High | P0: IDs are attacker-controlled and records are confidential | `SEC-AUTHZ-001`; matrix plus state/disclosure/event evidence | Missed object/action/state combination |
| `R-004` | BFLA on administrative action | Medium | High | P1: privilege boundary | `SEC-AUTHZ-002`; ordinary-user negative test | Authorized admin abuse |
| `R-005` | Mass assignment/protected field update | Medium | High | P1: writable JSON boundary | `SEC-INPUT-001`; unknown/protected-field tests | Semantic business-rule abuse |
| `R-006` | Webhook forgery/replay/misbinding | Medium | High | P1: public integrity boundary with financial-like state | `SEC-WEBHOOK-001`; eight-case suite + state assertions | Provider compromise and races |
| `R-007` | Unsafe upload | Medium | High | P1: untrusted bytes and storage | `SEC-UPLOAD-001`; seven-case suite + headers | Well-formed malicious content |
| `R-008` | XML entity/resource abuse | Medium | High | P1: parser and possible egress boundary | `SEC-XML-001`; safe no-network fixtures | Parser defects |
| `R-009` | SSRF policy bypass | Medium | High | P1: could cross network/credential boundary in production | `SEC-SSRF-001`; pure policy tests | DNS rebinding/allowlisted compromise |
| `R-010` | AI prompt/output/tool abuse | Medium | Medium | P2: mocked, no consequential real tool | `SEC-AI-001`; schema/allowlist/quota tests | Semantic manipulation |
| `R-011` | Sensitive or incomplete logs | Medium | High | P1: evidence and secret boundary | `SEC-LOG-001`; event schema/redaction tests | Unknown new fields/sinks |
| `R-012` | Secret/default configuration exposure | Medium | Critical | P0 when verified credential; currently hypothesis | `SEC-SECRET-001`; startup and Gitleaks fixture checks | Non-Git secret sources |
| `R-013` | CI workflow privilege/injection | Medium | Critical | P0/P1 depending on credentials and event | `SEC-CI-001`; policy review and action lint | CI platform/trusted maintainer compromise |
| `R-014` | Dependency/artifact substitution | Medium | High | P1: release integrity | `SEC-SUPPLY-001`; lock/SCA/SBOM/provenance | Unknown malicious dependency |
| `R-015` | Excessive Kubernetes workload privilege/exposure | Medium | Critical | P1 until real cluster exposure/reachability is known | `SEC-K8S-001`; IaC and policy checks | Managed plane, CNI and runtime specifics |

## Status transitions

`Modeled → Detected → Validated → Confirmed / False positive → Fixed / Accepted exception → Retested → Closed`

A scanner finding enters `Detected`, never `Confirmed`. An execution/configuration failure enters `Evidence error` and must not be reported as a clean result.
