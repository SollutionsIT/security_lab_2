# SYNTH-002 — Mass-assignment abuse case

- **Evidence state:** CONTROL VERIFIED IN SYNTHETIC LAB
- **Asset:** Property ownership and account privilege
- **Source:** NestJS e2e and Python integration regression
- **Scenario:** submit `ownerId`, `role` or `isVerified` outside the typed DTO contract
- **Expected/observed:** 400; resource state unchanged; no forbidden field persisted
- **Control:** strict `ValidationPipe` with whitelist and `forbidNonWhitelisted`; explicit DTO fields
- **Residual risk:** validation is not authorization; every mutable domain command still needs an ownership/state decision

This is a synthetic abuse case, not a claim that a customer application is vulnerable.
