"""Filed response (comment) creation and retrieval."""

import sqlite3
import uuid
from typing import Annotated, Any

import structlog
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from app.apns import send_comment_push
from app.auth import enforce_signer_match, require_auth
from app.routes import error_response

_log: structlog.stdlib.BoundLogger = structlog.get_logger()

COMMENT_MAX_LENGTH = 2000

router = APIRouter()


class CommentCreateBody(BaseModel):
    """JSON body for POST /comments."""

    content_id: str
    signer: str
    body: str = Field(min_length=1, max_length=COMMENT_MAX_LENGTH)


@router.post("/comments", status_code=201)
async def create_comment(
    request: Request,
    authenticated_signer: Annotated[str, Depends(require_auth)],
    payload: CommentCreateBody,
) -> Response:
    """File a response on a letter or thought."""
    if payload.signer not in ("dinesh", "carolina"):
        msg = "Invalid signer value."
        return error_response(422, "VALIDATION_ERROR", msg)

    enforce_signer_match(authenticated_signer, payload.signer)

    db: Any = request.app.state.db

    cursor = await db.execute(
        "SELECT id, type FROM content WHERE id = ?", (payload.content_id,)
    )
    row = await cursor.fetchone()
    if row is None:
        return error_response(404, "NOT_FOUND", "Content ID does not exist.")

    content_type: str = row["type"]
    if content_type not in ("letter", "thought"):
        msg = "Comments may only be filed on letters or thoughts."
        return error_response(422, "INVALID_CONTENT_TYPE", msg)

    comment_id = str(uuid.uuid4())
    try:
        await db.execute(
            "INSERT INTO comments (id, content_id, signer, body) VALUES (?, ?, ?, ?)",
            (comment_id, payload.content_id, payload.signer, payload.body),
        )
    except sqlite3.IntegrityError:
        await db.rollback()
        msg = "A response has already been filed by this signer."
        return error_response(409, "ALREADY_COMMENTED", msg)

    await db.execute(
        "INSERT INTO sync_log (entity_type, entity_id, action) VALUES (?, ?, ?)",
        ("comment", comment_id, "create"),
    )
    await db.commit()

    cursor = await db.execute(
        "SELECT created_at FROM comments WHERE id = ?", (comment_id,)
    )
    comment_row = await cursor.fetchone()

    settings = request.app.state.settings
    push_warnings = await send_comment_push(
        settings,
        db,
        content_type=content_type,
        content_id=payload.content_id,
        commenting_signer=payload.signer,
    )
    if push_warnings:
        _log.warning("comment_push_warnings", warnings=push_warnings)

    return JSONResponse(
        status_code=201,
        content={
            "id": comment_id,
            "content_id": payload.content_id,
            "signer": payload.signer,
            "body": payload.body,
            "created_at": comment_row["created_at"],
        },
    )


@router.get("/content/{content_id}/comments")
async def get_content_comments(
    request: Request,
    content_id: str,
) -> Response:
    """Return all filed responses for a content item."""
    db: Any = request.app.state.db

    cursor = await db.execute("SELECT id FROM content WHERE id = ?", (content_id,))
    if await cursor.fetchone() is None:
        return error_response(404, "NOT_FOUND", "Content ID does not exist.")

    cursor = await db.execute(
        "SELECT id, content_id, signer, body, created_at "
        "FROM comments WHERE content_id = ? ORDER BY created_at",
        (content_id,),
    )
    rows = await cursor.fetchall()

    return JSONResponse(
        content=[
            {
                "id": row["id"],
                "content_id": row["content_id"],
                "signer": row["signer"],
                "body": row["body"],
                "created_at": row["created_at"],
            }
            for row in rows
        ],
    )
