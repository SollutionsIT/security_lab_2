# ATT&CK, weaknesses and controls: what the mapping means

I use ATT&CK to discuss adversary actions, CWE/OWASP for application weakness classes, and local tests for control evidence. **A contextual ATT&CK mapping is not proof that a full adversary technique was simulated or detected.** The local event rules are experimental examples, not a deployed SIEM.

| Scenario | Primary application classification | ATT&CK context, where appropriate | Control / exact local evidence | Scope limit |
|---|---|---|---|---|
| Authenticated user changes another owner's resource | [CWE-639](https://cwe.mitre.org/data/definitions/639.html); [OWASP API1:2023 BOLA](https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/) | [T1078 Valid Accounts](https://attack.mitre.org/techniques/T1078/) only if a real adversary obtained/abused an account; not a BOLA-specific technique | `lab-api/src/properties/properties.service.ts`; `tests/security/test_authorization_matrix.py`; ownership demo | Synthetic users exercise policies; no stolen credentials |
| Client supplies protected fields in an update | [CWE-915](https://cwe.mitre.org/data/definitions/915.html); API3:2023 object property authorization | No forced one-to-one ATT&CK mapping | DTO allowlist; `tests/security/test_mass_assignment.py` | Does not verify every future business invariant |
| Known software flaw at an exposed HTTP boundary | Publisher GHSA/CVE and its stated CWE/severity | [T1190 Exploit Public-Facing Application](https://attack.mitre.org/techniques/T1190/) describes the possible adversary action | Actual npm advisory detection, patch/version verification and regressions | The lab is loopback-only; no exploitation reproduced; advisory severity is not automatically local severity |
| Malicious package or workflow changes a build | Supply-chain threat, not proof any installed package is malicious | [T1195.002 Compromise Software Supply Chain](https://attack.mitre.org/techniques/T1195/002/) | Lockfile/review, `npm ci --ignore-scripts`, pinned Action refs, minimal job permissions | Static configuration and tool checks do not simulate a malware campaign |
| A package/workflow reads credentials from files | Secret exposure scenario | [T1552.001 Credentials In Files](https://attack.mitre.org/techniques/T1552/001/) | Gitleaks scan/canary; redaction regression; publication hygiene | Secret pattern detection is not a runtime T1552.001 detector |
| Forged/stale/replayed webhook changes an invoice | Integrity/freshness/idempotency requirement | No forced direct ATT&CK equivalent | `webhook.service.ts`; `test_stripe_webhook.py` checks response and state | Synthetic provider; no real financial transaction |
| Hostile file/XML exhausts processing resources | Bounded parser/upload requirements | No DDoS technique claimed from small local limit tests | `test_upload_security.py`, `test_xml_security.py`, `test_rate_limiting.py` | No load/volumetric/DDoS test; no real malware or external-entity network request |
| Prompt injection requests unauthorized tools | Untrusted model/input/output boundary | No full ATT&CK/ATLAS coverage claimed | `test_ai_boundary.py`, mocked allowed-tool/schema policy | No real LLM, agent authority or enterprise AI leakage test |

## Detection examples and what I actually observed

`security/detections/repeated-authorization-denials.yaml` describes a threshold to triage repeated denials; the API records `authorization_denied` with a correlation ID. The current local demo verifies an individual denied change and its matching event. It does **not** run that aggregation rule in Wazuh, Splunk, Sentinel or another SIEM.

The same distinction applies to repeated login failures, suspicious administrative operations and webhook signature failures in `security/detections/`. Adversary-technique relevance, log emission and operational alerting are three different evidence levels.

MITRE ATT&CK mappings here were reviewed on 11 October 2026 against the linked technique pages. They are explanatory context, not formal detection-coverage percentages.
