# OBS-001 — Actual dependency advisories and remaining development risk

- **Category:** observed scanner findings, not demonstrated exploitation.
- **Scope/date:** this synthetic lab; 11 October 2026. Runtime API is loopback-only.
- **Evidence:** [sanitized counts and artifact hashes](../../docs/evidence/case-studies-latest.json); local raw audits are gitignored.
- **Initial retained audit:** 10 affected package entries: 2 critical, 5 high, 3 moderate. This is historical evidence, not a rerun of the vulnerable versions.
- **My priority:** P1 compatible runtime dependency updates and behavioral retest; P2 triage of the remaining development chain. Priority is contextual, not copied directly from CVSS.
- **Treatment completed:** NestJS `11.2.1 → 11.2.7`, Multer `2.2.0 → 2.4.0`, compatible transitive lockfile refresh; no forced major downgrade.
- **Current fresh full audit:** 20 moderate entries; 0 high/critical. Status: **WARN / residual development risk open**.
- **Current production-only audit:** 0 reported entries. This does not establish that every runtime path is safe.
- **Regression evidence:** fresh API security suite 72/72 passed; prior post-update Jest suite 71/71 retained in the execution ledger.
- **Reachability:** no exploit reproduction or complete call-path analysis. The September Multer disk-storage advisory was not shown reachable in this setup.
- **Owner:** Sollutions, portfolio maintainer; not a company security team.
- **Next action:** assess the affected Jest/Istanbul/config-parsing dependency chain against untrusted input and CI privileges; review compatible publisher fixes before adoption. Escalate if a consequential reachable path is confirmed.
- **Acceptance:** unresolved findings are not permanently accepted, suppressed or represented as a clean scan. No organizational SLA or risk sign-off is claimed.

For the advisory source, first-person reasoning, limitations and exact commands, see [CS-01](../../docs/security-case-studies.md#cs-01--an-actual-dependency-scan-led-to-a-fix) and [prioritization](../../docs/my-security-prioritization.md). KEV membership and EPSS values were not measured.
