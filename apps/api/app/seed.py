from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import ItemDefinition, QuestDefinition

QUESTS = (
    ("quest_focus_001", "Trial of Focus", "study", "NORMAL", "INT", {"type": "duration_minutes", "target": 30}),
    ("quest_run_001", "Road of Momentum", "running", "NORMAL", "AGI", {"type": "distance_km", "target": 3}),
    ("quest_code_001", "Forge of Logic", "coding", "HARD", "INT", {"type": "completion", "target": 1}),
    ("quest_journal_001", "Echoes of the Mind", "journal", "EASY", "WIL", {"type": "completion", "target": 1}),
    ("quest_endurance_001", "Trial of Endurance", "fitness", "HARD", "VIT", {"type": "duration_minutes", "target": 45}),
)

ITEMS = (
    ("item_common_focus_band", "Focus Band", "COMMON", "accessory", 5),
    ("item_uncommon_runner_charm", "Runner Charm", "UNCOMMON", "charm", 10),
    ("item_rare_momentum_boots", "Momentum Boots", "RARE", "boots", 20),
    ("item_epic_architect_mantle", "Architect's Mantle", "EPIC", "mantle", 35),
    ("item_legendary_archive_halo", "Archive Halo", "LEGENDARY", "artifact", 60),
    ("item_mythic_core_of_awakening", "Core of Awakening", "MYTHIC", "artifact", 100),
)


async def seed_content(session: AsyncSession) -> None:
    if await session.scalar(select(QuestDefinition.id).limit(1)) is None:
        for quest_id, title, category, difficulty, stat, objective in QUESTS:
            session.add(
                QuestDefinition(
                    id=quest_id,
                    version=1,
                    title=title,
                    category=category,
                    difficulty=difficulty,
                    primary_stat=stat,
                    objective=objective,
                    verification_policy={"accepted_evidence": ["manual"], "demo_only": True},
                )
            )
    if await session.scalar(select(ItemDefinition.id).limit(1)) is None:
        for item_id, name, rarity, item_type, power in ITEMS:
            session.add(
                ItemDefinition(
                    id=item_id,
                    version=1,
                    name=name,
                    rarity=rarity,
                    item_type=item_type,
                    power=power,
                )
            )
    await session.commit()
