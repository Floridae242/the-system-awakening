# The System — Awakening

**Real actions → real proof → deterministic growth.** A real-life RPG where every level is earned
by doing actual things (focus sessions, workouts, journaling) and proving them.

🔗 **Live:** [the-system-awakening-web.onrender.com](https://the-system-awakening-web.onrender.com/)
🎥 **Demo walkthrough:** see `DEMO_SCRIPT.md` · rehearsal video ships with the pitch

Built by **AI Orchestra** — an in-house multi-agent company (8 pixel agents + budget governor +
evidence-verified goal loops) that planned, coded, reviewed and shipped this product against a
฿900 budget. Every production commit on the timeline below was written by the AI workforce and
accepted through deterministic test gates.

## Numbers

| | |
|---|---|
| API tests | **36 passed** (+ PostgreSQL concurrency gate) · coverage **83.4%** |
| Web tests + E2E | 6 unit · 4 E2E scenarios incl. full production-like verification cycle |
| Deterministic rules | shared TS/Python test vectors (`packages/contracts/game-rules-v1.vectors.json`) |
| Audits | `npm audit` 0 vulnerabilities · assets provenance 37 tracked / 0 untracked |

## Core Loop

```
accept quest → do the REAL activity → submit proof (+ image) → deterministic
verification → exactly-once EXP/stat reward → persisted chest → inventory
```

Manual evidence without an attached image returns to the player (`NEED_MORE_EVIDENCE` → resubmit);
image-backed evidence meeting criteria settles deterministically. AI never mutates game state
(ADR-0003) and rewards are exactly-once under concurrent retries (ADR-0004, proven by the
PostgreSQL concurrency suite).

## Monorepo

```
apps/web             → Next.js 16 frontend (SYSTEM FANTASY v1 design system)
apps/api             → FastAPI + SQLAlchemy + Alembic (modular monolith)
packages/game-engine → Deterministic rules — levels/EXP/loot (AI never touches)
packages/contracts   → Shared test vectors binding TS and Python engines
infra                → docker compose (PostgreSQL 17)
```

## Contracts (source of truth)

`01_PRD.md` … `12_RISK_REGISTER.md` · **`13_GAME_EXPERIENCE_BIBLE.md`** (Game Experience Layer —
art/UX/game-design north star) · `SECURITY_PRIVACY_IP.md` · `SECURITY_CHECKLIST.md` (audited) ·
`docs/adr/0001-0004` · `09_CONTENT_SEED.json` (content versioned in DB)

## Quick start

```bash
npm install
npm run test              # workspace tests (vitest)
npm run test:api          # pytest + coverage gate (80%)
npm run test:e2e          # Playwright (demo-mode local stack)
npm run verify            # typecheck + tests + build
npm run dev:web           # frontend dev server
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
compose startup and only runs the reviewed migration plus the PostgreSQL suite. The suite exercises
concurrent quest acceptance, concurrent reward settlement (including aggregate XP), and concurrent
chest opening — asserting exactly-once results under row locks and unique constraints.

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
PostgreSQL volume before risky migrations. Roll back application images to the previous immutable
tag; use forward-fix database migrations.

`DATABASE_URL` is separate from `POSTGRES_PASSWORD` on purpose. Percent-encode reserved characters
in the password portion (`@`, `:`, `/`, `#`, `%`) so a strong password cannot corrupt URL parsing.

## Production auth & verification model

First-party email/password with scrypt-hashed credentials, server-side sessions, Secure/HttpOnly
cookies, double-submit CSRF, and the Next.js BFF (`AWAKENING_API_INTERNAL_URL`). The legacy
`/auth/demo` endpoint remains staging-only and issues a short-lived HttpOnly session for browser
smoke tests. Never expose `VERIFICATION_SERVICE_TOKEN` to the browser: production verification is
worker-only (`POST /api/v1/internal/submissions/{id}/verify`). Browser clients finalize evidence
at `POST /api/v1/submissions/{id}/finalize`; the database-backed scanner retries finalized
submissions after restarts while clients read owner-scoped results via `GET /api/v1/submissions/{id}`.

Production startup does not auto-seed content — promote immutable/versioned content through a
reviewed migration or admin job; changing an existing quest version in place is rejected.
State-changing requests are rate limited, image evidence is magic-byte validated and stored
privately (8 MiB cap), and account deletion erases profile, activity and evidence files
(privacy baseline — see `SECURITY_CHECKLIST.md`). The in-process limiter is intentionally
single-node MVP infrastructure; deploy behind a shared limiter (for example Redis) before
horizontal scaling.

## Verify

```bash
npm run verify
cd apps/api && python -m pytest tests/
```
