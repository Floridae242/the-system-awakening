# Security & Privacy Checklist — verified implementation state

Maps every item of `SECURITY_PRIVACY_IP.md` (Annex) to its implementation and proof. Audited 2026-08-31.

## Evidence Upload Baseline

| Requirement | Status | Proof |
|---|---|---|
| Authenticated uploader only | ✅ | `upload_routes.py` — `Depends(current_player)`; submission must belong to the player |
| Extension allowlist | ✅ | `uploads.py` — `.png/.jpg/.jpeg/.webp` only |
| Validate actual file type | ✅ | PIL decode + `image.verify()` + second decode (rejects probes/polyglots — E2E `auth-security` + rehearsal: fabricated PNG rejected) |
| Server-generated storage names | ✅ | `store_private_image()` — UUID object keys under `storage_root()`; client name discarded |
| Size limit | ✅ | `read_validated_image` byte cap + BFF `maxBodyBytes` (413 before upstream) |
| Private object storage | ✅ | files live outside any static mount; served nowhere |
| No public-by-default evidence URLs | ✅ | no route exposes evidence bytes; only ownership-scoped metadata |
| Malware/sandbox checks | ⏳ noted for production beta | Annex marks this "consider for production beta" |

## Auth & Sessions

| Requirement | Status | Proof |
|---|---|---|
| scrypt password hashing | ✅ | `auth_routes._password_hash/_password_verify` (+ unit tests incl. malformed-hash rejection) |
| HttpOnly server-side sessions | ✅ | `awakening_session` cookie = opaque token; server table `auth_sessions` holds only SHA-256 hash |
| CSRF on state-changing auth actions | ✅ | double-submit `X-CSRF-Token` vs `awakening_csrf`; enforced on logout + account deletion (tests) |
| Rate limiting | ✅ | `rate_limit.py` in-process limiter on auth + API routes |
| Ownership isolation (R-06) | ✅ | every query filters `player_id == current_player.id`; cross-user evidence read denied (test plan case) |

## Account Lifecycle (Privacy)

| Requirement | Status | Proof |
|---|---|---|
| User can delete account/activity | ✅ | `DELETE /api/v1/auth/account` — erases sessions, credentials, profile, quests, submissions, verifications, rewards, ledger, chests, inventory, idempotency keys, audit events; best-effort removal of private evidence files (test: files gone, `/me` 401) |
| Minimum data collection | ✅ | account = email + password hash only; evidence metadata without owner id is not retained after deletion |
| Raw evidence retention | ✅ | private files are deleted with the account; deletion test asserts storage returns to pre-upload state |
| Redact sensitive content from logs | ✅ | `redactSecrets()` on Office/agent logs; API logs carry ids and reason codes, not payloads |

## Idempotency & Integrity (Risk Register)

| Requirement | Status | Proof |
|---|---|---|
| Duplicate rewards impossible (R-04) | ✅ | unique `reward_grants.player_quest_id/submission_id` + `settle_verified_submission` re-check |
| Chest reroll impossible (R-05) | ✅ | persisted `chest_open_results` (unique chest) + idempotency key on open |
| Deterministic progression (ADR-0003) | ✅ | AI/agents never mutate game state; settlement only via `game_engine` rules + shared TS/Python vectors |
| Exactly-once progression guard | ✅ | migration `c7d81e2a4f30` (partial unique index on active submissions) |

## Art Provenance (IP)

| Requirement | Status | Proof |
|---|---|---|
| Every production asset records provenance | ✅ | `assets/provenance/*.json` — PixelLab generations carry provider + promoted hashes; external furniture carries MIT source manifest (`pixel-agents-furniture.json`) |
| No recognisable third-party characters | ✅ | pixel-agents characters (JIK-A-4 art) deliberately excluded; only original/MIT furniture imported |
| Integrity tracking | ✅ | `assets/integrity.json` sha256 manifest; `assets:audit` → 37 tracked / 0 untracked |
