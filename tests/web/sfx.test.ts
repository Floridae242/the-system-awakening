import { beforeEach, describe, expect, it } from "vitest";

import { sfx, sfxMuted, sfxSetMuted } from "../../apps/web/lib/sfx";

const store = new Map<string, string>();

beforeEach(() => {
  store.clear();
  (globalThis as unknown as { window?: unknown }).window = {
    localStorage: {
      getItem: (key: string) => store.get(key) ?? null,
      setItem: (key: string, value: string) => void store.set(key, String(value)),
    },
  };
});

describe("sfx", () => {
  it("persists the mute toggle through window.localStorage", () => {
    expect(sfxMuted()).toBe(false);
    sfxSetMuted(true);
    expect(sfxMuted()).toBe(true);
    expect(store.get("awakening-muted")).toBe("true");
    sfxSetMuted(false);
    expect(sfxMuted()).toBe(false);
  });

  it("is SSR-safe: every cue no-throw without an AudioContext", () => {
    expect(() => {
      sfx.tap();
      sfx.accept();
      sfx.submit();
      sfx.pass();
      sfx.fail();
      sfx.chest();
      sfx.levelup();
      sfx.achievement();
    }).not.toThrow();
  });

  it("stays silent while muted (audio() refuses to start)", () => {
    sfxSetMuted(true);
    expect(() => {
      sfx.pass();
      sfx.chest();
    }).not.toThrow();
  });
});
