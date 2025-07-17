.PHONY: help install dev test lint format type-check ci clean docker-build docker-up docker-down

# Default target
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -e ".[dev]"

dev: ## Install in development mode with all dependencies
	pip install -e ".[dev,test]"

test: ## Run tests
	pytest tests/ -v --cov=backend --cov=frontend --cov-report=html --cov-report=term

lint: ## Run linting
	ruff check .
	ruff format --check .

format: ## Format code
	ruff format .
	ruff check --fix .

type-check: ## Run type checking
	mypy backend/ frontend/

ci: lint type-check test ## Run CI pipeline (lint, type-check, test)

clean: ## Clean up build artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .coverage htmlcov/ .pytest_cache/ .mypy_cache/ .ruff_cache/

docker-build: ## Build Docker containers
	docker-compose build

docker-up: ## Start Docker containers
	docker-compose up -d

docker-down: ## Stop Docker containers
	docker-compose down

run-backend: ## Run FastAPI backend
	uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

run-frontend: ## Run Streamlit frontend
	streamlit run frontend/app.py --server.port 8501 