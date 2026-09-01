"""add player_profiles.last_quest_date (daily streak engine)"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c9d0e1f2a345"
down_revision: str | None = "b7c8d9e0f123"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "player_profiles",
        sa.Column("last_quest_date", sa.Date(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("player_profiles", "last_quest_date")
