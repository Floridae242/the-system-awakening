# 02 MVP Scope Freeze — The System: Awakening

## 1. Frozen 18-Day Critical Path
1. Auth
2. Player Profile
3. Seeded Quest Board
4. Accept Quest
5. Submit Image/Screenshot or Manual Evidence
6. Verification Workflow
7. Deterministic Reward Settlement
8. Chest Grant
9. Chest Open
10. Inventory Update
11. Visible Player Growth
12. Deploy + Demo fallback

## 2. MUST
- Auth and ownership checks
- PostgreSQL source of truth
- Quest lifecycle
- Submission lifecycle
- AI verification contract
- Game Rules v1
- Reward idempotency
- Chest idempotency
- Inventory
- Audit trail
- Core E2E
- Feature flag for live AI
- DEMO_MODE

## 3. SHOULD — Only After Core E2E Is Green on Deployed Demo
- Achievement reveal
- One personal Nemesis mock/polish flow
- Basic world boss visual
- Sound effects
- Extra animations

## 4. COULD
- AI dynamic quest generation behind feature flag
- Additional quest categories
- Titles
- Limited skill mastery display

## 5. WON'T for MVP
- Web3/SBT
- Paid gacha or premium currency
- PvP
- Guild system
- Tower system
- Strava/GitHub/Health integrations
- Native mobile
- Autonomous agents
- Full seasonal live-ops
- Marketplace

## 6. Change-Control Rule
A new feature may enter MUST only if:
- Core E2E is already green in staging/demo.
- It does not change Quest/Submission/Verification/Reward/Chest state contracts.
- It has explicit acceptance criteria.
- It does not threaten deployment by Day 10–12.

## 7. Scope Freeze
Days 15–18: no major new features. Only QA, polish, regression, performance, demo rehearsal and pitch.
