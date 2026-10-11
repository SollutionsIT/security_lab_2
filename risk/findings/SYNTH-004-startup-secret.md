# SYNTH-004 — Production placeholder secret abuse case

- **Evidence state:** CONTROL VERIFIED BY UNIT TEST
- **Asset:** JWT signing key
- **Source:** `app-config.spec.ts`
- **Scenario:** start production with a short or placeholder signing value, or enable test support
- **Expected/observed:** startup fails closed before listening
- **Control:** typed environment validation and production-only placeholder rejection
- **Residual risk:** secret strength checks do not provide rotation, custody, access review or HSM-backed signing
