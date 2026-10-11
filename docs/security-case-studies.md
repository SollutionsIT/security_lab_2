# Security case studies: findings, blocked abuse and remaining risk

This page separates **detected dependency advisories**, **successful control verification**, **source-inspected weaknesses** and **modeled threats**. No customer incident, active intruder or production exploit was discovered. The examples below use real local runs of this fictional lab.

Case-study snapshot verification: **11 October 2026**, Python 3.12.14 compatibility run. Public, sanitized totals and raw-artifact SHA-256 hashes: [case-studies-latest.json](evidence/case-studies-latest.json). Later CI/Gherkin extensions add tests and have their own entry in the [execution ledger](../PROJECT_STATUS.md); this retained snapshot does not silently inherit their counts. Private/local raw reports remain gitignored. Hashes link the snapshot to retained artifacts; they are not digital signatures or independent attestations.

## At a glance

| Case | Evidence category | Observed result | My decision |
|---|---|---|---|
| CS-01 Dependency advisories | Real scan detection; version remediation | Earlier audit: 2 critical + 5 high + 3 moderate package entries. Current: 0 critical/high, 20 moderate; production-only: 0 entries | P1 compatible updates and retest; P2 triage remaining dev chain |
| CS-02 Cross-owner access/change | Blocked synthetic abuse; not a discovered BOLA | Owner GET 200; other-user GET/PATCH 404; unchanged state + correlated denial; 20 matrix cases passed | Ownership was a P0 design concern; retain P1 regression coverage |
| CS-03 Mass assignment | Blocked synthetic abuse | 5 cases passed: protected/nested fields rejected with 400 and no partial mutation | P1 DTO and invariant verification |
| CS-04 Forged/replayed webhook | Blocked synthetic abuse | 8 cases passed: signatures/freshness/binding/idempotency and state effects | P1 integrity boundary; require production transaction review |
| CS-05 Upload/XML/resource abuse | Control verification, not exploitation | 7 upload + 7 XML + 4 rate-limit cases passed | P1 input/resource controls; no DDoS or malware-resilience claim |
| CS-06 Misleading security evidence | Source-inspected implementation weakness; current synthetic regressions | Missing report collections rejected; Trivy secret records preserved; 21 gate/evidence tests passed | P1 verification integrity; no live Semgrep/Trivy scan implied |

## CS-01 — An actual dependency scan led to a fix

**What I observed.** A retained earlier `npm audit` report from this lab recorded 10 affected package entries, including runtime dependencies and development tooling. These are not ten unique CVEs or ten demonstrated exploitable application flaws. Multer was pinned to `2.2.0`; NestJS packages were `11.2.1`. The advisories concerned multipart handling and other dependency paths.

**A timely example.** [GHSA-3pph-fpjx-jg34](https://github.com/advisories/GHSA-3pph-fpjx-jg34), published in September 2026, covers Multer `>=2.2.0 <2.4.0` and is fixed in `2.4.0`. This particular advisory is moderate and storage-specific; the package's high audit classification also reflected other advisories. I did not reproduce an aborted-upload exploit or prove that the disk-storage path was reachable in this application's setup.

**Why I prioritized it.** Known affected dependencies at a request-processing boundary, plus compatible fixes, justified P1 maintenance. Loopback-only exposure and no exploit proof meant I did not present it as an active production emergency or a discovered remote-code-execution bug.

**What changed.** I refreshed compatible transitive resolutions, updated NestJS to `11.2.7` and Multer to `2.4.0`, and reran behavioral checks. I did not run `npm audit fix --force` to force an incompatible downgrade. Source and lockfile: `lab-api/package.json`, `lab-api/package-lock.json`.

**What the new run proved.** Fresh full audit: 0 high/critical, 20 moderate package entries. Fresh `--omit=dev` audit: 0 reported entries. API suite: 72/72 passed. The 71/71 Jest result is retained in the [execution ledger](../PROJECT_STATUS.md); it was not rerun solely for this documentation extension.

**What remains.** Moderate reports propagate through the `sprintf-js` / `argparse` / legacy `js-yaml` / Istanbul / Jest development chain. Production-only filtering is context, not a waiver: build/test tools may process untrusted material or run with release authority. I retain WARN and would escalate if a consequential reachable path is confirmed. No KEV membership or EPSS value was measured for these findings.

## CS-02 — “Logged in” did not mean “authorized”

**Threat.** An authenticated ordinary user substitutes another owner's property ID and tries to read or update it. The potential impact is data disclosure or unauthorized change. Primary classification: OWASP API1 BOLA / CWE-639; not a bespoke ATT&CK technique.

**Actual local requests.** The ownership demonstration ran real HTTP calls against loopback, using two synthetic users. Owner read: 200; cross-owner read: 404; cross-owner PATCH: 404. The original resource stayed identical, and its denial event matched the supplied correlation ID. The broader authorization matrix passed 20 cases covering object/function/action/state combinations.

**Control and evidence.** `PropertiesService.isAllowed()` checks role, owner and archived state before mutation; `tests/security/test_authorization_matrix.py` checks responses, disclosure, state and event fields. Minimal excerpt from the actual service:

```ts
if (actor.role === Role.Admin) return true;
if (actor.id !== property.ownerId) return false;
return action === 'read' || property.state !== PropertyState.Archived;
```

**My reasoning.** This came before extra scanners because only application logic knows who owns the record. A 404 is useful concealment, but unchanged state is the decisive negative-test assertion. A successful test shows the implemented control held for those inputs; it does not mean I found and exploited a BOLA bug.

**Residual risk.** Uncovered object types/actions, administrator misuse, new routes and real multi-tenant database races remain review topics.

## CS-03 — An invalid update could not partially apply

**Threat.** The owner sends a valid `title` together with a protected `ownerId`, `role` or `isVerified`, or adds `ownerId` inside an address object. A naive object merge could transfer authority or partially change state before failing.

**Observed result.** All 5 cases in `tests/security/test_mass_assignment.py` passed: HTTP 400 and an unchanged original property. The controller's validated DTO permits documented fields; unknown/protected fields are rejected.

Actual assertion pattern:

```python
assert response.status_code == 400
assert property_from_state(api.state(), property_id) == before
```

**My decision.** P1 verification of request boundaries, informed by CWE-915 / object-property authorization. Validation is necessary but not sufficient for price limits, ownership transitions or other future business rules.

## CS-04 — A signature did not replace business validation

**Threat.** A forged webhook marks an invoice paid; an old signed event is replayed; a duplicate applies twice; or a validly signed payload supplies an incorrect amount/order binding.

**Observed result.** All 8 `tests/security/test_stripe_webhook.py` cases passed. Missing/invalid signatures and stale messages returned 401 without changing an open invoice. A valid event applied once; a duplicate was reported as duplicate with only one event record. Amount-binding and modified-body checks also passed.

**Controls.** Raw-body HMAC verification, timing-safe comparison, 300-second timestamp tolerance, server-side invoice/order/amount/currency binding and event-ID claiming in `lab-api/src/boundaries/webhook/webhook.service.ts`.

**My decision.** P1 integrity requirement. Trust is checked at several independent boundaries: signature → freshness → business binding → idempotency. Provider stubs and in-memory state do not establish real payment correctness or multi-process exactly-once behavior; production needs transactions and a durable uniqueness constraint.

## CS-05 — Small hostile inputs stayed inside bounded tests

**Threat.** An untrusted upload uses traversal names, inconsistent MIME/magic bytes or excessive size; XML uses DTD/entities or excessive size/depth/node count; repeated expensive requests consume the local budget.

**Observed result.** Upload 7/7, XML 7/7 and rate-limit 4/4 cases passed. XML DTD/entities were rejected with 400; oversized XML with 413. Upload tests exercise server-generated names and safe download headers alongside rejected inputs. The tests do not download external entities, execute malware or conduct destructive load attacks.

**My decision.** P1 boundary verification. Code: `lab-api/src/boundaries/upload/`, `xml/`; tests: `test_upload_security.py`, `test_xml_security.py`, `test_rate_limiting.py`.

**Residual risk.** Well-formed malicious file content, parser defects, cross-process quotas, antivirus/CDR and volumetric DDoS are not covered. A local rate-limit test is not proof of operational availability protection.

## CS-06 — Missing evidence must not look like a clean scan

**How this was identified.** Source inspection during portfolio preparation showed that missing scanner collections could fall back to empty results, and the Trivy adapter omitted `Secrets` entries. This was an evidence-integrity weakness, not an observed CI compromise or a live scanner finding.

**What changed and was executed.** Normalization now rejects missing collections; gate schema validation rejects missing finding/scanner data; the Trivy adapter retains secret detections without automatically declaring them verified credentials. Current synthetic-input tests confirm those behaviors. The new evidence exporter also rejects empty JUnit and inconsistent audit totals, and explicitly omits an unavailable historical baseline on a fresh clone. Total current gate/evidence unit results: 21/21 passed.

**My decision.** P1, because security automation must distinguish “nothing detected” from “nothing usable was produced.” Tests live in `tests/gate/test_normalization.py`, `test_security_gate.py`, `tests/portfolio/`. Operational scanner failures and triage still need actual CI execution evidence.

## Reproduce the current evidence safely

Start the built native API with `make lab-native` in a separate terminal, then:

```sh
mkdir -p reports/case-studies
PYTEST_ADDOPTS=--junitxml=reports/case-studies/api-security.xml make security-test
.venv/bin/python -m pytest tests/gate tests/portfolio --junitxml=reports/case-studies/gate-tests.xml
npm --prefix lab-api audit --audit-level=high --json > reports/case-studies/npm-audit.json
npm --prefix lab-api audit --omit=dev --audit-level=high --json > reports/case-studies/npm-audit-production.json
.venv/bin/python security/scripts/build_case_study_evidence.py
make publication-check secrets
```

The exporter expects the retained historical baseline `reports/portfolio/npm-audit.json`. On a fresh clone, use `build_case_study_evidence.py --current-only` instead; it explicitly omits the unavailable historical comparison. Do not fabricate a baseline or downgrade to vulnerable software merely to recreate an earlier count. Dependency results may change with the advisory database.

No automatic publishing or external target testing is part of these steps. Only reviewed aggregate counts/hashes and synthetic demo observations enter `docs/evidence/`; tokens, credentials, stdout/stderr and raw API bodies do not.
