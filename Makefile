.PHONY: help setup doctor postgres-up postgres-down local-init local docker build up up-faiss up-qdrant up-pinecone down wait-healthy restart logs logs-streamlit migrate seed test test-unit test-integration lint format security-audit all run backend backend-up backend-up-qdrant stop-backend streamlit stop-streamlit shell clean clean-venv

# ── Configuration ──────────────────────────────────────────────────────────────
COMPOSE          := docker compose
APP_SERVICE      := app
POSTGRES_SERVICE := postgres
VENV_DIR         := .venv
PYTHON3          := python3

ifneq ("$(wildcard $(VENV_DIR)/bin/python)","")
  PYTHON    := $(VENV_DIR)/bin/python
  PIP       := $(VENV_DIR)/bin/pip
  UVICORN   := $(VENV_DIR)/bin/uvicorn
  STREAMLIT := $(VENV_DIR)/bin/streamlit
else
  PYTHON    := python3
  PIP       := pip3
  UVICORN   := uvicorn
  STREAMLIT := streamlit
endif

export PYTHONPATH := $(CURDIR)
APP_PORT               ?= 8000
BACKEND_URL            ?= http://localhost:$(APP_PORT)
STREAMLIT_PORT         ?= 8501
VECTOR_STORE_BACKEND   ?= faiss
export VECTOR_STORE_BACKEND

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# ── Local setup (no Docker — SQLite + FAISS on disk) ───────────────────────────
setup: ## Create .venv and install dev dependencies
	$(PYTHON3) -m venv $(VENV_DIR)
	$(VENV_DIR)/bin/pip install --upgrade pip
	$(VENV_DIR)/bin/pip install -r requirements-dev.txt
	@if [ ! -f .env ] && [ -f .env.example ]; then cp .env.example .env; echo "Created .env from .env.example"; fi
	@mkdir -p data
	@echo ""
	@echo "Setup complete. Next step:"
	@echo "  make local"

doctor: ## Diagnose local setup (venv, .env, database)
	@test -d $(VENV_DIR) || (echo "Run 'make setup' first." && exit 1)
	@$(PYTHON) scripts/local_doctor.py doctor

postgres-up: ## Optional: start Postgres container (Docker) for PostgreSQL-based local dev
	$(COMPOSE) up -d $(POSTGRES_SERVICE)
	@echo "Waiting for Postgres..."
	@for i in 1 2 3 4 5 6 7 8 9 10; do \
		$(COMPOSE) exec -T $(POSTGRES_SERVICE) pg_isready -U $${POSTGRES_USER:-chatbot} >/dev/null 2>&1 && break; \
		sleep 1; \
	done
	@$(PYTHON) scripts/local_doctor.py postgres-up

postgres-down: ## Stop Postgres container
	$(COMPOSE) stop $(POSTGRES_SERVICE)

local-init: ## Migrate + seed + index for local dev (SQLite + FAISS, no Docker)
	@test -d $(VENV_DIR) || (echo "Run 'make setup' first." && exit 1)
	@mkdir -p data
	@$(PYTHON) scripts/local_doctor.py check
	$(VENV_DIR)/bin/alembic upgrade head
	$(PYTHON) -m src.infrastructure.seed
	$(PYTHON) -m src.infrastructure.index_documents

local: ## One-shot local bootstrap: venv + SQLite migrate/seed + FAISS index (no Docker)
	@if [ ! -d $(VENV_DIR) ]; then $(MAKE) setup; fi
	@$(MAKE) local-init
	@echo ""
	@echo "Local stack ready. Start services:"
	@echo "  Terminal 1: make run        # API  → http://localhost:$(APP_PORT)/docs"
	@echo "  Terminal 2: make streamlit    # UI   → http://localhost:$(STREAMLIT_PORT)"
	@echo "  Diagnostics: make doctor"

# ── Docker ─────────────────────────────────────────────────────────────────────
build: ## Build Docker images
	$(COMPOSE) build

up: ## Start all services and bootstrap DB + vector index (uses VECTOR_STORE_BACKEND)
	$(COMPOSE) up -d
	@$(MAKE) wait-healthy
	@$(MAKE) migrate seed index

up-faiss: ## Docker stack with FAISS (default local vector store)
	COMPOSE_PROFILES= VECTOR_STORE_BACKEND=faiss $(MAKE) up

up-qdrant: ## Docker stack with Qdrant (starts qdrant profile)
	COMPOSE_PROFILES=qdrant VECTOR_STORE_BACKEND=qdrant QDRANT_HOST=qdrant $(MAKE) up

up-pinecone: ## Docker stack with Pinecone (requires PINECONE_* in .env)
	VECTOR_STORE_BACKEND=pinecone $(MAKE) up
	@echo ""
	@echo ""
	@echo "Stack ready:"
	@echo "  API docs:  http://localhost:$${APP_PORT:-8000}/docs"
	@echo "  Streamlit: http://localhost:$(STREAMLIT_PORT)"
	@echo "  (Streamlit calls API at http://app:8000 inside Docker)"

docker: build up-faiss ## One-shot Docker bootstrap: build + Postgres + API + Streamlit + FAISS

wait-healthy: ## Wait for Postgres and app health checks
	@chmod +x scripts/wait_healthy.sh
	@COMPOSE="$(COMPOSE)" APP_SERVICE="$(APP_SERVICE)" POSTGRES_SERVICE="$(POSTGRES_SERVICE)" \
		APP_PORT="$${APP_PORT:-8000}" STREAMLIT_PORT="$(STREAMLIT_PORT)" \
		VECTOR_STORE_BACKEND="$(VECTOR_STORE_BACKEND)" QDRANT_HOST="$${QDRANT_HOST:-localhost}" \
		QDRANT_PORT="$${QDRANT_PORT:-6333}" scripts/wait_healthy.sh

down: ## Stop and remove containers
	$(COMPOSE) down

restart: down up ## Restart all services

logs: ## Tail application logs
	$(COMPOSE) logs -f $(APP_SERVICE)

logs-streamlit: ## Tail Streamlit UI logs
	$(COMPOSE) logs -f streamlit

# ── Database ───────────────────────────────────────────────────────────────────
migrate: ## Run Alembic migrations (Docker app, one-off container, or local fallback)
	@if $(COMPOSE) ps --status running -q $(APP_SERVICE) 2>/dev/null | grep -q .; then \
		$(COMPOSE) exec $(APP_SERVICE) alembic upgrade head; \
	elif $(COMPOSE) ps --status running -q $(POSTGRES_SERVICE) 2>/dev/null | grep -q .; then \
		if [ -d $(VENV_DIR) ]; then \
			echo "App container not running — using local alembic (make local-init workflow)."; \
			$(MAKE) migrate-local; \
		else \
			echo "App container not running — using one-off migrate container..."; \
			$(COMPOSE) run --rm $(APP_SERVICE) alembic upgrade head; \
		fi; \
	elif [ -d $(VENV_DIR) ]; then \
		echo "Using local alembic (SQLite or local Postgres)."; \
		$(MAKE) migrate-local; \
	else \
		echo "No running containers and no .venv. Run: make setup && make local-init  (or: make up)"; \
		exit 1; \
	fi

migrate-local: ## Run migrations locally (SQLite default, or Postgres with make postgres-up)
	@test -d $(VENV_DIR) || (echo "Run 'make setup' first." && exit 1)
	@mkdir -p data
	@$(PYTHON) scripts/local_doctor.py migrate-local
	$(VENV_DIR)/bin/alembic upgrade head

seed: ## Seed database with sample structured data
	$(COMPOSE) exec $(APP_SERVICE) python -m src.infrastructure.seed

seed-local: ## Seed database locally (SQLite default, or Postgres with make postgres-up)
	@test -d $(VENV_DIR) || (echo "Run 'make setup' first." && exit 1)
	@$(PYTHON) scripts/local_doctor.py seed-local
	$(PYTHON) -m src.infrastructure.seed

index: ## Index documents into active vector backend (Docker)
	$(COMPOSE) exec $(APP_SERVICE) python -m src.infrastructure.index_documents

index-local: ## Index documents into active vector backend (local)
	@test -d $(VENV_DIR) || (echo "Run 'make setup' first." && exit 1)
	$(PYTHON) -m src.infrastructure.index_documents

# ── Development ────────────────────────────────────────────────────────────────
stop-backend: ## Stop local uvicorn processes bound to APP_PORT
	@pids=$$(lsof -tiTCP:$(APP_PORT) -sTCP:LISTEN 2>/dev/null); \
	if [ -n "$$pids" ]; then \
		echo "Stopping process(es) on port $(APP_PORT): $$pids"; \
		kill $$pids 2>/dev/null || true; \
		sleep 1; \
		pids2=$$(lsof -tiTCP:$(APP_PORT) -sTCP:LISTEN 2>/dev/null); \
		[ -z "$$pids2" ] || kill -9 $$pids2 2>/dev/null || true; \
	else \
		echo "No listener on port $(APP_PORT)."; \
	fi

run: ## Run FastAPI locally with hot reload (requires: make setup)
	@test -d $(VENV_DIR) || (echo "Run 'make setup' first." && exit 1)
	@$(PYTHON) scripts/port_guard.py $(APP_PORT) backend
	$(UVICORN) src.main:app --host 0.0.0.0 --port $(APP_PORT) --reload

backend: run ## Alias: run FastAPI backend locally

backend-up: ## Start Postgres + API only (FAISS or Pinecone — no Qdrant container)
	$(COMPOSE) up -d $(POSTGRES_SERVICE) $(APP_SERVICE)

backend-up-qdrant: ## Start Postgres + Qdrant + API (no Streamlit)
	COMPOSE_PROFILES=qdrant VECTOR_STORE_BACKEND=qdrant QDRANT_HOST=qdrant \
		$(COMPOSE) up -d $(POSTGRES_SERVICE) qdrant $(APP_SERVICE)

stop-streamlit: ## Stop local Streamlit processes bound to STREAMLIT_PORT
	@pids=$$(lsof -tiTCP:$(STREAMLIT_PORT) -sTCP:LISTEN 2>/dev/null); \
	if [ -n "$$pids" ]; then \
		echo "Stopping process(es) on port $(STREAMLIT_PORT): $$pids"; \
		kill $$pids 2>/dev/null || true; \
		sleep 1; \
		pids2=$$(lsof -tiTCP:$(STREAMLIT_PORT) -sTCP:LISTEN 2>/dev/null); \
		[ -z "$$pids2" ] || kill -9 $$pids2 2>/dev/null || true; \
	else \
		echo "No listener on port $(STREAMLIT_PORT)."; \
	fi

streamlit: ## Run Streamlit UI locally (requires: make setup + make run)
	@test -d $(VENV_DIR) || (echo "Run 'make setup' first." && exit 1)
	@$(PYTHON) scripts/port_guard.py $(STREAMLIT_PORT) streamlit
	BACKEND_URL=$(BACKEND_URL) $(STREAMLIT) run frontend/app.py \
		--server.port $(STREAMLIT_PORT) \
		--server.address=0.0.0.0

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
	$(VENV_DIR)/bin/ruff check src tests
	$(VENV_DIR)/bin/mypy src

format: ## Auto-format code with ruff
	@test -d $(VENV_DIR) || (echo "Run 'make setup' first." && exit 1)
	$(VENV_DIR)/bin/ruff check --fix src tests
	$(VENV_DIR)/bin/ruff format src tests

security-audit: ## Scan production dependencies for known CVEs (pip-audit)
	@test -d $(VENV_DIR) || (echo "Run 'make setup' first." && exit 1)
	$(VENV_DIR)/bin/pip-audit -r requirements.txt

all: lint test ## Full quality gate: ruff + mypy + test suite with coverage

# ── Cleanup ────────────────────────────────────────────────────────────────────
clean: ## Remove caches and build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage dist/ build/ *.egg-info

clean-venv: ## Remove .venv only
	rm -rf $(VENV_DIR)
