"""App-facing API route registration."""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse


def error_response(status_code: int, code: str, message: str) -> JSONResponse:
    """Build a standard error envelope per Design Doc 7.3.2."""
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )


def build_api_router() -> APIRouter:
    """Assemble and return the app-facing API router.

    All routes under this router require Bearer authentication.
    """
    from app.auth import require_auth
    from app.routes.content import router as content_router
    from app.routes.devices import router as devices_router
    from app.routes.signatures import router as signatures_router

    api_router = APIRouter(dependencies=[Depends(require_auth)])
    api_router.include_router(content_router)
    api_router.include_router(signatures_router)
    api_router.include_router(devices_router)
    return api_router
