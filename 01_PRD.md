# 01 PRD — The System: Awakening

## 1. Product Summary
The System: Awakening is an AI-powered real-life RPG that converts verified real-world activities into deterministic RPG progression.

## 2. MVP Value Proposition
The MVP must prove one complete experience:

AUTH → PROFILE → SEE/ACCEPT QUEST → SUBMIT EVIDENCE → VERIFY → SETTLE EXP/STATS → GRANT CHEST → OPEN CHEST → ITEM ENTERS INVENTORY → PROFILE VISIBLY CHANGES.

## 3. Target Users
- Students and learners
- Developers / builders
- Self-improvement users
- RPG / progression-fantasy fans

## 4. Product Principles
1. Real action creates real progression.
2. AI interprets; the Game Engine decides.
3. Rewards are deterministic after verification.
4. User progress must be traceable and idempotent.
5. AI failure must not make the product unusable.

## 5. MVP Must-Have Features
- Authentication
- Player Profile
- Seeded Quest Board
- Quest acceptance
- Evidence submission: image/screenshot/manual structured entry
- AI-assisted verification
- Deterministic EXP and stat settlement
- Chest grant and server-side opening
- Inventory
- Visible profile progression
- Basic Juicy feedback / motion
- DEMO_MODE fallback

## 6. MVP Non-Goals
- PvP
- Full guilds
- Web3 / SBT in critical path
- Strava / GitHub / HealthKit / Health Connect
- Native mobile app
- Long-term AI memory
- Autonomous multi-agent system
- Complex skill tree
- Full world boss / tower / seasonal economy

## 7. Core User Stories
### US-01 Authenticate
As a user, I can sign in and access only my own player state.
Acceptance:
- Session persists securely.
- Unauthenticated users cannot access private routes.
- User A cannot access User B's evidence or inventory.

### US-02 Accept Quest
As a player, I can view an offered quest and accept it.
Acceptance:
- Only OFFERED quests may transition to ACCEPTED.
- Repeated accept requests are safe.

### US-03 Submit Evidence
As a player, I can submit allowed evidence for an ACCEPTED quest.
Acceptance:
- Submission receives a unique ID.
- Unsupported file types and oversized files are rejected.
- Same idempotency key cannot create duplicate submissions.

### US-04 Verify Quest
As the system, I can analyse evidence and produce a versioned structured result.
Acceptance:
- AI cannot mutate game state.
- Invalid AI JSON cannot reach the Game Engine.
- Failure triggers bounded retry then fallback.

### US-05 Reward Settlement
As a player, after successful verification I receive exactly one reward settlement.
Acceptance:
- EXP/stat/chest grant occurs atomically.
- Duplicate settlement attempts do not duplicate rewards.

### US-06 Open Chest
As a player, I can open an UNOPENED chest and receive exactly one persisted item result.
Acceptance:
- RNG occurs once server-side.
- Retry returns the same result.
- Inventory contains exactly one granted item instance.

### US-07 Visible Growth
As a player, I see my EXP, level/stat changes and new item immediately after settlement/opening.

## 8. Product Success Criteria
### MVP
- Core loop E2E green
- 0 known critical duplication bugs
- Public demo URL works
- AI live path and fallback path both work
- No critical authorization breach

### Initial Product Metric
Verified Meaningful Actions per Active User per Week.

## 9. Build Gate
Core-loop implementation may begin only when 02–07 are frozen at v1.
