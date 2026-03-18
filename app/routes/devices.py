"""Sync delta retrieval and device-token registration per Design Doc 7.3."""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.routes import error_response

router = APIRouter()


class DeviceTokenRequest(BaseModel):
    """POST /device-tokens request body."""

    signer: str
    token: str


@router.get("/sync")
async def get_sync(
    request: Request,
    since: Annotated[str | None, Query()] = None,
) -> JSONResponse:
    """Return sync log entries, optionally filtered after a timestamp."""
    db = request.app.state.db

    if since is not None:
        normalized = since.replace("T", " ").rstrip("Z")
        cursor = await db.execute(
            "SELECT id, entity_type, entity_id, action, occurred_at "
            "FROM sync_log WHERE occurred_at > ? ORDER BY occurred_at ASC",
            (normalized,),
        )
    else:
        cursor = await db.execute(
            "SELECT id, entity_type, entity_id, action, occurred_at "
            "FROM sync_log ORDER BY occurred_at ASC"
        )

    rows = await cursor.fetchall()
    return JSONResponse(
        content={
            "changes": [
                {
                    "id": row["id"],
                    "entity_type": row["entity_type"],
                    "entity_id": row["entity_id"],
                    "action": row["action"],
                    "occurred_at": row["occurred_at"],
                }
                for row in rows
            ]
        }
    )


@router.post("/device-tokens", status_code=201)
async def register_device_token(
    request: Request,
    body: DeviceTokenRequest,
) -> JSONResponse:
    """Register or update an APNS device token for a signer."""
    if body.signer not in ("dinesh", "carolina"):
        msg = "Invalid signer value."
        return error_response(422, "VALIDATION_ERROR", msg)

    db: Any = request.app.state.db
    token_id = str(uuid.uuid4())

    await db.execute(
        "DELETE FROM device_tokens WHERE signer = ? AND token != ?",
        (body.signer, body.token),
    )
    await db.execute(
        "INSERT INTO device_tokens (id, signer, token) "
        "VALUES (?, ?, ?) "
        "ON CONFLICT(token) DO UPDATE SET "
        "signer = excluded.signer, registered_at = datetime('now')",
        (token_id, body.signer, body.token),
    )
    await db.commit()

    cursor = await db.execute(
        "SELECT id, signer, token, registered_at FROM device_tokens WHERE token = ?",
        (body.token,),
    )
    row = await cursor.fetchone()

    return JSONResponse(
        status_code=201,
        content={
            "id": row["id"],
            "signer": row["signer"],
            "token": row["token"],
            "registered_at": row["registered_at"],
        },
    )
