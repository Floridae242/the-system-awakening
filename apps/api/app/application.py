from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import Base, SessionFactory, engine
from .routes import router
from .seed import seed_content


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.app_env in {"development", "test"}:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
    async with SessionFactory() as session:
        await seed_content(session)
    yield


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
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
    )
    app.include_router(router)
    return app
