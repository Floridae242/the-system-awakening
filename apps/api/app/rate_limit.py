"""Small, bounded in-process rate limiter for the single-node MVP.

The limiter deliberately keys on the direct peer address. Deployments behind a
trusted proxy should replace ``client_key`` with the proxy's authenticated
client identity and use a shared store (for example Redis).
"""

from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import HTTPException, Request


class RateLimiter:
    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str, *, limit: int, window_seconds: float) -> tuple[bool, int]:
        now = monotonic()
        with self._lock:
            events = self._events[key]
            cutoff = now - window_seconds
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= limit:
                retry_after = max(1, int(events[0] + window_seconds - now + 0.999))
                return False, retry_after
            events.append(now)
            return True, 0

    def clear(self) -> None:
        with self._lock:
            self._events.clear()


limiter = RateLimiter()


def client_key(request: Request) -> str:
    host = request.client.host if request.client else "unknown"
    return host[:128]


def enforce(request: Request, *, bucket: str, limit: int, window_seconds: float = 60) -> None:
    allowed, retry_after = limiter.allow(f"{bucket}:{client_key(request)}", limit=limit, window_seconds=window_seconds)
    if not allowed:
        error = HTTPException(status_code=429, detail="Too many requests")
        error.headers = {"Retry-After": str(retry_after)}
        raise error


def api_rate_limit(request: Request) -> None:
    """Apply a conservative limit to state-changing API requests."""
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        enforce(request, bucket="api", limit=120)
