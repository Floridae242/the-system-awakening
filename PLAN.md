# PLAN.md
# The System — Awakening
## Build Execution Plan for AI Orchestra / Codex

> Version: 1.0
> Status: Build-Ready Plan
> Primary Goal: Build and deploy a stable MVP of **The System — Awakening** with a complete, verifiable real-life RPG core loop.

---

## 1. Mission

Build a production-minded MVP that proves this experience end-to-end:

```text
AUTH
  ↓
PLAYER PROFILE
  ↓
QUEST OFFER / ACCEPT
  ↓
REAL-WORLD ACTION
  ↓
PROOF SUBMISSION
  ↓
VERIFICATION
  ↓
DETERMINISTIC REWARD SETTLEMENT
  ↓
EXP / STAT GROWTH
  ↓
CHEST GRANTED
  ↓
CHEST OPENED
  ↓
ITEM ADDED TO INVENTORY
  ↓
VISIBLE CHARACTER PROGRESSION
```

The MVP succeeds only when this path works repeatedly, safely, without duplicate rewards, and on a public deployment.

---

## 2. Product Rule

The product is **not** a to-do list with XP.

It is:

> **A persistent RPG identity that grows from real, verifiable actions.**

Every implementation decision should support:

```text
REAL ACTION
→ REAL PROOF
→ VERIFIED RESULT
→ GAME PROGRESSION
→ VISIBLE GROWTH
```

---

## 3. Non-Negotiable Engineering Invariants

1. AI interprets.
2. The Game Engine decides.
3. PostgreSQL stores authoritative player state.
4. The Orchestrator coordinates AI workflows.
5. AI never directly grants EXP, stats, items, achievements, or boss damage.
6. Every state-changing operation must be idempotent.
7. Reward settlement must be transactional.
8. Chest opening must produce one persisted result only.
9. Unknown or ambiguous evidence must not be invented into a PASS.
10. The product must remain usable when the AI provider fails.
11. Core gameplay must not depend on Web3.
12. No major feature enters the critical path after scope freeze.

---

## 4. MVP Scope

### MUST
- Authentication
- Player profile
- Five stats: STR, AGI, VIT, INT, WIL
- Level + EXP
- Quest board
- Seeded/template quests
- Quest acceptance
- Quest submission
- Image/screenshot proof
- Manual structured proof
- Built-in/system-generated proof where applicable
- AI evidence extraction/verification
- Deterministic verification policy
- Reward settlement
- Chest grant/open
- Loot rarity
- Inventory
- Basic character progression
- Juicy quest-clear/reward UX
- Error/fallback states
- DEMO_MODE
- Logging
- Public deployment
- Complete E2E test

### SHOULD
Only after the full MVP E2E path is green:
- Dynamic AI quest generation
- Achievement unlock
- Title
- Skill mastery
- Personal Nemesis
- World Boss
- Sound design
- Advanced animation

### WON'T — MVP Critical Path
- PvP
- Full guild system
- Native mobile app
- Full Tower
- Full Sanctuary
- Web3 economy
- NFT marketplace
- Paid random gacha
- HealthKit / Health Connect
- Strava integration
- GitHub integration
- Autonomous multi-agent swarm
- Long-term vector memory
- Complex seasonal economy

---

## 5. Authoritative Documents

Implementation must treat these as source-of-truth contracts:

```text
01_PRD.md
02_MVP_SCOPE.md
03_USER_FLOWS.md
04_GAME_RULES_V1.md
05_DATABASE_ERD.md
06_API_SPEC.yaml
07_AI_CONTRACTS.md
08_DESIGN_SYSTEM.md
09_CONTENT_SEED.json
10_TEST_PLAN.md
11_DEPLOYMENT_PLAN.md
12_RISK_REGISTER.md
SECURITY_PRIVACY_IP.md
PLAN.md
```

If code and documents disagree, stop and resolve the authoritative contract before proceeding.

---

## 6. Repository Target

```text
the-system-awakening/

├── apps/
│   ├── web/
│   ├── api/
│   └── worker/
├── packages/
│   ├── contracts/
│   ├── game-engine/
│   ├── ai/
│   ├── db/
│   ├── ui/
│   ├── config/
│   ├── telemetry/
│   └── test-utils/
├── prompts/
├── assets/
├── content/seed/
├── docs/adr/
├── infra/
├── scripts/
├── .github/workflows/
├── PLAN.md
└── README.md
```

---

## 7. Preferred MVP Stack

### Frontend
- Next.js / React
- TypeScript
- Tailwind CSS
- Framer Motion

### Backend
- Python
- FastAPI
- Pydantic
- SQLAlchemy or equivalent

### Database
- PostgreSQL
- Supabase or Neon acceptable for MVP

### AI
- Provider abstraction
- Structured output
- Vision-capable verification when image proof is used

### Infrastructure
- Vercel for frontend
- Managed API hosting
- Managed PostgreSQL
- Object storage for temporary evidence
- Error/telemetry service

---

## 8. BUILD GATE 0 — Specification Freeze

Do not implement core-loop business logic until:

- [ ] Exact MVP Core Loop frozen
- [ ] Quest lifecycle frozen
- [ ] Submission lifecycle frozen
- [ ] Verification lifecycle frozen
- [ ] Reward lifecycle frozen
- [ ] Chest lifecycle frozen
- [ ] Game Rules v1 constants frozen
- [ ] Database v1 entities frozen
- [ ] Reward idempotency strategy frozen
- [ ] Chest-open idempotency strategy frozen
- [ ] API skeleton frozen
- [ ] Verification input/output schema frozen
- [ ] Evidence storage/retention policy decided
- [ ] AI fallback behavior decided
- [ ] Seed quest schema valid
- [ ] Core-loop wireframes available

```text
PASS → Build Phase 1
FAIL → Resolve contract only; do not add new product concepts
```

---

## 9. State Machines

### Quest
```text
GENERATED
   ↓
VALIDATED
   ↓
OFFERED
   ↓ accept
ACCEPTED
   ↓
IN_PROGRESS
   ↓ submit
SUBMITTED
   ↓
VERIFYING
   ├──→ NEED_MORE_EVIDENCE
   │         ↓ resubmit
   │       SUBMITTED
   ├──→ REJECTED
   └──→ VERIFIED
              ↓ settlement
           COMPLETED
```

### Reward
```text
PENDING
  ↓
GRANTED
  ↓
CLAIMED   # only if the UX includes an explicit claim step
```

### Chest
```text
UNOPENED
   ↓ atomic server-side open
OPENED
```

A chest must never reroll after `OPENED`.

---

## 10. Core Stats

```text
STR — Strength-oriented selected activity progression
AGI — Movement / running / coordination progression
VIT — Routine consistency / sustainable rhythm
INT — Learning / coding / research / creation
WIL — Focus / follow-through / planning / completion
```

Stats represent in-game progression from activities. They are not judgments of a person's worth, health, intelligence, or body.

---

## 11. Quest Design Contract

Every quest must contain:

```text
id
version
title
fantasy_title
real_objective
quest_type
primary_stat
secondary_stat?
difficulty
estimated_minutes
success_conditions
proof_plan
safety_class
reward_profile
valid_from
valid_until
status
```

A quest may be offered only if:

```text
SAFE
AND
FEASIBLE
AND
PROOFABLE
AND
MACHINE-EVALUABLE
```

---

## 12. Quest Generation Pipeline

```text
USER CONTEXT
      ↓
GOAL ANALYSIS
      ↓
GENERATE 5–10 CANDIDATES
      ↓
SAFETY HARD GATE
      ↓
FEASIBILITY VALIDATION
      ↓
PROOF PLAN DESIGN
      ↓
PROOFABILITY VALIDATION
      ↓
RECENT-QUEST DUPLICATE CHECK
      ↓
DIFFICULTY VALIDATION
      ↓
GAME RULE VALIDATION
      ↓
RANK CANDIDATES
      ↓
SELECT / OFFER UP TO 3
      ↓
RPG NARRATIVE LAYER
```

Fantasy wording must never obscure the real requirement.

---

## 13. Quest Proof Hierarchy

```text
LEVEL 5 — DIRECT / CERTIFIED
Trusted API or system integration

LEVEL 4 — SYSTEM-GENERATED
Built-in timer, in-app quiz, internal event

LEVEL 3 — DIGITAL ARTIFACT
Git diff, file, document, deployment, design artifact

LEVEL 2 — VISUAL EVIDENCE
Screenshot or photo

LEVEL 1 — SELF-REPORT
Manual user confirmation
```

Rules:
- Personal noncompetitive quests may accept Level 1.
- Verified progression should prefer Level 2+.
- Competitive systems require Level 3+.
- Important certified achievements should prefer Level 4–5.
- Required proof must be disclosed before quest acceptance.

---

## 14. Proof-First Quest Rule

Never:
```text
Generate Quest
→ User completes
→ Discover it cannot be verified
```

Always:
```text
Generate Quest
→ Design Proof Plan
→ Validate available Proof
→ Offer Quest
```

---

## 15. Quest Families

Use reusable families:

```text
FOCUS
COMPLETE
CREATE
BUILD
LEARN
RECALL
EXPLAIN
PRACTICE
IMPROVE
EXPLORE
ORGANIZE
PLAN
REVIEW
REFLECT
COLLABORATE
MAINTAIN
RETURN
SHIP
TEST
TEACH
```

---

## 16. Stat Coverage Examples

### STR
- Complete a user-selected strength routine
- Practice a known physical technique
- Complete a consistent training session

Proof:
- connected activity record
- system timer
- activity session record

Never invent extreme repetitions or physical punishments.

### AGI
- user-selected movement session
- route exploration
- movement consistency

Proof:
- activity provider
- GPS summary
- workout screenshot
- system timer

### VIT
- maintain a selected routine
- complete weekly reset
- take a planned screen break
- consistency chain

Proof:
- in-app routine events
- timer
- timestamps

### INT
- focused study session
- recall challenge
- coding deliverable
- research summary
- diagram/explanation artifact

Proof:
- built-in timer
- quiz
- Git
- file
- deployment
- document

### WIL
- finish an open loop
- complete planned focus block
- plan and execute selected tasks
- return to a paused project

Proof:
- task events
- timer
- artifact change
- original quest completion

---

## 17. AI Verification Architecture

AI:
```text
EVIDENCE
↓
EXTRACT OBSERVATIONS
↓
RETURN STRUCTURED FACTS
```

AI does not:
```text
grant reward
change stats
change level
add items
damage boss
unlock competitive achievement
```

Backend:
```text
AI OBSERVATION
↓
SCHEMA VALIDATION
↓
POLICY EVALUATION
↓
SUCCESS CONDITIONS
↓
PASS / NEED_MORE_EVIDENCE / REVIEW / FAIL
↓
GAME ENGINE
```

---

## 18. Verification Result Contract

```json
{
  "schema_version": "verification-result-v1",
  "submission_id": "sub_...",
  "evidence_type": "image",
  "extracted_facts": {},
  "condition_results": [],
  "model_confidence": 0.0,
  "evidence_quality": "LOW",
  "risk_flags": [],
  "recommended_disposition": "UNKNOWN"
}
```

Allowed backend dispositions:
```text
PASS
NEED_MORE_EVIDENCE
REVIEW
FAIL
```

`UNKNOWN` is a valid AI observation. The model must never invent missing evidence.

---

## 19. Game Engine Boundary

The Game Engine owns:

```text
EXP
LEVEL
STAT CHANGE
LOOT
CHEST GRANT
ITEM GRANT
ACHIEVEMENT RULES
BOSS DAMAGE
```

---

## 20. Reward Settlement Transaction

```text
BEGIN

verify settlement not already completed
create reward_grant
append progression ledger entries
update cached player progression
create chest if eligible
mark quest completed
write audit event

COMMIT
```

On failure:
```text
ROLLBACK
```

---

## 21. Progression Ledger

Every mutation should be explainable.

```text
source_type = quest_submission
source_id   = sub_123

EXP +350
AGI +2
CHEST +1
```

---

## 22. Idempotency

State-changing operations must support idempotency:

```text
quest accept
quest submit
reward settlement
reward claim
chest open
inventory grant
```

Duplicate requests must not duplicate progression.

---

## 23. Chest Open Contract

First request:
```text
OPEN chest
↓
server RNG
↓
persist result
↓
grant item
↓
mark OPENED
↓
return result
```

Retry:
```text
detect existing open result
↓
return exact same item
```

Never reroll.

---

## 24. API Implementation Priority

```text
GET  /v1/player
GET  /v1/quests
POST /v1/quests/{quest_id}/accept
POST /v1/quests/{quest_id}/submissions
GET  /v1/submissions/{submission_id}
GET  /v1/rewards
POST /v1/rewards/{reward_id}/claim
POST /v1/chests/{chest_id}/open
GET  /v1/inventory
```

Verification is triggered internally by submission workflows.

---

## 25. Minimum Database Domains

```text
users
player_profiles
quest_definitions
player_quests
quest_submissions
verification_results
reward_grants
progression_ledger
item_definitions
inventory_items
chests
chest_open_results
audit_events
```

Do not model the entire future game before MVP needs it.

---

## 26. Database Invariants

- [ ] every owned resource has owner/player ID
- [ ] quest submission has stable ID
- [ ] reward source uniqueness enforced
- [ ] idempotency keys persisted
- [ ] one chest open result per chest
- [ ] progression mutations auditable
- [ ] verification stores schema/prompt/model versions
- [ ] timestamps exist on mutable records
- [ ] state fields use constrained values
- [ ] foreign keys enforce valid relations

---

## 27. AI Orchestra — MVP

Use:

```text
QUEST GENERATOR
+
DETERMINISTIC QUEST VALIDATOR
+
VERIFICATION AI
+
NARRATIVE AI
+
GAME ENGINE
```

Do not start with a large autonomous swarm.

---

## 28. AI Model Routing

```text
classification → fast/low-cost
quest generation → balanced
image verification → vision-capable
narrative → fast creative
complex future planning → reasoning
```

Keep providers behind an abstraction layer.

---

## 29. AI Failure Strategy

```text
PRIMARY CALL
↓ failure
ONE BOUNDED RETRY
↓ failure
FALLBACK
```

Hackathon fallback:
```text
DEMO_MODE deterministic fixture
```

Production fallback must never masquerade as real verification.

---

## 30. AI Observability

Store:

```text
request_id
workflow
agent/task
model/provider
prompt_version
schema_version
rules_version
latency
cost metadata where available
schema_valid
risk_flags
fallback_used
result
```

---

## 31. Evidence Safety & Privacy

Before upload:
- validate allowed types
- enforce max size
- generate server-side storage name
- do not trust client Content-Type alone
- authorize uploader
- isolate storage
- avoid public-by-default URLs

Prefer retaining:
```text
derived facts
verification result
hash
audit metadata
```

instead of raw evidence forever.

---

## 32. User Ownership Rules

Must deny:
```text
User A reads User B evidence
User A opens User B chest
User A claims User B reward
User A edits User B quest state
```

---

## 33. Frontend Critical Screens

Build order:

```text
1. Auth
2. Home / Profile
3. Quest Board
4. Quest Detail
5. Proof Submission
6. Verification Status
7. Quest Complete
8. Chest Reveal
9. Inventory
```

Optional after full path is green:
```text
10. Achievement
11. Nemesis
12. World Boss
```

---

## 34. UI State Requirements

Every interactive feature supports:

```text
LOADING
EMPTY
NORMAL
DISABLED
SUCCESS
ERROR
RETRY
```

AI actions must visibly communicate processing, failure, need-more-evidence, and fallback.

---

## 35. Design System Gate

Freeze before polish:
- color tokens
- rarity tokens
- typography
- spacing
- radius
- breakpoints
- buttons
- cards
- system panels
- progress bars
- modal/sheet pattern
- loading/error states
- reduced-motion behavior

---

## 36. Asset Strategy

Do not block engineering on final art.

Use:
```text
APPROVED ASSET
or
PROCEDURAL PLACEHOLDER
```

Use stable asset IDs through an asset registry.

---

## 37. Seed Content

MVP target:
```text
20–30 executable quests
15–20 items
5–6 rarity presentations
3 class concepts/labels
several achievements only if implemented
1 optional Nemesis
1 optional World Boss
```

All seed content must validate against canonical schemas in CI.

---

## 38. Core Automated E2E Test

```text
create/login user
↓
load profile
↓
accept quest
↓
submit proof
↓
mock/live verification
↓
settle reward
↓
assert EXP/stat changed exactly once
↓
assert one chest created
↓
open chest
↓
assert one item granted
↓
retry settlement
↓
retry chest open
↓
assert no duplicate reward/item
```

---

## 39. Must-Never-Happen Tests

- [ ] User A accesses User B evidence
- [ ] same submission grants twice
- [ ] same chest generates second result
- [ ] invalid AI JSON mutates state
- [ ] unknown evidence becomes PASS by guess
- [ ] AI outage destroys demo flow
- [ ] secret leaks into client bundle
- [ ] unsupported upload bypasses validation

Any failure blocks release.

---

## 40. CI Gate

Every PR runs:

```text
lint
↓
type check
↓
unit tests
↓
contract/schema validation
↓
integration tests
↓
build
```

Core-loop changes additionally run E2E.

---

## 41. Deployment Environments

Minimum:
```text
LOCAL
DEMO / STAGING
PRODUCTION
```

Separate DB, secrets, AI mode, and feature flags where practical.

---

## 42. Feature Flags

```text
AI_DYNAMIC_QUEST
AI_IMAGE_VERIFICATION
AI_NARRATIVE
DEMO_MODE
ACHIEVEMENTS
NEMESIS
WORLD_BOSS
```

---

## 43. Development Phases

### PHASE 0 — Contract Freeze
Deliver:
- authoritative states
- rules
- schema
- API skeleton
- AI verification contract
- wireframes

Exit when Build Gate 0 passes.

### PHASE 1 — Foundation
Deliver:
- monorepo
- local environment
- frontend shell
- backend shell
- DB connection
- migrations
- auth
- canonical contracts
- CI
- telemetry baseline

Exit:
- [ ] user authenticates
- [ ] player profile loads from DB
- [ ] dev/demo deployment reachable

### PHASE 2 — Quest Vertical Slice
Deliver:
- seeded quests
- quest board
- quest acceptance
- quest state
- quest detail

Exit:
- [ ] OFFERED → ACCEPTED works
- [ ] state persists after refresh
- [ ] ownership enforced

### PHASE 3 — Submission & Proof
Deliver:
- submission endpoint
- image/manual proof
- upload validation
- evidence metadata
- submission UI

Exit:
- [ ] valid proof can be submitted
- [ ] unsupported evidence rejected
- [ ] duplicate behavior controlled

### PHASE 4 — Verification
Deliver:
- verification workflow
- AI structured output
- schema validation
- backend decision policy
- fallback mode

Exit:
- [ ] PASS works
- [ ] NEED_MORE_EVIDENCE works
- [ ] FAIL works
- [ ] invalid model output causes no mutation
- [ ] AI outage fallback works

### PHASE 5 — Game Engine & Settlement
Deliver:
- EXP
- level
- stat
- progression ledger
- reward grant
- transaction

Exit:
- [ ] same submission settles exactly once
- [ ] all mutations auditable
- [ ] rollback tested

### PHASE 6 — Chest & Inventory
Deliver:
- chest grant
- rarity table
- server RNG
- chest open
- persisted result
- inventory

Exit:
- [ ] duplicate open returns same result
- [ ] exactly one item from one chest
- [ ] refresh preserves result

### PHASE 7 — Game Feel
Deliver:
- quest-complete sequence
- EXP animation
- stat-growth feedback
- chest animation
- rarity reveal
- responsive polish
- sound if time permits

Exit:
- [ ] motion does not block interaction
- [ ] reduced motion exists
- [ ] interrupted animation does not corrupt state

### PHASE 8 — Optional Intelligence
Only if Phases 1–7 are deployed and green:
- dynamic quest generation
- creative quest candidates
- proof-aware quest design
- narrative personalization

Exit:
- [ ] generated quest passes deterministic validator
- [ ] unsafe/unproofable quest rejected
- [ ] seeded quests remain fallback

### PHASE 9 — Optional Retention / Social
Only if capacity remains:
- achievements
- titles
- Nemesis
- World Boss

Must not destabilize Core Loop.

---

## 44. 18-Day Execution Plan

### Days 1–2 — Freeze + Foundation
- close blockers
- initialize repo
- canonical schemas
- auth
- DB migrations
- frontend shell
- deployment skeleton

**Outcome:** deployed skeleton.

### Days 3–4 — Player + Quest
- profile
- stats display
- seeded quest loader
- quest board
- quest acceptance

**Outcome:** persistent accepted quest.

### Days 5–6 — Submission
- proof model
- upload
- storage
- manual proof
- submission states

**Outcome:** proof can be submitted safely.

### Days 7–8 — Verification
- AI contract
- structured output
- deterministic backend policy
- failure states
- DEMO_MODE

**Outcome:** PASS / NEED_MORE_EVIDENCE / FAIL works.

### Days 9–10 — Game Engine
- EXP
- level
- stat
- ledger
- reward transaction
- idempotency

**Outcome:** verified quest updates character exactly once.

### Days 11–12 — Chest + Inventory + Public Core Loop
- chest creation
- RNG
- open
- inventory
- retry safety
- deployed E2E

**Outcome:** Core Loop feature-complete on public demo.

### Days 13–14 — Juicy UX
- animation
- rarity frames
- VFX
- sound
- art integration
- responsive polish

No architecture changes.

### Day 15 — Optional Feature Gate
Only if:
```text
DEPLOYED CORE LOOP = GREEN
AND
E2E = GREEN
AND
NO CRITICAL BUG
```

Choose at most 1–2:
- Achievement
- Nemesis
- World Boss
- Dynamic Quest

### Days 16–18 — Hard Scope Freeze
Only:
```text
QA
BUG FIX
PERFORMANCE
SECURITY CHECK
DEMO DATA
FALLBACK CHECK
PITCH
REHEARSAL
```

No new large feature.

---

## 45. Agent Responsibilities

### Product Architect Agent
May:
- interpret PRD
- identify task requirements
- detect contract contradictions

May not:
- silently change scope

### Backend Agent
Owns:
```text
API
domain logic
DB
authz
transactions
idempotency
```

### Game Engine Agent
Owns:
```text
EXP
level
stats
loot tables
reward rules
```

Must not use LLM output as authoritative game rules.

### AI Agent
Owns:
```text
prompt registry
structured outputs
verification extraction
quest generation
evals
fallback
```

May not mutate authoritative game state.

### Frontend Agent
Owns:
```text
screen flows
components
UI states
motion
accessibility
API integration
```

May not duplicate backend rules as independent truth.

### QA Agent
Owns:
```text
unit
integration
E2E
duplicate-request tests
AI schema tests
authorization tests
```

### Security Reviewer
Checks:
```text
auth
ownership
upload safety
secrets
rate limits
prompt injection
evidence exposure
```

### Release Agent
May deploy only if release gates pass.

---

## 46. Task Execution Contract for AI Orchestra

Every engineering task includes:

```text
TASK ID
GOAL
SCOPE
INPUT CONTRACT
OUTPUT
DEPENDENCIES
FILES / MODULE OWNERSHIP
ACCEPTANCE CRITERIA
TESTS REQUIRED
RISKS
STATUS
```

Example:

```text
TASK: CORE-014

Goal:
Implement idempotent chest opening.

Dependencies:
DB migration for chests and chest_open_results.

Acceptance:
- unopened chest can be opened
- RNG occurs on server
- result persisted
- duplicate request returns same result
- one item granted only
- wrong owner denied

Tests:
unit + integration + duplicate request
```

---

## 47. Definition of Ready

A task is `READY` only if:

- [ ] requirement clear
- [ ] scope bounded
- [ ] dependencies resolved
- [ ] API/schema known
- [ ] owner known
- [ ] acceptance criteria exist
- [ ] test expectation exists

---

## 48. Definition of Done

A feature is `DONE` only if:

- [ ] code implemented
- [ ] tests pass
- [ ] error states handled
- [ ] auth/ownership checked where relevant
- [ ] telemetry added where relevant
- [ ] schema/contracts updated
- [ ] documentation updated
- [ ] deployed to demo/staging
- [ ] acceptance criteria verified

"Code compiles" is not Done.

---

## 49. Release Gate

Release requires:

```text
CORE E2E GREEN
NO SEV-1/SEV-2 BUG
NO DUPLICATE REWARD BUG
NO DUPLICATE CHEST BUG
AUTHORIZATION TESTS GREEN
AI FALLBACK GREEN
MIGRATION FROM CLEAN DB GREEN
SECRETS OUTSIDE REPO
DEMO ACCOUNT READY
ROLLBACK PATH KNOWN
```

---

## 50. Risk Priority

Critical risks:

1. Scope creep
2. Duplicate reward/chest settlement
3. AI verification hallucination
4. Evidence privacy leak
5. Demo dependency on live AI only
6. Late deployment
7. Frontend/backend contract drift

Mitigation:

```text
Scope creep → strict MUST/SHOULD/WON'T
Duplicate reward → DB constraints + idempotency + transaction
AI hallucination → structured observations + UNKNOWN + backend policy
Privacy → minimum retention + authorization + upload controls
AI outage → DEMO_MODE + bounded retry
Late deploy → deploy skeleton immediately
Contract drift → canonical schemas + OpenAPI
```

---

## 51. Stop Conditions for AI Agents

Stop and report a contract conflict when:

```text
two authoritative documents disagree
a required state is undefined
a reward value is missing
a schema requires guessing
security ownership is unclear
AI is being asked to mutate game state
proof cannot actually verify the objective
```

Do not invent business-critical rules.

---

## 52. Scope Change Protocol

Any new feature after build begins must provide:

```text
WHY NOW?
VALUE
COST
DEPENDENCIES
CORE LOOP RISK
DELAY RISK
WHAT GETS REMOVED?
```

If nothing is removed, default MVP decision is:

```text
DEFER
```

---

## 53. Build Priority Rule

Always prioritize:

```text
CORRECTNESS
↓
CORE LOOP COMPLETENESS
↓
DEPLOYABILITY
↓
RELIABILITY
↓
GAME FEEL
↓
OPTIONAL FEATURES
```

Not feature count.

---

## 54. Demo Scenario

```text
1. Login as prepared player
2. Show Profile before quest
3. Accept a clear quest
4. Submit prepared proof
5. Show verification
6. Quest Clear
7. EXP/stat increase
8. Chest appears
9. Open chest
10. Show item
11. Return to profile
12. Show visible progression
```

Optional only if stable:
```text
13. Achievement / Nemesis / World Boss
```

---

## 55. Demo Failure Strategy

If AI fails:
```text
DEMO_MODE fixture
```

If network is unstable:
- preloaded demo account
- cached static art
- clear retry
- no dependency on optional providers

If optional feature fails:
```text
disable flag
continue core demo
```

---

## 56. Post-MVP Roadmap

### Phase 2
- GitHub proof provider
- Strava proof provider
- skill mastery
- achievements
- Nemesis
- World Boss

### Phase 3
- adaptive quest generation
- long-term progression analysis
- guild/community quests
- verified leaderboard

### Phase 4
- mobile
- health integrations
- push notifications
- background sync

### Phase 5
- scalable event architecture
- advanced fraud detection
- seasonal content platform
- creator/content tooling

### Phase 6 — Optional
- portable verified achievements
- SBT/Web3 layer

---

## 57. Scale Strategy

Start with:

```text
MODULAR MONOLITH
+
POSTGRESQL
+
WORKER
+
AI ORCHESTRATION MODULE
```

Add only based on measured bottlenecks:

```text
REDIS
QUEUE
OBJECT STORAGE
AI WORKERS
EVENT BUS
READ REPLICAS
DOMAIN SERVICES
```

Do not adopt microservices simply because the future product may be large.

---

## 58. North-Star Technical Questions

For every new system ask:

```text
1. Is AI necessary?
2. Who owns truth?
3. Is the result auditable?
4. Is it idempotent?
5. What happens on retry?
6. What happens on failure?
7. Can the user prove the action?
8. Does proof expose unnecessary data?
9. Does it destabilize the Core Loop?
10. Can we defer it?
```

---

## 59. Final Definition of MVP Success

A real user can:

```text
ENTER
↓
UNDERSTAND THEIR CHARACTER
↓
ACCEPT A MEANINGFUL QUEST
↓
DO A REAL ACTION
↓
PROVIDE REAL PROOF
↓
GET A RELIABLE VERIFICATION RESULT
↓
RECEIVE ONE CORRECT REWARD
↓
OPEN ONE CHEST
↓
GET ONE PERSISTED ITEM
↓
SEE THEIR CHARACTER GROW
↓
RETURN AND DO IT AGAIN
```

---

## 60. MASTER EXECUTION RULE

> **Do not build more until the loop works.**

> **Do not call something verified unless the proof supports it.**

> **Do not let AI own authoritative game state.**

> **Do not allow retries to create duplicate value.**

> **Do not let visual polish hide broken logic.**

> **Do not wait until the final day to deploy.**

> **Do not add optional systems after scope freeze unless the core loop is already green.**

The objective is not to create the largest possible hackathon project.

The objective is to create the smallest complete version of **The System — Awakening** that demonstrates the product identity, proof philosophy, game feel, architecture, and technical foundation needed to scale into the full platform.
