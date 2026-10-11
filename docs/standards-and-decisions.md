# Standards and engineering decisions

This project uses public security guidance to make decisions explainable. It does not reproduce standards text, claim certified compliance or promise complete coverage.

| Reference | How it informs this lab | Inspect the evidence | Boundary |
|---|---|---|---|
| [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/) | Authentication, authorization, validation and log-handling requirements | `docs/04-security-requirements.md`, `lab-api/src/`, `tests/security/` | Topic-level mapping, not a complete ASVS assessment |
| [OWASP API Security Top 10 (2023)](https://owasp.org/API-Security/editions/2023/en/0x11-t10/) | Object/function authorization, resource budgets and unsafe integration inputs | Authorization matrix, mass-assignment, webhook/upload/XML cases | Risk awareness, not ten checks proving security |
| [NIST SSDF v1.1](https://csrc.nist.gov/pubs/sp/800/218/final) | Prepare, protect, produce well-secured software, respond to vulnerabilities | Policies, lockfiles, tests, gates, synthetic finding lifecycle | A small learning implementation, not an organization-wide assessment |
| [ISO/IEC 27001:2022](https://www.iso.org/standard/27001) | Risk ownership, treatment, retained evidence, review and time-bounded exceptions | Risk register, evidence ledger, exception/gate policy | Management-system lens only: no ISMS certification or complete control mapping |
| [OWASP SAMM](https://owaspsamm.org/model/) | Separate governance, design, implementation, verification and operations | Threat model, Secure SDLC map, adoption plan | No maturity score or external audit |
| [Kubernetes security checklist](https://kubernetes.io/docs/concepts/security/security-checklist/) | Least privilege and workload containment | `kubernetes/`, `docs/10-kubernetes-security.md` | Manifests do not prove admission/CNI enforcement |

## Decisions worth discussing in an interview

1. **Server-side ownership:** a trusted login is insufficient; services verify the owner, action and resource state. A denied request must leave state unchanged.
2. **Concealed 404:** inaccessible objects use a concealed response. This reduces existence disclosure but is not a replacement for policy checks.
3. **Synthetic in-memory state:** faster deterministic learning; not durable storage or safe distributed execution. Replace with database transactions in a real pilot.
4. **Explicit test-only helpers:** reset/state/log endpoints support verification, gated by test mode and key. Never deploy them as public operational APIs.
5. **Unvalidated scanner findings:** normalization preserves triage needs; a detector hit is not automatically exploitable. Conversely, scanner or parser errors are not clean results.
6. **Separate collection from enforcement:** Trivy `exit-code: 0` collects results; an actual policy gate is needed to block delivery. See workflow-specific behavior before claiming enforcement.
7. **Redacted evidence:** correlation IDs retain explainability without printing bearer tokens, passwords or payloads.

## A repeatable review

Choose a risk ID → read its requirement → inspect the service/policy → run its negative test → inspect the unchanged state and security event → identify what was not tested → assign an owner and review date for residual risk. Record version and date when running scanners; vulnerability databases change.
