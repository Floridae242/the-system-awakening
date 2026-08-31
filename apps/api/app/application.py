import asyncio
import secrets
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from .auth_routes import router as auth_router
from .config import settings
from .database import Base, SessionFactory, engine
from .rate_limit import api_rate_limit_shared
from .routes import router
from .seed import seed_content
from .upload_routes import router as upload_router
from .verification_worker import router as verification_router
from .verification_worker import run_worker_loop


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.app_env in {"development", "test"}:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
    if settings.app_env != "production":
        async with SessionFactory() as session:
            await seed_content(session)
    worker_stop = asyncio.Event()
    worker_task = None
    if settings.app_env == "production":
        worker_task = asyncio.create_task(run_worker_loop(worker_stop))
    try:
        yield
    finally:
        if worker_task is not None:
            worker_stop.set()
            worker_task.cancel()
            with suppress(asyncio.CancelledError):
                await worker_task


def create_app() -> FastAPI:
    app = FastAPI(
        title="The System — Awakening API",
        version="0.1.0",
        description="Real action → proof → verification → deterministic progression",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-CSRF-Token"],
    )

    @app.middleware("http")
    async def enforce_http_boundaries(request: Request, call_next) -> Response:
        await api_rate_limit_shared(request)
        # Browser session authentication uses a double-submit CSRF token.
        # Login/register are exempt because they establish the session.
        if (
            request.method in {"POST", "PUT", "PATCH", "DELETE"}
            and request.cookies.get("awakening_session")
            and not request.headers.get("authorization")
            and "/internal/" not in request.url.path
        ):
            if not request.url.path.endswith(("/auth/login", "/auth/register", "/auth/demo")):
                csrf_cookie = request.cookies.get("awakening_csrf")
                csrf_header = request.headers.get("X-CSRF-Token")
                if not csrf_cookie or not csrf_header or not secrets.compare_digest(csrf_cookie, csrf_header):
                    return Response(content="CSRF validation failed", status_code=403)
        content_type = request.headers.get("content-type", "")
        max_body = 8 * 1024 * 1024 + 16_384 if content_type.startswith("multipart/form-data") else 16_384
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > max_body:
                    response = Response(content="Request body too large", status_code=413)
                    response.headers["X-Content-Type-Options"] = "nosniff"
                    response.headers["X-Frame-Options"] = "DENY"
                    response.headers["Referrer-Policy"] = "no-referrer"
                    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
                    response.headers["Content-Security-Policy"] = (
                        "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
                    )
                    return response
            except ValueError:
                pass
            else:
                response = await call_next(request)
                response.headers["X-Content-Type-Options"] = "nosniff"
                response.headers["X-Frame-Options"] = "DENY"
                response.headers["Referrer-Policy"] = "no-referrer"
                response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
                response.headers["Content-Security-Policy"] = (
                    "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
                )
                return response
        chunks: list[bytes] = []
        total = 0
        async for chunk in request.stream():
            total += len(chunk)
            if total > max_body:
                response = Response(content="Request body too large", status_code=413)
                break
            chunks.append(chunk)
        else:
            body = b"".join(chunks)

            request._body = body
            response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
        return response

    app.include_router(router)
    app.include_router(auth_router)
    app.include_router(upload_router)
    app.include_router(verification_router)
    return app
