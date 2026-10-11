# How I prioritize security work

This is my documented, AI-assisted portfolio decision rationale, not a record of running a company's security programme. I distinguish **which control to build first** from **which currently confirmed issue needs emergency remediation**. A P0 design concern is not automatically an active incident.

## My method

I start with the asset and unacceptable business outcome, then evaluate an attack path. The qualitative approach is informed by [NIST SP 800-30 Rev. 1](https://csrc.nist.gov/pubs/sp/800/30/r1/final); the P0/P1/P2 labels below are my project convention, not a NIST or ISO scoring standard.

1. **Impact:** could the outcome disclose another customer's data, alter financial-like state, compromise credentials/release integrity or interrupt service?
2. **Exposure and likelihood:** is the boundary public, authenticated, privileged, development-only or loopback-only? Is the vulnerable component actually used?
3. **Evidence confidence:** modeled possibility, scanner detection, version match, demonstrated control failure, or confirmed exploitation? I never upgrade detection into exploitation without evidence.
4. **Threat activity:** for an applicable CVE, I would check KEV and EPSS alongside publisher advice. CVSS describes technical severity; EPSS estimates exploitation in the next 30 days; neither replaces local context. No automated feed or specific score is claimed here. [FIRST CVSS](https://www.first.org/cvss/), [EPSS](https://www.first.org/epss/), [CISA KEV mirror](https://github.com/cisagov/kev-data).
5. **Treatment:** is a compatible fix available, what breaks if I apply it, what compensating control exists, and how will I retest?
6. **Residual risk and review:** document unknowns, an owner, the next verification and any exception expiry. A successful test narrows uncertainty; it does not erase the threat.

## My priorities and actual decisions

| Work item | My priority | Why I put it there | Current disposition |
|---|---|---|---|
| Verified usable secret exposure or demonstrated cross-customer write | P0 containment if discovered in a real scoped environment | Direct authority or sensitive-data loss; act before routine backlog | Not discovered here. Synthetic canary is not a leaked production credential. |
| Ownership isolation and privileged actions | P0 **design order** | Authentication alone cannot protect another customer's records; scanners miss business ownership | Implemented and locally regression-verified; ongoing coverage remains P1, not an open emergency finding. |
| Detected runtime dependency advisories | P1 remediation in this isolated lab | Request-processing dependency, known affected version and compatible fixes available | Updated NestJS/Multer + lockfile; audit and behavior tests rerun. No claim of exploit reproduction. |
| Unusable/partial scanner input and omitted secret detections | P1 verification integrity | A pipeline that mistakes missing evidence for a clean scan can authorize the wrong decision | Parser/gate regression checks now reject incomplete reports and preserve Trivy secret detections; no live Trivy scan claimed. |
| Webhook binding/replay; DTO mass assignment; uploads/XML | P1 control verification | Integrity and resource boundaries; denied requests must not partially mutate state | Positive and negative synthetic cases passed; distributed races/content malware remain untested. |
| Remaining moderate development dependency entries | P2 **triage**, not permanent acceptance | Fresh production-only audit reports zero entries; remaining chain is in build/test tooling | Keep WARN visible; review untrusted config/templates and build privileges. Escalate if a reachable high-impact path is established. |
| Mocked AI policy expansion and deployment templates | P2 extension work | No real model/tool authority or deployed cluster; no measured production exposure | Clearly labeled mocked/configured; platform validation required before adoption. |

I did not optimize for the biggest number of tools or a completely green screenshot. I patched compatible dependencies first, retained unresolved findings, and reran behavior checks. I did not use a forced incompatible downgrade merely to remove advisory warnings.

## Protection choices and best practices

| My decision | Implemented evidence | Production addition I would require |
|---|---|---|
| Deny by default; check actor, owner, role and state server-side | `PropertiesService.isAllowed()`, authorization matrix | Proper tenancy model, transactional checks, full object/action inventory |
| Validate only permitted fields; reject partial updates on invalid DTOs | `UpdatePropertyDto`, mass-assignment cases | Business-invariant checks and reviewed schema evolution |
| Verify token/signature semantics, not just parse data | JWT claim tests; webhook HMAC/freshness/binding cases | Real key rotation, secret store, provider contract and distributed idempotency |
| Constrain untrusted input and resource budgets | File/XML limits, deterministic rate-limit tests | Distributed limits, availability monitoring and reviewed content scanning |
| Make delivery evidence explicit and fail on errors | Normalization and PASS/WARN/FAIL/ERROR regressions | Mandatory branch/release gates, operational triage ownership |
| Minimize disclosed evidence | Redaction tests, correlation IDs, sanitized public aggregates | Secure log transport, retention, alert delivery and incident response |

## What laws and standards contribute

- **GDPR Articles 25 and 32:** privacy-conscious design and security appropriate to risk, including evaluating protective measures. I use synthetic data, ownership checks and repeatable verification to illustrate the engineering direction. This is not a GDPR compliance determination or full privacy programme. [Official regulation](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng).
- **NIS2 Article 21:** risk management, supply-chain and secure development/maintenance concerns for entities within scope. This motivates delivery and vulnerability-management examples; applicability and current national implementation in Poland require separate legal review. I make no NIS2 certification or legal-readiness claim. [Official directive](https://eur-lex.europa.eu/eli/dir/2022/2555/oj?locale=en).
- **ISO/IEC 27001:2022:** risk treatment, ownership, review and evidence within an ISMS lens. The lab is not a certified management system. [ISO](https://www.iso.org/standard/27001).
- **OWASP ASVS / API Security and NIST SSDF:** technical verification topics and secure development practices; their application is traceable in the requirements, tests and workflows. See [standards mapping](standards-and-decisions.md).
- **MITRE ATT&CK / CWE:** ATT&CK describes adversary behavior; CWE describes software weakness classes. Neither is a vulnerability scanner, likelihood calculator or compliance certificate. See [precise mapping](attack-and-control-mapping.md).

An organization's legal obligations depend on its processing, business, role and jurisdiction. This fictional laboratory is not a legal assessment. I do not promise fines avoided, financial savings or incident reduction without measured evidence.
