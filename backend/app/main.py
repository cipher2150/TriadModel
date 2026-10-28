import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import health
from app.config import Settings, get_settings
from app.db.session import build_engine


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    logging.basicConfig(level=settings.log_level.upper())

    db_engine = build_engine(settings.database_url)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        db_engine.dispose()

    app = FastAPI(title="TriadModel", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.db_engine = db_engine
    app.include_router(health.router)
    return app


app = create_app()
