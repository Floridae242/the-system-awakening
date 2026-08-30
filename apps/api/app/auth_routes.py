"""First-party email/password auth with server-side HttpOnly sessions."""

import base64
import hashlib
import hmac
import re
import secrets
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import current_player
from .auth_store import auth_credentials, auth_sessions
from .config import settings
from .database import get_session
from .models import PlayerProfile, User
from .rate_limit import enforce_shared

router = APIRouter(prefix="/api/v1/auth")
SESSION_COOKIE = "awakening_session"
CSRF_COOKIE = "awakening_csrf"
SESSION_TTL = timedelta(hours=12)
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def envelope(data: object) -> dict:
    return {"success": True, "data": data}


def player_data(player: PlayerProfile) -> dict:
    return {
        "id": player.id,
        "display_name": player.display_name,
        "level": player.level,
        "current_xp": player.current_xp,
        "stats": {
            "str": player.str_stat,
            "agi": player.agi,
            "vit": player.vit,
            "int": player.int_stat,
            "wil": player.wil,
        },
    }


class Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=5, max_length=320)
    password: str = Field(min_length=12, max_length=128)
    display_name: str | None = Field(default=None, min_length=3, max_length=80)


def _password_hash(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return "scrypt$16384$8$1$" + base64.urlsafe_b64encode(salt + digest).decode()


def _password_verify(password: str, encoded: str) -> bool:
    try:
        prefix, n, r, p, raw = encoded.split("$", 4)
        if prefix != "scrypt":
            return False
        packed = base64.urlsafe_b64decode(raw.encode())
        salt, expected = packed[:16], packed[16:]
        actual = hashlib.scrypt(password.encode(), salt=salt, n=int(n), r=int(r), p=int(p))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def _email(value: str) -> str:
    normalized = value.strip().lower()
    if not EMAIL_RE.fullmatch(normalized):
        raise HTTPException(status_code=422, detail="Valid email is required")
    return normalized


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _set_cookies(response: Response, session_token: str, csrf: str) -> None:
    secure = settings.app_env == "production"
    response.set_cookie(
        SESSION_COOKIE,
        session_token,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=int(SESSION_TTL.total_seconds()),
        path="/",
    )
    response.set_cookie(
        CSRF_COOKIE,
        csrf,
        httponly=False,
        secure=secure,
        samesite="lax",
        max_age=int(SESSION_TTL.total_seconds()),
        path="/",
    )


@router.post("/register", status_code=201)
async def register(
    request: Request, response: Response, body: Credentials, session: AsyncSession = Depends(get_session)
) -> dict:
    await enforce_shared(request, bucket="auth", limit=8)
    email = _email(body.email)
    exists = await session.scalar(select(auth_credentials.c.user_id).where(auth_credentials.c.email == email))
    if exists:
        raise HTTPException(status_code=409, detail="Account already exists")
    user = User(auth_provider_id=f"password:{email}")
    session.add(user)
    await session.flush()
    profile = PlayerProfile(user_id=user.id, display_name=body.display_name or email.split("@", 1)[0])
    session.add(profile)
    await session.flush()
    await session.execute(
        auth_credentials.insert().values(user_id=user.id, email=email, password_hash=_password_hash(body.password))
    )
    token, csrf = await _create_session(session, user.id)
    await session.commit()
    _set_cookies(response, token, csrf)
    return envelope({"player": player_data(profile), "csrf_token": csrf})


@router.post("/login")
async def login(
    request: Request, response: Response, body: Credentials, session: AsyncSession = Depends(get_session)
) -> dict:
    await enforce_shared(request, bucket="auth", limit=8)
    email = _email(body.email)
    credential = await session.execute(select(auth_credentials).where(auth_credentials.c.email == email))
    row = credential.mappings().first()
    if row is None or not _password_verify(body.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    player = await session.scalar(select(PlayerProfile).where(PlayerProfile.user_id == row["user_id"]))
    if player is None:
        raise HTTPException(status_code=401, detail="Account profile unavailable")
    token, csrf = await _create_session(session, row["user_id"])
    await session.commit()
    _set_cookies(response, token, csrf)
    return envelope({"player": player_data(player), "csrf_token": csrf})


@router.get("/me")
async def me(player: PlayerProfile = Depends(current_player)) -> dict:
    return envelope({"player": player_data(player)})


@router.post("/logout")
async def logout(request: Request, response: Response, session: AsyncSession = Depends(get_session)) -> dict:
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        await session.execute(auth_sessions.delete().where(auth_sessions.c.token_hash == _token_hash(token)))
        await session.commit()
    response.delete_cookie(SESSION_COOKIE, path="/")
    response.delete_cookie(CSRF_COOKIE, path="/")
    return envelope({"logged_out": True})


async def _create_session(session: AsyncSession, user_id: str) -> tuple[str, str]:
    raw = secrets.token_urlsafe(48)
    csrf = secrets.token_urlsafe(32)
    await session.execute(
        auth_sessions.insert().values(
            id=str(uuid4()),
            user_id=user_id,
            token_hash=_token_hash(raw),
            csrf_token=csrf,
            expires_at=datetime.now(UTC) + SESSION_TTL,
        )
    )
    return raw, csrf


async def establish_session(session: AsyncSession, user_id: str, response: Response) -> str:
    """Issue a browser session for legacy/demo login handlers too."""
    token, csrf = await _create_session(session, user_id)
    _set_cookies(response, token, csrf)
    return csrf
