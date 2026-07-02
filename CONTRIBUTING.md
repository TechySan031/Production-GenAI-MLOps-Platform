# Contributing to Production GenAI MLOps Platform

Thank you for your interest in contributing! This document provides guidelines.

## Development Setup

```bash
# Clone the repository
git clone https://github.com/TechySan031/Production-GenAI-MLOps-Platform.git
cd Production-GenAI-MLOps-Platform

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install with dev dependencies
pip install -e ".[dev]"

# Copy environment file
cp .env.example .env
# Edit .env with your API keys
```

## Code Quality

All code must pass the following checks before merging:

```bash
# Lint
ruff check app/ tests/ scripts/

# Format
ruff format --check app/ tests/ scripts/

# Type check
mypy app/ --ignore-missing-imports --disallow-untyped-defs

# Security scan
bandit -r app/ -ll

# Tests with coverage
pytest tests/ -v --cov=app --cov-fail-under=75
```

Or run all checks at once:

```bash
make ci-check
```

## Pull Request Process

1. Fork the repository and create a feature branch
2. Make your changes with clear, atomic commits
3. Ensure all CI checks pass
4. Update documentation if applicable
5. Submit a pull request with a clear description

## Commit Messages

Follow conventional commit format:

```
feat: add Azure OpenAI provider support
fix: correct cost calculation for GPT-4 Turbo
docs: update deployment instructions
refactor: extract common provider logic
test: add unit tests for Groq provider
ci: add Docker build verification step
infra: add managed identity RBAC assignments
```

## Architecture Principles

- **Provider abstraction**: LLM providers implement `BaseProvider` interface
- **Fail-fast config**: Invalid configuration crashes at startup, not at request time
- **Null Object pattern**: Observability failures never propagate to inference
- **Environment-driven**: All behavior controlled via environment variables
