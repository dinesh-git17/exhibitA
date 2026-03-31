"""Admin panel routes: session auth, dashboard, content CRUD per Design Doc 9.1-9.8."""

import re
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import structlog
from fastapi import APIRouter, Form, Query, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.apns import send_push
from app.models import ContentType, SyncAction

_log: structlog.stdlib.BoundLogger = structlog.get_logger()

router = APIRouter(prefix="/admin")

_templates: Jinja2Templates | None = None

_SESSION_COOKIE_NAME = "admin_session"
_SESSION_DURATION_DAYS = 7

_LETTER_CLASSIFICATIONS = [
    "Sincere",
    "Grievance",
    "Motion to Appreciate",
    "Emergency Filing",
    "Brief in Support",
    "Petition for Cuddles",
    "Amicus Brief",
    "Closing Statement",
    "Addendum to Previous Affection",
]


def configure_templates(templates: Jinja2Templates) -> None:
    """Inject the shared Jinja2Templates instance into the admin router."""
    global _templates
    _templates = templates


def _get_templates() -> Jinja2Templates:
    """Return the configured Jinja2Templates instance."""
    if _templates is None:
        msg = "Admin templates not configured"
        raise RuntimeError(msg)
    return _templates


async def _validate_session(request: Request) -> bool:
    """Check if the request has a valid, non-expired admin session cookie."""
    session_id = request.cookies.get(_SESSION_COOKIE_NAME)
    if not session_id:
        return False

    db = request.app.state.db
    cursor = await db.execute(
        "SELECT expires_at FROM admin_sessions WHERE session_id = ?",
        (session_id,),
    )
    row = await cursor.fetchone()
    if row is None:
        return False

    expires_at = datetime.fromisoformat(row["expires_at"]).replace(tzinfo=UTC)
    if datetime.now(tz=UTC) >= expires_at:
        await db.execute(
            "DELETE FROM admin_sessions WHERE session_id = ?", (session_id,)
        )
        await db.commit()
        return False

    return True


def _login_redirect() -> RedirectResponse:
    return RedirectResponse(url="/admin/login", status_code=303)


def _set_session_cookie(
    response: RedirectResponse, session_id: str, expires_at: datetime
) -> None:
    response.set_cookie(
        key=_SESSION_COOKIE_NAME,
        value=session_id,
        httponly=True,
        secure=True,
        samesite="strict",
        expires=int(expires_at.timestamp()),
    )


async def _verify_api_key(db: Any, raw_key: str) -> bool:
    """Compare raw key against stored hashes with constant-time verification."""
    cursor = await db.execute("SELECT key_hash FROM api_keys")
    rows = await cursor.fetchall()

    matched = False
    key_bytes = raw_key.encode("utf-8")
    for row in rows:
        stored_hash = row["key_hash"].encode("utf-8")
        if bcrypt.checkpw(key_bytes, stored_hash):
            matched = True

    return matched


def _render_markdown(text: str) -> str:
    """Convert basic markdown (bold, italic, paragraphs) to HTML."""
    if not text.strip():
        return ""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    paragraphs = re.split(r"\n\s*\n", text)
    return "".join(f"<p>{p.strip()}</p>" for p in paragraphs if p.strip())


# --- Session/Auth Routes ---


@router.get("", response_model=None)
async def admin_root(request: Request) -> Response:
    """Dashboard or redirect to login."""
    if not await _validate_session(request):
        return _login_redirect()
    return RedirectResponse(url="/admin/dashboard", status_code=303)


@router.get("/login", response_model=None)
async def login_page(request: Request) -> Response:
    """Render the admin login form."""
    templates = _get_templates()
    return templates.TemplateResponse(request, "login.html", {"error": None})


@router.post("/login", response_model=None)
async def login_submit(request: Request, api_key: str = Form(...)) -> Response:
    """Validate API key and create admin session."""
    db = request.app.state.db

    if not await _verify_api_key(db, api_key):
        _log.warning("admin_login_failed", reason="invalid_api_key")
        templates = _get_templates()
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "Invalid API key. Access denied, counselor."},
            status_code=401,
        )

    session_id = str(uuid.uuid4())
    now = datetime.now(tz=UTC)
    expires_at = now + timedelta(days=_SESSION_DURATION_DAYS)

    await db.execute(
        "INSERT INTO admin_sessions (session_id, created_at, expires_at) "
        "VALUES (?, ?, ?)",
        (session_id, now.isoformat(), expires_at.isoformat()),
    )
    await db.commit()
    _log.info("admin_login_success", session_id=session_id[:8])

    response = RedirectResponse(url="/admin/dashboard", status_code=303)
    _set_session_cookie(response, session_id, expires_at)
    return response


@router.get("/logout")
async def logout(request: Request) -> RedirectResponse:
    """Destroy session and redirect to login."""
    session_id = request.cookies.get(_SESSION_COOKIE_NAME)
    if session_id:
        db = request.app.state.db
        await db.execute(
            "DELETE FROM admin_sessions WHERE session_id = ?", (session_id,)
        )
        await db.commit()

    response = RedirectResponse(url="/admin/login", status_code=303)
    response.delete_cookie(key=_SESSION_COOKIE_NAME)
    return response


# --- Dashboard ---


@router.get("/dashboard", response_model=None)
async def dashboard(request: Request) -> Response:
    """Render admin dashboard with content counts and recent filings."""
    if not await _validate_session(request):
        return _login_redirect()

    db = request.app.state.db

    contract_count = 0
    letter_count = 0
    thought_count = 0
    cursor = await db.execute("SELECT type, COUNT(*) as cnt FROM content GROUP BY type")
    for row in await cursor.fetchall():
        if row["type"] == ContentType.CONTRACT:
            contract_count = row["cnt"]
        elif row["type"] == ContentType.LETTER:
            letter_count = row["cnt"]
        elif row["type"] == ContentType.THOUGHT:
            thought_count = row["cnt"]

    sig_cursor = await db.execute("SELECT COUNT(*) as cnt FROM signatures")
    sig_row = await sig_cursor.fetchone()
    signature_count = sig_row["cnt"] if sig_row else 0

    total_signable_cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM content WHERE requires_signature = 1"
    )
    total_signable_row = await total_signable_cursor.fetchone()
    total_signable = (total_signable_row["cnt"] * 2) if total_signable_row else 0

    recent_cursor = await db.execute(
        "SELECT id, type, title, body, created_at FROM content "
        "ORDER BY created_at DESC LIMIT 5"
    )
    recent_filings = [dict(row) for row in await recent_cursor.fetchall()]

    templates = _get_templates()
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "contract_count": contract_count,
            "letter_count": letter_count,
            "thought_count": thought_count,
            "signature_count": signature_count,
            "total_signable": total_signable,
            "recent_filings": recent_filings,
            "active": "dashboard",
            "flash": request.cookies.get("_flash"),
            "flash_level": request.cookies.get("_flash_level", "success"),
        },
    )


# --- Content List & Forms ---


@router.get("/content", response_model=None)
async def content_list(request: Request) -> Response:
    """Render grouped content list for all types."""
    if not await _validate_session(request):
        return _login_redirect()

    db = request.app.state.db
    cursor = await db.execute(
        "SELECT id, type, title, body, article_number, classification, "
        "section_order, created_at FROM content ORDER BY section_order"
    )
    rows = [dict(r) for r in await cursor.fetchall()]

    contracts = [r for r in rows if r["type"] == ContentType.CONTRACT]
    letters = [r for r in rows if r["type"] == ContentType.LETTER]
    thoughts = [r for r in rows if r["type"] == ContentType.THOUGHT]

    templates = _get_templates()
    return templates.TemplateResponse(
        request,
        "content_list.html",
        {
            "contracts": contracts,
            "letters": letters,
            "thoughts": thoughts,
            "active": "content",
            "flash": request.cookies.get("_flash"),
            "flash_level": request.cookies.get("_flash_level", "success"),
        },
    )


@router.get("/content/new", response_model=None)
async def content_new_form(
    request: Request,
    content_type: str = Query("contract", alias="type"),
) -> Response:
    """Render create form adapted to content type."""
    if not await _validate_session(request):
        return _login_redirect()

    if content_type not in (
        ContentType.CONTRACT,
        ContentType.LETTER,
        ContentType.THOUGHT,
    ):
        return _flash_response("/admin/content", "Invalid content type.", level="error")

    db = request.app.state.db
    cursor = await db.execute(
        "SELECT COALESCE(MAX(section_order), 0) + 1 as next_pos "
        "FROM content WHERE type = ?",
        (content_type,),
    )
    row = await cursor.fetchone()
    next_position = row["next_pos"] if row else 1

    templates = _get_templates()
    return templates.TemplateResponse(
        request,
        "content_form.html",
        {
            "content_type": content_type,
            "item": None,
            "next_position": next_position,
            "classifications": _LETTER_CLASSIFICATIONS,
            "preview_html": None,
            "active": "content",
            "flash": request.cookies.get("_flash"),
            "flash_level": request.cookies.get("_flash_level", "success"),
        },
    )


@router.get("/content/{content_id}/edit", response_model=None)
async def content_edit_form(request: Request, content_id: str) -> Response:
    """Render edit form pre-populated with existing content values."""
    if not await _validate_session(request):
        return _login_redirect()

    db = request.app.state.db
    cursor = await db.execute("SELECT * FROM content WHERE id = ?", (content_id,))
    item = await cursor.fetchone()

    if item is None:
        return _flash_response("/admin/content", "Content not found.", level="error")

    item_dict = dict(item)
    preview_html = (
        _render_markdown(item_dict["body"])
        if item_dict["type"] == ContentType.LETTER and item_dict.get("body")
        else None
    )

    comment_cursor = await db.execute(
        "SELECT signer, body, created_at FROM comments "
        "WHERE content_id = ? ORDER BY created_at",
        (content_id,),
    )
    comments = [dict(r) for r in await comment_cursor.fetchall()]

    templates = _get_templates()
    return templates.TemplateResponse(
        request,
        "content_form.html",
        {
            "content_type": item_dict["type"],
            "item": item_dict,
            "next_position": item_dict["section_order"],
            "classifications": _LETTER_CLASSIFICATIONS,
            "preview_html": preview_html,
            "comments": comments,
            "active": "content",
            "flash": request.cookies.get("_flash"),
            "flash_level": request.cookies.get("_flash_level", "success"),
        },
    )


@router.post("/content/preview", response_model=None)
async def content_preview(request: Request, body: str = Form("")) -> Response:
    """Return rendered markdown HTML fragment for HTMX preview swap."""
    if not await _validate_session(request):
        return HTMLResponse("", status_code=401)

    return HTMLResponse(_render_markdown(body))


# --- Content CRUD ---


def _flash_response(url: str, message: str, level: str = "success") -> RedirectResponse:
    """Redirect with a flash message cookie."""
    response = RedirectResponse(url=url, status_code=303)
    response.set_cookie(
        key="_flash", value=message, max_age=10, httponly=True, samesite="strict"
    )
    response.set_cookie(
        key="_flash_level", value=level, max_age=10, httponly=True, samesite="strict"
    )
    return response


@router.post("/content/create", response_model=None)
async def content_create(
    request: Request,
    content_type: str = Form(...),
    title: str = Form(""),
    subtitle: str = Form(""),
    body: str = Form(...),
    article_number: str = Form(""),
    classification: str = Form(""),
    section_order: int = Form(...),
    requires_signature: bool = Form(False),
) -> Response:
    """Create new content and trigger APNS push."""
    if not await _validate_session(request):
        return _login_redirect()

    if content_type not in (
        ContentType.CONTRACT,
        ContentType.LETTER,
        ContentType.THOUGHT,
    ):
        return _flash_response(
            "/admin/dashboard", "Invalid content type.", level="error"
        )

    db = request.app.state.db
    settings = request.app.state.settings
    content_id = str(uuid.uuid4())

    await db.execute(
        "INSERT INTO content "
        "(id, type, title, subtitle, body, article_number, classification, "
        "section_order, requires_signature) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            content_id,
            content_type,
            title or None,
            subtitle or None,
            body,
            article_number or None,
            classification or None,
            section_order,
            requires_signature,
        ),
    )
    await db.execute(
        "INSERT INTO sync_log (entity_type, entity_id, action) VALUES (?, ?, ?)",
        ("content", content_id, SyncAction.CREATE),
    )
    await db.commit()
    _log.info("content_created", content_id=content_id, content_type=content_type)

    cursor = await db.execute(
        "SELECT created_at FROM content WHERE id = ?", (content_id,)
    )
    content_row = await cursor.fetchone()
    content_created_at: str | None = content_row["created_at"] if content_row else None

    apns_warnings = await send_push(
        settings,
        db,
        content_type,
        content_id=content_id,
        article_number=article_number or None,
        classification=classification or None,
        title=title or None,
        subtitle=subtitle or None,
        body_text=body,
        section_order=section_order,
        requires_signature=requires_signature,
        created_at=content_created_at,
    )

    if apns_warnings:
        flash_msg = f"Content created. Push warning: {apns_warnings[0]}"
        return _flash_response("/admin/dashboard", flash_msg, level="warning")

    return _flash_response("/admin/dashboard", "Content filed successfully.")


@router.post("/content/{content_id}/update", response_model=None)
async def content_update(
    request: Request,
    content_id: str,
    title: str = Form(""),
    subtitle: str = Form(""),
    body: str = Form(...),
    article_number: str = Form(""),
    classification: str = Form(""),
    section_order: int = Form(...),
    requires_signature: bool = Form(False),
) -> Response:
    """Update existing content."""
    if not await _validate_session(request):
        return _login_redirect()

    db = request.app.state.db

    cursor = await db.execute("SELECT id FROM content WHERE id = ?", (content_id,))
    if await cursor.fetchone() is None:
        return _flash_response("/admin/dashboard", "Content not found.", level="error")

    await db.execute(
        "UPDATE content SET title = ?, subtitle = ?, body = ?, "
        "article_number = ?, classification = ?, section_order = ?, "
        "requires_signature = ?, updated_at = datetime('now') WHERE id = ?",
        (
            title or None,
            subtitle or None,
            body,
            article_number or None,
            classification or None,
            section_order,
            requires_signature,
            content_id,
        ),
    )
    await db.execute(
        "INSERT INTO sync_log (entity_type, entity_id, action) VALUES (?, ?, ?)",
        ("content", content_id, SyncAction.UPDATE),
    )
    await db.commit()
    _log.info("content_updated", content_id=content_id)

    return _flash_response("/admin/dashboard", "Filing updated.")


@router.post("/content/{content_id}/reorder", response_model=None)
async def content_reorder(
    request: Request,
    content_id: str,
    section_order: int = Form(...),
) -> Response:
    """Reorder content position."""
    if not await _validate_session(request):
        return _login_redirect()

    db = request.app.state.db

    cursor = await db.execute("SELECT id FROM content WHERE id = ?", (content_id,))
    if await cursor.fetchone() is None:
        return _flash_response("/admin/dashboard", "Content not found.", level="error")

    await db.execute(
        "UPDATE content SET section_order = ?, updated_at = datetime('now') "
        "WHERE id = ?",
        (section_order, content_id),
    )
    await db.execute(
        "INSERT INTO sync_log (entity_type, entity_id, action) VALUES (?, ?, ?)",
        ("content", content_id, SyncAction.UPDATE),
    )
    await db.commit()
    _log.info("content_reordered", content_id=content_id, new_order=section_order)

    return _flash_response("/admin/dashboard", "Filing reordered.")


@router.post("/content/{content_id}/delete", response_model=None)
async def content_delete(
    request: Request,
    content_id: str,
) -> Response:
    """Delete content and write sync_log entry."""
    if not await _validate_session(request):
        return _login_redirect()

    db = request.app.state.db

    cursor = await db.execute("SELECT id FROM content WHERE id = ?", (content_id,))
    if await cursor.fetchone() is None:
        return _flash_response("/admin/dashboard", "Content not found.", level="error")

    await db.execute("DELETE FROM content WHERE id = ?", (content_id,))
    await db.execute(
        "INSERT INTO sync_log (entity_type, entity_id, action) VALUES (?, ?, ?)",
        ("content", content_id, SyncAction.DELETE),
    )
    await db.commit()
    _log.info("content_deleted", content_id=content_id)

    return _flash_response("/admin/dashboard", "Filing removed from record.")
