# The System — Awakening

Real-life RPG platform: real actions → real proof → verified results → visible character growth.

## Monorepo

```
apps/web       → Next.js frontend
apps/api       → FastAPI backend
packages/game-engine → Deterministic game rules (AI never touches)
```

## Contracts (source of truth)

`01_PRD.md` through `12_RISK_REGISTER.md` + `SECURITY_PRIVACY_IP.md` + `docs/adr/`

## Quick start

```bash
npm install
npm run test              # game engine tests
cd apps/api && pip install -r requirements.txt && uvicorn main:app --reload
npm run dev:web           # frontend
```

## PostgreSQL development path

Docker Desktop must be running. The development database binds only to `127.0.0.1:5433`.

```bash
export POSTGRES_PASSWORD='choose-a-local-password'
bash scripts/db-up.sh
export DATABASE_URL="postgresql+asyncpg://awakening:${POSTGRES_PASSWORD}@127.0.0.1:5433/awakening"
bash scripts/db-migrate.sh
APP_ENV=development DEMO_MODE=true DATABASE_URL="$DATABASE_URL" \
  apps/api/.venv/bin/python -m uvicorn main:app --app-dir apps/api --host 127.0.0.1 --port 8000
```

`db-migrate.sh` runs `alembic upgrade head` and prints the applied revision. Never run a downgrade
against production; prefer a reviewed forward-fix migration. Run the real database concurrency gate
after Docker is ready:

```bash
bash scripts/run-postgres-concurrency.sh
```

To use an already-running or CI database, set `TEST_POSTGRES_URL` first; the script then skips local
compose startup and only runs the reviewed migration plus the PostgreSQL suite:

```bash
TEST_POSTGRES_URL='postgresql+asyncpg://user:password@127.0.0.1:5433/awakening' \
  bash scripts/run-postgres-concurrency.sh
```

The suite exercises concurrent quest acceptance, concurrent reward settlement (including aggregate XP),
and concurrent chest opening. It asserts exactly-once results under PostgreSQL row locks and unique
constraints.

## Hardened staging/demo containers

The production-shaped compose file defaults to a working `staging` deployment with explicit
`DEMO_MODE=true`; it requires secrets and does not publish PostgreSQL to the host:

```bash
export POSTGRES_PASSWORD='replace-with-a-strong-password'
export DATABASE_URL='postgresql+asyncpg://awakening:URL_ENCODED_PASSWORD@postgres:5432/awakening'
export JWT_SECRET='replace-with-at-least-32-random-characters'
export VERIFICATION_SERVICE_TOKEN='use-a-different-32-character-secret'
export NEXT_PUBLIC_API_URL='https://api.example.com/api/v1'
docker compose -f docker-compose.prod.yaml config
docker compose -f docker-compose.prod.yaml build
docker compose -f docker-compose.prod.yaml up -d --wait
curl -fsS http://127.0.0.1:8000/api/v1/health
```

API and web containers run as UID `10001`, drop Linux capabilities, and use read-only filesystems.
Store production secrets in the deployment platform, not in `.env` committed to Git. Back up the
PostgreSQL volume before risky migrations. Roll back application images to the previous immutable tag;
use forward-fix database migrations.

`DATABASE_URL` is separate from `POSTGRES_PASSWORD` on purpose. Percent-encode reserved characters in
the password portion (`@`, `:`, `/`, `#`, `%`) so a strong password cannot corrupt URL parsing.

The production authentication path is first-party email/password with scrypt-hashed credentials,
server-side sessions, Secure/HttpOnly cookies, double-submit CSRF protection, and the Next.js BFF
(`AWAKENING_API_INTERNAL_URL`). The legacy `/auth/demo` endpoint remains staging-only and also issues a
short-lived HttpOnly session for browser smoke tests. Do not expose `VERIFICATION_SERVICE_TOKEN` to the
browser: production verification is worker-only at
`POST /api/v1/internal/submissions/{submission_id}/verify`.

Production startup does not auto-seed content. Promote immutable/versioned content through a reviewed
migration or admin job; changing an existing quest version in place is rejected. State-changing requests
are rate limited, image evidence is magic-byte validated and stored privately (8 MiB cap), and the
PostgreSQL concurrency gate proves aggregate XP equals its ledgers under row locks and unique constraints.
The in-process limiter is intentionally single-node MVP infrastructure; deploy behind a shared limiter
(for example Redis) before horizontal scaling.

## Verify

```bash
npm run verify
cd apps/api && python -m pytest tests/
```
