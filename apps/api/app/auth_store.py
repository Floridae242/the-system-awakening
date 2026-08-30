"""Tables used by first-party session authentication.

Kept separate from the gameplay models so the auth migration can evolve without
coupling the game aggregate to credential/session concerns.
"""

from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Table

from .database import Base


def _now() -> datetime:
    return datetime.now(UTC)


auth_credentials = Table(
    "auth_credentials",
    Base.metadata,
    Column("user_id", String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("email", String(320), unique=True, nullable=False),
    Column("password_hash", String(512), nullable=False),
    Column("created_at", DateTime(timezone=True), default=_now, nullable=False),
)

auth_sessions = Table(
    "auth_sessions",
    Base.metadata,
    Column("id", String(36), primary_key=True),
    Column("user_id", String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("token_hash", String(64), unique=True, nullable=False),
    Column("csrf_token", String(64), nullable=False),
    Column("expires_at", DateTime(timezone=True), nullable=False),
    Column("created_at", DateTime(timezone=True), default=_now, nullable=False),
    Index("ix_auth_sessions_user_id", "user_id"),
    Index("ix_auth_sessions_expires_at", "expires_at"),
)
