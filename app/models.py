"""Shared typed primitives and base Pydantic models."""

from enum import StrEnum

from pydantic import BaseModel


class Signer(StrEnum):
    """Valid signer identities."""

    DINESH = "dinesh"
    CAROLINA = "carolina"


class ContentType(StrEnum):
    """Content classification types."""

    CONTRACT = "contract"
    LETTER = "letter"
    THOUGHT = "thought"


class SyncAction(StrEnum):
    """Sync log action types."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class HealthResponse(BaseModel):
    """Health endpoint response."""

    status: str
