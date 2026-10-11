# Career positioning: what this lab demonstrates

## Real engineering tasks, in a learning environment

The work is relevant to AppSec and DevSecOps: identify trust boundaries, prioritize risks, implement and test application controls, triage dependencies, configure repeatable security gates and retain evidence. The API and negative HTTP tests really execute. However, the business, identities, integrations and data are synthetic; this is **AI-assisted personal project experience**, not commercial security ownership.

This interpretation follows the task-oriented [OWASP DevSecOps guideline](https://owasp.org/projects/devsecops-guideline?tab=main) and the [NIST NICE distinction between work roles and job titles](https://www.nist.gov/itl/applied-cybersecurity/nice/nice-framework-resource-center/resources/occupations-jobs-and-work). The fit below is my evidence-based interpretation, not a hiring guarantee or proof of a professional grade.

## Roles and the evidence an interviewer can inspect

| Role | Relevance of this project | What is still missing |
|---|---|---|
| Security QA / QA Engineer with security responsibilities | Strongest bridge from QA: negative API cases, state invariants, authorization matrix and readable acceptance criteria | Real-product contracts, distributed behavior and release responsibility in the employer's environment |
| Junior Application Security Engineer | Threat reasoning, authentication/authorization review, input controls, dependency triage and regression evidence | Broader code review, exploitation validation, production architecture, developer collaboration and incident feedback |
| Junior / early-mid Security Automation Engineer | Python/pytest, typed clients, report normalization, gate/error contracts and portable pipeline entrypoint | Operational integrations, scale, maintenance ownership and actual remote job evidence |
| Junior DevSecOps Engineer focused on application pipelines | CI definitions, SAST/SCA/secrets jobs, permission/pinning decisions, policy and artifact delivery | Remote CI validation, cloud/IaC operations, runner hardening in production, durable secrets and workload enforcement |
| Junior Vulnerability Management Analyst | Advisory interpretation, context-aware prioritization, compatible remediation and retest | Enterprise inventory/reachability, stakeholder remediation tracking, organizational SLAs and reporting |

An early-mid security role may consider transferable QA experience alongside this project; the lab alone does not establish that level. Infrastructure-heavy DevSecOps roles expecting independent AWS/EKS/Terraform/Vault ownership are a larger gap. SOC, red-team/pentesting and cloud security are not the main evidence here: no operational SIEM, incident response, adversary campaign or deployed cloud was validated.

## CV entry — accurate before the first remote CI run

**COMPANY Security Lab — AppSec & DevSecOps Personal Project**

AI-assisted security learning project translating business risks into application controls, negative tests and reviewable evidence.

- Developed and validated a synthetic NestJS API with Python/pytest security regressions covering authorization, protected fields, webhook integrity and input limits.
- Added executable Gherkin acceptance scenarios and configured GitHub Actions/GitLab CI for a shared native verification command, security jobs and retained build/report artifacts; remote execution pending.
- Used npm audit and Gitleaks locally; applied compatible dependency updates and retained unresolved development findings for triage.
- Documented impact/exposure/evidence-based priorities and OWASP/NIST/MITRE references, with explicit production and compliance limitations.

**Stack:** Python, pytest, pytest-bdd/Gherkin, HTTPX, TypeScript, NestJS, Jest, Supertest, Gitleaks, npm audit, GitHub Actions, GitLab CI.

Keep this in **Projects / Practical Security Training**, not a paid role in Employment. Add dates and a public URL only when verified. List Semgrep/Trivy/CodeQL/ZAP separately as configured integrations until actual execution evidence exists.

## Cisco-course framing

If accurate, introduce the entry with:

> Alongside Cisco cybersecurity coursework, developed an independent, AI-assisted security lab to practise application controls, threat prioritization and security automation.

Do not claim that Cisco commissioned, endorsed or formally assessed the project without evidence. Do not invent a course title, completion date, certificate or certification. After confirming the course details, list the course separately in Training/Certifications.

## How to explain it in an interview

> I come from QA and am building practical AppSec and security-automation skills. In this lab, I start with the business outcome—for example, one customer's record must not be changed by another user. I implement the server-side ownership check and test both the denied response and unchanged state. I then make that verification reproducible through a shared CI command, preserve failures and document remaining risks. A real dependency scan led to compatible updates and retesting. The environment is synthetic, and remote CI/cloud enforcement still need separate evidence.

For AppSec, lead with the trust boundary and testable invariant. For DevSecOps, lead with reproducibility, permission/pinning decisions, failure behavior and evidence. For Security QA, lead with negative coverage, deterministic reset and state assertions. Explain a real code path rather than listing tool names.

## Common questions

- **Why not rely on SAST alone?** Resource ownership is business logic; a scanner cannot infer every tenant/action relationship. HTTP and state assertions complement static checks.
- **What did you actually find?** Dependency advisories and source-inspected evidence handling issues. Current blocked BOLA/replay requests verify controls; they are not newly discovered production vulnerabilities.
- **What does a green pipeline mean?** The declared checks passed or permitted WARN. It does not mean every dependency is clean or every attack is covered.
- **Is Gherkin security tooling?** It is executable specification. Step definitions exercise the API/gate; the format makes acceptance rules reviewable. It is not a scanner.
- **Where is CD?** CI verifies code; delivery retains a reviewed build candidate. No production deployment/rollback is configured without a target and operational requirements.
- **Why not claim ISO compliance?** Referencing risk practices and technical controls is not a complete ISMS, independent audit or legal assessment.
- **What would you do next?** Run the first authorized remote pipelines, inspect actual artifacts and denied cases, triage remaining advisories, execute pending scanners, then validate platform controls in an authorized environment.
- **What was your role versus AI?** Be explicit about assistance; demonstrate your own understanding, risk decisions, test modifications and ability to diagnose failures. Do not imply independent authorship of every line.

## Updating claims after remote verification

Only replace “configured / remote execution pending” after retaining the actual pipeline URL, commit, versions, job outcomes and artifacts. A single successful pipeline does not establish production operations experience or coverage of every configured scanner. No post, CV or application is sent automatically.
