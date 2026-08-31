# AI Judge Rehearsal

## The System — Awakening

> Status: Internal simulated judging rehearsal
> Purpose: Pitch preparation, objection discovery, technical-defense practice
> Important: This document is **not independent third-party validation**. The simulated judge is part of the AI Office environment and may contain self-evaluation bias.

---

## 1. Simulated Judge Scorecard

| Category                  |  Score | Judge Rationale                                                                                                                  |
| ------------------------- | -----: | -------------------------------------------------------------------------------------------------------------------------------- |
| Product & Core Loop       | 9.5/10 | MVP Core Loop implemented end-to-end; clear product vision; usable UX; mobile support and reduced-motion support                 |
| Engineering               |  10/10 | Automated test suites, reported 87.84% coverage, deterministic game engine, security controls, idempotency and concurrency tests |
| Innovation — AI Orchestra |  10/10 | AI development workflow coordinates Codex CLI, budget governor, Run Viewer, context/token compression and quota recovery         |
| Demo Readiness            | 9.5/10 | Production deployment available; E2E includes verification flow; fallback/demo material available                                |

---

## 2. Simulated Verdict

The simulated panel assessed the project as demonstrating a complete Core Loop, strong engineering discipline, a distinctive AI Orchestra development approach, and high demo readiness.

This verdict must be treated as **internal rehearsal feedback**, not an independent endorsement.

---

# 3. Evidence That Matters More Than the Score

For the actual pitch, prioritize measurable repository evidence over the numerical judge score.

Present evidence such as:

* Production deployment
* Core Loop E2E result
* Automated test count
* Test coverage
* Security/audit results
* Idempotency tests
* Concurrency tests
* Deterministic Game Engine
* Versioned contracts
* ADRs
* AI/provider abstraction
* Budget Governor
* Actual AI development expenditure
* Token/context compression
* DEMO_MODE/fallback behavior

Every numerical claim should be reproducible from repository or runtime evidence.

---

# 4. Hard Question #1

## "If an AI provider introduces a major model update, how do you prevent it from affecting core game logic?"

### Short Stage Answer

The AI is intentionally outside the authoritative game logic.

AI interprets evidence and returns structured observations. The deterministic backend validates those observations, and the Game Engine alone decides EXP, stats, rewards, loot and state mutations.

Therefore, replacing or upgrading an AI model does not change the rules of the game.

### Technical Defense

```text
Evidence
↓
AI Provider
↓
Structured Verification Result
↓
Schema Validation
↓
Backend Verification Policy
↓
Deterministic Game Engine
↓
Transactional State Mutation
```

Controls include:

* provider abstraction
* versioned prompt contracts
* versioned schemas
* model/version logging
* deterministic test vectors
* fallback verification behavior
* regression evaluation before provider/model promotion

Relevant architecture decision:

```text
ADR-0003
AI cannot mutate authoritative game state
```

### Stronger Follow-up Answer

A new model is treated like a replaceable interpreter, not a replacement for the Game Engine.

Before promotion, it must pass the same verification contract and regression dataset. If it does not, the previous provider/model or deterministic fallback remains available.

---

# 5. Hard Question #2

## "If you add many new Quest types or Stats later, can you preserve determinism and idempotency?"

### Short Stage Answer

Yes, because content and rules are separated from state mutation.

New Quest definitions are versioned data, while reward calculation remains inside a versioned deterministic Game Engine.

Every state mutation has a causal source and idempotency protection, so retries cannot create duplicate progression.

### Technical Defense

```text
Versioned Quest Definition
↓
Success Conditions
↓
Verified Result
↓
Reward Profile
↓
Game Rules Version
↓
Reward Settlement Transaction
↓
Progression Ledger
```

Important invariants:

```text
same verified submission
→ one settlement

same chest
→ one persisted roll

network retry
→ same result
```

Expansion therefore happens by introducing:

* new versioned content
* explicit schema migration where necessary
* reviewed reward profiles
* deterministic rule versions
* new test vectors

rather than giving AI permission to improvise progression values.

---

# 6. Hard Question #3

## "Codex wrote the production code. How will you control technical debt long-term?"

### Short Stage Answer

The project does not treat AI-generated code as trusted merely because AI generated it.

Codex is an implementation worker operating behind contracts, CI gates, automated tests, cross-model review and Definition of Done.

The repository—not the model—is the source of truth.

### Technical Defense

```text
Specification
↓
Task Contract
↓
Codex Implementation
↓
Tests
↓
Independent Review
↓
CI Gate
↓
Repository
```

Long-term controls include:

* contracts-first architecture
* canonical schemas
* OpenAPI contract
* ADRs
* deterministic Game Rules
* automated E2E
* unit/integration tests
* security gates
* small scoped changes
* versioned migrations
* reviewer separation
* future agents read the same repository contracts

### Strong Pitch Line

> "AI writes code for us, but AI does not define correctness for us. Contracts and tests do."

---

# 7. AI Orchestra Cost Evidence

Record the exact run metadata used for the rehearsal.

```text
Judge model:        gpt-5.6-luna (AI_ORCHESTRA office, deep-analysis path)
Run ID:             session T-ASTEST3 · deep-analyze turns (2026-08-31 19:1x local)
Timestamp:          2026-08-31T19:1x+07:00
Input tokens:       ~4k per judge turn (governor ledger)
Output tokens:      ~1k per judge turn
Cached tokens:      0
Cost USD:           $0.005 (judge session total: $0.002 + $0.001 + $0.002; an earlier
                    failed goal-loop attempt cost $0.01 — Gemini 429 + allowlist probes)
Cost THB:           ~฿0.50 at rate 33 (of the ฿900 ceiling)
Repository commit:  df9ddd6 (fix: EXP count-up animates from pre-settlement value)
Test run ID:        local vitest 8/8 · pytest 40 passed/3 skipped · GH Actions 33390794312 (success)
Coverage artifact:  87.84% (pytest-cov, gate 80%)
Deployment tested:  https://the-system-awakening-web.onrender.com (Render, commit df9ddd6 live)
```

Do not rely on approximate numbers when presenting final cost claims.

---

# 8. Self-Bias Disclosure

The simulated judge belongs to the same AI Office environment that participated in the development workflow.

Therefore:

```text
Judge score
≠
independent benchmark
```

Potential bias includes:

* familiarity with project architecture
* familiarity with internal terminology
* evaluation criteria derived from project documents
* possible preference toward decisions made by the same system

The score should therefore be used for:

```text
rehearsal
question discovery
pitch preparation
weakness detection
```

not as:

```text
external certification
independent validation
market validation
```

---

# 9. Recommended Pitch Usage

Do **not** lead with:

> "Our AI judge gave us 10/10."

Lead with:

> "We built an AI development office that produced the MVP under strict engineering and budget gates."

Then show measurable evidence:

```text
Core Loop
✓

Production
✓

Tests
✓

Deterministic Game Engine
✓

Idempotency
✓

Fallback
✓

AI development cost
✓
```

Afterward, explain that an internal simulated judging round was used to identify difficult questions before the real presentation.

---

# 10. Strong Demo Narrative

### Problem

Real-life productivity applications record tasks.

They rarely make personal progression feel like a persistent RPG.

### Product

The System — Awakening converts verified real-world action into RPG progression.

### Proof

Show live:

```text
Quest
↓
Real Proof
↓
Verification
↓
EXP
↓
Chest
↓
Item
↓
Character Growth
```

### Technical Differentiator

```text
AI interprets.
Game Engine decides.
Database remembers.
```

### Development Differentiator

The product itself was built through AI Orchestra:

```text
Human
↓
AI Office
↓
Task Graph
↓
Codex / Gemini
↓
Tests
↓
Evidence
↓
Production
```

### Cost Differentiator

Show actual ledger data rather than estimated savings.

---

# 11. Questions to Add to the Next Rehearsal

The next simulated panel should challenge the project with at least these questions:

### Product

1. Why is this better than adding XP to a normal habit tracker?
2. What makes users return after the novelty wears off?
3. What happens if users do not want to upload evidence?
4. Who is the first narrow target user?

### Verification

5. How do you handle fake screenshots?
6. What happens when AI is uncertain?
7. How do you prevent false rejection?
8. What data do you retain from evidence?

### Engineering

9. What fails first at 10,000 users?
10. How do you migrate game rules without invalidating historical rewards?
11. What happens halfway through a reward transaction?
12. How do you recover if an external AI provider is unavailable?

### AI Orchestra

13. How do you know the agents did not simply produce a large amount of plausible but poor code?
14. How much human intervention was actually required?
15. How reproducible is the development run?
16. Could another developer maintain the repository without AI Orchestra?

### Business

17. Who pays?
18. What prevents another company from copying the concept?
19. What is the cost per active user?
20. What is the path from hackathon MVP to sustainable product?

---

# 12. Rehearsal Rule

Each future rehearsal should become progressively more adversarial.

Do not instruct the simulated judge to praise the project.

Instruct it to:

```text
find unsupported claims
challenge metrics
attack architecture assumptions
look for demo failure modes
look for security weaknesses
look for product weaknesses
look for scalability limits
look for business-model gaps
```

The purpose is not to maximize the rehearsal score.

The purpose is to maximize readiness for a real panel.

---

# 13. Final Position

The value of this simulated judging round is not:

```text
9.5
10
10
9.5
```

The value is:

```text
MEASURABLE EVIDENCE
+
DIFFICULT QUESTIONS
+
DEFENSIBLE ANSWERS
+
DISCOVERED WEAKNESSES
+
BETTER PITCH PREPARATION
```

Use the score as internal context.

Use the evidence as the pitch.
