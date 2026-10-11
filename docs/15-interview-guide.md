# Interview guide

Each answer is designed for a 30–60 second Middle AppSec/DevSecOps response and points back to this repository.

## 1. SAST versus DAST

SAST inspects source/AST/data flow without a running target and gives early, code-located feedback; DAST observes runtime behavior from outside and catches headers, routing and deployment behavior. Here custom Semgrep runs in PR, CodeQL runs deep, and ZAP baseline runs only against the isolated Compose lab. Neither proves absence, so findings are validated and combined with targeted API tests.

## 2. SAST versus SCA

SAST looks for insecure code patterns or flows we wrote. SCA inventories direct/transitive components and correlates them with advisories. This repo uses Semgrep/CodeQL for source and lockfile/Dependabot/Trivy for dependencies. A dependency CVE still needs exposure, reachability, fix and asset context before business priority is set.

## 3. Secret scanning

Secret scanning detects credential-like material before it spreads into history, logs or artifacts. Gitleaks scans the repo; an isolated, explicitly unusable canary proves the custom rule works while the normal policy allowlists only that path. A hit is quarantined and validated—never pasted into a ticket or automatically treated as a live credential.

## 4. Why not fail on every scanner alert?

Scanners produce hypotheses with different confidence and context. Failing everything creates noise and bypass culture. The gate distinguishes `WARN` from validated `FAIL`, while a scanner crash becomes `ERROR`. High-impact confirmed conditions block; uncertain findings retain evidence for triage; exceptions are reviewed and expire.

## 5. What is a security gate?

A gate is a versioned decision policy over normalized evidence, not a raw CVSS threshold. Here credential verification, reachability, exploitability, confidence, validation and newness influence PASS/WARN/FAIL/ERROR. Gate fixtures test all outcomes, and release consumes an artifact scan rather than only source results.

## 6. BOLA / IDOR

BOLA occurs when an authenticated user can act on another user’s object by changing its identifier. The lab derives owner from repository relationships, returns the same concealed 404 as a missing object, preserves state and emits a denial event. The Python matrix tests user B against property/attachment A—not only status but response equivalence and side effects.

## 7. BFLA

BFLA is unauthorized use of a function, such as an ordinary user calling an admin audit endpoint. A global JWT guard establishes identity; a separate role guard enforces function policy. Tests prove user denial plus audit, and admin success, keeping authentication and authorization distinct.

## 8. Mass assignment

Mass assignment happens when generic binding lets a client set fields like `ownerId`, `role` or `isVerified`. Strict NestJS DTOs whitelist intended fields and `forbidNonWhitelisted` rejects extras. Tests assert 400 and unchanged state. That is still only input validation; the domain layer separately checks ownership and state.

## 9. JWT validation

Signature verification alone is insufficient. The lab pins HS256 and exact issuer/audience, requires subject/role/iat/exp, bounds lifetime and rejects wrong algorithm, issuer, audience, expiry and tampering. In production I would also define key rotation, asymmetric trust where appropriate and revocation/session strategy.

## 10. Webhook security

Verify the exact raw body, expected signature algorithm and timestamp window; claim event IDs atomically; tolerate duplicates; and bind order, amount and currency to server state. The lab covers seven negative/positive cases. Provider SDK and distributed transaction behavior remain explicit production validation items.

## 11. File upload security

I do not trust filename or client MIME. The lab independently checks byte limit, allowlisted extension, MIME and magic; generates a UUID storage key; confines writes below OS temp; binds owner metadata; and forces safe download headers. Tests cover traversal, spoofing, empty/large files and cross-owner reads. Malware scanning/object-store ACLs are later layers.

## 12. SSRF

SSRF defense starts with avoiding arbitrary fetch. The demonstration tests a pure policy: HTTPS only, exact normalized host allowlist, no IP/private/literal targets, no redirects, bounded time/bytes. It makes no real network request. Production also needs controlled DNS resolution, rebinding defense and revalidation after every redirect.

## 13. Container security

The Dockerfile uses a digest-pinned base, multi-stage `npm ci` build, pruned dependencies, no secret ARG/ENV, and UID 1000. Runtime is compatible with read-only root and bounded `/tmp`; Compose drops capabilities and blocks privilege escalation. Trivy validates known packages/config, but runtime policy and application security still need separate tests.

## 14. Kubernetes RBAC

The workload has no Kubernetes API use case, so its dedicated ServiceAccount has token automount disabled and an empty Role—least privilege can mean no permission. Pod security, resources and NetworkPolicy contain impact. I validate `kubectl auth can-i`, admission and real CNI behavior because YAML scanning alone cannot prove enforcement.

## 15. SBOM

An SBOM is inventory: which packages and versions are in an artifact. It is not a vulnerability result. Syft/Anchore emits CycloneDX, Trivy correlates components with advisories, and the risk gate applies context. The SBOM is retained with the release evidence and artifact digest for later incident response.

## 16. Artifact provenance

Provenance answers who/what built an artifact from which source/workflow. Release builds once, hashes/scans the candidate, emits SBOM and creates GitHub attestation. In production I would publish by digest, use protected OIDC identity and optionally keyless Cosign, then enforce provenance at admission.

## 17. Handling a false positive

Keep the original evidence, reproduce safely, inspect source/flow/preconditions, and record why it is false—not just suppress it. If risk is accepted instead, document scope, owner, reviewer, compensating controls and expiration. The exception format is machine-readable; expired entries stop applying.

## 18. Adding security to existing CI/CD

Start from threats and current build, not a tool shopping list. Add fast low-noise controls first—secrets, tests, selected SAST/SCA—measure results, then introduce deep CodeQL/image/DAST/SBOM on main or nightly. Normalize evidence and tune before blocking. This repo’s three workflows demonstrate that rollout.

## 19. How not to block developers

Keep PR jobs parallel and bounded, make messages actionable, test custom rules, separate reporting from blocking, and provide a reviewed exception path. Move expensive runtime checks to deep CI while protecting release with artifact-bound gates. Track false-positive and time-to-feedback metrics, not raw alert volume.

## 20. Vulnerability lifecycle

Discover, validate, classify, prioritize, assign, remediate, retest, close and measure. Validation separates a modeled threat/scanner hypothesis from a confirmed issue. Priority combines technical severity with reachability and asset impact. Closure includes exact retest evidence and residual risk; exceptions remain temporary and auditable.

## Suggested repository walkthrough

```text
Threat model (attachment BOLA)
  -> security requirement
  -> owner-bound UploadService
  -> cross-owner/anonymous/admin tests
  -> deep CI evidence
  -> normalized gate
  -> SYNTH-001 lifecycle record
  -> residual object-store/distributed-state risk
```
