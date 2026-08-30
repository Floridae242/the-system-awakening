import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.database import Base, SessionFactory, engine
from app.models import QuestDefinition
from app.seed import seed_content
from main import app


def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post("/api/v1/auth/demo", json={"handle": "seed-contract"})
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


def test_seeded_quests_match_authoritative_content_contract():
    contract_path = Path(__file__).parents[3] / "09_CONTENT_SEED.json"
    expected_quests = json.loads(contract_path.read_text(encoding="utf-8"))["quests"]

    with TestClient(app) as client:
        headers = auth_headers(client)
        response = client.get("/api/v1/quests", headers=headers)

    assert response.status_code == 200
    actual_by_id = {quest["definition_id"]: quest for quest in response.json()["data"]}
    assert set(actual_by_id) == {quest["id"] for quest in expected_quests}
    for expected in expected_quests:
        actual = actual_by_id[expected["id"]]
        assert actual == {
            "definition_id": expected["id"],
            "version": expected["version"],
            "title": expected["title"],
            "category": expected["category"],
            "difficulty": expected["difficulty"],
            "primary_stat": expected["primary_stat"],
            "objective": expected["objective"],
            "verification_policy": {
                **expected["verification"],
                "available_evidence": ["manual"],
                "demo_only": True,
            },
            "reward_profile": expected["reward_profile"],
            "active": expected["status"] == "active",
        }


@pytest.mark.asyncio
async def test_seed_refuses_to_rewrite_an_existing_version():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with SessionFactory() as session:
        await seed_content(session)
        quest = await session.get(QuestDefinition, "quest_focus_001")
        quest.title = "STALE TITLE"
        await session.commit()

    async with SessionFactory() as session:
        with pytest.raises(RuntimeError, match="immutable quest definition drift"):
            await seed_content(session)

    async with SessionFactory() as session:
        quest = await session.get(QuestDefinition, "quest_focus_001")
        quest.title = "Trial of Focus"
        await session.commit()
