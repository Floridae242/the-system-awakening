"""promote authoritative content v1

Revision ID: d4e5f6a7b890
Revises: c7d81e2a4f30
"""

import json
from collections.abc import Sequence
from pathlib import Path

import sqlalchemy as sa

from alembic import op

revision: str = "d4e5f6a7b890"
down_revision: str | None = "c7d81e2a4f30"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    content_path = Path(__file__).resolve().parents[4] / "09_CONTENT_SEED.json"
    content = json.loads(content_path.read_text(encoding="utf-8"))
    connection = op.get_bind()
    quests = sa.table(
        "quest_definitions", sa.column("id", sa.String()), sa.column("version", sa.Integer()),
        sa.column("title", sa.String()), sa.column("category", sa.String()),
        sa.column("difficulty", sa.String()), sa.column("primary_stat", sa.String()),
        sa.column("objective", sa.JSON()), sa.column("verification_policy", sa.JSON()),
        sa.column("reward_profile", sa.String()), sa.column("active", sa.Boolean()),
    )
    for quest in content["quests"]:
        values = {
            "version": quest["version"], "title": quest["title"], "category": quest["category"],
            "difficulty": quest["difficulty"], "primary_stat": quest["primary_stat"],
            "objective": quest["objective"],
            "verification_policy": {**quest["verification"], "available_evidence": ["manual"], "demo_only": True},
            "reward_profile": quest["reward_profile"], "active": quest["status"] == "active",
        }
        query = sa.select(quests.c.id).where(quests.c.id == quest["id"])
        if connection.execute(query).first():
            connection.execute(quests.update().where(quests.c.id == quest["id"]).values(**values))
        else:
            connection.execute(quests.insert().values(id=quest["id"], **values))

    items = sa.table(
        "item_definitions", sa.column("id", sa.String()), sa.column("version", sa.Integer()),
        sa.column("name", sa.String()), sa.column("rarity", sa.String()),
        sa.column("item_type", sa.String()), sa.column("power", sa.Integer()),
    )
    for item in content["items"]:
        values = {"version": item["version"], "name": item["name"], "rarity": item["rarity"],
                  "item_type": item["type"], "power": item["power"]}
        query = sa.select(items.c.id).where(items.c.id == item["id"])
        if connection.execute(query).first():
            connection.execute(items.update().where(items.c.id == item["id"]).values(**values))
        else:
            connection.execute(items.insert().values(id=item["id"], **values))


def downgrade() -> None:
    # Content promotion is forward-only; snapshots and inventory survive rollback.
    pass
