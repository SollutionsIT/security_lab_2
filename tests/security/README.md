# Security regression tests

This directory contains the PHASE 8 Python 3.13+ API security framework for the
synthetic lab. It is deliberately contract-driven: resource identifiers come
from the gated lab state endpoint, credentials and signing material come from
settings, and every test starts from reset state.

```text
settings
   ↓
local-target-only httpx client (redirects disabled)
   ↓
identities + gated seed aliases
   ↓
security scenarios
   ↓
status + response + state/audit side effects
```

## Safety boundary

- `SECURITY_TEST_BASE_URL` is rejected unless it is explicit HTTP on
  `127.0.0.1`, `localhost`, or the isolated `lab-api` container hostname.
- The client accepts path references only and uses `follow_redirects=False`.
- Every test calls `POST /__test/reset`; test support is available only when
  `LAB_TEST_MODE=true` and the matching `X-Lab-Test-Key` is supplied.
- Webhook, upload, XML, SSRF-policy, and AI inputs are synthetic. No test has an
  external transport or a production target.
- Current local evidence is recorded only in the root `PROJECT_STATUS.md`.

## Configuration

Copy the safe template and keep the resulting file untracked:

```bash
cp tests/security/.env.example tests/security/.env
```

The values must match the synthetic seed and the lab process. Passwords, test
key, webhook secret, base URL, and replacement password are not embedded in
test modules. Property and invoice IDs are resolved from
`/__test/state.seedAliases` after every reset.

For a loopback test process, export matching lab variables before startup:

```bash
export NODE_ENV=test
export HOST=127.0.0.1
export PORT=3001
export JWT_SECRET=synthetic-test-jwt-secret-at-least-32-bytes
export LAB_TEST_MODE=true
export LAB_TEST_KEY=local-test-key-long-enough
export SYNTHETIC_WEBHOOK_SECRET=whsec_synthetic_local_only_do_not_reuse
npm --prefix lab-api run start:dev
```

These values are local synthetic examples, not production credentials.

## Python setup and expected commands

The root `pyproject.toml` pins every direct Python tool/dependency requested by
the project. In a separate shell:

```bash
python3.13 -m venv .venv
. .venv/bin/activate
python -m pip install .
pytest tests/security
ruff check tests/security
mypy tests/security
```

The canonical workflow uses Python 3.13. A compatibility run under the available
Python 3.12.13 is recorded in `PROJECT_STATUS.md`; GitHub Actions is responsible
for the required 3.13 execution.

## Coverage

| Module | Verified control |
|---|---|
| `test_authentication.py` | generic login/reset responses, bearer enforcement, custom wrong issuer/audience/expiry/algorithm tokens, reset metadata/single use, password policy, content type |
| `test_authorization_matrix.py` | actor × action × owner × state decisions, BOLA/BFLA hiding, state side effects, denial audit events |
| `test_mass_assignment.py` | top-level and nested forbidden fields rejected without partial update |
| `test_rate_limiting.py` | deterministic login/reset/public-form/AI thresholds and retry headers |
| `test_stripe_webhook.py` | seven required signature/replay/idempotency cases plus server-side invoice binding |
| `test_upload_security.py` | seven required size/MIME/extension/magic/traversal/empty/type cases and safe download headers |
| `test_xml_security.py` | bounded valid XML, DTD/entity rejection, byte/depth/node limits, content type |
| `test_ai_boundary.py` | prompt/tool trust boundary, output non-echo, URL allowlist without fetch, byte quota |
| `test_log_redaction.py` | retained structured events exclude credentials, reset/JWT values, prompts, webhook material, and email |

## What these tests do not prove

Passing locally does not prove production security, scanner accuracy, absence of
all authorization paths, or cloud/Kubernetes correctness. The lab is an
in-memory reference implementation, and its gated state/mailbox/log endpoints
must never exist in a production build. Findings still require validation and
risk-based triage.
