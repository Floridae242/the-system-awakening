# 04 Game Rules v1.0
rules_version: 1.0.0

## 1. Attributes
- STR: strength-oriented activities
- AGI: running/movement activities
- VIT: endurance/consistency activities
- INT: study/coding/learning activities
- WIL: focus/discipline activities

## 2. Quest Difficulty
EASY, NORMAL, HARD, ELITE, EXTREME

### Base EXP
- EASY: 80
- NORMAL: 120
- HARD: 180
- ELITE: 260
- EXTREME: 360

### Difficulty Multipliers
- EASY: 1.00
- NORMAL: 1.10
- HARD: 1.25
- ELITE: 1.45
- EXTREME: 1.70

## 3. Performance Bands
Derived by backend from verified condition results.
- PARTIAL: 0.70
- PASS: 1.00
- STRONG: 1.10
- EXCELLENT: 1.20

## 4. Consistency Modifier
MVP uses a bounded modifier based on current streak:
- 0–2 days: 1.00
- 3–6 days: 1.05
- 7+ days: 1.10
Maximum 1.10.

## 5. Final EXP
final_exp = round(base_exp × difficulty_multiplier × performance_multiplier × consistency_multiplier)
Minimum successful reward: 50 EXP.
Maximum per quest in MVP: 1000 EXP.

## 6. Level Curve
XP required to advance from level L to L+1:
required_xp(L) = round(100 × L^1.35)
Level starts at 1.
No level cap in MVP, but demo seed users should remain below Level 30.

## 7. Stat Growth
Successful quest grants +1 to its primary mapped stat when difficulty is NORMAL or higher.
HARD/ELITE/EXTREME with EXCELLENT performance grants an additional +1 to primary stat.
Maximum stat gain per quest: +2.
No secondary stat gain in v1.

## 8. Chest Grant Rule
A successfully completed quest grants exactly one chest.
Chest tier is determined by server-side rarity roll after settlement.

## 9. Chest Rarities and Probabilities
- COMMON: 55%
- UNCOMMON: 20%
- RARE: 13%
- EPIC: 7%
- LEGENDARY: 4%
- MYTHIC: 1%
Total = 100%.

PITY_SYSTEM = DEFERRED_PHASE_2
PAID_RANDOMNESS = DISABLED

## 10. Item Pool Rule
Each rarity has its own seed item pool. A chest can only draw from the pool matching the persisted chest rarity.

## 11. Duplicate Handling
MVP: item instances are allowed to duplicate. Each duplicate is a separate inventory instance. Conversion/essence is Phase 2.

## 12. Power Score
MVP display formula:
power = 100 + (level × 25) + ((STR+AGI+VIT+INT+WIL) × 10) + sum(item_power)
Power is a game visualization only.

## 13. Streak
Timezone: player timezone, default Asia/Bangkok for MVP demo users.
A day counts when at least one quest is COMPLETED on that local calendar date.
Grace/shield system = Phase 2.

## 14. Randomness
- RNG executes server-side only.
- Chest open result is persisted before response.
- Same chest cannot reroll.
- Random result is auditable with rng_version and optional seed/hash metadata.

## 15. Reward Transaction
For a verified submission, one database transaction must:
1. create reward_grant
2. append progression ledger entries
3. update cached profile totals
4. create exactly one chest
5. commit
On failure: rollback all.

## 16. Normative Test Vectors
### Vector A
Input: NORMAL, PASS, streak 0
Base 120 × 1.10 × 1.00 × 1.00 = 132 EXP
Expected: 132 EXP, +1 primary stat.

### Vector B
Input: HARD, EXCELLENT, streak 7
180 × 1.25 × 1.20 × 1.10 = 297
Expected: 297 EXP, +2 primary stat.

### Vector C
Duplicate settlement request for same submission
Expected: same existing reward_grant returned; no additional EXP/stat/chest.
