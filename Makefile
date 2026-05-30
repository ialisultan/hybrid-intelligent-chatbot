.PHONY: help setup doctor postgres-up postgres-down local-init build up down wait-healthy restart logs migrate seed test test-unit test-integration lint format run shell clean clean-venv

# ── Configuration ──────────────────────────────────────────────────────────────
COMPOSE          := docker compose
APP_SERVICE      := app
POSTGRES_SERVICE := postgres
VENV_DIR         := .venv
PYTHON3          := python3

ifneq ("$(wildcard $(VENV_DIR)/bin/python)","")
  PYTHON  := $(VENV_DIR)/bin/python
  PIP     := $(VENV_DIR)/bin/pip
  UVICORN := $(VENV_DIR)/bin/uvicorn
else
  PYTHON  := python3
  PIP     := pip3
  UVICORN := uvicorn
endif

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# ── Local setup (no Docker app — Postgres via Docker optional) ─────────────────
setup: ## Create .venv and install dev dependencies
	$(PYTHON3) -m venv $(VENV_DIR)
	$(VENV_DIR)/bin/pip install --upgrade pip
	$(VENV_DIR)/bin/pip install -r requirements-dev.txt
	@if [ ! -f .env ] && [ -f .env.example ]; then cp .env.example .env; echo "Created .env from .env.example"; fi
	@echo ""
	@echo "Setup complete. Next steps:"
	@echo "  make postgres-up"
	@echo "  make local-init"
	@echo "  make run"

doctor: ## Diagnose local setup (venv, .env, Postgres)
	@test -d $(VENV_DIR) || (echo "Run 'make setup' first." && exit 1)
	@$(PYTHON) scripts/local_doctor.py doctor

postgres-up: ## Start Postgres container for local dev (localhost:5432)
	$(COMPOSE) up -d $(POSTGRES_SERVICE)
	@echo "Waiting for Postgres..."
	@for i in 1 2 3 4 5 6 7 8 9 10; do \
		$(COMPOSE) exec -T $(POSTGRES_SERVICE) pg_isready -U $${POSTGRES_USER:-chatbot} >/dev/null 2>&1 && break; \
		sleep 1; \
	done
	@$(PYTHON) scripts/local_doctor.py postgres-up

postgres-down: ## Stop Postgres container
	$(COMPOSE) stop $(POSTGRES_SERVICE)

local-init: ## Migrate + seed + index for local dev (FAISS)
	@test -d $(VENV_DIR) || (echo "Run 'make setup' first." && exit 1)
	@$(PYTHON) scripts/local_doctor.py check
	$(VENV_DIR)/bin/alembic upgrade head
	$(PYTHON) -m src.infrastructure.seed
	$(PYTHON) -m src.infrastructure.index_documents

# ── Docker ─────────────────────────────────────────────────────────────────────
build: ## Build Docker images
	$(COMPOSE) build

up: ## Start all services and bootstrap DB + vector index
	$(COMPOSE) up -d
	@$(MAKE) wait-healthy
	@$(MAKE) migrate seed index
	@echo ""
	@echo "Stack ready: http://localhost:$${APP_PORT:-8000}/docs"

wait-healthy: ## Wait for Postgres and app health checks
	@chmod +x scripts/wait_healthy.sh
	@COMPOSE="$(COMPOSE)" APP_SERVICE="$(APP_SERVICE)" POSTGRES_SERVICE="$(POSTGRES_SERVICE)" \
		APP_PORT="$${APP_PORT:-8000}" scripts/wait_healthy.sh

down: ## Stop and remove containers
	$(COMPOSE) down

restart: down up ## Restart all services

logs: ## Tail application logs
	$(COMPOSE) logs -f $(APP_SERVICE)

# ── Database ───────────────────────────────────────────────────────────────────
migrate: ## Run Alembic migrations
	$(COMPOSE) exec $(APP_SERVICE) alembic upgrade head

migrate-local: ## Run migrations locally (requires: make postgres-up)
	@test -d $(VENV_DIR) || (echo "Run 'make setup' first." && exit 1)
	@$(PYTHON) scripts/local_doctor.py migrate-local
	$(VENV_DIR)/bin/alembic upgrade head

seed: ## Seed database with sample structured data
	$(COMPOSE) exec $(APP_SERVICE) python -m src.infrastructure.seed

seed-local: ## Seed database locally (requires: make postgres-up)
	@test -d $(VENV_DIR) || (echo "Run 'make setup' first." && exit 1)
	@$(PYTHON) scripts/local_doctor.py seed-local
	$(PYTHON) -m src.infrastructure.seed

index: ## Index documents into Qdrant (Docker)
	$(COMPOSE) exec $(APP_SERVICE) python -m src.infrastructure.index_documents

index-local: ## Index documents into FAISS (local)
	@test -d $(VENV_DIR) || (echo "Run 'make setup' first." && exit 1)
	$(PYTHON) -m src.infrastructure.index_documents

# ── Development ────────────────────────────────────────────────────────────────
run: ## Run FastAPI locally with hot reload (requires: make setup)
	@test -d $(VENV_DIR) || (echo "Run 'make setup' first." && exit 1)
	$(UVICORN) main:app --host 0.0.0.0 --port 8000 --reload

install: ## Install production dependencies into .venv
	@test -d $(VENV_DIR) || (echo "Run 'make setup' first." && exit 1)
	$(PIP) install -r requirements.txt

install-dev: ## Install dev dependencies into .venv
	@test -d $(VENV_DIR) || (echo "Run 'make setup' first." && exit 1)
	$(PIP) install -r requirements-dev.txt

shell: ## Open a shell inside the app container
	$(COMPOSE) exec $(APP_SERVICE) /bin/bash

# ── Quality ────────────────────────────────────────────────────────────────────
test: ## Run test suite with coverage
	@test -d $(VENV_DIR) || (echo "Run 'make setup' first." && exit 1)
	$(VENV_DIR)/bin/pytest tests/ -v --cov=src --cov-report=term-missing

test-unit: ## Run unit tests only
	@test -d $(VENV_DIR) || (echo "Run 'make setup' first." && exit 1)
	$(VENV_DIR)/bin/pytest tests/ -v -m unit

test-integration: ## Run integration tests only
	@test -d $(VENV_DIR) || (echo "Run 'make setup' first." && exit 1)
	$(VENV_DIR)/bin/pytest tests/ -v -m integration

lint: ## Run ruff linter and mypy type checker
	@test -d $(VENV_DIR) || (echo "Run 'make setup' first." && exit 1)
	$(VENV_DIR)/bin/ruff check src tests main.py
	$(VENV_DIR)/bin/mypy src main.py

format: ## Auto-format code with ruff
	@test -d $(VENV_DIR) || (echo "Run 'make setup' first." && exit 1)
	$(VENV_DIR)/bin/ruff check --fix src tests main.py
	$(VENV_DIR)/bin/ruff format src tests main.py

# ── Cleanup ────────────────────────────────────────────────────────────────────
clean: ## Remove caches and build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage dist/ build/ *.egg-info

clean-venv: ## Remove .venv only
	rm -rf $(VENV_DIR)
