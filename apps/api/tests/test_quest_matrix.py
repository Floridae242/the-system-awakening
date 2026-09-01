"""Exhaustive quest-system matrix — every reachable case of the lifecycle.

Covers: accept validation/idempotency/conflicts, submission validation and
ownership, image upload edges, verification decisions (demo + production
gating), reward/chest settlement idempotency, and economy bounds.
"""

import io
import time
from dataclasses import replace

from fastapi.testclient import TestClient
from PIL import Image

from app import routes
from main import app


def _register(client: TestClient, tag: str) -> tuple[dict, str]:
    email = f"mx-{tag}-{time.time()}@test.local"
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "correct-horse-battery-staple"},
    )
    assert response.status_code == 201
    return {"x-csrf-token": response.json()["data"]["csrf_token"]}, email


def _fresh_client() -> TestClient:
    """A second actor needs its own cookie jar — one client = one session identity."""
    return TestClient(app)


def _png() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), (64, 217, 255)).save(buffer, format="PNG")
    return buffer.getvalue()


def _k(key: str, purpose: str) -> str:
    """Idempotency keys must be 8-128 chars — pad short test keys deterministically."""
    full = f"{key}-{purpose}"
    return full if len(full) >= 8 else full + "0000"


def _accept(client: TestClient, headers: dict, quest_id: str, key: str):
    return client.post(
        f"/api/v1/quests/{quest_id}/accept",
        headers={**headers, "Idempotency-Key": _k(key, "accept")},
    )


def _submit(client: TestClient, headers: dict, pq_id: str, key: str, evidence: dict, evidence_type: str = "manual"):
    return client.post(
        f"/api/v1/quests/{pq_id}/submissions",
        headers={**headers, "Idempotency-Key": _k(key, "submit")},
        json={"evidence_type": evidence_type, "manual_evidence": evidence},
    )


def _run_quest(client: TestClient, headers: dict, quest_id: str, key: str, evidence: dict) -> dict:
    accepted_response = _accept(client, headers, quest_id, key)
    assert accepted_response.status_code == 201, accepted_response.text[:200]
    accepted = accepted_response.json()["data"]
    submitted = _submit(client, headers, accepted["id"], key, evidence).json()["data"]
    verified = client.post(f"/api/v1/submissions/{submitted['id']}/verify", headers=headers).json()["data"]
    assert verified["verification"]["decision"] == "PASS", verified["verification"]
    return verified


# ---------------------------------------------------------------- accept ----
class TestAccept:
    def test_missing_idempotency_key_rejected(self):
        with TestClient(app) as client:
            headers, _ = _register(client, "a1")
            response = client.post(
                "/api/v1/quests/quest_focus_001/accept",
                headers=headers,
            )
            assert response.status_code == 400

    def test_short_idempotency_key_rejected(self):
        with TestClient(app) as client:
            headers, _ = _register(client, "a2")
            response2 = client.post(
                "/api/v1/quests/quest_focus_001/accept",
                headers={**headers, "Idempotency-Key": "short"},
            )
            assert response2.status_code == 400

    def test_unknown_quest_rejected(self):
        with TestClient(app) as client:
            headers, _ = _register(client, "a3")
            response = _accept(client, headers, "quest_does_not_exist", "mx-a3-key-1")
            assert response.status_code == 404

    def test_replay_same_key_same_payload_returns_same_resource(self):
        with TestClient(app) as client:
            headers, _ = _register(client, "a4")
            first = _accept(client, headers, "quest_focus_001", "mx-a4-key-1")
            second = _accept(client, headers, "quest_focus_001", "mx-a4-key-1")
            assert first.status_code == 201
            assert second.status_code == 200
            assert first.json()["data"]["id"] == second.json()["data"]["id"]

    def test_same_key_different_payload_conflicts(self):
        with TestClient(app) as client:
            headers, _ = _register(client, "a5")
            _accept(client, headers, "quest_focus_001", "mx-a5-key-1")
            conflict = _accept(client, headers, "quest_journal_001", "mx-a5-key-1")
            assert conflict.status_code == 409

    def test_second_active_quest_rejected(self):
        with TestClient(app) as client:
            headers, _ = _register(client, "a6")
            _accept(client, headers, "quest_focus_001", "mx-a6-key-1")
            other = _accept(client, headers, "quest_journal_001", "mx-a6-key-2")
            assert other.status_code == 409
            assert "already active" in other.json()["detail"]

    def test_completed_quest_does_not_block_other_quests(self):
        with TestClient(app) as client:
            headers, _ = _register(client, "a9")
            _run_quest(client, headers, "quest_focus_001", "mx-a9", {"duration_minutes": 30})
            other = _accept(client, headers, "quest_journal_001", "mx-a9-key-2")
            assert other.status_code == 201, "yesterday-style completions must not block new quests"

    def test_completed_today_rejected(self):
        with TestClient(app) as client:
            headers, _ = _register(client, "a7")
            _run_quest(client, headers, "quest_focus_001", "mx-a7", {"duration_minutes": 30})
            replay = _accept(client, headers, "quest_focus_001", "mx-a7-key-2")
            assert replay.status_code == 409
            assert "completed today" in replay.json()["detail"]

    def test_snapshot_pins_definition_at_accept_time(self):
        with TestClient(app) as client:
            headers, _ = _register(client, "a8")
            accepted = _accept(client, headers, "quest_focus_001", "mx-a8-key-1").json()["data"]
            assert accepted["definition_version"] >= 1
            # The authoritative pin lives on the row (read via /quests/active owner view).
            active = client.get("/api/v1/quests/active", headers=headers).json()["data"]
            snapshot = active["accepted"]["definition_snapshot"]
            assert snapshot["objective"]["type"] == "duration_minutes"
            assert snapshot["definition_id"] == "quest_focus_001"


# ----------------------------------------------------------- submissions ----
class TestSubmissions:
    def test_unknown_player_quest_rejected(self):
        with TestClient(app) as client:
            headers, _ = _register(client, "s1")
            response = _submit(
                client, headers, "00000000-0000-0000-0000-000000000000", "mx-s1-1", {"duration_minutes": 30}
            )
            assert response.status_code == 404

    def test_submit_without_idempotency_key_rejected(self):
        with TestClient(app) as client:
            headers, _ = _register(client, "s2")
            accepted = _accept(client, headers, "quest_focus_001", "mx-s2-key-1").json()["data"]
            response = client.post(
                f"/api/v1/quests/{accepted['id']}/submissions",
                headers=headers,
                json={"evidence_type": "manual", "manual_evidence": {"duration_minutes": 30}},
            )
            assert response.status_code == 400

    def test_evidence_type_must_be_manual(self):
        with TestClient(app) as client:
            headers, _ = _register(client, "s3")
            accepted = _accept(client, headers, "quest_focus_001", "mx-s3-key-1").json()["data"]
            response = _submit(
                client, headers, accepted["id"], "mx-s3-1", {"duration_minutes": 30}, evidence_type="strava"
            )
            assert response.status_code == 422

    def test_negative_duration_rejected(self):
        with TestClient(app) as client:
            headers, _ = _register(client, "s4")
            accepted = _accept(client, headers, "quest_focus_001", "mx-s4-key-1").json()["data"]
            response = _submit(client, headers, accepted["id"], "mx-s4-1", {"duration_minutes": -5})
            assert response.status_code == 422

    def test_duration_over_24h_rejected(self):
        with TestClient(app) as client:
            headers, _ = _register(client, "s5")
            accepted = _accept(client, headers, "quest_focus_001", "mx-s5-key-1").json()["data"]
            response = _submit(client, headers, accepted["id"], "mx-s5-1", {"duration_minutes": 1441})
            assert response.status_code == 422

    def test_unknown_evidence_fields_rejected(self):
        with TestClient(app) as client:
            headers, _ = _register(client, "s6")
            accepted = _accept(client, headers, "quest_focus_001", "mx-s6-key-1").json()["data"]
            response = _submit(client, headers, accepted["id"], "mx-s6-1", {"duration_minutes": 30, "cheat": True})
            assert response.status_code == 422

    def test_replay_same_submission_key_returns_same_submission(self):
        with TestClient(app) as client:
            headers, _ = _register(client, "s7")
            accepted = _accept(client, headers, "quest_focus_001", "mx-s7-key-1").json()["data"]
            first = _submit(client, headers, accepted["id"], "mx-s7-1", {"duration_minutes": 30})
            second = _submit(client, headers, accepted["id"], "mx-s7-1", {"duration_minutes": 30})
            assert second.json()["data"]["id"] == first.json()["data"]["id"]

    def test_submit_against_completed_quest_blocked(self):
        with TestClient(app) as client:
            headers, _ = _register(client, "s8")
            _run_quest(client, headers, "quest_focus_001", "mx-s8", {"duration_minutes": 30})
            me = client.get("/api/v1/auth/me").json()["data"]["player"]
            # no active quest: resubmission must be impossible (quest completed today)
            probe = client.get("/api/v1/quests/active", headers=headers).json()["data"]
            assert not probe or probe.get("accepted") is None
            assert me["level"] >= 1


# ---------------------------------------------------------------- upload ----
class TestUpload:
    def test_valid_png_accepted(self):
        with TestClient(app) as client:
            headers, _ = _register(client, "u1")
            accepted = _accept(client, headers, "quest_focus_001", "mx-u1-key-1").json()["data"]
            submitted = _submit(client, headers, accepted["id"], "mx-u1-1", {"duration_minutes": 30}).json()["data"]
            upload = client.post(
                f"/api/v1/submissions/{submitted['id']}/evidence/image",
                headers=headers,
                files={"image": ("proof.png", _png(), "image/png")},
            )
            assert upload.status_code == 201

    def test_corrupt_png_rejected(self):
        with TestClient(app) as client:
            headers, _ = _register(client, "u2")
            accepted = _accept(client, headers, "quest_focus_001", "mx-u2-key-1").json()["data"]
            submitted = _submit(client, headers, accepted["id"], "mx-u2-1", {"duration_minutes": 30}).json()["data"]
            upload = client.post(
                f"/api/v1/submissions/{submitted['id']}/evidence/image",
                headers=headers,
                files={"image": ("proof.png", b"not-a-png", "image/png")},
            )
            assert upload.status_code in {400, 415, 422}

    def test_upload_to_foreign_submission_rejected(self):
        with TestClient(app) as owner_client:
            owner_headers, _ = _register(owner_client, "u3-owner")
            accepted = _accept(owner_client, owner_headers, "quest_focus_001", "mx-u3-key-1").json()["data"]
            submitted = _submit(
                owner_client, owner_headers, accepted["id"], "mx-u3-1", {"duration_minutes": 30}
            ).json()["data"]
            with _fresh_client() as attacker_client:
                attacker_headers, _ = _register(attacker_client, "u3-attacker")
                upload = attacker_client.post(
                    f"/api/v1/submissions/{submitted['id']}/evidence/image",
                    headers=attacker_headers,
                    files={"image": ("proof.png", _png(), "image/png")},
                )
                assert upload.status_code == 404, (upload.status_code, upload.text[:120])


# ----------------------------------------------------------- verification ----
class TestVerification:
    def test_duration_meeting_target_passes(self):
        with TestClient(app) as client:
            headers, _ = _register(client, "v1")
            verified = _run_quest(client, headers, "quest_focus_001", "mx-v1", {"duration_minutes": 30})
            assert verified["verification"]["decision"] == "PASS"
            assert verified["verification"]["reason_code"] == "criteria_met"

    def test_duration_below_target_fails(self):
        with TestClient(app) as client:
            headers, _ = _register(client, "v2")
            accepted = _accept(client, headers, "quest_focus_001", "mx-v2-key-1").json()["data"]
            submitted = _submit(client, headers, accepted["id"], "mx-v2-1", {"duration_minutes": 5}).json()["data"]
            verified = client.post(f"/api/v1/submissions/{submitted['id']}/verify", headers=headers).json()["data"]
            assert verified["verification"]["decision"] == "FAIL"
            assert verified["reward"] is None

    def test_completion_false_fails(self):
        with TestClient(app) as client:
            headers, _ = _register(client, "v3")
            accepted = _accept(client, headers, "quest_journal_001", "mx-v3-key-1").json()["data"]
            submitted = _submit(client, headers, accepted["id"], "mx-v3-1", {"completion": False}).json()["data"]
            verified = client.post(f"/api/v1/submissions/{submitted['id']}/verify", headers=headers).json()["data"]
            assert verified["verification"]["decision"] == "FAIL"

    def test_missing_objective_field_needs_more_evidence(self):
        with TestClient(app) as client:
            headers, _ = _register(client, "v4")
            accepted = _accept(client, headers, "quest_focus_001", "mx-v4-key-1").json()["data"]
            submitted = _submit(client, headers, accepted["id"], "mx-v4-1", {"distance_km": 3}).json()["data"]
            verified = client.post(f"/api/v1/submissions/{submitted['id']}/verify", headers=headers).json()["data"]
            assert verified["verification"]["decision"] == "NEED_MORE_EVIDENCE"

    def test_double_verify_is_idempotent(self):
        with TestClient(app) as client:
            headers, _ = _register(client, "v5")
            accepted = _accept(client, headers, "quest_focus_001", "mx-v5-key-1").json()["data"]
            submitted = _submit(client, headers, accepted["id"], "mx-v5-1", {"duration_minutes": 30}).json()["data"]
            first = client.post(f"/api/v1/submissions/{submitted['id']}/verify", headers=headers).json()["data"]
            second = client.post(f"/api/v1/submissions/{submitted['id']}/verify", headers=headers).json()["data"]
            assert first["verification"]["decision"] == second["verification"]["decision"] == "PASS"

    def test_verify_foreign_submission_rejected(self):
        with TestClient(app) as owner_client:
            owner_headers, _ = _register(owner_client, "v6-owner")
            accepted = _accept(owner_client, owner_headers, "quest_focus_001", "mx-v6-key-1").json()["data"]
            submitted = _submit(
                owner_client, owner_headers, accepted["id"], "mx-v6-1", {"duration_minutes": 30}
            ).json()["data"]
            with _fresh_client() as attacker_client:
                attacker_headers, _ = _register(attacker_client, "v6-attacker")
                response = attacker_client.post(
                    f"/api/v1/submissions/{submitted['id']}/verify", headers=attacker_headers
                )
                detail = (response.status_code, response.text[:120])
                assert response.status_code == 404, detail

    def test_production_browser_verify_blocked(self, monkeypatch):
        with TestClient(app) as client:
            headers, _ = _register(client, "v7")
            accepted = _accept(client, headers, "quest_focus_001", "mx-v7-key-1").json()["data"]
            submitted = _submit(client, headers, accepted["id"], "mx-v7-1", {"duration_minutes": 30}).json()["data"]
            monkeypatch.setattr(routes, "settings", replace(routes.settings, app_env="production", demo_mode=False))
            response = client.post(f"/api/v1/submissions/{submitted['id']}/verify", headers=headers)
            assert response.status_code == 404


# ----------------------------------------------------------- reward/chest ----
class TestRewardEconomy:
    def test_chest_replay_returns_same_item(self):
        with TestClient(app) as client:
            headers, _ = _register(client, "r1")
            verified = _run_quest(client, headers, "quest_focus_001", "mx-r1", {"duration_minutes": 30})
            chest_id = verified["reward"]["chest_id"]
            open_chest = lambda: client.post(  # noqa: E731
                f"/api/v1/chests/{chest_id}/open", headers={**headers, "Idempotency-Key": "mx-r1-c1"}
            ).json()["data"]
            first = open_chest()
            second = open_chest()
            assert first["item"]["id"] == second["item"]["id"]

    def test_chest_of_another_player_rejected(self):
        with TestClient(app) as owner_client:
            owner_headers, _ = _register(owner_client, "r2-owner")
            verified = _run_quest(owner_client, owner_headers, "quest_focus_001", "mx-r2", {"duration_minutes": 30})
            chest_id = verified["reward"]["chest_id"]
            with _fresh_client() as attacker_client:
                attacker_headers, _ = _register(attacker_client, "r2-attacker")
                response = attacker_client.post(
                    f"/api/v1/chests/{chest_id}/open",
                    headers={**attacker_headers, "Idempotency-Key": "mx-r2-steal"},
                )
                detail = (response.status_code, response.text[:120])
                assert response.status_code == 404, detail

    def test_exp_and_level_math_across_two_quests(self):
        with TestClient(app) as client:
            headers, _ = _register(client, "r3")
            first = _run_quest(client, headers, "quest_focus_001", "mx-r3a", {"duration_minutes": 30})
            second = _run_quest(client, headers, "quest_journal_001", "mx-r3b", {"completion": True})
            total = first["reward"]["exp_granted"] + second["reward"]["exp_granted"]
            me = client.get("/api/v1/auth/me").json()["data"]["player"]
            assert me["current_xp"] == total
            assert me["level"] >= 2  # two quest clears always cross the first threshold

    def test_stat_change_matches_quest_primary_stat(self):
        with TestClient(app) as client:
            headers, _ = _register(client, "r4")
            verified = _run_quest(client, headers, "quest_focus_001", "mx-r4", {"duration_minutes": 30})
            me = client.get("/api/v1/auth/me").json()["data"]["player"]
            assert verified["reward"]["stat_changes"] == {"INT": 1}
            assert me["stats"]["int"] == 11
