"""Content read endpoints per Design Doc 7.3."""

from typing import Annotated, Any

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from app.routes import error_response

router = APIRouter()


def _row_to_content(row: Any) -> dict[str, Any]:
    return {
        "id": row["id"],
        "type": row["type"],
        "title": row["title"],
        "subtitle": row["subtitle"],
        "body": row["body"],
        "article_number": row["article_number"],
        "classification": row["classification"],
        "section_order": row["section_order"],
        "requires_signature": bool(row["requires_signature"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


@router.get("/content")
async def list_content(
    request: Request,
    content_type: Annotated[str | None, Query(alias="type")] = None,
    since: Annotated[str | None, Query()] = None,
) -> JSONResponse:
    """List content, optionally filtered by type or updated-after timestamp."""
    db = request.app.state.db
    query = "SELECT * FROM content"
    params: list[str] = []
    conditions: list[str] = []

    if content_type is not None:
        conditions.append("type = ?")
        params.append(content_type)

    if since is not None:
        normalized = since.replace("T", " ").rstrip("Z")
        conditions.append("updated_at > ?")
        params.append(normalized)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY type, section_order"

    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()
    return JSONResponse(content={"items": [_row_to_content(row) for row in rows]})


@router.post("/content/batch")
async def batch_content(
    request: Request,
) -> JSONResponse:
    """Retrieve multiple content items by ID in a single request."""
    body = await request.json()
    ids: list[str] = body.get("ids", [])
    if not ids:
        return JSONResponse(content={"items": []})

    placeholders = ",".join("?" for _ in ids)
    db = request.app.state.db
    cursor = await db.execute(
        f"SELECT * FROM content WHERE id IN ({placeholders}) "  # noqa: S608
        "ORDER BY type, section_order",
        ids,
    )
    rows = await cursor.fetchall()
    return JSONResponse(content={"items": [_row_to_content(row) for row in rows]})


@router.get("/content/{content_id}")
async def get_content(
    request: Request,
    content_id: str,
) -> JSONResponse:
    """Retrieve a single content item by ID."""
    db = request.app.state.db
    cursor = await db.execute("SELECT * FROM content WHERE id = ?", (content_id,))
    row = await cursor.fetchone()
    if row is None:
        return error_response(404, "NOT_FOUND", "Content ID does not exist.")
    return JSONResponse(content=_row_to_content(row))


@router.get("/content/{content_id}/signatures")
async def get_content_signatures(
    request: Request,
    content_id: str,
) -> JSONResponse:
    """Retrieve signature metadata for a specific content item."""
    db = request.app.state.db
    cursor = await db.execute("SELECT id FROM content WHERE id = ?", (content_id,))
    if await cursor.fetchone() is None:
        return error_response(404, "NOT_FOUND", "Content ID does not exist.")

    cursor = await db.execute(
        "SELECT id, content_id, signer, signed_at FROM signatures WHERE content_id = ?",
        (content_id,),
    )
    rows = await cursor.fetchall()
    return JSONResponse(
        content=[
            {
                "id": row["id"],
                "content_id": row["content_id"],
                "signer": row["signer"],
                "signed_at": row["signed_at"],
            }
            for row in rows
        ]
    )
