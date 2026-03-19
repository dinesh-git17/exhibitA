"""Filing creation, retrieval, and ruling endpoints."""

import uuid
from typing import Annotated, Any

import structlog
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from app.apns import send_filing_push, send_ruling_push
from app.auth import enforce_signer_match, require_auth
from app.models import FilingType, RulingVerdict, SyncAction
from app.routes import error_response

_log: structlog.stdlib.BoundLogger = structlog.get_logger()

FILING_BODY_MAX_LENGTH = 2000
RULING_REASON_MAX_LENGTH = 2000

router = APIRouter()


class FilingCreateBody(BaseModel):
    """JSON body for POST /filings."""

    filing_type: str
    filed_by: str
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=FILING_BODY_MAX_LENGTH)


class RulingCreateBody(BaseModel):
    """JSON body for POST /filings/{id}/ruling."""

    ruling: str
    ruling_reason: str = Field(min_length=1, max_length=RULING_REASON_MAX_LENGTH)
    ruled_by: str


def _row_to_filing(row: Any) -> dict[str, Any]:
    return {
        "id": row["id"],
        "filing_type": row["filing_type"],
        "filed_by": row["filed_by"],
        "title": row["title"],
        "body": row["body"],
        "ruling": row["ruling"],
        "ruling_reason": row["ruling_reason"],
        "ruled_by": row["ruled_by"],
        "ruled_at": row["ruled_at"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


@router.post("/filings", status_code=201)
async def create_filing(
    request: Request,
    authenticated_signer: Annotated[str, Depends(require_auth)],
    payload: FilingCreateBody,
) -> Response:
    """File a new motion, objection, or emergency order."""
    valid_types = {t.value for t in FilingType}
    if payload.filing_type not in valid_types:
        msg = f"Invalid filing_type. Must be one of: {', '.join(sorted(valid_types))}."
        return error_response(422, "VALIDATION_ERROR", msg)

    if payload.filed_by not in ("dinesh", "carolina"):
        msg = "Invalid filed_by value."
        return error_response(422, "VALIDATION_ERROR", msg)

    enforce_signer_match(authenticated_signer, payload.filed_by)

    db: Any = request.app.state.db
    filing_id = str(uuid.uuid4())

    await db.execute(
        "INSERT INTO filings (id, filing_type, filed_by, title, body) "
        "VALUES (?, ?, ?, ?, ?)",
        (filing_id, payload.filing_type, payload.filed_by, payload.title, payload.body),
    )
    await db.execute(
        "INSERT INTO sync_log (entity_type, entity_id, action) VALUES (?, ?, ?)",
        ("filing", filing_id, SyncAction.CREATE),
    )
    await db.commit()

    cursor = await db.execute("SELECT * FROM filings WHERE id = ?", (filing_id,))
    row = await cursor.fetchone()

    settings = request.app.state.settings
    push_warnings = await send_filing_push(
        settings,
        db,
        filing_type=payload.filing_type,
        filing_id=filing_id,
        filing_signer=payload.filed_by,
    )
    if push_warnings:
        _log.warning("filing_push_warnings", warnings=push_warnings)

    return JSONResponse(status_code=201, content=_row_to_filing(row))


@router.get("/filings")
async def list_filings(request: Request) -> JSONResponse:
    """List all filings ordered by creation date descending."""
    db: Any = request.app.state.db
    cursor = await db.execute("SELECT * FROM filings ORDER BY created_at DESC")
    rows = await cursor.fetchall()
    return JSONResponse(content={"items": [_row_to_filing(row) for row in rows]})


@router.get("/filings/{filing_id}")
async def get_filing(request: Request, filing_id: str) -> Response:
    """Retrieve a single filing by ID."""
    db: Any = request.app.state.db
    cursor = await db.execute("SELECT * FROM filings WHERE id = ?", (filing_id,))
    row = await cursor.fetchone()
    if row is None:
        return error_response(404, "NOT_FOUND", "Filing ID does not exist.")
    return JSONResponse(content=_row_to_filing(row))


@router.post("/filings/{filing_id}/ruling")
async def create_ruling(
    request: Request,
    filing_id: str,
    authenticated_signer: Annotated[str, Depends(require_auth)],
    payload: RulingCreateBody,
) -> Response:
    """Issue a ruling on a filing."""
    valid_verdicts = {v.value for v in RulingVerdict}
    if payload.ruling not in valid_verdicts:
        msg = f"Invalid ruling. Must be one of: {', '.join(sorted(valid_verdicts))}."
        return error_response(422, "VALIDATION_ERROR", msg)

    if payload.ruled_by not in ("dinesh", "carolina"):
        msg = "Invalid ruled_by value."
        return error_response(422, "VALIDATION_ERROR", msg)

    enforce_signer_match(authenticated_signer, payload.ruled_by)

    db: Any = request.app.state.db

    cursor = await db.execute("SELECT * FROM filings WHERE id = ?", (filing_id,))
    row = await cursor.fetchone()
    if row is None:
        return error_response(404, "NOT_FOUND", "Filing ID does not exist.")

    if row["ruling"] is not None:
        msg = "A ruling has already been issued on this filing."
        return error_response(409, "ALREADY_RULED", msg)

    if row["filed_by"] == payload.ruled_by:
        msg = "The filer cannot rule on their own filing."
        return error_response(422, "SELF_RULING", msg)

    await db.execute(
        "UPDATE filings SET ruling = ?, ruling_reason = ?, ruled_by = ?, "
        "ruled_at = datetime('now'), updated_at = datetime('now') WHERE id = ?",
        (payload.ruling, payload.ruling_reason, payload.ruled_by, filing_id),
    )
    await db.execute(
        "INSERT INTO sync_log (entity_type, entity_id, action) VALUES (?, ?, ?)",
        ("filing", filing_id, SyncAction.UPDATE),
    )
    await db.commit()

    cursor = await db.execute("SELECT * FROM filings WHERE id = ?", (filing_id,))
    updated_row = await cursor.fetchone()

    settings = request.app.state.settings
    push_warnings = await send_ruling_push(
        settings,
        db,
        filing_type=row["filing_type"],
        filing_id=filing_id,
        ruling=payload.ruling,
        ruling_signer=payload.ruled_by,
    )
    if push_warnings:
        _log.warning("ruling_push_warnings", warnings=push_warnings)

    return JSONResponse(content=_row_to_filing(updated_row))
