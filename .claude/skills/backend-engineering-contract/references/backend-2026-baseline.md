# Backend 2026 Baseline

Research date: March 2, 2026.

## FastAPI and Backend Engineering Baseline

- FastAPI modern app lifecycle should use `lifespan`; `startup`/`shutdown` events are legacy-facing.
- FastAPI supports `default_response_class=ORJSONResponse` and CORS middleware with explicit origin restrictions.
- Pydantic v2 + `pydantic-settings` are the modern typed configuration baseline.
- Structured logging should use `structlog` with JSON rendering and contextvars integration for request correlation.
- SQLite production concurrency requires WAL mode; async app paths should use `aiosqlite`.
- Error payload design should follow RFC 9457 problem details with structured 4xx/5xx handling.
- APNS provider requests require HTTP/2 and token-based auth (Apple `.p8` key + JWT).
- Quality gates should be deterministic (`mypy --strict`, Ruff, async tests, coverage thresholds).

## Primary Sources

- FastAPI docs: Lifespan events
  - https://fastapi.tiangolo.com/advanced/events/
- FastAPI docs: ORJSONResponse
  - https://fastapi.tiangolo.com/advanced/custom-response/
- FastAPI docs: CORS middleware
  - https://fastapi.tiangolo.com/tutorial/cors/
- Pydantic docs (v2)
  - https://docs.pydantic.dev/latest/
- pydantic-settings docs
  - https://docs.pydantic.dev/latest/concepts/pydantic_settings/
- structlog docs
  - https://www.structlog.org/en/stable/getting-started.html
  - https://www.structlog.org/en/stable/contextvars.html
- aiosqlite docs
  - https://aiosqlite.omnilib.dev/en/stable/
- SQLite WAL documentation
  - https://www.sqlite.org/wal.html
- RFC 9457 (Problem Details)
  - https://datatracker.ietf.org/doc/html/rfc9457
- Apple APNS provider API / token auth
  - https://developer.apple.com/documentation/usernotifications/establishing-a-token-based-connection-to-apns
  - https://developer.apple.com/documentation/usernotifications/sending_notification_requests_to_apns
- HTTPX docs (HTTP/2)
  - https://www.python-httpx.org/http2/
- Ruff docs
  - https://docs.astral.sh/ruff/
- mypy docs
  - https://mypy.readthedocs.io/en/stable/
- pytest-asyncio docs
  - https://pytest-asyncio.readthedocs.io/
