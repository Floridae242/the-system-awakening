from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .database import get_session
from .models import PlayerProfile

ALGORITHM = "HS256"
bearer = HTTPBearer(auto_error=False)


def create_access_token(user_id: str) -> str:
    expires = datetime.now(UTC) + timedelta(hours=12)
    return jwt.encode({"sub": user_id, "exp": expires}, settings.jwt_secret, algorithm=ALGORITHM)


async def current_player(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    session: AsyncSession = Depends(get_session),
) -> PlayerProfile:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required")
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
