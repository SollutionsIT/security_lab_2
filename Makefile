.DEFAULT_GOAL := help
PYTHON ?= python3.13
VENV := .venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: help status install lint unit lab-native lab-up lab-down security-test secrets sast sca iac-scan container-build container-scan sbom dast gate security clean-evidence publication-check publication-bundle portfolio-evidence evidence-report case-study-evidence bdd-test ci-verify

help: ## Show supported commands.
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z0-9_-]+:.*## / {printf "%-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

status: ## Show the phase and evidence ledger.
	@sed -n '1,160p' PROJECT_STATUS.md

install: ## Reproducibly install Node and Python project dependencies.
	@command -v npm >/dev/null || { echo "ERROR: npm is required"; exit 2; }
	@command -v $(PYTHON) >/dev/null || { echo "ERROR: Python 3.13 is required (set PYTHON=...)"; exit 2; }
	npm --prefix lab-api ci --ignore-scripts
	$(PYTHON) -m venv $(VENV)
	$(PIP) install .
	$(VENV)/bin/pre-commit install

lint: ## Run deterministic TypeScript/Python static checks.
	npm --prefix lab-api run typecheck
	$(VENV)/bin/ruff check tests/security tests/gate tests/portfolio tests/bdd security/scripts
	$(VENV)/bin/mypy tests/security tests/bdd security/scripts

unit: ## Run NestJS unit/e2e and security-gate tests.
	npm --prefix lab-api test -- --runInBand
	$(VENV)/bin/pytest tests/gate tests/portfolio

lab-native: ## Start the built lab in foreground on loopback.
	NODE_ENV=test HOST=127.0.0.1 PORT=3001 JWT_SECRET=local-synthetic-jwt-secret-32-bytes-min JWT_ISSUER=company-security-lab JWT_AUDIENCE=company-security-lab-clients SYNTHETIC_WEBHOOK_SECRET=whsec_synthetic_local_only_do_not_reuse LAB_TEST_MODE=true LAB_TEST_KEY=local-test-key-long-enough npm --prefix lab-api run start:prod

lab-up: ## Build and start the isolated Docker lab on 127.0.0.1:3001.
	@command -v docker >/dev/null || { echo "ERROR: Docker with Compose is required"; exit 2; }
	docker compose up --build --wait -d lab-api

lab-down: ## Destroy the isolated Docker lab and volumes.
	@command -v docker >/dev/null || { echo "ERROR: Docker with Compose is required"; exit 2; }
	docker compose --profile security down --volumes --remove-orphans

security-test: ## Run API security tests against loopback lab only.
	$(PY) security/scripts/assert_local_target.py http://127.0.0.1:3001
	SECURITY_TEST_BASE_URL=http://127.0.0.1:3001 SECURITY_TEST_LAB_TEST_KEY=local-test-key-long-enough SECURITY_TEST_WEBHOOK_SECRET=whsec_synthetic_local_only_do_not_reuse SECURITY_TEST_JWT_SECRET=local-synthetic-jwt-secret-32-bytes-min SECURITY_TEST_JWT_ISSUER=company-security-lab SECURITY_TEST_JWT_AUDIENCE=company-security-lab-clients SECURITY_TEST_AI_ALLOWED_SOURCE_URL=https://content.example.test/document/1 SECURITY_TEST_USER_A_EMAIL=alice@example.test SECURITY_TEST_USER_A_PASSWORD='Alice-Local-Only!42' SECURITY_TEST_USER_B_EMAIL=bob@example.test SECURITY_TEST_USER_B_PASSWORD='Bob-Local-Only!42' SECURITY_TEST_ADMIN_EMAIL=admin@example.test SECURITY_TEST_ADMIN_PASSWORD='Admin-Local-Only!42' SECURITY_TEST_UNKNOWN_EMAIL=unknown@example.test SECURITY_TEST_REPLACEMENT_PASSWORD='Replacement-Local!84' $(PY) -m pytest tests/security

secrets: ## Scan the repository and prove the synthetic canary is detected.
	@command -v gitleaks >/dev/null || { echo "ERROR: gitleaks is required"; exit 2; }
	gitleaks dir --no-banner --redact=100 --config .gitleaks.toml .
	$(PY) security/scripts/test_gitleaks_config.py

sast: ## Validate, test and run custom Semgrep policy.
	mkdir -p reports
	$(VENV)/bin/semgrep --validate --config semgrep.yml
	$(VENV)/bin/semgrep --test --config semgrep.yml security/semgrep
	$(VENV)/bin/semgrep scan --config semgrep.yml --json --output reports/semgrep.json

sca: ## Run npm audit and Trivy filesystem dependency scan.
	@command -v trivy >/dev/null || { echo "ERROR: trivy is required"; exit 2; }
	npm --prefix lab-api audit --audit-level=high
	mkdir -p reports
	trivy fs --scanners vuln --exit-code 0 --format json --output reports/trivy-fs.json .

iac-scan: ## Scan Docker/Kubernetes configuration with Trivy.
	@command -v trivy >/dev/null || { echo "ERROR: trivy is required"; exit 2; }
	mkdir -p reports
	trivy config --exit-code 0 --format json --output reports/trivy-iac.json lab-api kubernetes compose.yaml .github/workflows

container-build: ## Build the hardened local container.
	@command -v docker >/dev/null || { echo "ERROR: Docker is required"; exit 2; }
	docker build --pull=false --tag company-security-lab:local lab-api

container-scan: container-build ## Scan the local image with Trivy.
	@command -v trivy >/dev/null || { echo "ERROR: trivy is required"; exit 2; }
	mkdir -p reports
	trivy image --exit-code 0 --format json --output reports/trivy-image.json company-security-lab:local

sbom: ## Generate a CycloneDX SBOM with Syft.
	sh security/scripts/generate_sbom.sh

dast: ## Run reporting-mode ZAP only against the Compose lab.
	@command -v docker >/dev/null || { echo "ERROR: Docker with Compose is required"; exit 2; }
	$(PY) security/scripts/assert_local_target.py http://lab-api:3001
	mkdir -p reports/zap
	docker compose up --build --wait -d lab-api
	docker compose --profile security run --rm zap

gate: ## Exercise all normalized security-gate outcomes.
	$(PY) security/scripts/evaluate_security_gate.py security/fixtures/gate/pass.json
	$(PY) security/scripts/evaluate_security_gate.py security/fixtures/gate/warn.json
	@$(PY) security/scripts/evaluate_security_gate.py security/fixtures/gate/fail.json >/dev/null 2>&1; test $$? -eq 1
	@$(PY) security/scripts/evaluate_security_gate.py security/fixtures/gate/error.json >/dev/null 2>&1; test $$? -eq 2

security: lint unit secrets sast sca iac-scan ## Run the non-dynamic local security suite.

publication-check: ## Check distributable text/names for private material.
	$(PY) security/scripts/publication_check.py
	$(PY) -m security.scripts.publication_preflight

publication-bundle: publication-check ## Export reviewed candidates without Git/runtime/private data.
	$(PY) -m security.scripts.publication_preflight --bundle

portfolio-evidence: ## Execute checks and render real local evidence (lab must be running).
	$(PY) security/scripts/portfolio_evidence.py

bdd-test: ## Execute Gherkin API/gate scenarios (native lab must be running).
	$(PY) security/scripts/run_bdd.py

ci-verify: ## Own the local API lifecycle; run core, BDD and dependency gates.
	$(PY) security/scripts/run_ci.py

evidence-report: ## Re-render the existing evidence without rerunning checks.
	$(PY) security/scripts/portfolio_evidence.py --render-only

case-study-evidence: ## Export safe case-study aggregates (fresh reports + running lab required).
	$(PY) security/scripts/build_case_study_evidence.py $(CASE_STUDY_FLAGS)

clean-evidence: ## Remove generated reports/SBOM only.
	@find reports -type f -delete 2>/dev/null || true
	@find sbom -type f ! -name README.md -delete 2>/dev/null || true
