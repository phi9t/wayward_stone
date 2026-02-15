.DEFAULT_GOAL := help

.PHONY: help install lint format test test-unit test-offline typecheck clean preflight

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install in editable mode with dev deps
	pip install -e '.[dev]'

lint: ## Run ruff linter
	ruff check .
	ruff format --check .

format: ## Auto-format code with ruff
	ruff check --fix .
	ruff format .

test: ## Run all non-runtime tests
	pytest

test-unit: ## Run unit tests only
	pytest -m unit

test-offline: ## Run unit + integration-offline tests
	pytest -m "unit or integration_offline"

typecheck: ## Run mypy type checks
	mypy inkforge_loop/

clean: ## Remove build artifacts
	rm -rf build/ dist/ *.egg-info/ htmlcov/ .mypy_cache/ .pytest_cache/ .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

preflight: lint typecheck test ## Run lint + typecheck + test
