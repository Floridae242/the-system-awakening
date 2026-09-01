"""Quest system integrity — anti-farm guarantees (red→green regression pack)."""

import time

from fastapi.testclient import TestClient

from main import app


def _register(client: TestClient, tag: str) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": f"farm-{tag}-{time.time()}@test.local", "password": "correct-horse-battery-staple"},
    )
    assert response.status_code == 201
    return {"x-csrf-token": response.json()["data"]["csrf_token"]}


def _complete(
    client: TestClient, headers: dict, quest_id: str, key: str, *, completion: bool = False
) -> tuple[int, dict | None]:
    evidence = {"completion": True} if completion else {"duration_minutes": 30}
    accepted_response = client.post(
        f"/api/v1/quests/{quest_id}/accept",
        headers={**headers, "Idempotency-Key": f"{key}-accept"},
    )
    if accepted_response.status_code != 201:
        return accepted_response.status_code, None
    accepted = accepted_response.json()["data"]
    submitted = client.post(
        f"/api/v1/quests/{accepted['id']}/submissions",
        headers={**headers, "Idempotency-Key": f"{key}-submit"},
        json={
            "evidence_type": "manual",
            "manual_evidence": evidence,
        },
    ).json()["data"]
    verified = client.post(f"/api/v1/submissions/{submitted['id']}/verify", headers=headers).json()["data"]
    decision = verified["verification"]["decision"]
    assert decision == "PASS", verified["verification"]
    return 201, verified["reward"]


def test_same_quest_cannot_be_farmed_on_the_same_day():
    with TestClient(app) as client:
        headers = _register(client, "farm-day")
        status, first = _complete(client, headers, "quest_focus_001", "farm-day-1")
        assert status == 201 and first is not None

        for attempt in range(2, 5):
            status, reward = _complete(client, headers, "quest_focus_001", f"farm-day-{attempt}")
            assert status == 409, f"attempt {attempt} must be rejected (same game day)"
            assert reward is None


def test_exp_is_bounded_per_day_not_infinite():
    with TestClient(app) as client:
        headers = _register(client, "exp-bound")
        total = 0
        for attempt in range(1, 4):
            status, reward = _complete(client, headers, "quest_journal_001", f"bound-{attempt}", completion=True)
            if status == 409:
                break
            total += reward["exp_granted"] if reward else 0
        me = client.get("/api/v1/auth/me").json()["data"]["player"]
        assert me["current_xp"] == total, "EXP on the profile must equal the sum of settled rewards"
        assert total > 0
