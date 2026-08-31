"use client";

const MUTE_KEY = "awakening-muted";

let ctx: AudioContext | null = null;

export function sfxMuted(): boolean {
  if (typeof window === "undefined") return true;
  return window.localStorage.getItem(MUTE_KEY) === "true";
}

export function sfxSetMuted(muted: boolean): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(MUTE_KEY, String(muted));
}

function audio(): AudioContext | null {
  if (sfxMuted() || typeof window === "undefined") return null;
  try {
    ctx ??= new (window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)();
    if (ctx.state === "suspended") void ctx.resume();
    return ctx;
  } catch {
    return null;
  }
}

function tone(
  frequency: number,
  duration: number,
  { type = "sine", gain = 0.07, delay = 0, slideTo }: { type?: OscillatorType; gain?: number; delay?: number; slideTo?: number } = {},
): void {
  const context = audio();
  if (!context) return;
  try {
    const oscillator = context.createOscillator();
    const amplifier = context.createGain();
    const start = context.currentTime + delay;
    oscillator.type = type;
    oscillator.frequency.setValueAtTime(frequency, start);
    if (slideTo) oscillator.frequency.exponentialRampToValueAtTime(slideTo, start + duration);
    amplifier.gain.setValueAtTime(0, start);
    amplifier.gain.linearRampToValueAtTime(gain, start + 0.012);
    amplifier.gain.exponentialRampToValueAtTime(0.0001, start + duration);
    oscillator.connect(amplifier).connect(context.destination);
    oscillator.start(start);
    oscillator.stop(start + duration + 0.02);
  } catch {
    /* audio must never break the app */
  }
}

export const sfx = {
  tap(): void {
    tone(320, 0.06, { type: "square", gain: 0.04 });
  },
  accept(): void {
    tone(392, 0.09, { type: "triangle" });
    tone(523, 0.12, { type: "triangle", delay: 0.09 });
  },
  submit(): void {
    tone(300, 0.18, { type: "sine", slideTo: 720 });
  },
  pass(): void {
    tone(523, 0.12, { type: "triangle" });
    tone(659, 0.12, { type: "triangle", delay: 0.11 });
    tone(784, 0.2, { type: "triangle", delay: 0.22 });
  },
  fail(): void {
    tone(200, 0.2, { type: "sawtooth", gain: 0.05, slideTo: 130 });
  },
  chest(): void {
    tone(392, 0.12, { type: "triangle" });
    tone(523, 0.12, { type: "triangle", delay: 0.1 });
    tone(659, 0.12, { type: "triangle", delay: 0.2 });
    tone(784, 0.16, { type: "triangle", delay: 0.3 });
    tone(1046, 0.3, { type: "sine", gain: 0.05, delay: 0.42 });
  },
  levelup(): void {
    tone(440, 0.1, { type: "square", gain: 0.05 });
    tone(554, 0.1, { type: "square", gain: 0.05, delay: 0.1 });
    tone(659, 0.1, { type: "square", gain: 0.05, delay: 0.2 });
    tone(880, 0.25, { type: "square", gain: 0.06, delay: 0.3 });
  },
  achievement(): void {
    tone(880, 0.08, { type: "sine", gain: 0.05 });
    tone(1174, 0.14, { type: "sine", gain: 0.05, delay: 0.08 });
  },
};
