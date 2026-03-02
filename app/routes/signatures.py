"""Signature image retrieval and multipart upload per Design Doc 7.3."""

import sqlite3
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse, Response

from app.routes import error_response

SIGNATURE_MAX_BYTES = 1_048_576  # 1 MB

router = APIRouter()


@router.get("/signatures/{signature_id}/image")
async def get_signature_image(
    request: Request,
    signature_id: str,
) -> Response:
    """Return raw signature PNG by ID."""
    db = request.app.state.db
    cursor = await db.execute(
        "SELECT image FROM signatures WHERE id = ?", (signature_id,)
    )
    row = await cursor.fetchone()
    if row is None:
        return error_response(404, "NOT_FOUND", "Signature not found.")
    return Response(content=row["image"], media_type="image/png")


@router.post("/signatures", status_code=201)
async def create_signature(
    request: Request,
    content_id: Annotated[str, Form()],
    signer: Annotated[str, Form()],
    image: Annotated[UploadFile, File()],
) -> Response:
    """Accept a multipart signature upload and persist it."""
    if signer not in ("dinesh", "carolina"):
        msg = "Invalid signer value."
        return error_response(422, "VALIDATION_ERROR", msg)

    image_data = await image.read()
    if len(image_data) > SIGNATURE_MAX_BYTES:
        msg = "Signature PNG exceeds 1MB."
        return error_response(413, "PAYLOAD_TOO_LARGE", msg)

    db: Any = request.app.state.db

    cursor = await db.execute("SELECT id FROM content WHERE id = ?", (content_id,))
    if await cursor.fetchone() is None:
        return error_response(404, "NOT_FOUND", "Content ID does not exist.")

    signature_id = str(uuid.uuid4())
    try:
        await db.execute(
            "INSERT INTO signatures (id, content_id, signer, image) "
            "VALUES (?, ?, ?, ?)",
            (signature_id, content_id, signer, image_data),
        )
    except sqlite3.IntegrityError:
        await db.rollback()
        msg = "Signer has already signed this contract."
        return error_response(409, "ALREADY_SIGNED", msg)

    await db.execute(
        "INSERT INTO sync_log (entity_type, entity_id, action) VALUES (?, ?, ?)",
        ("signature", signature_id, "create"),
    )
    await db.commit()

    cursor = await db.execute(
        "SELECT signed_at FROM signatures WHERE id = ?", (signature_id,)
    )
    sig_row = await cursor.fetchone()

    return JSONResponse(
        status_code=201,
        content={
            "id": signature_id,
            "content_id": content_id,
            "signer": signer,
            "signed_at": sig_row["signed_at"],
        },
    )
