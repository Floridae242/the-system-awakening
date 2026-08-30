import { describe, expect, it } from "vitest";
import {
  levelFromExp,
  calculateQuestReward,
  chestRarityFromRoll,
  xpRequiredForNextLevel,
  xpProgress,
  settleReward,
  rollLootTable,
  evaluateCriteria,
  validateRewardProfile,
  zeroStats,
} from "../src/index.js";
import vectors from "../../contracts/game-rules-v1.vectors.json";

describe("game engine — deterministic rules", () => {
  it("calculates level from exp", () => {
    for (const vector of vectors.levels) {
      expect(levelFromExp(vector.total_exp)).toBe(vector.level);
    }
    expect(xpRequiredForNextLevel(1)).toBe(100);
    expect(xpRequiredForNextLevel(2)).toBe(255);
    expect(() => levelFromExp(-1)).toThrow();
  });

  it("calculates progress within the current level", () => {
    expect(xpProgress(0)).toEqual({ level: 1, earned: 0, required: 100, percent: 0 });
    expect(xpProgress(99)).toEqual({ level: 1, earned: 99, required: 100, percent: 99 });
    expect(xpProgress(100)).toEqual({ level: 2, earned: 0, required: 255, percent: 0 });
    expect(xpProgress(132)).toEqual({ level: 2, earned: 32, required: 255, percent: 13 });
  });

  it("matches the normative reward vectors", () => {
    for (const vector of vectors.rewards) {
      expect(calculateQuestReward(vector.difficulty, vector.performance, vector.streak_days)).toEqual({
        exp: vector.exp,
        statGain: vector.stat_gain,
      });
    }
  });

  it("maps persisted server rolls to the Game Rules v1 rarity table", () => {
    for (const vector of vectors.rarity_rolls) {
      expect(chestRarityFromRoll(vector.roll)).toBe(vector.rarity);
    }
    expect(() => chestRarityFromRoll(1)).toThrow();
    expect(() => chestRarityFromRoll(-0.01)).toThrow();
  });

  it("settles rewards deterministically", () => {
    const result = settleReward({
      playerTotalExp: 0,
      playerStats: zeroStats(),
      playerLevel: 1,
      rewardProfile: { exp: 100, stats: { INT: 2, WIL: 1 }, chestTableId: "DEMO_COMMON_CHEST_V1" },
    });
    expect(result.newTotalExp).toBe(100);
    expect(result.newLevel).toBe(2);
    expect(result.expGained).toBe(100);
    expect(result.newStats.INT).toBe(2);
    expect(result.newStats.WIL).toBe(1);
  });

  it("rolls loot table deterministically with seeded rng", () => {
    const table = {
      id: "DEMO_COMMON_CHEST_V1",
      version: 1,
      entries: [{ itemId: "FOCUS_CHARM", itemVersion: 1, weight: 1 }],
    };
    expect(rollLootTable(table, () => 0.5)).toBe("FOCUS_CHARM");
    expect(() => rollLootTable({ ...table, entries: [{ ...table.entries[0]!, weight: -1 }] }, () => 0.5)).toThrow();
    expect(() => rollLootTable(table, () => 1)).toThrow();
  });

  it("evaluates quest criteria deterministically", () => {
    const criteria = { requiredObservation: "duration_minutes", operator: ">=" as const, value: 30, unit: "minute" };
    const obs = (v: number | null, conf = 0.95) => [{ name: "duration_minutes", value: v, unit: "minute", source: "timer", confidence: conf }];
    expect(evaluateCriteria(criteria, obs(30))).toBe("PASS");
    expect(evaluateCriteria(criteria, obs(29))).toBe("FAIL");
    expect(evaluateCriteria(criteria, obs(null))).toBe("NEED_MORE_EVIDENCE");
    expect(evaluateCriteria(criteria, obs(30, 0.3))).toBe("REVIEW");
  });

  it("rejects invalid reward profiles", () => {
    expect(validateRewardProfile({ exp: 0, stats: {}, chestTableId: "" }).ok).toBe(false);
    expect(validateRewardProfile({ exp: 501, stats: { STR: 1 }, chestTableId: "" }).ok).toBe(false);
    expect(validateRewardProfile({ exp: 100, stats: { STR: 11 }, chestTableId: "" }).ok).toBe(false);
  });
});
