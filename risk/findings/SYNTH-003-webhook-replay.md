# SYNTH-003 — Webhook replay and binding abuse case

- **Evidence state:** CONTROL VERIFIED IN SYNTHETIC LAB
- **Asset:** synthetic invoice integrity
- **Source:** webhook unit tests and Python integration tests
- **Scenario:** missing/invalid/old signature, duplicate ID, modified body, unknown type, or amount/order mismatch
- **Expected/observed:** invalid/replayed input rejected; duplicate handled idempotently; unknown event ignored; invoice changes only after server-side binding
- **Control:** raw-body HMAC, timestamp tolerance, atomic event claim and invoice state transition
- **Residual risk:** synthetic HMAC is not Stripe SDK behavior; distributed database transaction races need production validation
