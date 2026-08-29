// ── GAME ENGINE — Deterministic rules only. AI never touches this code. ──

// ── Stats ──
export type StatKey = "STR" | "AGI" | "VIT" | "INT" | "WIL";
export const STAT_KEYS: StatKey[] = ["STR", "AGI", "VIT", "INT", "WIL"];

export interface Stats {
  STR: number;
  AGI: number;
  VIT: number;
  INT: number;
  WIL: number;
}

export function zeroStats(): Stats {
  return { STR: 0, AGI: 0, VIT: 0, INT: 0, WIL: 0 };
}

// ── Level ──
export function levelFromExp(totalExp: number): number {
  if (totalExp < 0 || !Number.isInteger(totalExp)) throw new Error("total_exp must be a non-negative integer");
  return 1 + Math.floor(Math.sqrt(totalExp / 100));
}

// ── Reward profile ──
export interface RewardProfile {
  exp: number;
  stats: Partial<Stats>;
  chestTableId: string;
}

// Bounds per Game Rules V1
export const EXP_MAX_PER_QUEST = 500;
export const STAT_MAX_PER_QUEST = 10;

export function validateRewardProfile(profile: RewardProfile): { ok: boolean; errors: string[] } {
  const errors: string[] = [];
  if (!Number.isInteger(profile.exp) || profile.exp < 1 || profile.exp > EXP_MAX_PER_QUEST) {
    errors.push(`exp must be integer 1-${EXP_MAX_PER_QUEST}, got ${profile.exp}`);
  }
  const statKeys = Object.keys(profile.stats) as StatKey[];
  if (statKeys.length === 0) errors.push("at least one stat delta required");
  for (const key of statKeys) {
    if (!STAT_KEYS.includes(key)) errors.push(`invalid stat key: ${key}`);
    const val = profile.stats[key]!;
    if (!Number.isInteger(val) || val < 0 || val > STAT_MAX_PER_QUEST) {
      errors.push(`stat ${key} must be integer 0-${STAT_MAX_PER_QUEST}, got ${val}`);
    }
  }
  return { ok: errors.length === 0, errors };
}

// ── Settlement (transactional — caller wraps in DB transaction) ──
export interface SettlementInput {
  playerTotalExp: number;
  playerStats: Stats;
  playerLevel: number;
  rewardProfile: RewardProfile;
}

export interface SettlementOutput {
  newTotalExp: number;
  newLevel: number;
  statDeltas: Partial<Stats>;
  newStats: Stats;
  expGained: number;
}

export function settleReward(input: SettlementInput): SettlementOutput {
  const { rewardProfile } = input;
  const validation = validateRewardProfile(rewardProfile);
  if (!validation.ok) throw new Error(`Invalid reward profile: ${validation.errors.join("; ")}`);

  const expGained = rewardProfile.exp;
  const newTotalExp = input.playerTotalExp + expGained;
  const newLevel = levelFromExp(newTotalExp);

  const statDeltas: Partial<Stats> = {};
  const newStats = { ...input.playerStats };
  for (const [key, delta] of Object.entries(rewardProfile.stats)) {
    if (delta && delta > 0) {
      statDeltas[key as StatKey] = delta;
      newStats[key as StatKey] = (newStats[key as StatKey] ?? 0) + delta;
    }
  }

  return { newTotalExp, newLevel, statDeltas, newStats, expGained };
}

// ── Chest ──
export interface LootTableEntry {
  itemId: string;
  itemVersion: number;
  weight: number;
}

export interface LootTable {
  id: string;
  version: number;
  entries: LootTableEntry[];
}

export function rollLootTable(table: LootTable, rng: () => number): string {
  const totalWeight = table.entries.reduce((sum, e) => sum + e.weight, 0);
  if (totalWeight <= 0) throw new Error("loot table has no positive weight");
  let roll = rng() * totalWeight;
  for (const entry of table.entries) {
    roll -= entry.weight;
    if (roll <= 0) return entry.itemId;
  }
  return table.entries[table.entries.length - 1]!.itemId;
}

// ── Idempotency ──
export function isSafeRetry(existingHash: string, newHash: string): boolean {
  return existingHash === newHash;
}

// ── Verification decision (deterministic policy) ──
export type VerificationDecision = "PASS" | "NEED_MORE_EVIDENCE" | "REVIEW" | "FAIL";

export interface QuestCriteria {
  requiredObservation: string;
  operator: ">=" | "<=" | ">" | "<" | "==";
  value: number;
  unit: string;
}

export interface Observation {
  name: string;
  value: number | null;
  unit: string;
  source: string;
  confidence: number;
}

export function evaluateCriteria(
  criteria: QuestCriteria,
  observations: Observation[],
): VerificationDecision {
  const obs = observations.find((o) => o.name === criteria.requiredObservation);
  if (!obs || obs.value === null || obs.value === undefined) return "NEED_MORE_EVIDENCE";
  if (obs.confidence < 0.5) return "REVIEW";

  let passed = false;
  switch (criteria.operator) {
    case ">=": passed = obs.value >= criteria.value; break;
    case "<=": passed = obs.value <= criteria.value; break;
    case ">": passed = obs.value > criteria.value; break;
    case "<": passed = obs.value < criteria.value; break;
    case "==": passed = obs.value === criteria.value; break;
  }
  return passed ? "PASS" : "FAIL";
}
