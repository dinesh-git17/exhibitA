"""APNS push notification client with JWT token auth per Design Doc 9.6."""

from pathlib import Path
from typing import Any

import structlog
from aioapns import APNs, NotificationRequest, PushType

from app.config import Settings
from app.models import ContentType, FilingType

_log: structlog.stdlib.BoundLogger = structlog.get_logger()

_NOTIFICATION_COPY: dict[str, dict[str, str]] = {
    ContentType.CONTRACT: {
        "title": "New Filing Received",
        "body": "Article {article_number} has been added to the record."
        " Your signature may be required.",
    },
    ContentType.LETTER: {
        "title": "Correspondence on Record",
        "body": "A new letter has been filed under {classification}.",
    },
    ContentType.THOUGHT: {
        "title": "Classified Memorandum",
        "body": "A sealed thought has been filed. For authorized eyes only.",
    },
}

_APNS_TOPIC = "com.exhibita.app"


def _build_client(settings: Settings) -> APNs | None:
    """Construct an APNs client from settings, or None if credentials are absent."""
    if not settings.apns_key_id or not settings.apns_team_id:
        _log.warning("apns_credentials_missing", reason="key_id or team_id empty")
        return None

    key_path = Path(settings.apns_key_path)
    if not key_path.exists():
        _log.warning("apns_key_file_missing", path=str(key_path))
        return None

    key_data = key_path.read_text()
    return APNs(
        key=key_data,
        key_id=settings.apns_key_id,
        team_id=settings.apns_team_id,
        topic=_APNS_TOPIC,
        use_sandbox=settings.apns_use_sandbox,
    )


def build_notification_copy(
    content_type: str,
    *,
    article_number: str | None = None,
    classification: str | None = None,
) -> dict[str, str]:
    """Build title and body for the notification based on content type."""
    template = _NOTIFICATION_COPY.get(content_type)
    if template is None:
        return {"title": "New Filing", "body": "New content has been filed."}

    title = template["title"]
    body = template["body"].format(
        article_number=article_number or "N/A",
        classification=classification or "General",
    )
    return {"title": title, "body": body}


def _build_route(content_type: str, content_id: str) -> str:
    """Build the deep-link route string matching the iOS Router.Route contract."""
    if content_type == ContentType.CONTRACT:
        return "contract"
    return f"{content_type}/{content_id}"


_BAD_TOKEN_REASONS = {"BadDeviceToken", "Unregistered", "DeviceTokenNotForTopic"}


async def _prune_token(db: Any, token: str) -> None:
    """Remove a stale device token from the database."""
    await db.execute("DELETE FROM device_tokens WHERE token = ?", (token,))
    await db.commit()
    _log.info("apns_token_pruned", token_prefix=token[:8])


_CONTENT_BODY_TRUNCATION_LIMIT = 500


def _build_content_payload(
    content_type: str,
    content_id: str,
    *,
    title: str | None = None,
    subtitle: str | None = None,
    body_text: str | None = None,
    section_order: int | None = None,
    requires_signature: bool = False,
    created_at: str | None = None,
) -> dict[str, Any]:
    """Build the enriched content object for the APNS payload."""
    obj: dict[str, Any] = {
        "id": content_id,
        "type": content_type,
    }
    if title is not None:
        obj["title"] = title
    if subtitle is not None:
        obj["subtitle"] = subtitle
    if body_text is not None:
        truncated = (
            content_type == ContentType.CONTRACT
            and len(body_text) > _CONTENT_BODY_TRUNCATION_LIMIT
        )
        obj["body"] = (
            body_text[:_CONTENT_BODY_TRUNCATION_LIMIT] if truncated else body_text
        )
        if truncated:
            obj["body_truncated"] = True
    if section_order is not None:
        obj["section_order"] = section_order
    obj["requires_signature"] = requires_signature
    if created_at is not None:
        obj["created_at"] = created_at
    return obj


async def send_push(
    settings: Settings,
    db: Any,
    content_type: str,
    *,
    content_id: str | None = None,
    article_number: str | None = None,
    classification: str | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    body_text: str | None = None,
    section_order: int | None = None,
    requires_signature: bool = False,
    created_at: str | None = None,
) -> list[str]:
    """Send APNS push to all registered device tokens.

    Returns a list of warning messages for any failures. An empty list
    indicates all pushes succeeded or no tokens were registered.
    """
    client = _build_client(settings)
    if client is None:
        return ["APNS not configured -- push notification skipped."]

    cursor = await db.execute("SELECT token FROM device_tokens")
    rows = await cursor.fetchall()
    tokens: list[str] = [row["token"] for row in rows]

    if not tokens:
        _log.info("apns_no_tokens", reason="no registered device tokens")
        return []

    copy = build_notification_copy(
        content_type,
        article_number=article_number,
        classification=classification,
    )

    route = _build_route(content_type, content_id or "") if content_id else None

    warnings: list[str] = []
    for token in tokens:
        message: dict[str, Any] = {
            "aps": {
                "alert": {
                    "title": copy["title"],
                    "body": copy["body"],
                },
                "sound": "default",
            },
        }
        if route:
            message["route"] = route

        if content_id and body_text is not None:
            message["content"] = _build_content_payload(
                content_type,
                content_id,
                title=title,
                subtitle=subtitle,
                body_text=body_text,
                section_order=section_order,
                requires_signature=requires_signature,
                created_at=created_at,
            )

        request = NotificationRequest(
            device_token=token,
            message=message,
            push_type=PushType.ALERT,
        )
        try:
            result = await client.send_notification(request)
            if not result.is_successful:
                warning = (
                    f"APNS delivery failed for token {token[:8]}...: "
                    f"{result.description}"
                )
                _log.warning(
                    "apns_send_failed",
                    token_prefix=token[:8],
                    status=result.status,
                    description=result.description,
                )
                warnings.append(warning)
                if result.description in _BAD_TOKEN_REASONS:
                    await _prune_token(db, token)
            else:
                _log.info("apns_send_success", token_prefix=token[:8])
        except Exception:
            warning = f"APNS connection error for token {token[:8]}..."
            _log.exception("apns_send_exception", token_prefix=token[:8])
            warnings.append(warning)

    return warnings


_COMMENT_COPY: dict[str, dict[str, str]] = {
    ContentType.LETTER: {
        "title": "Response on Record",
        "body": "A response has been filed on a letter.",
    },
    ContentType.THOUGHT: {
        "title": "Response on Record",
        "body": "A response has been filed on a sealed thought.",
    },
}


async def send_comment_push(
    settings: Settings,
    db: Any,
    *,
    content_type: str,
    content_id: str,
    commenting_signer: str,
) -> list[str]:
    """Send APNS push to the OTHER signer when a comment is filed.

    Only the non-authoring signer receives the notification.
    """
    client = _build_client(settings)
    if client is None:
        return ["APNS not configured -- comment push skipped."]

    cursor = await db.execute(
        "SELECT token FROM device_tokens WHERE signer != ?",
        (commenting_signer,),
    )
    rows = await cursor.fetchall()
    tokens: list[str] = [row["token"] for row in rows]

    if not tokens:
        _log.info("apns_comment_no_tokens", reason="no tokens for other signer")
        return []

    copy = _COMMENT_COPY.get(
        content_type,
        {
            "title": "Response on Record",
            "body": "A new response has been filed.",
        },
    )
    route = _build_route(content_type, content_id)

    warnings: list[str] = []
    for token in tokens:
        message: dict[str, Any] = {
            "aps": {
                "alert": {
                    "title": copy["title"],
                    "body": copy["body"],
                },
                "sound": "notif.caf",
            },
            "route": route,
        }

        request = NotificationRequest(
            device_token=token,
            message=message,
            push_type=PushType.ALERT,
        )
        try:
            result = await client.send_notification(request)
            if not result.is_successful:
                warning = (
                    f"APNS comment push failed for token {token[:8]}...: "
                    f"{result.description}"
                )
                _log.warning(
                    "apns_comment_send_failed",
                    token_prefix=token[:8],
                    status=result.status,
                    description=result.description,
                )
                warnings.append(warning)
                if result.description in _BAD_TOKEN_REASONS:
                    await _prune_token(db, token)
            else:
                _log.info("apns_comment_send_success", token_prefix=token[:8])
        except Exception:
            warning = f"APNS comment connection error for token {token[:8]}..."
            _log.exception("apns_comment_send_exception", token_prefix=token[:8])
            warnings.append(warning)

    return warnings


_FILING_TYPE_LABELS: dict[str, str] = {
    FilingType.MOTION: "motion",
    FilingType.OBJECTION: "objection",
    FilingType.EMERGENCY_ORDER: "emergency order",
}


async def send_filing_push(
    settings: Settings,
    db: Any,
    *,
    filing_type: str,
    filing_id: str,
    filing_signer: str,
    filing_title: str | None = None,
    filing_body: str | None = None,
    filed_by: str | None = None,
    created_at: str | None = None,
) -> list[str]:
    """Send APNS push to the OTHER signer when a filing is created."""
    client = _build_client(settings)
    if client is None:
        return ["APNS not configured -- filing push skipped."]

    cursor = await db.execute(
        "SELECT token FROM device_tokens WHERE signer != ?",
        (filing_signer,),
    )
    rows = await cursor.fetchall()
    tokens: list[str] = [row["token"] for row in rows]

    if not tokens:
        _log.info("apns_filing_no_tokens", reason="no tokens for other signer")
        return []

    label = _FILING_TYPE_LABELS.get(filing_type, "filing")
    title = "New Filing Received"
    body = f"A {label} has been filed requiring your attention."
    route = f"filing/{filing_id}"

    extra: dict[str, Any] = {}
    if filing_title is not None:
        filing_obj: dict[str, Any] = {
            "id": filing_id,
            "filing_type": filing_type,
            "title": filing_title,
        }
        if filing_body is not None:
            truncated = len(filing_body) > _CONTENT_BODY_TRUNCATION_LIMIT
            filing_obj["body"] = (
                filing_body[:_CONTENT_BODY_TRUNCATION_LIMIT]
                if truncated
                else filing_body
            )
            if truncated:
                filing_obj["body_truncated"] = True
        if filed_by is not None:
            filing_obj["filed_by"] = filed_by
        if created_at is not None:
            filing_obj["created_at"] = created_at
        extra["filing"] = filing_obj

    return await _send_to_tokens(
        client, db, tokens, title, body, route, "filing", extra_payload=extra
    )


async def send_ruling_push(
    settings: Settings,
    db: Any,
    *,
    filing_type: str,
    filing_id: str,
    ruling: str,
    ruling_signer: str,
) -> list[str]:
    """Send APNS push to the filer when a ruling is issued."""
    client = _build_client(settings)
    if client is None:
        return ["APNS not configured -- ruling push skipped."]

    cursor = await db.execute(
        "SELECT token FROM device_tokens WHERE signer != ?",
        (ruling_signer,),
    )
    rows = await cursor.fetchall()
    tokens: list[str] = [row["token"] for row in rows]

    if not tokens:
        _log.info("apns_ruling_no_tokens", reason="no tokens for filer")
        return []

    label = _FILING_TYPE_LABELS.get(filing_type, "filing")
    verdict = ruling.upper()
    title = "Ruling Issued"
    body = f"Your {label} has been {verdict}. See the court's reasoning."
    route = f"filing/{filing_id}"

    return await _send_to_tokens(client, db, tokens, title, body, route, "ruling")


async def _send_to_tokens(
    client: APNs,
    db: Any,
    tokens: list[str],
    title: str,
    body: str,
    route: str,
    log_prefix: str,
    *,
    extra_payload: dict[str, Any] | None = None,
) -> list[str]:
    """Deliver a push notification to a list of device tokens."""
    warnings: list[str] = []
    for token in tokens:
        message: dict[str, Any] = {
            "aps": {
                "alert": {"title": title, "body": body},
                "sound": "notif.caf",
            },
            "route": route,
        }
        if extra_payload:
            message.update(extra_payload)
        request = NotificationRequest(
            device_token=token,
            message=message,
            push_type=PushType.ALERT,
        )
        try:
            result = await client.send_notification(request)
            if not result.is_successful:
                warning = (
                    f"APNS {log_prefix} push failed for token {token[:8]}...: "
                    f"{result.description}"
                )
                _log.warning(
                    f"apns_{log_prefix}_send_failed",
                    token_prefix=token[:8],
                    status=result.status,
                    description=result.description,
                )
                warnings.append(warning)
                if result.description in _BAD_TOKEN_REASONS:
                    await _prune_token(db, token)
            else:
                _log.info(f"apns_{log_prefix}_send_success", token_prefix=token[:8])
        except Exception:
            warning = f"APNS {log_prefix} connection error for token {token[:8]}..."
            _log.exception(f"apns_{log_prefix}_send_exception", token_prefix=token[:8])
            warnings.append(warning)

    return warnings
