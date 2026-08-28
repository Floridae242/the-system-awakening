# 03 User Flows & State Machines

## 1. Primary Happy Path
LOGIN
→ PROFILE
→ QUEST BOARD
→ QUEST DETAIL
→ ACCEPT
→ SUBMIT EVIDENCE
→ VERIFYING
→ VERIFIED
→ COMPLETED
→ REWARD GRANTED
→ CHEST UNOPENED
→ CHEST OPENED
→ ITEM IN INVENTORY
→ PROFILE UPDATED

## 2. Quest Lifecycle
OFFERED
→ ACCEPTED
→ SUBMITTED
→ VERIFYING
→ VERIFIED
→ COMPLETED

Failure branch:
VERIFYING → REJECTED
REJECTED → SUBMITTED only when resubmission policy permits.

Terminal/non-active states may include EXPIRED or CANCELLED, but they are not required for the demo path.

## 3. Submission Lifecycle
CREATED
→ QUEUED
→ VERIFYING
→ PASSED | REJECTED | NEEDS_BETTER_EVIDENCE | ERROR

Rules:
- Each submission belongs to one player quest.
- A submission is immutable after verification begins except system metadata/status.
- Duplicate idempotency key returns the original submission.

## 4. Reward Lifecycle
PENDING
→ GRANTED
→ CLAIMED only if a claim interaction is actually used.

For MVP, EXP/stat/chest settlement is automatic at GRANTED. Reward animation is presentation and must not be the source of truth.

## 5. Chest Lifecycle
UNOPENED
→ OPENED

Invariant:
- One chest has at most one persisted open result.
- Repeated open requests return the same open result.

## 6. Error / Retry UX
### AI Timeout
VERIFYING → show retry-safe loading → bounded server retry → fallback.

### Invalid AI Output
Do not mutate state. Validation failure → retry/repair → fallback.

### Low-Quality Evidence
Return NEEDS_BETTER_EVIDENCE with user-readable reason and resubmit CTA.

### Lost Network After Reward Settlement
Client reloads authoritative profile/reward state. Server must not settle again.

### Lost Network After Chest Open
Client re-calls open endpoint with idempotency key or fetches chest result; server returns persisted item.

## 7. Ownership Rules
- Player can read/write only own player quests/submissions/evidence/inventory/chests.
- Verification decision is system-authoritative, not a public user command.
- Game Engine is the only authority that mutates progression.

## 8. Screen Transitions
/auth → /home
/home → /quests
/quests/:id → /quests/:id/submit
/submissions/:id → verification result
/rewards/:id → reward reveal
/chests/:id → chest reveal
/inventory → item detail
/profile → visible growth summary
