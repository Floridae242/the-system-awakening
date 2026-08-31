"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { xpProgress } from "@tsa/game-engine";
import { api } from "../lib/api";

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
type VerificationDetail = {
  verification: { decision: "PASS" | "NEED_MORE_EVIDENCE" | "REVIEW" | "FAIL"; reason_code: string };
  reward: Reward | null;
};
type SubmissionDetail = Submission & {
  verification: VerificationDetail["verification"] | null;
  reward: Reward | null;
};
type InventoryItem = { id: string; name: string; rarity: string; power: number };
type ChestResult = { chest_id: string; rarity: string; item: InventoryItem };

// Next inlines this public flag at build time. CI enables the deterministic
// demo flow for E2E; production explicitly disables it.
const demoEnabled = process.env.NEXT_PUBLIC_DEMO_MODE === "true";

const stats: Array<[keyof Stats, string]> = [
  ["str", "STR"], ["agi", "AGI"], ["vit", "VIT"], ["int", "INT"], ["wil", "WIL"],
];

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
    const [nextPlayer, nextQuests, nextInventory] = await Promise.all([
      api<Player>("/player", { token: accessToken }),
      api<Quest[]>("/quests", { token: accessToken }),
      api<InventoryItem[]>("/inventory", { token: accessToken }),
    ]);
    setPlayer(nextPlayer);
    setQuests(nextQuests);
    setInventory(nextInventory);
    setSelected((current) => current ?? nextQuests[0] ?? null);
  }, []);

  useEffect(() => {
    // Authentication is maintained by the HttpOnly BFF cookie. JavaScript
    // deliberately never persists or reads an access token.
    loadWorld("").catch(() => undefined);
  }, [loadWorld]);

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
      setSubmission(finalized);
      setNotice(evidenceFile ? "PROOF + IMAGE RECEIVED — verification queued." : "PROOF RECEIVED — verification queued.");
    });
  }

  function verify() {
    if (!submission) return;
    void act(async () => {
      let result: VerificationDetail | SubmissionDetail = demoEnabled
        ? await api<VerificationDetail>(`/submissions/${submission.id}/verify`, { method: "POST", token })
        : await api<SubmissionDetail>(`/submissions/${submission.id}`, { token });
      for (let attempt = 0; !demoEnabled && !result.verification && attempt < 5; attempt += 1) {
        await new Promise((resolve) => setTimeout(resolve, 500));
        result = await api<SubmissionDetail>(`/submissions/${submission.id}`, { token });
      }
      if (!result.verification) {
        setNotice("VERIFICATION IN PROGRESS — check again shortly.");
        return;
      }
      setVerification({ verification: result.verification, reward: result.reward });
      await loadWorld(token);
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
      setChest(result);
      await loadWorld(token);
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
          <p className="notice" aria-live="polite">{notice}</p>
        </section>
      </main>
    );
  }

  const experience = xpProgress(player.current_xp);

  return (
    <main className="app-shell">
      <header className="topbar">
        <div><p className="eyebrow">THE SYSTEM // ONLINE</p><h1>{player.display_name}</h1></div>
        <div className="level-orb" aria-label={`Level ${player.level}`}><small>LEVEL</small>{player.level}</div>
      </header>
      <p className="notice" aria-live="polite">{notice}</p>

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
            {inventory.length ? inventory.map((item) => <li key={item.id}><b>{item.name}</b><span>{item.rarity} · PWR {item.power}</span></li>) : <li className="empty">No awakened items yet.</li>}
          </ul>
        </article>

        <article className="system-card quest-panel">
          <h2>QUEST BOARD</h2>
          <div className="quest-list" role="list">
            {quests.map((quest) => (
              <button className={selected?.definition_id === quest.definition_id ? "quest active" : "quest"} key={quest.definition_id} onClick={() => chooseQuest(quest)} disabled={busy || Boolean(accepted && !verification)}>
                <span>{quest.difficulty} · {quest.primary_stat}</span><b>{quest.title}</b>
              </button>
            ))}
          </div>
          {selected && <div className="quest-detail">
            <p className="eyebrow">REAL OBJECTIVE</p>
            <h3>{selected.title}</h3>
            <p>Complete <strong>{selected.objective.target} {selected.objective.type.replaceAll("_", " ")}</strong>.</p>
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
            {verification && <div className={`decision ${verification.verification.decision.toLowerCase()}`}>
              <b>{verification.verification.decision}</b>
              {verification.reward && <p>+{verification.reward.exp_granted} EXP · {JSON.stringify(verification.reward.stat_changes)}</p>}
            </div>}
            {verification?.reward && !chest && <button className="reward-button" onClick={openChest} disabled={busy}>OPEN PERSISTED CHEST</button>}
            {chest && <div className="chest-result"><span>{chest.rarity}</span><strong>{chest.item.name}</strong><small>Saved to authoritative inventory</small></div>}
          </div>}
        </article>
      </section>
    </main>
  );
}
