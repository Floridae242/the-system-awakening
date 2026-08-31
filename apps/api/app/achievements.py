"""Deterministic, server-authoritative achievement evaluation (reveal-only)."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import AchievementUnlock, InventoryItem, ItemDefinition, PlayerProfile, PlayerQuest

RARE_PLUS = {"RARE", "EPIC", "LEGENDARY", "MYTHIC"}


async def _completed_quests(session: AsyncSession, player_id: str) -> int:
    return int(
        await session.scalar(
            select(func.count())
            .select_from(PlayerQuest)
            .where(PlayerQuest.player_id == player_id, PlayerQuest.status == "COMPLETED")
        )
        or 0
    )


async def _has_rare_or_better(session: AsyncSession, player_id: str) -> bool:
    rows = await session.scalars(
        select(ItemDefinition.rarity)
        .join(InventoryItem, InventoryItem.item_definition_id == ItemDefinition.id)
        .where(InventoryItem.player_id == player_id)
    )
    return any(rarity in RARE_PLUS for rarity in rows)


async def evaluate_achievements(
    session: AsyncSession, player: PlayerProfile, *, commit: bool = False
) -> list[dict]:
    """Unlock any newly satisfied achievements and return them for the response.

    Reads only committed authoritative state (plus in-transaction settlement
    changes) and persists new unlocks exactly once via the unique constraint.
    """

    completed = await _completed_quests(session, player.id)
    has_rare = await _has_rare_or_better(session, player.id)
    satisfied: dict[str, tuple[str, str]] = {
        "first_quest": ("The Awakening", "Complete your first quest."),
        "level_2": ("Ascendant", "Reach Level 2."),
        "level_5": ("Veteran Awakened", "Reach Level 5."),
        "five_quests": ("Momentum", "Complete five quests."),
        "first_rare": ("Rare Find", "Obtain a RARE or better item."),
    }
    conditions = {
        "first_quest": completed >= 1,
        "level_2": player.level >= 2,
        "level_5": player.level >= 5,
        "five_quests": completed >= 5,
        "first_rare": has_rare,
    }

    existing = set(
        await session.scalars(
            select(AchievementUnlock.code).where(AchievementUnlock.player_id == player.id)
        )
    )
    unlocked: list[dict] = []
    for code, satisfied_now in conditions.items():
        if not satisfied_now or code in existing:
            continue
        name, description = satisfied[code]
        session.add(AchievementUnlock(player_id=player.id, code=code))
        unlocked.append({"code": code, "name": name, "description": description})
    if unlocked:
        await session.flush()
    if commit:
        await session.commit()
    return unlocked
