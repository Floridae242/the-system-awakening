"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { api } from "../lib/api";

type Stats = { str: number; agi: number; vit: number; int: number; wil: number };
type Player = { id: string; display_name: string; level: number; current_xp: number; stats: Stats };
type Quest = {
  definition_id: string;
  title: string;
  category: string;
  difficulty: string;
  primary_stat: string;
  objective: { type: string; target: number };
};
type Accepted = { id: string; definition_id: string; status: string };
type Submission = { id: string; status: string };
type Reward = { id: string; exp_granted: number; stat_changes: Record<string, number>; chest_id: string };
type VerificationDetail = {
  verification: { decision: "PASS" | "NEED_MORE_EVIDENCE" | "REVIEW" | "FAIL"; reason_code: string };
  reward: Reward | null;
};
type InventoryItem = { id: string; name: string; rarity: string; power: number };
type ChestResult = { chest_id: string; rarity: string; item: InventoryItem };

const stats: Array<[keyof Stats, string]> = [
  ["str", "STR"], ["agi", "AGI"], ["vit", "VIT"], ["int", "INT"], ["wil", "WIL"],
];

export function AwakeningApp() {
  const [token, setToken] = useState("");
  const [handle, setHandle] = useState("hunter");
  const [player, setPlayer] = useState<Player | null>(null);
  const [quests, setQuests] = useState<Quest[]>([]);
  const [selected, setSelected] = useState<Quest | null>(null);
  const [accepted, setAccepted] = useState<Accepted | null>(null);
  const [submission, setSubmission] = useState<Submission | null>(null);
  const [verification, setVerification] = useState<VerificationDetail | null>(null);
  const [inventory, setInventory] = useState<InventoryItem[]>([]);
  const [chest, setChest] = useState<ChestResult | null>(null);
  const [duration, setDuration] = useState(30);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("Enter the System to begin.");

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
    const saved = window.sessionStorage.getItem("awakening-token");
    if (!saved) return;
    setToken(saved);
    loadWorld(saved).catch(() => window.sessionStorage.removeItem("awakening-token"));
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
      const result = await api<{ access_token: string }>("/auth/demo", {
        method: "POST",
        body: JSON.stringify({ handle }),
      });
      window.sessionStorage.setItem("awakening-token", result.access_token);
      setToken(result.access_token);
      await loadWorld(result.access_token);
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
      setNotice("QUEST ACCEPTED — complete the real objective, then submit proof.");
    });
  }

  function submitProof() {
    if (!accepted || !selected) return;
    void act(async () => {
      const manual_evidence = { [selected.objective.type]: duration };
      const result = await api<Submission>(`/quests/${accepted.id}/submissions`, {
        method: "POST",
        token,
        idempotencyKey: crypto.randomUUID(),
        body: JSON.stringify({ evidence_type: "manual", manual_evidence }),
      });
      setSubmission(result);
      setNotice("PROOF RECEIVED — ready for deterministic demo verification.");
    });
  }

  function verify() {
    if (!submission) return;
    void act(async () => {
      const result = await api<VerificationDetail>(`/submissions/${submission.id}/verify`, { method: "POST", token });
      setVerification(result);
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
          <form onSubmit={login}>
            <label htmlFor="handle">Demo hunter name</label>
            <input id="handle" value={handle} minLength={3} maxLength={40} pattern="[A-Za-z0-9_\-]+" onChange={(event) => setHandle(event.target.value)} />
            <button disabled={busy}>{busy ? "AWAKENING…" : "ENTER THE SYSTEM"}</button>
          </form>
          <p className="notice" aria-live="polite">{notice}</p>
        </section>
      </main>
    );
  }

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
              <button className={selected?.definition_id === quest.definition_id ? "quest active" : "quest"} key={quest.definition_id} onClick={() => setSelected(quest)} disabled={busy}>
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
              <label htmlFor="duration">Observed value</label>
              <input id="duration" type="number" min={0} value={duration} onChange={(event) => setDuration(Number(event.target.value))} />
              <button onClick={submitProof} disabled={busy}>SUBMIT PROOF</button>
            </div>}
            {submission && !verification && <button onClick={verify} disabled={busy}>VERIFY EVIDENCE</button>}
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
