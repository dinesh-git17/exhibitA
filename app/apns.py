"""APNS push notification client with JWT token auth per Design Doc 9.6."""

from pathlib import Path
from typing import Any

import structlog
from aioapns import APNs, NotificationRequest, PushType

from app.config import Settings
from app.models import ContentType

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


async def send_push(
    settings: Settings,
    db: Any,
    content_type: str,
    *,
    content_id: str | None = None,
    article_number: str | None = None,
    classification: str | None = None,
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
            else:
                _log.info("apns_send_success", token_prefix=token[:8])
        except Exception:
            warning = f"APNS connection error for token {token[:8]}..."
            _log.exception("apns_send_exception", token_prefix=token[:8])
            warnings.append(warning)

    return warnings
