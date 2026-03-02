---
name: backend-engineering-contract
description: Enforce Exhibit A's backend engineering contract with deterministic PASS/REJECT validation and structured rejection diagnostics. Use when creating, modifying, reviewing, or validating Python/FastAPI backend services, API routes, data models, middleware, database access, migrations, logging, error handling, session security, APNS clients, or backend test/quality gates.
---

# Backend Engineering Contract

Strict contract enforcement. No advisory mode. Reject every violating change.

## Doctrine

Backend services must be typed, structured, observable, and migration-safe.

## Validation

Run:

```bash
python3 .claude/skills/backend-engineering-contract/scripts/validate_backend_engineering_contract.py --root . --format json
```

- Exit code `0` and zero violations = `PASS`.
- Non-zero exit code = `REJECT`.
- Never waive or downgrade a rule.

The validator deterministically scans Python backend code, config, and SQL migration files.

## Contract Rules

### Baseline

| Rule | Constraint |
|------|-----------|
| BEC000 | Python backend service files must exist |

### Runtime and Toolchain

| Rule | Constraint |
|------|-----------|
| BEC001 | FastAPI dependency must be `>=0.126.0` |
| BEC002 | Pydantic dependency must be `>=2.7.0` |
| BEC003 | No `pydantic.v1` compatibility imports |
| BEC004 | Config must use `pydantic-settings` typed `BaseSettings` models; no direct `os.getenv`/`os.environ` reads |
| BEC005 | Python runtime must be `>=3.12` |
| BEC006 | `mypy --strict` (or equivalent strict config) required |
| BEC007 | Ruff required |
| BEC008 | `flake8`, `black`, `isort` forbidden |

### Logging and Observability

| Rule | Constraint |
|------|-----------|
| BEC009 | `structlog` required |
| BEC010 | Logging pipeline must include JSON rendering and contextvars merge |
| BEC011 | Correlation IDs must propagate via contextvars |
| BEC020 | HTTP middleware must inject correlation IDs |
| BEC021 | HTTP middleware must measure request timing |
| BEC022 | HTTP middleware must emit structured request logs |

### API Contract

| Rule | Constraint |
|------|-----------|
| BEC012 | Every FastAPI route must declare `response_model` |
| BEC013 | Mutating routes (`POST`/`PUT`/`PATCH`) must use typed request models |
| BEC014 | Raw dict payloads for route input/output forbidden |
| BEC015 | RFC 9457 problem-details format required |
| BEC023 | Signature upload routes must enforce 10 requests/minute per signer |
| BEC024 | CORS must be restricted to the app bundle origin |
| BEC025 | `GET /health` required with `{ "status": "ok", "db": "writable", "uptime_seconds": N }` |
| BEC026 | FastAPI `default_response_class` must be `ORJSONResponse` |
| BEC027 | App lifecycle must use `lifespan` |
| BEC028 | Deprecated `on_event` hooks forbidden |
| BEC029 | Session cookies must set `HttpOnly`, `Secure`, `SameSite=Strict` |
| BEC035 | 4xx path must return structured problem-details errors |
| BEC036 | Raw 500 leakage forbidden; top-level structured handler required |

### Database and Migration Safety

| Rule | Constraint |
|------|-----------|
| BEC016 | Async DB access must use `aiosqlite` |
| BEC017 | SQLite WAL mode must be enabled |
| BEC018 | Migrations must be versioned SQL files (`V###__description.sql`) |
| BEC019 | Ad-hoc schema mutation forbidden outside migrations |
| BEC034 | SQL execute paths must be parameterized and non-interpolated |

### APNS and Quality Gates

| Rule | Constraint |
|------|-----------|
| BEC030 | APNS client transport must use `httpx` with HTTP/2 |
| BEC031 | APNS auth must use Apple P8 JWT token flow |
| BEC032 | Every function must have full type annotations |
| BEC033 | `print()` forbidden; use `structlog` |
| BEC037 | `pytest-asyncio` required and coverage floor must be `>=90%` |

Reference baseline: `references/backend-2026-baseline.md`

## Output

Emit this exact structure:

```json
{
  "contract": "backend-engineering-contract",
  "verdict": "PASS | REJECT",
  "summary": {
    "files_scanned": 0,
    "rules_checked": 38,
    "violations": 0
  },
  "violations": [
    {
      "rule_id": "BEC000",
      "title": "...",
      "rejection": "REJECT: ...",
      "file": "path/to/file.py",
      "line": 1,
      "snippet": "offending code"
    }
  ]
}
```

If `verdict` is `REJECT`, block approval until every violation is resolved.
