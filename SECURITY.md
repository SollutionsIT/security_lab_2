# Security policy

## Scope

This is an intentionally synthetic defensive security lab. Report flaws in the lab, its automation, or its CI/CD controls through a private GitHub security advisory after publication. Do not include live credentials, personal data, or production targets in a report.

## Safe testing rules

- Test only a checkout you control.
- Dynamic targets are limited to `127.0.0.1`, `localhost`, or the repository's isolated container network.
- Never repoint the supplied DAST or API-security configuration at an external system.
- Do not add malware, live exploit payloads, cloud metadata probes, or real payment-provider secrets.
- Use the synthetic fixtures supplied by this repository.

## Finding language

Use one of these evidence states:

- `CONFIRMED IN SYNTHETIC LAB`
- `SECURITY RECOMMENDATION`
- `REQUIRES RUNTIME VALIDATION`
- `FALSE POSITIVE`
- `ACCEPTED EXCEPTION`

Static analysis and scanner output are evidence inputs. Neither is, on its own, proof of exploitability or business impact.

## Supported versions

Until the first tagged release, only the default branch is maintained. Security fixes will be documented with affected scope, evidence, remediation, and retest status without publishing usable secrets.
