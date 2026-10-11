# Documentation map

For a quick review: [business value](business-value.md) → [standards and decisions](standards-and-decisions.md) → [local runbook / CI](local-runbook.md) → [adoption boundaries](company-adoption.md). The current execution ledger is [PROJECT_STATUS.md](../PROJECT_STATUS.md).

For threat reasoning and observed behavior: [case studies](security-case-studies.md), [my prioritization](my-security-prioritization.md), [2026 source context](threat-intelligence-2026.md), [ATT&CK vs CWE](attack-and-control-mapping.md). [LinkedIn drafts](linkedin-project-copy.md) are not published posts.

For execution and career handover: [GitHub/GitLab CI and executable Gherkin](ci-cd-and-gherkin.md), [role relevance, CV and interview wording](career-positioning.md).

Before public upload: [publication, safe transfer and final review](publication.md).
The [2026-10-11 local publication review](evidence/publication-review.md) records checks and remaining limitations.

The documentation follows the engineering chain used throughout the project:

`Threat → Requirement → Control → Implementation → Automated verification → CI/CD gate → Evidence → Vulnerability management → Residual risk`

Each major control documents what it is, the threat, SDLC placement, implementation, local verification, CI/CD integration, gate behavior, limitations, real-world adaptation, and a short interview answer.

Detailed documents are added in implementation order so that claims never precede working code or explicit production recommendations.
