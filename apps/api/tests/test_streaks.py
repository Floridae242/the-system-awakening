"""Daily streak engine — deterministic per Game Rules (reward multiplier input)."""

import time
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.models import PlayerProfile
from main import app


def _headers(client: TestClient, tag: str) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": f"streak-{tag}-{time.time()}@test.local", "password": "correct-horse-battery-staple"},
    )
    assert response.status_code == 201
    return {"x-csrf-token": response.json()["data"]["csrf_token"]}


EVIDENCE_BY_QUEST = {
    "quest_focus_001": {"duration_minutes": 30},
    "quest_endurance_001": {"duration_minutes": 45},
    "quest_journal_001": {"completion": True},
    "quest_code_001": {"completion": True},
    "quest_run_001": {"distance_km": 3},
}


def _complete_quest(client: TestClient, headers: dict, quest_id: str, key: str) -> None:
    accepted = client.post(
        f"/api/v1/quests/{quest_id}/accept",
        headers={**headers, "Idempotency-Key": f"{key}-accept"},
    ).json()["data"]
    submitted = client.post(
        f"/api/v1/quests/{accepted['id']}/submissions",
        headers={**headers, "Idempotency-Key": f"{key}-submit"},
        json={"evidence_type": "manual", "manual_evidence": EVIDENCE_BY_QUEST[quest_id]},
    ).json()["data"]
    verified = client.post(f"/api/v1/submissions/{submitted['id']}/verify", headers=headers).json()["data"]
    assert verified["verification"]["decision"] == "PASS", verified["verification"]
    client.post(
        f"/api/v1/chests/{verified['reward']['chest_id']}/open",
        headers={**headers, "Idempotency-Key": f"{key}-chest"},
    )


def _player(client: TestClient, headers: dict) -> PlayerProfile:
    # Read through the app session to get the actual ORM row (dates included).
    import anyio

    from app.database import SessionFactory

    profile: PlayerProfile | None = None

    async def read():
        nonlocal profile
        async with SessionFactory() as session:
            me = client.get("/api/v1/auth/me").json()["data"]["player"]
            profile = await session.get(PlayerProfile, me["id"])

    anyio.run(read)
    assert profile is not None
    return profile


def _run(coro):
    import asyncio

    return asyncio.get_event_loop().run_until_complete(coro) if False else None


def test_streak_same_day_multiple_quests_counts_once():
    with TestClient(app) as client:
        headers = _headers(client, "same-day")
        _complete_quest(client, headers, "quest_focus_001", "sd-1")
        player = _player(client, headers)
        assert player.streak_days == 1
        assert player.last_quest_date == datetime.now(UTC).date()

        _complete_quest(client, headers, "quest_journal_001", "sd-2")
        player = _player(client, headers)
        assert player.streak_days == 1, "same-day quests must not inflate the streak"


def test_streak_extends_on_consecutive_day():
    with TestClient(app) as client:
        headers = _headers(client, "consecutive")
        _complete_quest(client, headers, "quest_focus_001", "cx-1")
        player = _player(client, headers)
        yesterday = datetime.now(UTC).date() - timedelta(days=1)
        player.last_quest_date = yesterday  # simulate the previous session was yesterday

        import anyio

        async def save():
            from app.database import SessionFactory

            async with SessionFactory() as session:
                merged = await session.merge(player)
                merged.streak_days = player.streak_days
                merged.last_quest_date = player.last_quest_date
                await session.commit()

        anyio.run(save)

        _complete_quest(client, headers, "quest_journal_001", "cx-2")
        updated = _player(client, headers)
        assert updated.streak_days == 2


def test_streak_resets_after_a_gap():
    with TestClient(app) as client:
        headers = _headers(client, "gap")
        _complete_quest(client, headers, "quest_focus_001", "gap-1")
        player = _player(client, headers)
        player.streak_days = 7
        player.last_quest_date = datetime.now(UTC).date() - timedelta(days=4)

        import anyio

        async def save():
            from app.database import SessionFactory

            async with SessionFactory() as session:
                merged = await session.merge(player)
                merged.streak_days = player.streak_days
                merged.last_quest_date = player.last_quest_date
                await session.commit()

        anyio.run(save)

        _complete_quest(client, headers, "quest_journal_001", "gap-2")
        updated = _player(client, headers)
        assert updated.streak_days == 1, "a multi-day gap resets the streak"


def test_player_response_exposes_streak():
    with TestClient(app) as client:
        headers = _headers(client, "expose")
        _complete_quest(client, headers, "quest_focus_001", "expose-1")
        me = client.get("/api/v1/auth/me").json()["data"]["player"]
        assert me["streak_days"] == 1
