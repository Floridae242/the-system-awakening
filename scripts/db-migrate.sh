#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

export DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://awakening:local-awakening-only@127.0.0.1:5433/awakening}"
apps/api/.venv/bin/alembic -c alembic.ini upgrade head
apps/api/.venv/bin/alembic -c alembic.ini current
