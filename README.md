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

## Verify

```bash
npm run verify
cd apps/api && python -m pytest tests/
```
