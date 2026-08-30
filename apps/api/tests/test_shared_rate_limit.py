import pytest
from starlette.requests import Request

from app import rate_limit
from app.config import settings


def _request() -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/auth/login",
            "client": ("127.0.0.1", 1),
            "headers": [],
        }
    )


@pytest.mark.asyncio
async def test_shared_limiter_uses_redis(monkeypatch):
    class FakeRedis:
        def __init__(self):
            self.count = 0
            self.closed = False

        async def incr(self, _key):
            self.count += 1
            return self.count

        async def expire(self, _key, _seconds):
            return True

        async def ttl(self, _key):
            return 12

        async def aclose(self):
            self.closed = True

    fake = FakeRedis()
    monkeypatch.setattr(rate_limit, "settings", settings.__class__(**{**settings.__dict__, "redis_url": "redis://test"}))
    monkeypatch.setattr("redis.asyncio.Redis.from_url", lambda _url, decode_responses=True: fake)
    await rate_limit.enforce_shared(_request(), bucket="auth", limit=2)
    assert fake.count == 1
    assert fake.closed


@pytest.mark.asyncio
async def test_shared_limiter_falls_back_without_redis(monkeypatch):
    monkeypatch.setattr(rate_limit, "settings", settings.__class__(**{**settings.__dict__, "redis_url": ""}))
    rate_limit.limiter.clear()
    await rate_limit.enforce_shared(_request(), bucket="fallback", limit=2)
