"""add quest reward profile

Revision ID: 9f2a1c4b7d10
Revises: 468f4134bb21
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "9f2a1c4b7d10"
down_revision: str | None = "468f4134bb21"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("quest_definitions") as batch_op:
        batch_op.add_column(sa.Column("reward_profile", sa.String(length=40), nullable=True))
    op.execute(
        """
        UPDATE quest_definitions
        SET reward_profile = CASE difficulty
            WHEN 'EASY' THEN 'easy_v1'
            WHEN 'NORMAL' THEN 'normal_v1'
            WHEN 'HARD' THEN 'hard_v1'
            WHEN 'ELITE' THEN 'elite_v1'
            WHEN 'EXTREME' THEN 'extreme_v1'
            ELSE 'normal_v1'
        END
        """
    )
    with op.batch_alter_table("quest_definitions") as batch_op:
        batch_op.alter_column("reward_profile", existing_type=sa.String(length=40), nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("quest_definitions") as batch_op:
        batch_op.drop_column("reward_profile")
