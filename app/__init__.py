"""Exhibit A backend application factory."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from app.config import Settings
from app.db import connect
from app.models import HealthResponse


def _configure_logging(*, debug: bool) -> None:
    log_level = logging.DEBUG if debug else logging.INFO
    renderer = (
        structlog.dev.ConsoleRenderer()
        if debug
        else structlog.processors.JSONRenderer()
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = Settings()
    _configure_logging(debug=settings.debug)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        connection = await connect(settings.database_path)
        app.state.db = connection
        yield
        await connection.close()

    app = FastAPI(title="Exhibit A", lifespan=lifespan)
    app.state.settings = settings

    @app.get("/health")
    async def health() -> HealthResponse:
        return HealthResponse(status="ok")

    return app
