import os
import sys
from pathlib import Path

TEST_POSTGRES_URL = os.getenv("TEST_POSTGRES_URL")
if TEST_POSTGRES_URL:
    os.environ.setdefault("DATABASE_URL", TEST_POSTGRES_URL)

TEST_DB = Path(__file__).with_name("test-awakening.db")
if not os.getenv("DATABASE_URL", "").startswith(("postgresql+asyncpg://", "postgresql://")):
    TEST_DB.unlink(missing_ok=True)

os.environ["APP_ENV"] = "test"
os.environ["DEMO_MODE"] = "true"
os.environ["JWT_SECRET"] = "test-only-secret-that-is-long-enough-for-hs256"
os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{TEST_DB}")
sys.path.insert(0, str(Path(__file__).parents[1]))
