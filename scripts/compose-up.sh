#!/usr/bin/env bash
# One-command deploy: Streamlit UI + FastAPI on Docker Compose.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo "Creating .env from .env.example (edit with your keys)..."
  cp .env.example .env
fi

USE_POSTGRES=false
for arg in "$@"; do
  if [[ "$arg" == "--postgres" ]]; then
    USE_POSTGRES=true
  fi
done

echo "Building and starting IVSURF containers..."
if $USE_POSTGRES; then
  docker compose -f docker-compose.yml -f docker-compose.postgres.yml up -d --build
else
  docker compose up -d --build
fi

echo ""
echo "IVSURF is running:"
echo "  UI:  http://localhost:${IVSURF_UI_PORT:-8501}"
echo "  API: http://localhost:${IVSURF_API_PORT:-8000}/health"
echo ""
echo "Stop: docker compose down"
