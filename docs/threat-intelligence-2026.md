# Why these threats are relevant now

Research snapshot: **11 October 2026**. I use current primary reports to guide scenario selection—not to claim that a fictional loopback application has the same attack probability as a production company. Publication year and observation period are separate facts.

## Current signals and their practical use

| Primary source | Published / observations | Signal I used | My lab decision—and its limit |
|---|---|---|---|
| [Verizon DBIR 2026 announcement](https://www.verizon.com/about/news/breach-industry-wide-dbir-finds) | 19 May 2026; uses 2025 data | Vulnerability exploitation accounts for 31% of breach entry points; third parties are involved in 48% of breaches in that dataset | Review dependency exposure and release integrity first. These are not probabilities for this lab; vendor involvement is broader than malicious npm packages. |
| [Mandiant M-Trends 2026](https://cloud.google.com/blog/topics/threat-intelligence/m-trends-2026) | 23 March 2026; investigations in 2025 | Exploits account for 32% of initial infection vectors; voice phishing for 11% | Combine patching with identity and access checks. No phishing campaign, credential theft or ransomware execution is performed here. |
| [ENISA Threat Landscape 2026](https://www.enisa.europa.eu/publications/enisa-threat-landscape-2026), [release analysis](https://www.enisa.europa.eu/news/exploring-the-evolution-of-the-cyber-threat-landscape-how-dependencies-weaken-our-digital-resilience) | 22 September 2026; 1 January–31 December 2025 | Interconnected dependencies amplify risk; ransomware, social engineering and hacktivist DDoS remain relevant in the EU | Test boundary integrity, retain security events and constrain resource use. Local rate/size tests do not demonstrate DDoS or ransomware resilience. |
| [GitHub supply-chain update](https://github.blog/security/supply-chain-security/disrupting-supply-chain-attacks-on-npm-and-github-actions/) | 28 July 2026 | Contemporary package/CI attack chains seek credentials and use them to propagate malicious releases | Install with scripts disabled, review lockfile changes, pin Actions, restrict job tokens and separate privileged release paths. Pinning alone cannot detect already-malicious code. |
| [Multer advisory GHSA-3pph-fpjx-jg34](https://github.com/advisories/GHSA-3pph-fpjx-jg34) | Published 14 September 2026; updated 28 September 2026 | Affected range `>=2.2.0 <2.4.0`; patch `2.4.0`; an aborted-upload disk-storage cleanup issue | A recent advisory present in the retained audit. I updated the dependency and reran regressions. This storage-specific issue was not exploited or shown reachable in the lab. |

These datasets have different populations and definitions. I do not combine their percentages or use them as an actuarial score. A recurring technique is not obsolete because its name is old: unauthorized object access still matters when the application's contracts allow an attacker-controlled identifier to cross an ownership boundary.

## Threat scenarios—not detected incidents

| Current attack pattern | Scenario for COMPANY | Evidence available | What remains outside the lab |
|---|---|---|---|
| Exploitation of reachable third-party software | A parser dependency handles hostile request bytes | Real before/after npm audit findings; current upload regressions | Exploitability proof, complete reachable-call analysis, zero-day detection |
| Abuse of compromised valid accounts | A logged-in user tries another owner's records or an admin action | Two-user authorization matrix and unchanged-state checks | Phishing-resistant MFA, session theft detection, enterprise IdP |
| Package / CI credential theft and release poisoning | An install script or privileged workflow compromises delivery | Reviewed install flags, pinned refs, Gitleaks/canary and gate regressions | Malware detonation, runner egress enforcement, production signing/IAM |
| Resource exhaustion | Oversized XML/file or repeated expensive requests consume resources | Bounded local tests, deterministic rate limits | Volumetric DDoS protection, distributed load/availability proof |
| Untrusted integration changes business state | Forged, stale or replayed webhook changes an invoice | Synthetic signature/freshness/binding/idempotency tests | Actual provider compromise and multi-process transactional races |
| AI-assisted social engineering / AI data leakage | Untrusted content tries to choose a tool or disclose data | Mocked AI schema/allowlist/quota tests only | Real LLM security, enterprise shadow-AI governance, phishing prevention |

See [case studies](security-case-studies.md) for results actually observed. I intentionally leave ransomware, real phishing, endpoint malware and cloud intrusion marked **not tested** instead of relabeling ordinary API tests as coverage for them.

## Refresh rules

Before a real deployment decision, check updated publisher advisories, runtime versions and dependency reachability. For CVEs, consult [CISA's official KEV data mirror](https://github.com/cisagov/kev-data), [FIRST EPSS](https://www.first.org/epss/) and [CVSS](https://www.first.org/cvss/) alongside business impact. KEV/EPSS are review inputs here, not connected live feeds or tested integrations. No live KEV membership or EPSS value is claimed for the lab findings. Absence of a KEV entry is not proof of safety.

The CISA catalogue web page was unavailable to the research tool (403); the agency-maintained public data mirror was used as the reference. No access restriction was bypassed.
