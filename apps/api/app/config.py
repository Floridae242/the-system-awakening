import os
from dataclasses import dataclass


def _bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name, str(default)).lower()
    if value not in {"true", "false"}:
        raise RuntimeError(f"{name} must be true or false")
    return value == "true"


@dataclass(frozen=True)
class Settings:
    app_env: str
    database_url: str
    jwt_secret: str
    demo_mode: bool
    cors_origins: tuple[str, ...]
    verification_token: str
    redis_url: str = ""


def load_settings() -> Settings:
    app_env = os.getenv("APP_ENV", "development")
    jwt_secret = os.getenv("JWT_SECRET", "development-only-change-before-production")
    demo_mode = _bool("DEMO_MODE", app_env != "production")
    database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./awakening-dev.db")
    verification_token = os.getenv("VERIFICATION_SERVICE_TOKEN", "")
    redis_url = os.getenv("REDIS_URL", "")
    if app_env == "production":
        if demo_mode or jwt_secret.startswith("development-only") or len(jwt_secret) < 32:
            raise RuntimeError("Production requires DEMO_MODE=false and a private JWT_SECRET")
        if not database_url.startswith(("postgresql+asyncpg://", "postgresql://")):
            raise RuntimeError("Production requires PostgreSQL as authoritative storage")
        if len(verification_token) < 32:
            raise RuntimeError("Production requires a private VERIFICATION_SERVICE_TOKEN")
    configured_origins = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    )
    origins = tuple(origin.strip() for origin in configured_origins.split(",") if origin.strip())
    return Settings(
        app_env=app_env,
        database_url=database_url,
        jwt_secret=jwt_secret,
        demo_mode=demo_mode,
        cors_origins=origins,
        verification_token=verification_token,
        redis_url=redis_url,
    )


settings = load_settings()
