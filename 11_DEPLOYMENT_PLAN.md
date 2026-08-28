# 11 Deployment Plan

## 1. Environments
LOCAL
DEV
DEMO/STAGING
PRODUCTION (post-hackathon if needed)

## 2. Recommended MVP Stack
Frontend: Next.js/React + Vercel
Backend: FastAPI
DB: PostgreSQL via Supabase/Neon/managed provider
Object Storage: private bucket
Queue/Worker: optional simple worker for verification; synchronous acceptable for earliest vertical slice if timeout safe
AI: provider through abstraction layer

## 3. Secrets
- never commit secrets
- frontend receives only public configuration
- backend/API keys in deployment secret store
- separate keys per environment

## 4. CI
On pull request:
- lint
- type check
- unit tests
- integration tests
- build
- schema/content validation
- security scan where available

## 5. CD
main merge
→ build
→ deploy demo/staging
→ run smoke tests
→ manual promotion if production exists

## 6. Database Migrations
- execute versioned migrations
- test clean install
- test upgrade path
- backup before risky production migrations

## 7. Feature Flags
- ai_live_verification
- ai_dynamic_quest
- demo_mode
- achievements
- world_boss

## 8. DEMO_MODE
- deterministic fixtures only
- visibly logged as fallback
- disabled from granting unintended production progression
- test before presentation

## 9. Observability
Log:
- request_id/correlation_id
- user/player id where appropriate
- endpoint/event
- latency
- error code
- AI provider/model/prompt version
- fallback_used

Metrics:
- API errors
- AI latency/failure
- DB errors
- reward/chest duplication errors (must remain zero)

## 10. Backup / Restore
- automated DB backup if provider supports it
- documented manual export for demo snapshot
- restore procedure tested at least once before final day

## 11. Rollback
Application: previous deployment
Prompt/model: config/version rollback
Feature: feature flag off
DB: prefer forward-fix migrations; destructive changes prohibited in MVP window

## 12. Public Demo Gate
Before public demo:
- auth/ownership verified
- upload restrictions enabled
- demo fallback verified
- no secrets in repo/client
- migration from clean DB succeeds
- core E2E green

## 13. Schedule
Day 1–3: dev/demo environment exists
Day 7–9: full vertical slice deployed
Day 10–12: public demo core-loop feature complete
Day 15–18: no major feature work
