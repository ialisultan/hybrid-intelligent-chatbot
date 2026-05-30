# Hybrid Intelligent Chatbot

Production-ready FastAPI backend implementing **strict SQL vs Vector routing** for the GenAI Engineer Assessment II.

## Architecture

Hexagonal (Ports & Adapters) with **LangGraph** orchestration and **LangChain LCEL** chains:

```
User Query
    ↓
LangGraph: Classifier Node (LangChain structured output + rule fallback)
    ↓
┌─────────────────────┬──────────────────────┐
│  SQL Pipeline       │  Vector Pipeline      │  ← no overlap
│  LangChain NL→SQL   │  LangChain LCEL RAG  │
│  (PostgreSQL)       │  FAISS local / Qdrant │
└──────────→ Response ←──────────────────────┘
```

| Layer | Responsibility |
|-------|----------------|
| `domain/` | Pure entities & exceptions — no LangChain/LangGraph |
| `application/` | LangGraph graph, LCEL chain definitions, pipeline services |
| `adapters/` | FAISS/Qdrant vectorstores, OpenAI LLM, chain factory |
| `infrastructure/` | DI wiring, config, indexing |

## Vector Store Backends

| Environment | Backend | Config |
|-------------|---------|--------|
| Local (`make run`) | **FAISS** (file-backed) | `VECTOR_STORE_BACKEND=faiss` |
| Docker (`make up`) | **Qdrant** (container) | `VECTOR_STORE_BACKEND=qdrant` |

## Quick Start — Docker

```bash
cp .env.example .env          # set OPENAI_API_KEY; compose overrides Qdrant
make build && make up
make migrate && make seed
make index                      # load data/ into Qdrant
open http://localhost:8000/docs
```

## Quick Start — Local (no Docker)

```bash
make setup                    # create .venv + install dependencies
make postgres-up              # start Postgres on localhost:5432 (Docker)
make local-init               # migrate + seed + index FAISS
make run                      # start uvicorn with hot reload
```

If something fails, run `make doctor` to diagnose venv, `.env`, and Postgres connectivity.

## Make Targets

| Target | Description |
|--------|-------------|
| `setup` | Create `.venv` and install dev dependencies (local, no Docker) |
| `postgres-up` | Start Postgres container for local dev |
| `local-init` | Migrate + seed + index (local FAISS) |
| `doctor` | Diagnose local setup issues |
| `run` | Start local uvicorn server with hot reload |
| `build` | Build Docker images |
| `up` / `down` | Start/stop postgres + qdrant + app |
| `migrate` / `migrate-local` | Run Alembic migrations |
| `seed` / `seed-local` | Seed sample SQL data |
| `index` / `index-local` | Index `data/` into Qdrant / FAISS |
| `test` | Run pytest with coverage |
| `lint` | Ruff + mypy |

## Project Structure

```
src/
├── domain/              # Entities & exceptions (pure Python)
├── application/
│   ├── chains/          # LangChain LCEL: RAG, classifier, SQL
│   ├── services/        # Pipeline services (LangGraph node targets)
│   ├── graph.py         # LangGraph StateGraph
│   └── ports/           # Hexagonal interfaces
├── adapters/
│   ├── vector/          # FAISS + Qdrant adapters, document loader
│   └── llm/             # LangChain LLM, classifier, chain factory
└── infrastructure/      # Config, DI, indexing, database
```

## API

**POST /api/v1/chat**

```json
{
  "query": "What is the total revenue this month?",
  "conversation_id": null
}
```

Response includes `route` (`sql` | `vector`), `confidence`, and pipeline-specific fields.

## Test Scenarios (Assessment)

| Type | Example Query |
|------|---------------|
| SQL | "Total revenue this month?" |
| SQL | "Top 5 customers by spending" |
| Vector | "What is your return policy?" |
| Edge | "Tell me about orders policy" |

## License

MIT
