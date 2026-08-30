#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

docker compose -f infra/compose.yaml up -d --wait postgres
docker compose -f infra/compose.yaml exec -T postgres pg_isready -U awakening -d awakening

echo "PostgreSQL is ready on 127.0.0.1:5433. Run scripts/db-migrate.sh next."
