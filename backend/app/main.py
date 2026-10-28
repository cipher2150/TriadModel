import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from app.api import calculate, health, models
from app.api.errors import register_error_handlers
from app.api.middleware import (
    BodySizeLimitMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
)
from app.api.static import mount_frontend
from app.config import Settings, get_settings
from app.db.session import build_engine, build_session_factory


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    logging.basicConfig(level=settings.log_level.upper())

    db_engine = build_engine(settings.database_url)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        db_engine.dispose()

    production = settings.app_env == "production"
    app = FastAPI(
        title="TriadModel",
        version="0.1.0",
        lifespan=lifespan,
        docs_url=None if production else "/docs",
        redoc_url=None,
        openapi_url=None if production else "/openapi.json",
    )
    register_error_handlers(app)
    app.add_middleware(SecurityHeadersMiddleware, hsts=production)
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=settings.max_request_bytes)
    app.add_middleware(RateLimitMiddleware, per_minute=settings.rate_limit_per_minute)
    app.state.settings = settings
    app.state.db_engine = db_engine
    app.state.session_factory = build_session_factory(db_engine)
    app.include_router(health.router)
    app.include_router(calculate.router)
    app.include_router(models.router)
    if not mount_frontend(app, Path(settings.static_dir)):
        logging.getLogger(__name__).info(
            "No frontend build at %s; serving API only", settings.static_dir
        )
    return app


app = create_app()
