# Security finding template

Use this template only after evidence exists. A modeled threat belongs in the threat register; a scanner result awaiting review is `DETECTED / UNVALIDATED`.

## Identification

- **Title:**
- **Finding ID:**
- **Evidence state:** `DETECTED / UNVALIDATED | CONFIRMED IN SYNTHETIC LAB | FALSE POSITIVE | ACCEPTED EXCEPTION | FIXED / RETESTED`
- **Asset:**
- **Environment:** synthetic local lab only
- **Source:** manual review, unit test, integration test, or named scanner
- **Requirement / threat IDs:**

## Evidence

- **Evidence:** minimal reproducible request, source location, test ID, or artifact reference
- **Preconditions:**
- **Affected trust boundary:**
- **Reproduction safety:** confirm no production/external target or real data
- **Observed result:**
- **Expected result:**
- **Side effect:** state before/after and relevant audit event

## Risk reasoning

- **CIA impact:** confidentiality / integrity / availability with explanation
- **Exploitability:**
- **Exposure and reachability:**
- **Asset criticality:**
- **Business impact:** synthetic-lab impact; production impact only as a clearly labeled hypothesis
- **CVSS (optional):** vector and rationale; one input only
- **Severity:**
- **Priority:**
- **Confidence:**

## Treatment

- **Remediation:**
- **Compensating controls:**
- **Owner:**
- **Deadline:**
- **Fix availability / dependency:**
- **Exception ID and expiration (if any):**

## Closure

- **Retest command and evidence:**
- **Retest result/date/reviewer:**
- **Residual risk:**
- **Closure decision:**

Never paste a usable secret, bearer token, full sensitive body, personal data, or external endpoint into a finding or its artifact.
