"""Bearer authentication and signer-identity enforcement per Design Doc 10.7."""

from typing import Any

import bcrypt
from fastapi import Request

_CODE_UNAUTHORIZED = "UNAUTHORIZED"
_CODE_INVALID_SIGNER = "INVALID_SIGNER"


class AuthenticationError(Exception):
    """Raised when Bearer authentication or signer-identity validation fails."""

    def __init__(self, code: str, message: str, *, status_code: int = 401) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


async def _resolve_signer(db: Any, raw_key: str) -> str | None:
    """Compare the raw key against all stored hashes using constant-time verification.

    Iterates every stored key regardless of early match to prevent timing leaks
    about key existence or ordering.
    """
    cursor = await db.execute("SELECT signer, key_hash FROM api_keys")
    rows = await cursor.fetchall()

    matched_signer: str | None = None
    key_bytes = raw_key.encode("utf-8")

    for row in rows:
        stored_hash = row["key_hash"].encode("utf-8")
        if bcrypt.checkpw(key_bytes, stored_hash):
            matched_signer = row["signer"]

    return matched_signer


async def require_auth(request: Request) -> str:
    """FastAPI dependency: validates Bearer token, returns authenticated signer.

    Raises:
        AuthenticationError: On missing, malformed, or invalid Bearer credentials.
    """
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        msg = "Missing or invalid authorization header."
        raise AuthenticationError(_CODE_UNAUTHORIZED, msg)

    raw_key = auth_header[len("Bearer ") :]
    signer = await _resolve_signer(request.app.state.db, raw_key)
    if signer is None:
        msg = "Invalid API key."
        raise AuthenticationError(_CODE_UNAUTHORIZED, msg)

    return signer


def enforce_signer_match(authenticated_signer: str, payload_signer: str) -> None:
    """Reject when payload signer differs from authenticated identity."""
    if authenticated_signer != payload_signer:
        msg = "Payload signer does not match authenticated identity."
        raise AuthenticationError(_CODE_INVALID_SIGNER, msg, status_code=400)
