import json
import os
import sqlite3
import subprocess
from pathlib import Path


def alembic(repo: Path, database_url: str, *arguments: str) -> subprocess.CompletedProcess[str]:
    environment = {
        **os.environ,
        "APP_ENV": "test",
        "DEMO_MODE": "true",
        "JWT_SECRET": "migration-test-secret-that-is-long-enough",
        "DATABASE_URL": database_url,
    }
    return subprocess.run(
        [
            str(repo / "apps/api/.venv/bin/alembic"),
            "-c",
            str(repo / "alembic.ini"),
            *arguments,
        ],
        cwd=repo,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )


def test_migrations_backfill_pinned_rules_and_exactly_once_key(tmp_path):
    repo = Path(__file__).parents[3]
    database = tmp_path / "migration.db"
    database_url = f"sqlite+aiosqlite:///{database}"
    alembic(repo, database_url, "upgrade", "9f2a1c4b7d10")

    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            INSERT INTO quest_definitions
                (id, version, title, category, difficulty, primary_stat, objective,
                 verification_policy, active, reward_profile)
            VALUES ('quest_focus_001', 1, 'Old Focus', 'study', 'NORMAL', 'INT', ?, ?, 1, 'normal_v1')
            """,
            (json.dumps({"type": "duration_minutes", "target": 15}), json.dumps({"accepted_evidence": ["manual"]})),
        )
        connection.execute(
            """
            INSERT INTO quest_definitions
                (id, version, title, category, difficulty, primary_stat, objective,
                 verification_policy, active, reward_profile)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "quest_migration_001",
                3,
                "Pinned Migration Quest",
                "study",
                "HARD",
                "INT",
                json.dumps({"type": "duration_minutes", "target": 20}),
                json.dumps({"accepted_evidence": ["manual"]}),
                1,
                "hard_v1",
            ),
        )
        connection.execute(
            "INSERT INTO users (id, auth_provider_id, created_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
            ("user-migration", "demo:migration"),
        )
        connection.execute(
            """
            INSERT INTO player_profiles
                (id, user_id, display_name, level, current_xp, str_stat, agi, vit,
                 int_stat, wil, streak_days, created_at)
            VALUES (?, ?, ?, 1, 0, 10, 10, 10, 10, 10, 0, CURRENT_TIMESTAMP)
            """,
            ("player-migration", "user-migration", "Migration Hunter"),
        )
        connection.execute(
            """
            INSERT INTO player_quests
                (id, player_id, quest_definition_id, quest_definition_version, status, accepted_at)
            VALUES ('old-player-quest', 'player-migration', 'quest_focus_001', 1, 'ACCEPTED', CURRENT_TIMESTAMP)
            """
        )
        connection.execute(
            """
            INSERT INTO player_quests
                (id, player_id, quest_definition_id, quest_definition_version, status, accepted_at)
            VALUES (?, ?, ?, 3, 'SUBMITTED', CURRENT_TIMESTAMP)
            """,
            ("player-quest-migration", "player-migration", "quest_migration_001"),
        )
        connection.execute(
            """
            INSERT INTO quest_submissions
                (id, player_quest_id, player_id, idempotency_key, request_hash,
                 evidence_type, manual_evidence, status, created_at)
            VALUES (?, ?, ?, ?, ?, 'manual', ?, 'DECIDED', CURRENT_TIMESTAMP)
            """,
            (
                "submission-migration",
                "player-quest-migration",
                "player-migration",
                "migration-key",
                "0" * 64,
                json.dumps({"duration_minutes": 20}),
            ),
        )
        connection.execute(
            """
            INSERT INTO reward_grants
                (id, player_id, submission_id, rules_version, exp_granted, stat_changes, created_at)
            VALUES (?, ?, ?, '1.0.0', 1, ?, CURRENT_TIMESTAMP)
            """,
            (
                "reward-migration",
                "player-migration",
                "submission-migration",
                json.dumps({"INT": 1}),
            ),
        )

    alembic(repo, database_url, "upgrade", "head")
    alembic(repo, database_url, "check")

    with sqlite3.connect(database) as connection:
        snapshot_json = connection.execute(
            "SELECT definition_snapshot FROM player_quests WHERE id = ?",
            ("player-quest-migration",),
        ).fetchone()[0]
        reward_player_quest = connection.execute(
            "SELECT player_quest_id FROM reward_grants WHERE id = ?",
            ("reward-migration",),
        ).fetchone()[0]

        snapshot = json.loads(snapshot_json)
    assert snapshot["definition_id"] == "quest_migration_001"
    assert snapshot["version"] == 3
    assert snapshot["objective"] == {"type": "duration_minutes", "target": 20}
    assert reward_player_quest == "player-quest-migration"

    with sqlite3.connect(database) as connection:
        promoted = json.loads(
            connection.execute(
                "SELECT objective FROM quest_definitions WHERE id = 'quest_focus_001'"
            ).fetchone()[0]
        )
        old_snapshot = json.loads(
            connection.execute(
                "SELECT definition_snapshot FROM player_quests WHERE id = 'old-player-quest'"
            ).fetchone()[0]
        )
    assert promoted == {"type": "duration_minutes", "target": 30}
    assert old_snapshot["objective"] == {"type": "duration_minutes", "target": 15}
