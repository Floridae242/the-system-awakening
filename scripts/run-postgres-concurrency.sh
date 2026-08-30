#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Keep the URL overrideable for CI or a managed test database. The local
# compose service uses the same credentials as db-migrate.sh.
USE_LOCAL_COMPOSE="${TEST_POSTGRES_URL:+false}"
export TEST_POSTGRES_URL="${TEST_POSTGRES_URL:-postgresql+asyncpg://awakening:local-awakening-only@127.0.0.1:5433/awakening}"
export DATABASE_URL="$TEST_POSTGRES_URL"

if [[ "$USE_LOCAL_COMPOSE" != "false" ]]; then
  bash scripts/db-up.sh
fi
bash scripts/db-migrate.sh
apps/api/.venv/bin/pytest -q apps/api/tests/test_postgres_concurrency.py
