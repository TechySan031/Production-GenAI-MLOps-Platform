.PHONY: install lint lint-fix typecheck security test test-cov
eval eval-update-baseline eval-verbose eval-category
smoke smoke-structural run docker docker-down ci-check clean

─────────────────────────────────────────────────────────────
Setup
─────────────────────────────────────────────────────────────

install:
pip install -e ".[dev]"

─────────────────────────────────────────────────────────────
Local Development
─────────────────────────────────────────────────────────────

run:
uvicorn app.main --reload --host 0.0.0.0 --port 8000

dev: run

─────────────────────────────────────────────────────────────
Docker
─────────────────────────────────────────────────────────────

docker:
docker compose up --build

docker-down:
docker compose down

─────────────────────────────────────────────────────────────
Code Quality
─────────────────────────────────────────────────────────────

lint:
ruff check app/ tests/ scripts/
ruff format --check app/ tests/ scripts/

lint-fix:
ruff check app/ tests/ scripts/ --fix
ruff format app/ tests/ scripts/

typecheck:
mypy app/ --ignore-missing-imports --disallow-untyped-defs

security:
bandit -r app/ -ll

─────────────────────────────────────────────────────────────
Testing
─────────────────────────────────────────────────────────────

test:
pytest tests/ -v

test-cov:
pytest tests/ -v
--cov=app
--cov-report=term-missing
--cov-fail-under=75

ci-check: lint typecheck security test
@echo ""
@echo "All code quality gates passed."

─────────────────────────────────────────────────────────────
Evaluation Gates
─────────────────────────────────────────────────────────────

API_URL ?= http://localhost:8000

eval:
python scripts/eval/run_evals.py --api-url $(API_URL)

eval-update-baseline:
python scripts/eval/run_evals.py
--api-url $(API_URL)
--update-baseline

eval-verbose:
python scripts/eval/run_evals.py
--api-url $(API_URL)
--verbose

eval-category:
python scripts/eval/run_evals.py
--api-url $(API_URL)
--category $(CATEGORY)

─────────────────────────────────────────────────────────────
Smoke Tests
─────────────────────────────────────────────────────────────

smoke:
python scripts/smoke_test.py --api-url $(API_URL)

smoke-structural:
python scripts/smoke_test.py
--api-url $(API_URL)
--skip-inference


# ── Azure infrastructure ──────────────────────────────────────────────────────
# Prerequisites: az login, set RESOURCE_GROUP, GROQ_API_KEY

RESOURCE_GROUP ?= $(shell echo $$RESOURCE_GROUP)

# Deploy staging infrastructure (first-time or updates)
infra-staging:
	@[ -n "$(RESOURCE_GROUP)" ] || (echo "Set RESOURCE_GROUP"; exit 1)
	@[ -n "$(GROQ_API_KEY)" ] || (echo "Set GROQ_API_KEY"; exit 1)
	az deployment group create \
		--resource-group $(RESOURCE_GROUP) \
		--template-file infra/main.bicep \
		--parameters infra/parameters/staging.bicepparam \
		--parameters groqApiKey="$(GROQ_API_KEY)" \
		--output table

# Deploy production infrastructure
infra-production:
	@[ -n "$(RESOURCE_GROUP)" ] || (echo "Set RESOURCE_GROUP"; exit 1)
	@[ -n "$(GROQ_API_KEY)" ] || (echo "Set GROQ_API_KEY"; exit 1)
	az deployment group create \
		--resource-group $(RESOURCE_GROUP) \
		--template-file infra/main.bicep \
		--parameters infra/parameters/production.bicepparam \
		--parameters groqApiKey="$(GROQ_API_KEY)" \
		--output table

# Show deployment outputs (FQDNs, ACR name, Key Vault name)
infra-outputs:
	@[ -n "$(RESOURCE_GROUP)" ] || (echo "Set RESOURCE_GROUP"; exit 1)
	az deployment group show \
		--resource-group $(RESOURCE_GROUP) \
		--name main \
		--query "properties.outputs" \
		--output table

# Set up OIDC service principal for GitHub Actions (run once)
azure-oidc-setup:
	@echo "Creating service principal for GitHub OIDC..."
	@[ -n "$(GITHUB_REPO)" ] || (echo "Set GITHUB_REPO=org/repo"; exit 1)
	@[ -n "$(RESOURCE_GROUP)" ] || (echo "Set RESOURCE_GROUP"; exit 1)
	az ad app create --display-name "genai-gateway-github-actions" \
		--query "{clientId:appId,tenantId:publisherDomain}" -o json
	@echo ""
	@echo "Next: create federated credential and Contributor role assignment."
	@echo "See: make azure-oidc-setup-docs"

# Quick smoke test against a live Azure URL
smoke-azure:
	@[ -n "$(AZURE_URL)" ] || (echo "Set AZURE_URL=https://..."; exit 1)
	python scripts/smoke_test.py --api-url $(AZURE_URL)

# Tail Container App logs
logs-staging:
	@[ -n "$(STAGING_APP_NAME)" ] || (echo "Set STAGING_APP_NAME"; exit 1)
	az containerapp logs show \
		--name $(STAGING_APP_NAME) \
		--resource-group $(RESOURCE_GROUP) \
		--follow

logs-production:
	@[ -n "$(PROD_APP_NAME)" ] || (echo "Set PROD_APP_NAME"; exit 1)
	az containerapp logs show \
		--name $(PROD_APP_NAME) \
		--resource-group $(RESOURCE_GROUP) \
		--follow

─────────────────────────────────────────────────────────────
Cleanup
─────────────────────────────────────────────────────────────

clean:
find . -type d -name pycache -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
rm -f eval_results.json coverage.xml .coverage
rm -rf htmlcov/