import { describe, expect, it } from "vitest";
import {
  levelFromExp,
  settleReward,
  rollLootTable,
  evaluateCriteria,
  validateRewardProfile,
  zeroStats,
} from "../src/index.js";

describe("game engine — deterministic rules", () => {
  it("calculates level from exp", () => {
    expect(levelFromExp(0)).toBe(1);
    expect(levelFromExp(99)).toBe(1);
    expect(levelFromExp(100)).toBe(2);
    expect(levelFromExp(399)).toBe(2);
    expect(levelFromExp(400)).toBe(3);
    expect(() => levelFromExp(-1)).toThrow();
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
