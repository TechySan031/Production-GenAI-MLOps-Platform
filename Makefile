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

─────────────────────────────────────────────────────────────
Cleanup
─────────────────────────────────────────────────────────────

clean:
find . -type d -name pycache -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
rm -f eval_results.json coverage.xml .coverage
rm -rf htmlcov/