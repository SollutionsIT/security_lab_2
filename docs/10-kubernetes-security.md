# Kubernetes security

## Evidence status

- **WORKING LAB IMPLEMENTATION:** manifests are concrete and render once a real image and runtime Secret are supplied.
- **PRODUCTION RECOMMENDATION:** external secret delivery, signed digest-pinned images and policy enforcement require the target platform.
- **REQUIRES RUNTIME VALIDATION:** admission, CNI NetworkPolicy behavior, scheduling and probes were not executed here.

| Control | Threat reduced | Verification | Limitation |
|---|---|---|---|
| non-root, no escalation, capabilities dropped, RuntimeDefault seccomp | privilege misuse | Trivy config scan and admission | not a substitute for runtime patching |
| read-only root and bounded `emptyDir` | persistence and disk exhaustion | manifest and runtime write test | `/tmp` remains writable by design |
| dedicated ServiceAccount, token disabled, empty Role | API credential theft and excess RBAC | `kubectl auth can-i` | no API use case exists |
| requests/limits and PDB | starvation and availability | manifest and cluster test | values need tuning |
| default-deny NetworkPolicy | lateral movement and egress | CNI connectivity tests | needs a compatible CNI |

The Secret is a placeholder excluded from Kustomize. Prefer an external secret manager. The hardened overlay retains a replace-me registry until release substitutes an attested image digest.

## Interview answer

I start Kubernetes hardening with identity and containment: a dedicated service account without an automounted token, restricted pod security, no capabilities, read-only root and resource bounds. Then I restrict connectivity and validate real cluster behavior, because an IaC scanner cannot prove that admission or the CNI enforces policy.
