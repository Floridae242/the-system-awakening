"""enforce exactly once progression

Revision ID: c7d81e2a4f30
Revises: 9f2a1c4b7d10
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c7d81e2a4f30"
down_revision: str | None = "9f2a1c4b7d10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _assert_no_duplicate(connection, query: str, label: str) -> None:
    if connection.execute(sa.text(query)).first() is not None:
        raise RuntimeError(
            f"migration preflight failed: duplicate {label}; audit and resolve rows before retrying"
        )


def upgrade() -> None:
    with op.batch_alter_table("player_quests") as batch_op:
        batch_op.add_column(sa.Column("definition_snapshot", sa.JSON(), nullable=True))
    connection = op.get_bind()
    player_quests = sa.table(
        "player_quests",
        sa.column("id", sa.String()),
        sa.column("quest_definition_id", sa.String()),
        sa.column("definition_snapshot", sa.JSON()),
    )
    quest_definitions = sa.table(
        "quest_definitions",
        sa.column("id", sa.String()),
        sa.column("version", sa.Integer()),
        sa.column("difficulty", sa.String()),
        sa.column("primary_stat", sa.String()),
        sa.column("objective", sa.JSON()),
        sa.column("verification_policy", sa.JSON()),
        sa.column("reward_profile", sa.String()),
    )
    rows = connection.execute(
        sa.select(
            player_quests.c.id.label("player_quest_id"),
            quest_definitions.c.id.label("definition_id"),
            quest_definitions.c.version,
            quest_definitions.c.difficulty,
            quest_definitions.c.primary_stat,
            quest_definitions.c.objective,
            quest_definitions.c.verification_policy,
            quest_definitions.c.reward_profile,
        ).join(
            quest_definitions,
            player_quests.c.quest_definition_id == quest_definitions.c.id,
        )
    ).mappings()
    for row in rows:
        snapshot = {
            "definition_id": row["definition_id"],
            "version": row["version"],
            "difficulty": row["difficulty"],
            "primary_stat": row["primary_stat"],
            "objective": row["objective"],
            "verification_policy": row["verification_policy"],
            "reward_profile": row["reward_profile"],
            "rules_version": "1.0.0",
        }
        connection.execute(
            player_quests.update()
            .where(player_quests.c.id == row["player_quest_id"])
            .values(definition_snapshot=snapshot)
        )
    with op.batch_alter_table("player_quests") as batch_op:
        batch_op.alter_column(
            "definition_snapshot",
            existing_type=sa.JSON(),
            nullable=False,
        )

    with op.batch_alter_table("reward_grants") as batch_op:
        batch_op.add_column(sa.Column("player_quest_id", sa.String(length=36), nullable=True))
        batch_op.create_foreign_key(
            "fk_reward_grants_player_quest_id",
            "player_quests",
            ["player_quest_id"],
            ["id"],
        )
    op.execute(
        """
        UPDATE reward_grants
        SET player_quest_id = (
            SELECT quest_submissions.player_quest_id
            FROM quest_submissions
            WHERE quest_submissions.id = reward_grants.submission_id
        )
        """
    )
    _assert_no_duplicate(
        connection,
        """
        SELECT player_quest_id
        FROM reward_grants
        GROUP BY player_quest_id
        HAVING COUNT(*) > 1
        LIMIT 1
        """,
        "reward grants per accepted quest",
    )
    with op.batch_alter_table("reward_grants") as batch_op:
        batch_op.alter_column(
            "player_quest_id",
            existing_type=sa.String(length=36),
            nullable=False,
        )
        batch_op.create_unique_constraint(
            "uq_reward_grants_player_quest_id",
            ["player_quest_id"],
        )

    _assert_no_duplicate(
        connection,
        """
        SELECT player_id
        FROM player_quests
        WHERE status IN ('ACCEPTED', 'SUBMITTED', 'NEED_MORE_EVIDENCE', 'REVIEW')
        GROUP BY player_id, quest_definition_id
        HAVING COUNT(*) > 1
        LIMIT 1
        """,
        "active quest definitions",
    )
    _assert_no_duplicate(
        connection,
        """
        SELECT player_quest_id
        FROM quest_submissions
        WHERE status = 'CREATED'
        GROUP BY player_quest_id
        HAVING COUNT(*) > 1
        LIMIT 1
        """,
        "active submissions",
    )
    _assert_no_duplicate(
        connection,
        """
        SELECT reward_grant_id
        FROM progression_ledger
        WHERE entry_type = 'EXP'
        GROUP BY reward_grant_id
        HAVING COUNT(*) > 1
        LIMIT 1
        """,
        "EXP ledger entries",
    )

    op.create_index(
        "uq_player_quest_active_definition",
        "player_quests",
        ["player_id", "quest_definition_id"],
        unique=True,
        postgresql_where=sa.text(
            "status IN ('ACCEPTED', 'SUBMITTED', 'NEED_MORE_EVIDENCE', 'REVIEW')"
        ),
        sqlite_where=sa.text(
            "status IN ('ACCEPTED', 'SUBMITTED', 'NEED_MORE_EVIDENCE', 'REVIEW')"
        ),
    )
    op.create_index(
        "uq_submission_active_player_quest",
        "quest_submissions",
        ["player_quest_id"],
        unique=True,
        postgresql_where=sa.text("status = 'CREATED'"),
        sqlite_where=sa.text("status = 'CREATED'"),
    )
    op.create_index(
        "uq_progression_exp_per_grant",
        "progression_ledger",
        ["reward_grant_id"],
        unique=True,
        postgresql_where=sa.text("entry_type = 'EXP'"),
        sqlite_where=sa.text("entry_type = 'EXP'"),
    )
    with op.batch_alter_table("progression_ledger") as batch_op:
        batch_op.create_check_constraint(
            "ck_progression_entry_shape",
            "(entry_type = 'EXP' AND stat_name IS NULL) OR "
            "(entry_type = 'STAT' AND stat_name IS NOT NULL)",
        )


def downgrade() -> None:
    with op.batch_alter_table("progression_ledger") as batch_op:
        batch_op.drop_constraint("ck_progression_entry_shape", type_="check")
    op.drop_index("uq_progression_exp_per_grant", table_name="progression_ledger")
    op.drop_index("uq_submission_active_player_quest", table_name="quest_submissions")
    op.drop_index("uq_player_quest_active_definition", table_name="player_quests")
    with op.batch_alter_table("reward_grants") as batch_op:
        batch_op.drop_constraint("uq_reward_grants_player_quest_id", type_="unique")
        batch_op.drop_constraint("fk_reward_grants_player_quest_id", type_="foreignkey")
        batch_op.drop_column("player_quest_id")
    with op.batch_alter_table("player_quests") as batch_op:
        batch_op.drop_column("definition_snapshot")
