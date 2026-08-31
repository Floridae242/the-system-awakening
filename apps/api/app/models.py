from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def new_id() -> str:
    return str(uuid4())


def now() -> datetime:
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    auth_provider_id: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class PlayerProfile(Base):
    __tablename__ = "player_profiles"
    __table_args__ = (
        CheckConstraint("level >= 1"),
        CheckConstraint("current_xp >= 0"),
        CheckConstraint("str_stat >= 0 AND agi >= 0 AND vit >= 0 AND int_stat >= 0 AND wil >= 0"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(80))
    level: Mapped[int] = mapped_column(Integer, default=1)
    current_xp: Mapped[int] = mapped_column(Integer, default=0)
    str_stat: Mapped[int] = mapped_column(Integer, default=10)
    agi: Mapped[int] = mapped_column(Integer, default=10)
    vit: Mapped[int] = mapped_column(Integer, default=10)
    int_stat: Mapped[int] = mapped_column(Integer, default=10)
    wil: Mapped[int] = mapped_column(Integer, default=10)
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class QuestDefinition(Base):
    __tablename__ = "quest_definitions"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    title: Mapped[str] = mapped_column(String(160))
    category: Mapped[str] = mapped_column(String(40))
    difficulty: Mapped[str] = mapped_column(String(20))
    primary_stat: Mapped[str] = mapped_column(String(3))
    objective: Mapped[dict] = mapped_column(JSON)
    verification_policy: Mapped[dict] = mapped_column(JSON)
    reward_profile: Mapped[str] = mapped_column(String(40))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class PlayerQuest(Base):
    __tablename__ = "player_quests"
    __table_args__ = (
        Index(
            "uq_player_quest_active_definition",
            "player_id",
            "quest_definition_id",
            unique=True,
            postgresql_where=text("status IN ('ACCEPTED', 'SUBMITTED', 'NEED_MORE_EVIDENCE', 'REVIEW')"),
            sqlite_where=text("status IN ('ACCEPTED', 'SUBMITTED', 'NEED_MORE_EVIDENCE', 'REVIEW')"),
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    player_id: Mapped[str] = mapped_column(ForeignKey("player_profiles.id"), index=True)
    quest_definition_id: Mapped[str] = mapped_column(ForeignKey("quest_definitions.id"))
    quest_definition_version: Mapped[int] = mapped_column(Integer)
    definition_snapshot: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(30), default="ACCEPTED")
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Submission(Base):
    __tablename__ = "quest_submissions"
    __table_args__ = (
        UniqueConstraint("player_id", "idempotency_key"),
        Index(
            "uq_submission_active_player_quest",
            "player_quest_id",
            unique=True,
            postgresql_where=text("status = 'CREATED'"),
            sqlite_where=text("status = 'CREATED'"),
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    player_quest_id: Mapped[str] = mapped_column(ForeignKey("player_quests.id"), index=True)
    player_id: Mapped[str] = mapped_column(ForeignKey("player_profiles.id"), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(128))
    request_hash: Mapped[str] = mapped_column(String(64))
    evidence_type: Mapped[str] = mapped_column(String(20))
    manual_evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="CREATED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class VerificationResult(Base):
    __tablename__ = "verification_results"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    submission_id: Mapped[str] = mapped_column(ForeignKey("quest_submissions.id"), unique=True)
    decision: Mapped[str] = mapped_column(String(30))
    extracted_facts: Mapped[dict] = mapped_column(JSON, default=dict)
    reason_code: Mapped[str] = mapped_column(String(80))
    schema_version: Mapped[str] = mapped_column(String(50), default="verification-observation-v1")
    fallback_used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class RewardGrant(Base):
    __tablename__ = "reward_grants"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    player_id: Mapped[str] = mapped_column(ForeignKey("player_profiles.id"), index=True)
    player_quest_id: Mapped[str] = mapped_column(ForeignKey("player_quests.id"), unique=True)
    submission_id: Mapped[str] = mapped_column(ForeignKey("quest_submissions.id"), unique=True)
    rules_version: Mapped[str] = mapped_column(String(30), default="1.0.0")
    exp_granted: Mapped[int] = mapped_column(Integer)
    stat_changes: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class ProgressionLedger(Base):
    __tablename__ = "progression_ledger"
    __table_args__ = (
        CheckConstraint(
            "(entry_type = 'EXP' AND stat_name IS NULL) OR "
            "(entry_type = 'STAT' AND stat_name IS NOT NULL)",
            name="ck_progression_entry_shape",
        ),
        UniqueConstraint("reward_grant_id", "entry_type", "stat_name"),
        Index(
            "uq_progression_exp_per_grant",
            "reward_grant_id",
            unique=True,
            postgresql_where=text("entry_type = 'EXP'"),
            sqlite_where=text("entry_type = 'EXP'"),
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    player_id: Mapped[str] = mapped_column(ForeignKey("player_profiles.id"), index=True)
    reward_grant_id: Mapped[str] = mapped_column(ForeignKey("reward_grants.id"))
    entry_type: Mapped[str] = mapped_column(String(20))
    stat_name: Mapped[str | None] = mapped_column(String(3), nullable=True)
    amount: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Chest(Base):
    __tablename__ = "chests"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    player_id: Mapped[str] = mapped_column(ForeignKey("player_profiles.id"), index=True)
    reward_grant_id: Mapped[str] = mapped_column(ForeignKey("reward_grants.id"), unique=True)
    rarity: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="UNOPENED")
    rng_version: Mapped[str] = mapped_column(String(30), default="secure-v1")
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ItemDefinition(Base):
    __tablename__ = "item_definitions"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    name: Mapped[str] = mapped_column(String(120))
    rarity: Mapped[str] = mapped_column(String(20), index=True)
    item_type: Mapped[str] = mapped_column(String(40))
    power: Mapped[int] = mapped_column(Integer, default=0)


class InventoryItem(Base):
    __tablename__ = "inventory_items"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    player_id: Mapped[str] = mapped_column(ForeignKey("player_profiles.id"), index=True)
    item_definition_id: Mapped[str] = mapped_column(ForeignKey("item_definitions.id"))
    item_definition_version: Mapped[int] = mapped_column(Integer)
    source_chest_id: Mapped[str] = mapped_column(ForeignKey("chests.id"), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class ChestOpenResult(Base):
    __tablename__ = "chest_open_results"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    chest_id: Mapped[str] = mapped_column(ForeignKey("chests.id"), unique=True)
    item_instance_id: Mapped[str] = mapped_column(ForeignKey("inventory_items.id"), unique=True)
    rng_metadata: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"
    __table_args__ = (UniqueConstraint("actor_id", "scope", "key"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    actor_id: Mapped[str] = mapped_column(String(36), index=True)
    scope: Mapped[str] = mapped_column(String(40))
    key: Mapped[str] = mapped_column(String(128))
    request_hash: Mapped[str] = mapped_column(String(64))
    resource_id: Mapped[str] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = (Index("ix_audit_events_player_created", "player_id", "created_at"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    event_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    player_id: Mapped[str | None] = mapped_column(ForeignKey("player_profiles.id"), nullable=True, index=True)
    correlation_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    causation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AchievementUnlock(Base):
    __tablename__ = "achievement_unlocks"
    __table_args__ = (UniqueConstraint("player_id", "code", name="uq_achievement_player_code"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    player_id: Mapped[str] = mapped_column(ForeignKey("player_profiles.id"), index=True, nullable=False)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    unlocked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
