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
export function xpRequiredForNextLevel(level: number): number {
  if (!Number.isSafeInteger(level) || level < 1) throw new Error("level must be a positive safe integer");
  return Math.round(100 * level ** 1.35);
}

export function levelFromExp(totalExp: number): number {
  if (totalExp < 0 || !Number.isSafeInteger(totalExp)) throw new Error("total_exp must be a non-negative safe integer");
  let remaining = totalExp;
  let level = 1;
  while (remaining >= xpRequiredForNextLevel(level)) {
    remaining -= xpRequiredForNextLevel(level);
    level += 1;
  }
  return level;
}

export interface XpProgress {
  level: number;
  earned: number;
  required: number;
  percent: number;
}

export function xpProgress(totalExp: number): XpProgress {
  const level = levelFromExp(totalExp);
  let threshold = 0;
  for (let previousLevel = 1; previousLevel < level; previousLevel++) {
    threshold += xpRequiredForNextLevel(previousLevel);
  }
  const earned = totalExp - threshold;
  const required = xpRequiredForNextLevel(level);
  return { level, earned, required, percent: Math.round((earned / required) * 100) };
}

// ── Quest reward policy ──
export type Difficulty = "EASY" | "NORMAL" | "HARD" | "ELITE" | "EXTREME";
export type PerformanceBand = "PARTIAL" | "PASS" | "STRONG" | "EXCELLENT";

const BASE_EXP: Readonly<Record<Difficulty, number>> = {
  EASY: 80,
  NORMAL: 120,
  HARD: 180,
  ELITE: 260,
  EXTREME: 360,
};
const DIFFICULTY_MULTIPLIER: Readonly<Record<Difficulty, number>> = {
  EASY: 1,
  NORMAL: 1.1,
  HARD: 1.25,
  ELITE: 1.45,
  EXTREME: 1.7,
};
const PERFORMANCE_MULTIPLIER: Readonly<Record<PerformanceBand, number>> = {
  PARTIAL: 0.7,
  PASS: 1,
  STRONG: 1.1,
  EXCELLENT: 1.2,
};

export function calculateQuestReward(
  difficulty: string,
  performance: string,
  streakDays: number,
): { exp: number; statGain: number } {
  if (!(difficulty in BASE_EXP)) throw new Error(`invalid difficulty: ${difficulty}`);
  if (!(performance in PERFORMANCE_MULTIPLIER)) throw new Error(`invalid performance: ${performance}`);
  if (!Number.isSafeInteger(streakDays) || streakDays < 0) throw new Error("streak_days must be a non-negative safe integer");
  const typedDifficulty = difficulty as Difficulty;
  const typedPerformance = performance as PerformanceBand;
  const consistency = streakDays >= 7 ? 1.1 : streakDays >= 3 ? 1.05 : 1;
  const calculated = Math.round(
    BASE_EXP[typedDifficulty] *
      DIFFICULTY_MULTIPLIER[typedDifficulty] *
      PERFORMANCE_MULTIPLIER[typedPerformance] *
      consistency,
  );
  const exp = Math.min(1_000, Math.max(50, calculated));
  const statGain = typedDifficulty === "EASY" ? 0 :
    (["HARD", "ELITE", "EXTREME"].includes(typedDifficulty) && typedPerformance === "EXCELLENT" ? 2 : 1);
  return { exp, statGain };
}

// ── Reward profile ──
export interface RewardProfile {
  exp: number;
  stats: Partial<Stats>;
  chestTableId: string;
}

// Bounds per Game Rules V1
export const EXP_MAX_PER_QUEST = 1_000;
export const STAT_MAX_PER_QUEST = 10;

export function validateRewardProfile(profile: RewardProfile): { ok: boolean; errors: string[] } {
  const errors: string[] = [];
  if (!Number.isInteger(profile.exp) || profile.exp < 1 || profile.exp > EXP_MAX_PER_QUEST) {
    errors.push(`exp must be integer 1-${EXP_MAX_PER_QUEST}, got ${profile.exp}`);
  }
  if (!profile.chestTableId.trim()) errors.push("chestTableId is required");
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

export type ChestRarity = "COMMON" | "UNCOMMON" | "RARE" | "EPIC" | "LEGENDARY" | "MYTHIC";

export function chestRarityFromRoll(roll: number): ChestRarity {
  if (!Number.isFinite(roll) || roll < 0 || roll >= 1) throw new Error("roll must be in [0, 1)");
  if (roll < 0.55) return "COMMON";
  if (roll < 0.75) return "UNCOMMON";
  if (roll < 0.88) return "RARE";
  if (roll < 0.95) return "EPIC";
  if (roll < 0.99) return "LEGENDARY";
  return "MYTHIC";
}

export function rollLootTable(table: LootTable, rng: () => number): string {
  if (!table.entries.length || table.entries.some((entry) => !Number.isFinite(entry.weight) || entry.weight <= 0)) {
    throw new Error("loot table entries must have positive finite weights");
  }
  const totalWeight = table.entries.reduce((sum, e) => sum + e.weight, 0);
  if (totalWeight <= 0) throw new Error("loot table has no positive weight");
  const random = rng();
  if (!Number.isFinite(random) || random < 0 || random >= 1) throw new Error("rng must return a value in [0, 1)");
  let roll = random * totalWeight;
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
