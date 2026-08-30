from app.auth_routes import _password_hash, _password_verify
from app.rate_limit import RateLimiter


def test_password_hash_is_salted_and_verifies_without_plaintext():
    first = _password_hash("correct horse battery staple")
    second = _password_hash("correct horse battery staple")
    assert first != second
    assert "correct horse" not in first
    assert _password_verify("correct horse battery staple", first)
    assert not _password_verify("wrong password", first)


def test_password_verify_rejects_malformed_hash():
    assert not _password_verify("anything", "not-a-scrypt-hash")


def test_rate_limiter_returns_retry_after_and_expires(monkeypatch):
    clock = iter([100.0, 100.1, 100.2, 161.0])
    monkeypatch.setattr("app.rate_limit.monotonic", lambda: next(clock))
    limiter = RateLimiter()
    assert limiter.allow("ip", limit=2, window_seconds=60) == (True, 0)
    assert limiter.allow("ip", limit=2, window_seconds=60) == (True, 0)
    allowed, retry_after = limiter.allow("ip", limit=2, window_seconds=60)
    assert not allowed
    assert retry_after >= 1
    assert limiter.allow("ip", limit=2, window_seconds=60) == (True, 0)
