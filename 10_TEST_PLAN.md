# 10 Test Plan

## 1. Quality Gate
A feature is not Done until tests appropriate to its risk are green.

## 2. Unit Tests
### Game Engine
- EXP formula vectors
- Level curve
- +1/+2 stat rules
- rarity probability table sums to 100
- power formula
- invalid difficulty rejected

### State Machines
- legal transitions accepted
- illegal transitions rejected

## 3. Database / Integration Tests
- one reward per submission
- one chest per reward grant
- one open result per chest
- transaction rollback on partial settlement failure
- idempotency key returns existing result
- ownership isolation

## 4. Core E2E — MUST NEVER BREAK
1. create/login user
2. load player
3. accept quest
4. submit evidence
5. mock verification PASS
6. settle reward
7. assert EXP/stat changed
8. assert exactly one chest exists
9. open chest
10. assert exactly one inventory item
11. retry settlement/open
12. assert no duplication

## 5. Failure E2E
- invalid AI JSON → no mutation, fallback/error
- AI timeout → bounded retry then fallback
- low-quality evidence → resubmit state
- User A reads User B evidence → denied
- lost network after chest open → same result on retry

## 6. AI Evaluation
Golden dataset categories:
- valid evidence
- wrong evidence
- ambiguous evidence
- unreadable evidence
- prompt injection inside screenshot
- wrong date / mismatch where detectable

Metrics:
- schema validity
- backend decision agreement with labeled PASS / NEED_MORE_EVIDENCE / REVIEW / FAIL
- false positive rate
- false negative rate
- latency
- fallback rate

## 7. Security Tests
- auth required
- object ownership checks
- file extension/type/size validation
- rate limit on AI-backed endpoints
- no secrets in client bundle

## 8. Visual Regression
Screens: Home, Quest, Verification, Reward, Chest, Inventory.

## 9. Performance Smoke Targets
- non-AI API p95 target < 500 ms in demo environment under light load
- UI remains responsive during AI verification

## 10. Demo Acceptance
- live AI path works
- DEMO_MODE works without external provider
- clean DB migration works
- public URL works on desktop and mobile browser
