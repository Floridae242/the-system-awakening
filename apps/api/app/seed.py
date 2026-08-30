import json
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from .models import ItemDefinition, QuestDefinition

CONTENT_PATH = Path(__file__).resolve().parents[3] / "09_CONTENT_SEED.json"


def load_seed_content() -> dict:
    return json.loads(CONTENT_PATH.read_text(encoding="utf-8"))


async def seed_content(session: AsyncSession) -> None:
    content = load_seed_content()
    for quest in content["quests"]:
        values = {
            "version": quest["version"],
            "title": quest["title"],
            "category": quest["category"],
            "difficulty": quest["difficulty"],
            "primary_stat": quest["primary_stat"],
            "objective": quest["objective"],
            "verification_policy": {
                **quest["verification"],
                "available_evidence": ["manual"],
                "demo_only": True,
            },
            "reward_profile": quest["reward_profile"],
            "active": quest["status"] == "active",
        }
        definition = await session.get(QuestDefinition, quest["id"])
        if definition is None:
            session.add(QuestDefinition(id=quest["id"], **values))
        elif any(getattr(definition, field) != value for field, value in values.items()):
            raise RuntimeError(
                f"immutable quest definition drift: {quest['id']} v{quest['version']}"
            )
    for item in content["items"]:
        values = {
            "version": item["version"],
            "name": item["name"],
            "rarity": item["rarity"],
            "item_type": item["type"],
            "power": item["power"],
        }
        definition = await session.get(ItemDefinition, item["id"])
        if definition is None:
            session.add(ItemDefinition(id=item["id"], **values))
        elif any(getattr(definition, field) != value for field, value in values.items()):
            raise RuntimeError(
                f"immutable item definition drift: {item['id']} v{item['version']}"
            )
    await session.commit()
