"""Completeness pass: history, daily board, rename, change-password, logout-all."""

import time

from fastapi.testclient import TestClient

from main import app

EMAIL_TPL = "full-{tag}-{now}@test.local"


def _register(client: TestClient, tag: str) -> tuple[dict, str]:
    now = int(time.time() * 1000)
    email = EMAIL_TPL.format(tag=tag, now=now)
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "correct-horse-battery-staple"},
    )
    assert response.status_code == 201
    return {"x-csrf-token": response.json()["data"]["csrf_token"]}, email


def _complete(client: TestClient, headers: dict, quest_id: str, key: str, evidence: dict) -> None:
    accepted = client.post(
        f"/api/v1/quests/{quest_id}/accept",
        headers={**headers, "Idempotency-Key": f"{key}-accept"},
    ).json()["data"]
    submitted = client.post(
        f"/api/v1/quests/{accepted['id']}/submissions",
        headers={**headers, "Idempotency-Key": f"{key}-submit"},
        json={"evidence_type": "manual", "manual_evidence": evidence},
    ).json()["data"]
    verified = client.post(f"/api/v1/submissions/{submitted['id']}/verify", headers=headers).json()["data"]
    assert verified["verification"]["decision"] == "PASS", verified["verification"]
    client.post(
        f"/api/v1/chests/{verified['reward']['chest_id']}/open",
        headers={**headers, "Idempotency-Key": f"{key}-chest"},
    )


def test_player_history_lists_completed_quests():
    with TestClient(app) as client:
        headers, _ = _register(client, "history")
        _complete(client, headers, "quest_focus_001", "hist-1", {"duration_minutes": 30})
        _complete(client, headers, "quest_journal_001", "hist-2", {"completion": True})

        history = client.get("/api/v1/player/history", headers=headers).json()["data"]
        assert history["total"] == 2
        titles = [entry["title"] for entry in history["history"]]
        assert "Trial of Focus" in titles
        assert "Echoes of the Mind" in titles
        newest = history["history"][0]
        assert newest["exp_granted"] > 0
        assert newest["completed_at"] is not None


def test_daily_board_is_deterministic_and_covers_all_quests():
    with TestClient(app) as client:
        headers, _ = _register(client, "daily")
        first = client.get("/api/v1/quests/daily", headers=headers).json()["data"]
        second = client.get("/api/v1/quests/daily", headers=headers).json()["data"]
        assert first == second, "same UTC date must produce the same rotation"
        assert first["main"] and first["side"]
        covered = {first["main"], first["side"], *first["optional"]}
        all_ids = {
            entry["definition_id"]
            for entry in client.get("/api/v1/quests", headers=headers).json()["data"]
        }
        assert covered == all_ids


def test_player_rename_validates_and_persists():
    with TestClient(app) as client:
        headers, _ = _register(client, "rename")

        invalid = client.patch(
            "/api/v1/player",
            headers=headers,
            json={"display_name": "bad name!"},
        )
        assert invalid.status_code == 422

        ok = client.patch(
            "/api/v1/player",
            headers=headers,
            json={"display_name": "Shadow Archivist"},
        )
        assert ok.status_code == 200, ok.text
        me = client.get("/api/v1/auth/me").json()["data"]["player"]
        assert me["display_name"] == "Shadow Archivist"


def test_change_password_rotates_credential_and_revokes_other_devices():
    with TestClient(app) as client:
        headers, email = _register(client, "passwd")

        wrong = client.post(
            "/api/v1/auth/change-password",
            headers=headers,
            json={"current_password": "wrong-password-1", "new_password": "another-long-password-9"},
        )
        assert wrong.status_code == 403

        changed = client.post(
            "/api/v1/auth/change-password",
            headers=headers,
            json={"current_password": "correct-horse-battery-staple", "new_password": "another-long-password-9"},
        )
        assert changed.status_code == 200
        assert client.get("/api/v1/auth/me").status_code == 200, "current device stays signed in"

        other = TestClient(app)
        old_login = other.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "correct-horse-battery-staple"},
        )
        assert old_login.status_code in {401, 403}, "old password must stop working"

        new_login = other.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "another-long-password-9"},
        )
        assert new_login.status_code == 200
        assert other.get("/api/v1/auth/me").status_code == 200, "other device had a fresh session"

        revoked = client.post("/api/v1/auth/logout-all", headers=headers)
        assert revoked.status_code == 200
        assert other.get("/api/v1/auth/me").status_code == 401, "logout-all revokes every device"


def test_logout_all_kills_sessions():
    with TestClient(app) as client:
        headers, _ = _register(client, "logout")
        assert client.get("/api/v1/auth/me").status_code == 200

        killed = client.post("/api/v1/auth/logout-all", headers=headers)
        assert killed.status_code == 200
        assert client.get("/api/v1/auth/me").status_code == 401
