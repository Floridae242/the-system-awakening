import hashlib
import hmac
from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .auth_store import auth_sessions
from .config import settings
from .database import get_session
from .models import PlayerProfile

ALGORITHM = "HS256"
bearer = HTTPBearer(auto_error=False)


async def require_csrf(request: Request) -> None:
    """Double-submit CSRF guard for cookie-authenticated state changes."""
    if request.method in {"GET", "HEAD", "OPTIONS"} or not request.cookies.get("awakening_session"):
        return
    cookie = request.cookies.get("awakening_csrf")
    header = request.headers.get("X-CSRF-Token")
    if not cookie or not header or not hmac.compare_digest(cookie, header):
        raise HTTPException(status_code=403, detail="CSRF token required")


def create_access_token(user_id: str) -> str:
    expires = datetime.now(UTC) + timedelta(hours=12)
    return jwt.encode({"sub": user_id, "exp": expires}, settings.jwt_secret, algorithm=ALGORITHM)


async def current_player(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    session: AsyncSession = Depends(get_session),
) -> PlayerProfile:
    user_id: str | None = None
    session_token = request.cookies.get("awakening_session") if credentials is None else None
    if session_token:
        row = (
            await session.execute(
                select(auth_sessions.c.user_id, auth_sessions.c.expires_at).where(
                    auth_sessions.c.token_hash == hashlib.sha256(session_token.encode()).hexdigest()
                )
            )
        ).first()
        expires_at = row.expires_at if row is not None else None
        if expires_at is not None:
            # SQLite returns timezone-naive values for DateTime(timezone=True).
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=UTC)
        if row is not None and expires_at is not None and expires_at > datetime.now(UTC):
            user_id = row.user_id
    if user_id is None and credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    if user_id is None:
        try:
            payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            if not isinstance(user_id, str):
                raise JWTError("missing subject")
        except JWTError as error:
            raise HTTPException(status_code=401, detail="Invalid token") from error
    player = await session.scalar(select(PlayerProfile).where(PlayerProfile.user_id == user_id))
    if player is None:
        raise HTTPException(status_code=401, detail="Player profile not found")
    return player
