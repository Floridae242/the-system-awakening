"""add achievement_unlocks (server-authoritative reveal ledger)"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b7c8d9e0f123"
down_revision: str | None = "f6a7b8c9d012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "achievement_unlocks",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("player_id", sa.String(length=36), sa.ForeignKey("player_profiles.id"), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column(
            "unlocked_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.UniqueConstraint("player_id", "code", name="uq_achievement_player_code"),
    )
    op.create_index("ix_achievement_unlocks_player_id", "achievement_unlocks", ["player_id"])


def downgrade() -> None:
    op.drop_index("ix_achievement_unlocks_player_id", table_name="achievement_unlocks")
    op.drop_table("achievement_unlocks")
