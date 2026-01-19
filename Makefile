.PHONY: help install lint format test test-cov clean all check

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install project dependencies with uv
	uv sync --extra dev

lint: ## Run ruff linter
	@echo "Running ruff linter..."
	uv run ruff check src/ tests/

lint-fix: ## Run ruff linter with auto-fix
	@echo "Running ruff linter with auto-fix..."
	uv run ruff check --fix src/ tests/

format: ## Format code with black
	@echo "Formatting code with black..."
	uv run black src/ tests/

format-check: ## Check code formatting without making changes
	@echo "Checking code formatting..."
	uv run black --check src/ tests/

test: ## Run tests with pytest
	@echo "Running tests..."
	uv run pytest -v

test-cov: ## Run tests with coverage report
	@echo "Running tests with coverage..."
	uv run pytest -v --cov=report2attack --cov-report=term-missing --cov-report=html

test-verbose: ## Run tests in verbose mode
	@echo "Running tests in verbose mode..."
	uv run pytest -vv

typecheck: ## Run mypy type checker
	@echo "Running mypy type checker..."
	uv run mypy src/

check: lint format-check typecheck ## Run all checks (lint, format, typecheck)
	@echo "All checks passed!"

all: lint-fix format test ## Run lint-fix, format, and tests

clean: ## Clean up generated files
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Cleanup complete!"

clean-data: ## Clean ATT&CK data and vector store
	@echo "Cleaning ATT&CK data and vector store..."
	rm -rf src/report2attack/data/attack/*.json
	rm -rf ~/.report2attack/chroma_db
	@echo "Data cleanup complete!"

build: ## Build package
	@echo "Building package..."
	uv build

run-example: ## Run example with a sample URL (requires API keys)
	@echo "Running example analysis..."
	uv run report2attack https://www.bleepingcomputer.com/news/ --formats json markdown

ci: check test ## Run CI pipeline (checks and tests)
	@echo "CI pipeline complete!"
