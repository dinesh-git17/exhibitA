"""Exhibit A backend application factory."""

import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import aiosqlite
import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.auth import AuthenticationError
from app.config import Settings
from app.db import checkpoint, connect
from app.models import HealthResponse
from app.routes import build_api_router
from app.routes.admin import configure_templates
from app.routes.admin import router as admin_router

_WAL_CHECKPOINT_INTERVAL_SECONDS = 300


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


async def _wal_checkpoint_loop(db: aiosqlite.Connection) -> None:
    """Periodically run passive WAL checkpoints to prevent unbounded growth.

    Litestream holds a read lock that prevents SQLite auto-checkpoints.
    When Litestream's own TRUNCATE checkpoint fails to acquire an exclusive
    lock, the WAL grows without bound. This loop runs PASSIVE checkpoints
    that transfer pages without requiring exclusive access.
    """
    log = structlog.get_logger()
    while True:
        await asyncio.sleep(_WAL_CHECKPOINT_INTERVAL_SECONDS)
        try:
            await checkpoint(db)
        except Exception:
            log.warning("wal_checkpoint_failed", exc_info=True)


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = Settings()
    _configure_logging(debug=settings.debug)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        connection = await connect(settings.database_path)
        app.state.db = connection
        checkpoint_task = asyncio.create_task(_wal_checkpoint_loop(connection))
        yield
        checkpoint_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await checkpoint_task
        await connection.close()

    app = FastAPI(title="Exhibit A", lifespan=lifespan)
    app.state.settings = settings

    @app.exception_handler(AuthenticationError)
    async def auth_error_handler(
        _request: Request, exc: AuthenticationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": str(exc),
                }
            },
        )

    app.include_router(build_api_router())

    static_dir = Path(__file__).resolve().parent / "static"
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    templates_dir = Path(__file__).resolve().parent / "templates"
    templates = Jinja2Templates(directory=str(templates_dir))
    configure_templates(templates)
    app.include_router(admin_router)

    @app.get("/health")
    async def health() -> HealthResponse:
        return HealthResponse(status="ok")

    return app
