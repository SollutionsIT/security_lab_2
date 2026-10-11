# Risk-based security gates

`evaluate_security_gate.py` consumes normalized JSON and returns `PASS`, `WARN`, `FAIL` or `ERROR`. `ERROR` means the scanner or evidence pipeline did not complete; it never masquerades as “no findings.” A validated credential, reachable/exploitable Critical or new validated High-confidence issue fails. Mediums, uncertain reachability and unvalidated scanner hypotheses warn.

Exceptions require a finding ID, bounded scope, rationale, owner, reviewer, compensating controls and expiration. An expired exception is ignored. CVSS alone is insufficient: reachability, exposure, fix availability, asset criticality and validation determine priority.

## Interview answer

I do not fail every pipeline on every alert because that creates noise and bypass culture. I normalize evidence, separate scanner failure from a finding, fail immediately on validated high-impact conditions, warn on uncertain results, and allow only reviewed expiring exceptions. The policy itself has fixtures and automated tests.
