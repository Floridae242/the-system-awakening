import pytest

from app.config import load_settings


def test_production_requires_postgres_and_disables_demo(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.setenv("JWT_SECRET", "production-test-secret-that-is-long-and-random")
    monkeypatch.setenv("VERIFICATION_SERVICE_TOKEN", "production-verification-token-long-enough")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///unsafe.db")
    with pytest.raises(RuntimeError, match="PostgreSQL"):
        load_settings()

    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@db/awakening")
    assert load_settings().demo_mode is False
