# Adapting the approach in an authorized company pilot

Not turnkey production deployment. Commercial use also requires license permission.

1. Agree written scope, data classification, systems, risk owner, acceptance criteria and rollback plan.
2. Select one high-value journey, such as cross-customer record access. Model identity, tenancy and trust boundaries with the product team.
3. Map lab controls to the real service contracts. Replace synthetic persistence with transactional storage; review concurrency and multi-tenancy.
4. Remove test-only endpoints and synthetic secrets. Add a reviewed secrets manager, rotation, TLS and production identity/provider integration.
5. Add negative regression tests to the team's CI. Keep PR jobs unprivileged and separate credentials/deployment authorization.
6. Integrate scanners; tune rules; triage false positives; assign owners and expiring exceptions. Verify that policy gates actually block the intended release path.
7. Test workload policies on the real platform, operational logging, alerts, backups and rollback. Manifests alone are not runtime evidence.
8. Review residual risks and hand over runbooks. Measure feedback time, coverage of critical journeys and overdue findings before claiming impact.

## Future integrations—not implemented experience

- **DefectDojo:** ingest normalized findings with ownership and deduplication after defining a stable schema.
- **Wazuh / a SIEM:** map redacted events and correlation IDs to detection rules; secure transport and retention need operational work.
- **Vault / a cloud secrets manager:** replace local synthetic values; design bootstrap trust, access policy and rotation first.
- **Checkov:** add an independent IaC rule set and compare findings with Trivy; tune overlaps rather than counting duplicate alerts.

These are roadmap items. Included improvements that do work locally are the publication hygiene guard and actual HTML evidence report/demo.
