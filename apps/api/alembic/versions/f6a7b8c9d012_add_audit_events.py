"""add immutable domain audit events"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f6a7b8c9d012"
down_revision: str | None = "e1f2a3b4c5d6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("event_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("player_id", sa.String(length=36), nullable=True),
        sa.Column("correlation_id", sa.String(length=128), nullable=True),
        sa.Column("causation_id", sa.String(length=36), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["player_id"], ["player_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_events_player_id", "audit_events", ["player_id"], unique=False)
    op.create_index("ix_audit_events_player_created", "audit_events", ["player_id", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_audit_events_player_created", table_name="audit_events")
    op.drop_index("ix_audit_events_player_id", table_name="audit_events")
    op.drop_table("audit_events")
