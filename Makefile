.PHONY: dev docker test lint clean install

# --- Development ---
install:
	pip install -e ".[dev]"

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# --- Docker ---
docker:
	docker compose up --build

docker-down:
	docker compose down

# --- Testing ---
test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=app --cov-report=term-missing

# --- Linting ---
lint:
	ruff check app/ tests/

format:
	ruff format app/ tests/

# --- Cleanup ---
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov/ dist/ build/ *.egg-info/
