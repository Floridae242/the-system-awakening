from fastapi.testclient import TestClient

from main import app


def auth_headers(client: TestClient, handle: str) -> dict[str, str]:
    response = client.post("/api/v1/auth/demo", json={"handle": handle})
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


def idempotent(headers: dict[str, str], key: str) -> dict[str, str]:
    return {**headers, "Idempotency-Key": key}


def test_complete_core_loop_is_idempotent_and_visible():
    with TestClient(app) as client:
        headers = auth_headers(client, "hunter-one")

        initial = client.get("/api/v1/player", headers=headers)
        assert initial.status_code == 200
        assert initial.json()["data"]["current_xp"] == 0
        assert initial.json()["data"]["stats"] == {"str": 10, "agi": 10, "vit": 10, "int": 10, "wil": 10}

        quests = client.get("/api/v1/quests", headers=headers).json()["data"]
        focus = next(quest for quest in quests if quest["definition_id"] == "quest_focus_001")

        accepted = client.post(
            f"/api/v1/quests/{focus['definition_id']}/accept",
            headers=idempotent(headers, "accept-focus-0001"),
        )
        replay = client.post(
            f"/api/v1/quests/{focus['definition_id']}/accept",
            headers=idempotent(headers, "accept-focus-0001"),
        )
        assert accepted.status_code == 201
        assert replay.status_code == 200
        assert replay.json()["data"]["id"] == accepted.json()["data"]["id"]
        player_quest_id = accepted.json()["data"]["id"]

        submitted = client.post(
            f"/api/v1/quests/{player_quest_id}/submissions",
            headers=idempotent(headers, "submit-focus-0001"),
            json={"evidence_type": "manual", "manual_evidence": {"duration_minutes": 30}},
        )
        assert submitted.status_code == 202
        submission_id = submitted.json()["data"]["id"]

        verified = client.post(f"/api/v1/submissions/{submission_id}/verify", headers=headers)
        verified_replay = client.post(f"/api/v1/submissions/{submission_id}/verify", headers=headers)
        assert verified.status_code == 200
        assert verified.json()["data"]["verification"]["decision"] == "PASS"
        assert verified_replay.json()["data"]["reward"]["id"] == verified.json()["data"]["reward"]["id"]
        assert verified.json()["data"]["reward"]["exp_granted"] == 132
        chest_id = verified.json()["data"]["reward"]["chest_id"]

        progressed = client.get("/api/v1/player", headers=headers).json()["data"]
        assert progressed["current_xp"] == 132
        assert progressed["level"] == 2
        assert progressed["stats"]["int"] == 11

        opened = client.post(
            f"/api/v1/chests/{chest_id}/open",
            headers=idempotent(headers, "open-chest-0001"),
        )
        opened_replay = client.post(
            f"/api/v1/chests/{chest_id}/open",
            headers=idempotent(headers, "open-chest-0001"),
        )
        assert opened.status_code == 201
        assert opened_replay.status_code == 200
        assert opened_replay.json()["data"] == opened.json()["data"]

        inventory = client.get("/api/v1/inventory", headers=headers).json()["data"]
        assert len(inventory) == 1
        assert inventory[0]["id"] == opened.json()["data"]["item"]["id"]


def test_unknown_evidence_never_progresses():
    with TestClient(app) as client:
        headers = auth_headers(client, "needs-evidence")
        accepted = client.post(
            "/api/v1/quests/quest_focus_001/accept",
            headers=idempotent(headers, "accept-unknown-0001"),
        ).json()["data"]
        submission = client.post(
            f"/api/v1/quests/{accepted['id']}/submissions",
            headers=idempotent(headers, "submit-unknown-0001"),
            json={"evidence_type": "manual", "manual_evidence": {}},
        ).json()["data"]

        result = client.post(f"/api/v1/submissions/{submission['id']}/verify", headers=headers)
        assert result.json()["data"]["verification"]["decision"] == "NEED_MORE_EVIDENCE"
        assert result.json()["data"]["reward"] is None
        assert client.get("/api/v1/player", headers=headers).json()["data"]["current_xp"] == 0


def test_player_cannot_access_another_players_submission_or_chest():
    with TestClient(app) as client:
        owner = auth_headers(client, "owner")
        intruder = auth_headers(client, "intruder")
        accepted = client.post(
            "/api/v1/quests/quest_focus_001/accept",
            headers=idempotent(owner, "accept-owner-0001"),
        ).json()["data"]
        submission = client.post(
            f"/api/v1/quests/{accepted['id']}/submissions",
            headers=idempotent(owner, "submit-owner-0001"),
            json={"evidence_type": "manual", "manual_evidence": {"duration_minutes": 30}},
        ).json()["data"]
        verified = client.post(f"/api/v1/submissions/{submission['id']}/verify", headers=owner).json()["data"]

        assert client.get(f"/api/v1/submissions/{submission['id']}", headers=intruder).status_code == 404
        assert (
            client.post(
                f"/api/v1/chests/{verified['reward']['chest_id']}/open",
                headers=idempotent(intruder, "intruder-open-0001"),
            ).status_code
            == 404
        )
