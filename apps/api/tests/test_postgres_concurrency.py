"""Concurrency regression tests against a real PostgreSQL database.

These tests intentionally use the HTTP application boundary and separate
threads (and therefore separate SQLAlchemy sessions) to exercise row locks and
database-enforced uniqueness. They are skipped for the normal SQLite test
suite; run them with ``TEST_POSTGRES_URL`` set to a PostgreSQL async URL.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from main import app


def _postgres_url() -> str:
    # conftest maps TEST_POSTGRES_URL to DATABASE_URL before app import.
    import os

    return os.getenv("TEST_POSTGRES_URL") or os.getenv("DATABASE_URL", "")


pytestmark = pytest.mark.skipif(
    not _postgres_url().startswith(("postgresql+asyncpg://", "postgresql://")),
    reason="set TEST_POSTGRES_URL to run real PostgreSQL concurrency tests",
)


@pytest.fixture(scope="module")
def postgres_client():
    """Keep one event loop for the asyncpg engine for the whole module."""

    with TestClient(app) as client:
        yield client


def _headers(token: str, key: str | None = None) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {token}"}
    if key:
        headers["Idempotency-Key"] = key
    return headers


def _demo_token(client: TestClient, handle: str) -> str:
    response = client.post("/api/v1/auth/demo", json={"handle": handle})
    assert response.status_code == 201, response.text
    return response.json()["data"]["access_token"]


def _concurrent(client: TestClient, requests: list[tuple[str, dict[str, str], dict | None]]) -> list:
    """Run requests concurrently while retaining each response for diagnostics."""

    def send(request: tuple[str, dict[str, str], dict | None]):
        path, headers, payload = request
        return client.post(path, headers=headers, json=payload)

    with ThreadPoolExecutor(max_workers=len(requests)) as pool:
        return list(pool.map(send, requests))


def test_concurrent_acceptance_allows_exactly_one_active_quest(postgres_client: TestClient) -> None:
    token = _demo_token(postgres_client, f"pg-accept-{uuid4().hex[:12]}")
    responses = _concurrent(
        postgres_client,
        [
            ("/api/v1/quests/quest_focus_001/accept", _headers(token, "pg-accept-a"), None),
            ("/api/v1/quests/quest_focus_001/accept", _headers(token, "pg-accept-b"), None),
        ],
    )

    assert sorted(response.status_code for response in responses) == [201, 409]
    assert sum(response.status_code == 201 for response in responses) == 1


def test_concurrent_verification_settles_two_quests_once_and_serializes_player(postgres_client: TestClient) -> None:
    client = postgres_client
    token = _demo_token(client, f"pg-settle-{uuid4().hex[:12]}")
    accepted_focus = client.post(
        "/api/v1/quests/quest_focus_001/accept", headers=_headers(token, "pg-settle-accept-focus")
    )
    accepted_journal = client.post(
        "/api/v1/quests/quest_journal_001/accept", headers=_headers(token, "pg-settle-accept-journal")
    )
    assert accepted_focus.status_code == accepted_journal.status_code == 201

    focus_id = accepted_focus.json()["data"]["id"]
    journal_id = accepted_journal.json()["data"]["id"]
    focus_submission = client.post(
        f"/api/v1/quests/{focus_id}/submissions",
        headers=_headers(token, "pg-settle-submit-focus"),
        json={"evidence_type": "manual", "manual_evidence": {"duration_minutes": 30}},
    )
    journal_submission = client.post(
        f"/api/v1/quests/{journal_id}/submissions",
        headers=_headers(token, "pg-settle-submit-journal"),
        json={"evidence_type": "manual", "manual_evidence": {"completion": True}},
    )
    assert focus_submission.status_code == journal_submission.status_code == 202

    submission_ids = [focus_submission.json()["data"]["id"], journal_submission.json()["data"]["id"]]
    responses = _concurrent(
        client,
        [
            (f"/api/v1/submissions/{submission_id}/verify", _headers(token), None)
            for submission_id in submission_ids
        ],
    )
    assert [response.status_code for response in responses] == [200, 200]
    rewards = [response.json()["data"]["reward"] for response in responses]
    assert all(reward is not None for reward in rewards)
    assert len({reward["id"] for reward in rewards}) == 2

    player = client.get("/api/v1/player", headers=_headers(token))
    assert player.status_code == 200
    assert player.json()["data"]["current_xp"] == sum(reward["exp_granted"] for reward in rewards)

    # Retrying both requests must return the persisted grants, not create more value.
    retries = [
        client.post(f"/api/v1/submissions/{submission_id}/verify", headers=_headers(token))
        for submission_id in submission_ids
    ]
    assert {response.json()["data"]["reward"]["id"] for response in retries} == {
        reward["id"] for reward in rewards
    }


def test_concurrent_chest_open_has_one_persisted_result(postgres_client: TestClient) -> None:
    client = postgres_client
    token = _demo_token(client, f"pg-chest-{uuid4().hex[:12]}")
    accepted = client.post(
        "/api/v1/quests/quest_journal_001/accept", headers=_headers(token, "pg-chest-accept")
    )
    submission = client.post(
        f"/api/v1/quests/{accepted.json()['data']['id']}/submissions",
        headers=_headers(token, "pg-chest-submit"),
        json={"evidence_type": "manual", "manual_evidence": {"completion": True}},
    )
    verified = client.post(f"/api/v1/submissions/{submission.json()['data']['id']}/verify", headers=_headers(token))
    assert verified.status_code == 200
    chest_id = verified.json()["data"]["reward"]["chest_id"]

    responses = _concurrent(
        client,
        [
            (f"/api/v1/chests/{chest_id}/open", _headers(token, "pg-chest-open-a"), None),
            (f"/api/v1/chests/{chest_id}/open", _headers(token, "pg-chest-open-b"), None),
        ],
    )
    assert sorted(response.status_code for response in responses) == [200, 201]
    results = [response.json()["data"] for response in responses]
    assert results[0] == results[1]

    inventory = client.get("/api/v1/inventory", headers=_headers(token))
    assert inventory.status_code == 200
    assert len(inventory.json()["data"]) == 1
