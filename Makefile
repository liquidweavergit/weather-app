# Temperature Display App - Makefile
# Provides convenient targets for development, testing, and code quality

.PHONY: help install dev-install test test-docker lint format type-check pre-commit clean docker-build docker-up docker-down docker-logs

# Default target
help: ## Show this help message
	@echo "Temperature Display App - Available Commands"
	@echo "============================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ====================================================================
# Installation and Setup
# ====================================================================

install: ## Install production dependencies
	pip install -r requirements.txt

dev-install: ## Install development dependencies
	pip install -r requirements.txt
	pip install -e .[dev]
	pre-commit install

# ====================================================================
# Testing
# ====================================================================

test: ## Run tests locally
	pytest tests/ -v

test-docker: ## Run tests in Docker environment
	docker-compose -f docker-compose.yml exec app pytest tests/ -v

test-coverage: ## Run tests with coverage report
	pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html

test-coverage-docker: ## Run tests with coverage in Docker
	docker-compose -f docker-compose.yml exec app pytest tests/ -v --cov=app --cov-report=term-missing

# ====================================================================
# Code Quality - Local
# ====================================================================

format: ## Format code with Black and isort
	black .
	isort .

lint: ## Run linting with flake8
	flake8 .

type-check: ## Run type checking with mypy
	mypy .

security-check: ## Run security checks with bandit
	bandit -r . -x tests/,migrations/

pre-commit: ## Run all pre-commit hooks
	pre-commit run --all-files

pre-commit-install: ## Install pre-commit hooks
	pre-commit install

pre-commit-update: ## Update pre-commit hooks
	pre-commit autoupdate

# ====================================================================
# Code Quality - Docker
# ====================================================================

format-docker: ## Format code using Docker environment
	./scripts/pre-commit-docker.sh run black --all-files
	./scripts/pre-commit-docker.sh run isort --all-files

lint-docker: ## Run linting using Docker environment
	./scripts/pre-commit-docker.sh run flake8 --all-files

type-check-docker: ## Run type checking using Docker environment
	./scripts/pre-commit-docker.sh run mypy --all-files

security-check-docker: ## Run security checks using Docker environment
	./scripts/pre-commit-docker.sh run bandit --all-files

pre-commit-docker: ## Run all pre-commit hooks using Docker
	./scripts/pre-commit-docker.sh run --all-files

pre-commit-install-docker: ## Install pre-commit hooks in Docker
	./scripts/pre-commit-docker.sh install

# ====================================================================
# Docker Management
# ====================================================================

docker-build: ## Build Docker images
	docker-compose build

docker-up: ## Start development environment
	docker-compose up -d

docker-down: ## Stop development environment
	docker-compose down

docker-restart: ## Restart development environment
	docker-compose restart

docker-logs: ## Show logs from all services
	docker-compose logs -f

docker-logs-app: ## Show logs from app service only
	docker-compose logs -f app

docker-shell: ## Open shell in app container
	docker-compose exec app bash

docker-clean: ## Clean up Docker resources
	docker-compose down -v
	docker system prune -f

# ====================================================================
# Database Management
# ====================================================================

db-migrate: ## Run database migrations
	docker-compose exec app alembic upgrade head

db-migrate-create: ## Create new migration (usage: make db-migrate-create MESSAGE="description")
	docker-compose exec app alembic revision --autogenerate -m "$(MESSAGE)"

db-reset: ## Reset database (WARNING: destroys all data)
	docker-compose down -v
	docker-compose up -d db
	sleep 5
	docker-compose exec app alembic upgrade head

# ====================================================================
# Development Workflow
# ====================================================================

dev-setup: ## Complete development setup
	make docker-build
	make docker-up
	sleep 10
	make pre-commit-install-docker
	make db-migrate
	@echo "Development environment ready!"

dev-check: ## Run all code quality checks
	make format
	make lint
	make type-check
	make security-check
	make test

dev-check-docker: ## Run all code quality checks in Docker
	make format-docker
	make lint-docker
	make type-check-docker
	make security-check-docker
	make test-docker

# ====================================================================
# Cleanup
# ====================================================================

clean: ## Clean up generated files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf dist/
	rm -rf build/

clean-docker: ## Clean up Docker resources and generated files
	make docker-clean
	make clean

# ====================================================================
# Production
# ====================================================================

prod-build: ## Build production Docker image
	docker build -f Dockerfile.prod -t temperature-app:latest .

prod-test: ## Test production build
	docker run --rm temperature-app:latest python -c "import app; print('Production build OK')"

# ====================================================================
# Utility
# ====================================================================

check-deps: ## Check for outdated dependencies
	pip list --outdated

update-deps: ## Update pre-commit hooks and show outdated packages
	pre-commit autoupdate
	pip list --outdated

validate-config: ## Validate configuration files
	python -m yaml --version > /dev/null && echo "YAML validation: OK" || echo "YAML validation: FAILED"
	python -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb')); print('pyproject.toml: OK')" 2>/dev/null || echo "pyproject.toml: FAILED"
	pre-commit validate-config

# ====================================================================
# Documentation
# ====================================================================

docs-serve: ## Serve documentation locally (if available)
	@echo "Documentation serving not yet implemented"

# ====================================================================
# Environment Information
# ====================================================================

info: ## Show environment information
	@echo "Temperature Display App - Environment Information"
	@echo "================================================"
	@echo "Python version: $$(python --version)"
	@echo "Docker version: $$(docker --version 2>/dev/null || echo 'Not installed')"
	@echo "Docker Compose version: $$(docker-compose --version 2>/dev/null || echo 'Not installed')"
	@echo "Pre-commit version: $$(pre-commit --version 2>/dev/null || echo 'Not installed')"
	@echo "Git version: $$(git --version 2>/dev/null || echo 'Not installed')"
	@echo ""
	@echo "Project structure:"
	@find . -maxdepth 2 -type f -name "*.py" -o -name "*.yml" -o -name "*.yaml" -o -name "*.toml" -o -name "Dockerfile*" -o -name "Makefile" | head -20 