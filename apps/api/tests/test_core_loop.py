import asyncio

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database import SessionFactory
from app.models import AuditEvent, QuestDefinition
from main import app


def auth_headers(client: TestClient, handle: str) -> dict[str, str]:
    response = client.post("/api/v1/auth/demo", json={"handle": handle})
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


def idempotent(headers: dict[str, str], key: str) -> dict[str, str]:
    return {**headers, "Idempotency-Key": key}


async def set_focus_target(target: int) -> None:
    async with SessionFactory() as session:
        quest = await session.get(QuestDefinition, "quest_focus_001")
        quest.objective = {"type": "duration_minutes", "target": target}
        await session.commit()


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
        opened_with_new_key = client.post(
            f"/api/v1/chests/{chest_id}/open",
            headers=idempotent(headers, "open-chest-replay-new-key"),
        )
        assert opened.status_code == 201
        assert opened_replay.status_code == 200
        assert opened_with_new_key.status_code == 200
        assert opened_replay.json()["data"] == opened.json()["data"]

        journal = client.post(
            "/api/v1/quests/quest_journal_001/accept",
            headers=idempotent(headers, "accept-journal-second-chest"),
        ).json()["data"]
        journal_submission = client.post(
            f"/api/v1/quests/{journal['id']}/submissions",
            headers=idempotent(headers, "submit-journal-second-chest"),
            json={"evidence_type": "manual", "manual_evidence": {"completion": True}},
        ).json()["data"]
        journal_verified = client.post(
            f"/api/v1/submissions/{journal_submission['id']}/verify",
            headers=headers,
        ).json()["data"]
        reused_key = client.post(
            f"/api/v1/chests/{journal_verified['reward']['chest_id']}/open",
            headers=idempotent(headers, "open-chest-replay-new-key"),
        )
        assert reused_key.status_code == 409

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


def test_completion_quest_uses_explicit_boolean_observation():
    with TestClient(app) as client:
        headers = auth_headers(client, "journal-hunter")
        accepted = client.post(
            "/api/v1/quests/quest_journal_001/accept",
            headers=idempotent(headers, "accept-journal-0001"),
        ).json()["data"]
        submission = client.post(
            f"/api/v1/quests/{accepted['id']}/submissions",
            headers=idempotent(headers, "submit-journal-0001"),
            json={"evidence_type": "manual", "manual_evidence": {"completion": True}},
        )

        assert submission.status_code == 202
        verified = client.post(
            f"/api/v1/submissions/{submission.json()['data']['id']}/verify",
            headers=headers,
        )
        assert verified.status_code == 200
        assert verified.json()["data"]["verification"]["decision"] == "PASS"
        assert verified.json()["data"]["reward"] is not None


def test_manual_evidence_rejects_unknown_and_oversized_observations():
    with TestClient(app) as client:
        headers = auth_headers(client, "bounded-proof")
        accepted = client.post(
            "/api/v1/quests/quest_focus_001/accept",
            headers=idempotent(headers, "accept-bounded-0001"),
        ).json()["data"]

        unknown = client.post(
            f"/api/v1/quests/{accepted['id']}/submissions",
            headers=idempotent(headers, "submit-bounded-0001"),
            json={"evidence_type": "manual", "manual_evidence": {"nested": {"payload": "x"}}},
        )
        oversized = client.post(
            f"/api/v1/quests/{accepted['id']}/submissions",
            headers=idempotent(headers, "submit-bounded-0002"),
            json={"evidence_type": "manual", "manual_evidence": {"duration_minutes": 100000}},
        )

        assert unknown.status_code == 422
        assert oversized.status_code == 422


def test_same_accepted_quest_cannot_create_two_active_submissions():
    with TestClient(app) as client:
        headers = auth_headers(client, "single-settlement")
        accepted = client.post(
            "/api/v1/quests/quest_focus_001/accept",
            headers=idempotent(headers, "accept-single-0001"),
        ).json()["data"]
        path = f"/api/v1/quests/{accepted['id']}/submissions"
        proof = {"evidence_type": "manual", "manual_evidence": {"duration_minutes": 30}}

        first = client.post(path, headers=idempotent(headers, "submit-single-0001"), json=proof)
        second = client.post(path, headers=idempotent(headers, "submit-single-0002"), json=proof)

        assert first.status_code == 202
        assert second.status_code == 409


def test_same_definition_cannot_be_accepted_twice_with_different_keys():
    with TestClient(app) as client:
        headers = auth_headers(client, "single-active-quest")
        first = client.post(
            "/api/v1/quests/quest_focus_001/accept",
            headers=idempotent(headers, "accept-active-0001"),
        )
        second = client.post(
            "/api/v1/quests/quest_focus_001/accept",
            headers=idempotent(headers, "accept-active-0002"),
        )

        assert first.status_code == 201
        assert second.status_code == 409
        assert second.json()["detail"] == "Quest is already active"


def test_accepted_quest_verifies_against_immutable_snapshot():
    with TestClient(app) as client:
        headers = auth_headers(client, "snapshot-rules")
        accepted = client.post(
            "/api/v1/quests/quest_focus_001/accept",
            headers=idempotent(headers, "accept-snapshot-0001"),
        ).json()["data"]
        asyncio.run(set_focus_target(999))
        try:
            submission = client.post(
                f"/api/v1/quests/{accepted['id']}/submissions",
                headers=idempotent(headers, "submit-snapshot-0001"),
                json={"evidence_type": "manual", "manual_evidence": {"duration_minutes": 30}},
            ).json()["data"]
            verified = client.post(
                f"/api/v1/submissions/{submission['id']}/verify",
                headers=headers,
            )
        finally:
            asyncio.run(set_focus_target(30))

    assert verified.status_code == 200
    assert verified.json()["data"]["verification"]["decision"] == "PASS"


def test_api_applies_security_headers_and_rejects_large_json_bodies():
    def oversized_chunks():
        yield b'{"handle":"'
        yield b"x" * 17000
        yield b'"}'

    with TestClient(app) as client:
        health = client.get("/api/v1/health")
        oversized = client.post(
            "/api/v1/auth/demo",
            content='{"handle":"' + ("x" * 17000) + '"}',
            headers={"Content-Type": "application/json"},
        )
        chunked = client.post(
            "/api/v1/auth/demo",
            content=oversized_chunks(),
            headers={"Content-Type": "application/json", "Transfer-Encoding": "chunked"},
        )

    assert health.headers["x-content-type-options"] == "nosniff"
    assert health.headers["x-frame-options"] == "DENY"
    assert health.headers["referrer-policy"] == "no-referrer"
    assert oversized.status_code == 413
    assert chunked.status_code == 413


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


def test_core_mutations_write_audit_events_in_transaction():
    with TestClient(app) as client:
        headers = auth_headers(client, "audit-trail-player")
        accepted = client.post(
            "/api/v1/quests/quest_focus_001/accept",
            headers=idempotent(headers, "audit-accept-0001"),
        ).json()["data"]
        submission = client.post(
            f"/api/v1/quests/{accepted['id']}/submissions",
            headers=idempotent(headers, "audit-submit-0001"),
            json={"evidence_type": "manual", "manual_evidence": {"duration_minutes": 30}},
        ).json()["data"]
        result = client.post(f"/api/v1/submissions/{submission['id']}/verify", headers=headers).json()["data"]
        client.post(
            f"/api/v1/chests/{result['reward']['chest_id']}/open",
            headers=idempotent(headers, "audit-open-0001"),
        )

    async def events() -> list[str]:
        async with SessionFactory() as session:
            rows = await session.scalars(select(AuditEvent.event_type).where(AuditEvent.player_id.is_not(None)))
            return list(rows)

    event_types = asyncio.run(events())
    expected = {"quest.accepted", "submission.created", "submission.verified", "reward.granted", "chest.opened"}
    assert expected <= set(event_types)
