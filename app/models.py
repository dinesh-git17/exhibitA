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


class FilingType(StrEnum):
    """Filing classification types."""

    MOTION = "motion"
    OBJECTION = "objection"
    EMERGENCY_ORDER = "emergency_order"


class RulingVerdict(StrEnum):
    """Ruling verdict options."""

    GRANTED = "granted"
    DENIED = "denied"
    SUSTAINED = "sustained"
    OVERRULED = "overruled"


class SyncAction(StrEnum):
    """Sync log action types."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class HealthResponse(BaseModel):
    """Health endpoint response."""

    status: str
