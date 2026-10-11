# Local-only DAST

## What is it?

The deep pipeline starts the isolated Compose lab, waits for `/health`, then runs the time-bounded ZAP 2.17.0 baseline container against `http://lab-api:3001/health`. Reports are retained under `reports/zap`; the environment is destroyed afterward.

## Threat and scope

Passive DAST observes runtime headers and responses that SAST cannot. It is not authorization proof and must never receive a production target. `assert_local_target.py` accepts only loopback or the Compose service name; the ZAP command is fixed to the Compose network.

## Gate and limitations

The baseline initially uses reporting mode (`-I`): scanner execution failure is `ERROR`, while alerts are normalized for review. After tuning, stable high-confidence rules can block. Authenticated crawling and production topology remain out of scope.

## Interview answer

SAST analyzes code without running it; DAST observes a running application from outside. I use fast SAST on pull requests and a bounded ZAP baseline against an isolated local lab in the deep pipeline. I preserve reports, tune noise before gating, and technically prevent a production URL.
