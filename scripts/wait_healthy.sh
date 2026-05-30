#!/usr/bin/env bash
# Wait for Postgres and app health before bootstrap (used by make up).
set -euo pipefail

COMPOSE="${COMPOSE:-docker compose}"
APP_SERVICE="${APP_SERVICE:-app}"
POSTGRES_SERVICE="${POSTGRES_SERVICE:-postgres}"
POSTGRES_USER="${POSTGRES_USER:-chatbot}"
APP_PORT="${APP_PORT:-8000}"
MAX_ATTEMPTS="${MAX_ATTEMPTS:-60}"

echo "Waiting for Postgres..."
for i in $(seq 1 "$MAX_ATTEMPTS"); do
  if $COMPOSE exec -T "$POSTGRES_SERVICE" pg_isready -U "$POSTGRES_USER" >/dev/null 2>&1; then
    echo "Postgres is ready."
    break
  fi
  if [ "$i" -eq "$MAX_ATTEMPTS" ]; then
    echo "Postgres did not become ready in time." >&2
    exit 1
  fi
  sleep 1
done

echo "Waiting for app /health..."
for i in $(seq 1 "$MAX_ATTEMPTS"); do
  if curl -sf "http://localhost:${APP_PORT}/health" >/dev/null 2>&1; then
    echo "App is healthy."
    exit 0
  fi
  if [ "$i" -eq "$MAX_ATTEMPTS" ]; then
    echo "App did not become healthy in time." >&2
    exit 1
  fi
  sleep 1
done
