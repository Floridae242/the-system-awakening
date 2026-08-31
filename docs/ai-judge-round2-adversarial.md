# AI Judge Rehearsal — Round 2 (Adversarial)

> Status: Internal adversarial attack round — the panel was instructed to destroy the project on paper. No scores given (per rehearsal rule §12).
> Round 1 (scores + verdict): see `docs/ai-judge-rehearsal.md`.
> **Reality-check column added by the team**: the simulated judge sometimes proposed mitigations that do **not exist in the code**. Each item below is marked REAL (defense exists in the repo), ASPIRATIONAL (defense is a future plan — do not claim it on stage), or DEFECT (confirmed gap that contradicts an existing claim).

Run metadata:

```text
Judge model:   gpt-5.6-luna (AI_ORCHESTRA office, deep-analysis path, adversarial prompt)
Timestamp:     2026-08-31T19:4x+07:00
Cost USD:      $0.002 (single turn; an earlier attempt failed on provider fetch — $0.000)
Evidence base: pytest 40/3skip cov 87.84% · vitest 9/9 · npm audit 0 · 47 commits/3 days ·
               LOC ~5,287 · CI green · Render FREE tier · team = 1 human + AI Orchestra
Repository:    1c91cc1
```

---

## Attack Results (15 points, 7 angles)

| # | Attack | Sev | Judge's mitigation | Reality-check |
|---|---|---|---|---|
| 1 | **C1 "production-ready" overstated** — Render FREE tier, sleeps, single node | HIGH | Position it as MVP validation deployment, not production | **WORDING FIX (do it)** — on stage say "production-*shaped* MVP on free tier" |
| 2 | C2 "AI never touches state" — who enforces ADR-0003? | LOW | Cite AI Contracts v1 + docs | **WEAK DEFENSE** — docs are not enforcement; real enforcement = settlement only reachable through `game_engine` functions + CI tests. Say exactly that |
| 3 | C3 exactly-once proof | LOW | Idempotency keys + unique constraints | **REAL** — partial unique index migration + concurrency suite |
| 4 | no 2FA | MED | Planned via auth provider | **ASPIRATIONAL** — fine as roadmap, not as current capability |
| 5 | no malware scan | MED | Gateway/object-storage scan | **ASPIRATIONAL** — Annex marks it "consider for beta" |
| 6 | **manual evidence + photo still forgeable** | HIGH | Phase 2: real API integrations + risk flags + AI/human review | **TRUE GAP (core-loop threat)** — MVP wording: "MVP trusts self-reported numbers with photo; deterministic rules bound the reward; API-verified evidence is the roadmap" |
| 7 | in-memory rate limiter | MED | "Managed hosting has built-in limiting; will add distributed limiter" | **ASPIRATIONAL/FICTIONAL** — Render adds no rate limiting; only the in-process limiter exists. Do not claim otherwise |
| 8 | C7 coverage measures easy paths | LOW | E2E covers functional paths; coverage not the only metric | **REAL** — but concede: only 4 E2E scenarios; hard paths (payments, scale) untested because they don't exist yet |
| 9 | cold start 502 (seen live) | MED | Upgrade tier / warm-up function | **ASPIRATIONAL** — today: open the app 1 min early (demo script) + retry |
| 10 | worker in-process | LOW | Claims separate `apps/worker/` + queue exists | **FICTIONAL** — worker is in-process by design (single-node MVP). Real defense: DB-backed scanner is restart-safe by design |
| 11 | single node / no HA | HIGH | Multi-instance on production | **ASPIRATIONAL** — honest answer: "single-node MVP; modular monolith + Postgres means scale-up is infra work, not rewrite" |
| 12 | 10k users | MED | Modular monolith + Postgres + queue scaling | **PARTLY REAL** — architecture direction true; queue does not exist yet. Say "scale path designed, not yet built" |
| 13 | **audit log deleted with account** | HIGH | Claims audit is an independent table with separate retention | **DEFECT CONFIRMED** — `delete_account` erases `audit_events` for the player. Compliance wants retention; privacy wants erasure. Candidate fix: anonymize player_id instead of deleting audit rows (small change, revisit before submission) |
| 14 | self-review loop (AI checks AI) | LOW | AI checks schema/contract conformance only, not rule-making | **PARTLY REAL** — tests/CI are the actual gate; but reviewer separation is genuinely thin with 1 human. Concede honestly |
| 15 | 1-person bus factor | HIGH | Know-how docs reduce it; team growth planned | **PARTLY REAL** — 13 contracts + bible + README are the mitigation; true risk, say so |

---

## The 3 Most Dangerous Findings

1. **"Production-ready" is an overstatement** — it is a production-*shaped* MVP on a free tier. Fix the wording everywhere (pitch, README claims).
2. **Manual evidence + photo is still forgeable** — the deterministic engine bounds the reward, but it cannot detect a lying human. Roadmap answer: API-verified evidence + risk flags + review queue. Do not claim anti-cheat today.
3. **Audit log is destroyed on account deletion** — conflicts with the compliance/retention expectation that SECURITY_CHECKLIST implies. Candidate small fix: anonymize instead of delete (kept out of freeze scope for now — flagged for pre-submission decision).

---

## Pitch Wording Changes (apply before the demo)

| Do not say | Say instead |
|---|---|
| "production-ready" | "production-shaped MVP, live on a free tier" |
| "AI never touches game state" | "settlement is only reachable through the deterministic engine; CI + concurrency tests enforce it" |
| "secure by checklist" | "security baseline implemented and audited; malware scanning and 2FA are roadmap items" |
| "scales to 10k" | "the scale path is designed (modular monolith + Postgres); it is infra work, not a rewrite" |

---

## Next-rehearsal queue (Round 3 — if run)

1. Attack the AI-judge itself: "how do you know the agents' code is good beyond tests passing?" (§11 Q13-16 remain only partially covered)
2. Business model round: who pays, cost per active user, path to sustainability (§11 Q17-20 — untouched this round)
3. Live-demo failure drill: run the demo on a throttled connection + cold API deliberately
