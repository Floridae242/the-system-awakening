"""Server-authoritative achievement reveals settle exactly once."""

import time

from fastapi.testclient import TestClient

from main import app


def _headers(client: TestClient, tag: str) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": f"ach-{tag}-{time.time()}@test.local", "password": "correct-horse-battery-staple"},
    )
    assert response.status_code == 201
    return {"x-csrf-token": response.json()["data"]["csrf_token"]}


def test_first_completion_reveals_achievements_exactly_once():
    with TestClient(app) as client:
        headers = _headers(client, "first")
        accepted = client.post(
            "/api/v1/quests/quest_focus_001/accept",
            headers={**headers, "Idempotency-Key": "ach-accept-1"},
        ).json()["data"]
        submitted = client.post(
            f"/api/v1/quests/{accepted['id']}/submissions",
            headers={**headers, "Idempotency-Key": "ach-submit-1"},
            json={"evidence_type": "manual", "manual_evidence": {"duration_minutes": 30}},
        ).json()["data"]
        verified = client.post(f"/api/v1/submissions/{submitted['id']}/verify", headers=headers).json()["data"]

        codes = [item["code"] for item in verified["achievements_unlocked"]]
        assert "first_quest" in codes
        assert "level_2" in codes
        first = next(item for item in verified["achievements_unlocked"] if item["code"] == "first_quest")
        assert first["name"] and first["description"]

        chest = client.post(
            f"/api/v1/chests/{verified['reward']['chest_id']}/open",
            headers={**headers, "Idempotency-Key": "ach-chest-1"},
        ).json()["data"]
        replay_codes = [item["code"] for item in chest["achievements_unlocked"]]
        assert "first_quest" not in replay_codes
        assert "level_2" not in replay_codes


def test_second_completion_does_not_repeat_earlier_reveals():
    with TestClient(app) as client:
        headers = _headers(client, "second")
        first = client.post(
            "/api/v1/quests/quest_focus_001/accept",
            headers={**headers, "Idempotency-Key": "ach2-accept-1"},
        ).json()["data"]
        first_sub = client.post(
            f"/api/v1/quests/{first['id']}/submissions",
            headers={**headers, "Idempotency-Key": "ach2-submit-1"},
            json={"evidence_type": "manual", "manual_evidence": {"duration_minutes": 30}},
        ).json()["data"]
        client.post(f"/api/v1/submissions/{first_sub['id']}/verify", headers=headers)
        first_detail = client.get(f"/api/v1/submissions/{first_sub['id']}", headers=headers).json()["data"]
        client.post(
            f"/api/v1/chests/{first_detail['reward']['chest_id']}/open",
            headers={**headers, "Idempotency-Key": "ach2-chest-1"},
        )

        second = client.post(
            "/api/v1/quests/quest_endurance_001/accept",
            headers={**headers, "Idempotency-Key": "ach2-accept-2"},
        ).json()["data"]
        second_sub = client.post(
            f"/api/v1/quests/{second['id']}/submissions",
            headers={**headers, "Idempotency-Key": "ach2-submit-2"},
            json={"evidence_type": "manual", "manual_evidence": {"duration_minutes": 45}},
        ).json()["data"]
        verified = client.post(f"/api/v1/submissions/{second_sub['id']}/verify", headers=headers).json()["data"]

        codes = [item["code"] for item in verified.get("achievements_unlocked", [])]
        assert "first_quest" not in codes
        assert "level_2" not in codes
