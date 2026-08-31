"use client";

import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import { xpProgress } from "@tsa/game-engine";
import { api } from "../lib/api";
import { sfx, sfxMuted, sfxSetMuted } from "../lib/sfx";

type Stats = { str: number; agi: number; vit: number; int: number; wil: number };
type Player = { id: string; display_name: string; level: number; current_xp: number; stats: Stats };
type Quest = {
  definition_id: string;
  title: string;
  category: string;
  difficulty: string;
  primary_stat: string;
  objective: { type: string; target: number | string };
};
type Accepted = { id: string; definition_id: string; status: string };
type Submission = { id: string; status: string };
type Reward = { id: string; exp_granted: number; stat_changes: Record<string, number>; chest_id: string };
type Achievement = { code: string; name: string; description: string };
type VerificationDetail = {
  verification: { decision: "PASS" | "NEED_MORE_EVIDENCE" | "REVIEW" | "FAIL"; reason_code: string };
  reward: Reward | null;
  achievements_unlocked?: Achievement[];
  flashPass?: boolean;
};
type SubmissionDetail = Submission & {
  verification: VerificationDetail["verification"] | null;
  reward: Reward | null;
  achievements_unlocked?: Achievement[];
};
type ActiveProgress = { accepted: Accepted; submission: SubmissionDetail | null } | null;
type InventoryItem = { id: string; name: string; rarity: string; power: number };
type ChestResult = { chest_id: string; rarity: string; item: InventoryItem; achievements_unlocked?: Achievement[] };

// Next inlines this public flag at build time. CI enables the deterministic
// demo flow for E2E; production explicitly disables it.
const demoEnabled = process.env.NEXT_PUBLIC_DEMO_MODE === "true";

const stats: Array<[keyof Stats, string]> = [
  ["str", "STR"], ["agi", "AGI"], ["vit", "VIT"], ["int", "INT"], ["wil", "WIL"],
];

function SystemCore({ level }: { level: number }) {
  const rings = Math.min(5, 1 + Math.floor(level / 2));
  const radii = [11, 15, 19, 23, 27];
  return (
    <svg className="system-core" width="36" height="36" viewBox="0 0 64 64" aria-hidden="true" role="presentation">
      <circle cx="32" cy="32" r="5" className="core-heart" />
      {radii.slice(0, rings).map((r, i) => (
        <circle key={r} cx="32" cy="32" r={r} className={`core-ring ring-${i + 1}`} pathLength={100} />
      ))}
    </svg>
  );
}

function runeSeed(code: string): number {
  let sum = 0;
  for (let i = 0; i < code.length; i++) sum += code.charCodeAt(i) * (i + 3);
  return sum % 360;
}

function Rune({ seed }: { seed: number }) {
  const angle = (seed % 60) - 30;
  return (
    <svg className="rune" width="20" height="20" viewBox="0 0 24 24" aria-hidden="true" role="presentation">
      <polygon points="12,2 21,7 21,17 12,22 3,17 3,7" fill="none" stroke="currentColor" strokeWidth="1.4" />
      <polygon
        points="12,6 18,15 6,15"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.1"
        transform={`rotate(${angle} 12 13)`}
      />
      <circle cx="12" cy="13" r="1.6" fill="currentColor" />
    </svg>
  );
}

export function AwakeningApp() {
  const [token, setToken] = useState("");
  const [handle, setHandle] = useState("hunter");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  // Production disables the demo endpoint (DEMO_MODE=false), so real account
  // authentication must be the safe default. Demo remains available when
  // explicitly selected in local/demo environments.
  const [authMode, setAuthMode] = useState<"demo" | "account" | "register">("account");
  const [player, setPlayer] = useState<Player | null>(null);
  const [quests, setQuests] = useState<Quest[]>([]);
  const [selected, setSelected] = useState<Quest | null>(null);
  const [accepted, setAccepted] = useState<Accepted | null>(null);
  const [submission, setSubmission] = useState<Submission | null>(null);
  const [verification, setVerification] = useState<VerificationDetail | null>(null);
  const [inventory, setInventory] = useState<InventoryItem[]>([]);
  const [chest, setChest] = useState<ChestResult | null>(null);
  const [duration, setDuration] = useState(30);
  const [evidenceFile, setEvidenceFile] = useState<File | null>(null);
  const [completed, setCompleted] = useState(false);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("Enter the System to begin.");
  const [toasts, setToasts] = useState<Achievement[]>([]);
  const [muted, setMuted] = useState(false);
  const [scanning, setScanning] = useState("");
  const levelRef = useRef(0);
  const xpRef = useRef(0);

  function chooseQuest(quest: Quest) {
    if (accepted && !verification) return;
    setSelected(quest);
    setAccepted(null);
    setSubmission(null);
    setVerification(null);
    setChest(null);
    setCompleted(false);
    setEvidenceFile(null);
  }

  const loadWorld = useCallback(async (accessToken: string) => {
    const [nextPlayer, nextQuests, nextInventory, active] = await Promise.all([
      api<Player>("/player", { token: accessToken }),
      api<Quest[]>("/quests", { token: accessToken }),
      api<InventoryItem[]>("/inventory", { token: accessToken }),
      api<ActiveProgress>("/quests/active", { token: accessToken }),
    ]);
    setPlayer(nextPlayer);
    setQuests(nextQuests);
    setInventory(nextInventory);
    if (active) {
      setAccepted(active.accepted);
      setSubmission(active.submission);
      setVerification(active.submission?.verification
        ? { verification: active.submission.verification, reward: active.submission.reward }
        : null);
      setSelected(nextQuests.find((quest) => quest.definition_id === active.accepted.definition_id) ?? nextQuests[0] ?? null);
    } else {
      setSelected((current) => current ?? nextQuests[0] ?? null);
    }
    if (levelRef.current && nextPlayer.level > levelRef.current) sfx.levelup();
    levelRef.current = nextPlayer.level;
    xpRef.current = nextPlayer.current_xp;
  }, []);

  useEffect(() => {
    // Authentication is maintained by the HttpOnly BFF cookie. JavaScript
    // deliberately never persists or reads an access token.
    setMuted(sfxMuted());
    loadWorld("").catch(() => undefined);
  }, [loadWorld]);

  function countUpExp(from: number, to: number): void {
    if (to <= from) { xpRef.current = to; return; }
    const startedAt = performance.now();
    const tick = (now: number) => {
      const progress = Math.min(1, (now - startedAt) / 900);
      const eased = 1 - Math.pow(1 - progress, 3);
      setPlayer((current) => (current ? { ...current, current_xp: Math.round(from + (to - from) * eased) } : current));
      if (progress < 1) requestAnimationFrame(tick);
      else xpRef.current = to;
    };
    requestAnimationFrame(tick);
  }

  function revealAchievements(items: Achievement[] | undefined): void {
    if (!items?.length) return;
    sfx.achievement();
    setToasts((current) => [...current, ...items]);
    window.setTimeout(() => setToasts((current) => current.slice(items.length)), 4600);
  }

  async function act(action: () => Promise<void>) {
    setBusy(true);
    try {
      await action();
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "The System encountered an unknown error.");
    } finally {
      setBusy(false);
    }
  }

  function login(event: FormEvent) {
    event.preventDefault();
    void act(async () => {
      if (authMode === "demo") {
        await api<{ access_token: string }>("/auth/demo", { method: "POST", body: JSON.stringify({ handle }) });
      } else if (authMode === "register") {
        await api("/auth/register", { method: "POST", body: JSON.stringify({ email, password }) });
      } else {
        await api("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
      }
      setToken("");
      await loadWorld("");
      setNotice("SYSTEM ONLINE — choose a quest.");
    });
  }

  function acceptQuest() {
    if (!selected) return;
    void act(async () => {
      const result = await api<Accepted>(`/quests/${selected.definition_id}/accept`, {
        method: "POST", token, idempotencyKey: crypto.randomUUID(),
      });
      sfx.accept();
      setAccepted(result);
      setSubmission(null);
      setVerification(null);
      setChest(null);
      setCompleted(false);
      setNotice("QUEST ACCEPTED — complete the real objective, then submit proof.");
    });
  }

  function submitProof() {
    if (!accepted || !selected) return;
    void act(async () => {
      const manual_evidence = selected.objective.type === "completion"
        ? { completion: completed }
        : { [selected.objective.type]: duration };
      const result = await api<Submission>(`/quests/${accepted.id}/submissions`, {
        method: "POST",
        token,
        idempotencyKey: crypto.randomUUID(),
        body: JSON.stringify({ evidence_type: "manual", manual_evidence }),
      });
      if (evidenceFile) {
        const form = new FormData();
        form.append("image", evidenceFile);
        await api(`/submissions/${result.id}/evidence/image`, { method: "POST", body: form });
      }
      const finalized = demoEnabled
        ? result
        : await api<Submission>(`/submissions/${result.id}/finalize`, { method: "POST", token });
      sfx.submit();
      setSubmission(finalized);
      setNotice(evidenceFile ? "PROOF + IMAGE RECEIVED — verification queued." : "PROOF RECEIVED — verification queued.");
    });
  }

  function verify() {
    if (!submission) return;
    void act(async () => {
      let current = submission;
      if (!demoEnabled && current.status === "CREATED") {
        current = await api<Submission>(`/submissions/${current.id}/finalize`, { method: "POST", token });
        setSubmission(current);
      }
      let result: VerificationDetail | SubmissionDetail = demoEnabled
        ? await api<VerificationDetail>(`/submissions/${current.id}/verify`, { method: "POST", token })
        : await api<SubmissionDetail>(`/submissions/${current.id}`, { token });
      const scanPhases = ["SCANNING EVIDENCE…", "CHECKING QUEST CONDITIONS…", "PREPARING RESULT…"];
      for (let attempt = 0; !demoEnabled && !result.verification && attempt < 5; attempt += 1) {
        setScanning(scanPhases[Math.min(attempt, scanPhases.length - 1)]!);
        await new Promise((resolve) => setTimeout(resolve, 700));
        result = await api<SubmissionDetail>(`/submissions/${current.id}`, { token });
      }
      setScanning("");
      if (!result.verification) {
        setNotice("VERIFICATION IN PROGRESS — check again shortly.");
        return;
      }
      setVerification({ verification: result.verification, reward: result.reward, flashPass: result.verification.decision === "PASS" });
      const gained = result.reward?.exp_granted ?? 0;
      await loadWorld(token);
      if (gained > 0) countUpExp(xpRef.current, xpRef.current + gained);
      if (result.verification.decision === "PASS") sfx.pass(); else sfx.fail();
      revealAchievements(result.achievements_unlocked);
      setNotice(result.verification.decision === "PASS" ? "QUEST CLEAR — exactly one reward and chest granted." : result.verification.reason_code);
    });
  }

  function openChest() {
    const chestId = verification?.reward?.chest_id;
    if (!chestId) return;
    void act(async () => {
      const result = await api<ChestResult>(`/chests/${chestId}/open`, {
        method: "POST", token, idempotencyKey: crypto.randomUUID(),
      });
      sfx.chest();
      setChest(result);
      await loadWorld(token);
      revealAchievements(result.achievements_unlocked);
      setNotice(`CHEST OPENED — ${result.item.name} persisted in inventory.`);
    });
  }

  if (!player) {
    return (
      <main className="login-shell">
        <section className="system-card login-card">
          <p className="eyebrow">AI RPG IDENTITY PROTOCOL</p>
          <h1>THE SYSTEM <span>AWAKENING</span></h1>
          <p>Real action. Real proof. Deterministic growth.</p>
          <div className="auth-tabs" role="tablist" aria-label="Authentication method">
            {demoEnabled && <button type="button" role="tab" aria-selected={authMode === "demo"} onClick={() => setAuthMode("demo")}>Demo</button>}
            <button type="button" role="tab" aria-selected={authMode === "account"} onClick={() => setAuthMode("account")}>Account</button>
            <button type="button" role="tab" aria-selected={authMode === "register"} onClick={() => setAuthMode("register")}>Register</button>
          </div>
          <form onSubmit={login}>
            {authMode === "demo" ? <>
              <label htmlFor="handle">Demo hunter name</label>
              <input id="handle" value={handle} minLength={3} maxLength={40} pattern="[A-Za-z0-9_\-]+" onChange={(event) => setHandle(event.target.value)} />
            </> : <>
              <label htmlFor="email">Email</label>
              <input id="email" type="email" required value={email} onChange={(event) => setEmail(event.target.value)} />
              <label htmlFor="password">Password</label>
              <input id="password" type="password" required minLength={12} value={password} onChange={(event) => setPassword(event.target.value)} />
            </>}
            <button disabled={busy}>{busy ? "AWAKENING…" : authMode === "demo" ? "ENTER THE SYSTEM" : authMode === "register" ? "CREATE ACCOUNT" : "SIGN IN"}</button>
          </form>
          <p className="notice" aria-live="polite">{scanning || notice}</p>
        </section>
      </main>
    );
  }

  const experience = xpProgress(player.current_xp);

  return (
    <main className="app-shell">
      <header className="topbar">
        <div><p className="eyebrow">THE SYSTEM // ONLINE</p><h1>{player.display_name}</h1></div>
        <div className="topbar-controls">
          <SystemCore level={player.level} />
          <button
            type="button"
            className="mute-toggle"
            aria-pressed={muted}
            aria-label={muted ? "เปิดเสียง" : "ปิดเสียง"}
            onClick={() => { sfxSetMuted(!muted); setMuted(!muted); if (muted) sfx.tap(); }}
          >{muted ? "🔇" : "🔊"}</button>
          <div className="level-orb" aria-label={`Level ${player.level}`}><small>LEVEL</small>{player.level}</div>
        </div>
      </header>
      <div className="ach-stack" aria-live="polite">
        {toasts.map((item) => (
          <div className="ach-toast" key={item.code}>
            <Rune seed={runeSeed(item.code)} />
            <div><b>ACHIEVEMENT — {item.name}</b><small>{item.description}</small></div>
          </div>
        ))}
      </div>
      <p className="notice" aria-live="polite">{scanning || notice}</p>

      <section className="grid">
        <article className="system-card profile-panel">
          <h2>HUNTER STATUS</h2>
          <div className="xp"><span>EXP</span><strong>{player.current_xp}</strong></div>
          <div className="xp-progress">
            <label htmlFor="xp-progress">Level {experience.level} progress</label>
            <span>{experience.earned} / {experience.required} XP</span>
            <progress id="xp-progress" max={experience.required} value={experience.earned}>
              {experience.percent}%
            </progress>
          </div>
          <div className="stats">
            {stats.map(([key, label]) => <div key={key}><span>{label}</span><strong>{player.stats[key]}</strong></div>)}
          </div>
          <h3>INVENTORY · {inventory.length}</h3>
          <ul className="inventory">
            {inventory.length ? inventory.map((item) => <li key={item.id} data-rarity={item.rarity.toLowerCase()}><b>{item.name}</b><span><small className="rarity-tag">{item.rarity}</small> · PWR {item.power}</span></li>) : <li className="empty">No awakened items yet.</li>}
          </ul>
        </article>

        <article className="system-card quest-panel">
          <h2>QUEST BOARD</h2>
          <div className="quest-list" role="list">
            {quests.map((quest) => (
              <button className={selected?.definition_id === quest.definition_id ? "quest active" : "quest"} key={quest.definition_id} onClick={() => chooseQuest(quest)} disabled={busy || Boolean(accepted && !verification)}>
                <span>{quest.category}</span><b>{quest.title}</b>
                <span className="chip" data-difficulty={quest.difficulty}>{quest.difficulty} · {quest.primary_stat}</span>
              </button>
            ))}
          </div>
          {selected && <div className="quest-detail">
            <p className="eyebrow">REAL OBJECTIVE</p>
            <h3>{selected.title}</h3>
            {selected.objective.type === "completion"
              ? <p>{selected.objective.target}</p>
              : <p>Complete <strong>{selected.objective.target} {selected.objective.type.replaceAll("_", " ")}</strong>.</p>}
            {!accepted && <button onClick={acceptQuest} disabled={busy}>ACCEPT QUEST</button>}
            {accepted && !submission && <div className="proof-form">
              {selected.objective.type === "completion" ? (
                <label htmlFor="completion">
                  <input id="completion" type="checkbox" checked={completed} onChange={(event) => setCompleted(event.target.checked)} />
                  I completed the stated objective (demo self-report)
                </label>
              ) : (
                <>
                  <label htmlFor="duration">Observed value</label>
                  <input id="duration" type="number" min={0} value={duration} onChange={(event) => setDuration(Number(event.target.value))} />
                </>
              )}
              <label htmlFor="evidence-image">Image evidence (optional)</label>
              <input id="evidence-image" type="file" accept="image/png,image/jpeg,image/webp" onChange={(event) => setEvidenceFile(event.target.files?.[0] ?? null)} />
              <button onClick={submitProof} disabled={busy || (selected.objective.type === "completion" && !completed)}>SUBMIT PROOF</button>
            </div>}
            {submission && !verification && <button onClick={verify} disabled={busy}>{demoEnabled ? "VERIFY EVIDENCE" : "CHECK VERIFICATION"}</button>}
            {verification && <div className={`decision ${verification.verification.decision.toLowerCase()}${(verification as VerificationDetail).flashPass ? " flash" : ""}`}>
              <b>{verification.verification.decision}</b>
              {verification.reward && <p>+{verification.reward.exp_granted} EXP · {JSON.stringify(verification.reward.stat_changes)}</p>}
            </div>}
            {verification?.verification.decision === "NEED_MORE_EVIDENCE" && (
              <button onClick={() => { setSubmission(null); setVerification(null); }} disabled={busy}>
                ATTACH IMAGE &amp; RESUBMIT
              </button>
            )}
            {verification?.reward && !chest && <button className="reward-button" onClick={openChest} disabled={busy}>OPEN PERSISTED CHEST</button>}
            {chest && <div className="chest-result" data-rarity={chest.rarity.toLowerCase()}><span>{chest.rarity}</span><strong>{chest.item.name}</strong><small>Saved to authoritative inventory</small></div>}
          </div>}
        </article>
      </section>
    </main>
  );
}
