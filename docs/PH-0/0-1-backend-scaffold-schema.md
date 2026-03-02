# E0.1: Scaffold Backend Runtime and SQLite Schema

**Phase:** 0 - Backend Foundation **Class:** Infrastructure **Design Doc Reference:** 7.1, 7.2, 7.3, 10.9, 10.10, 10.11,
14.3, 15.1 **Dependencies:**

- None (Phase 0 entry criteria are met: VPS access, Python 3.13+, APNS key generated, repository cloned)
- Service: `uv` environment management and Python 3.13 runtime available locally and on VPS
- Service: SQLite with WAL support available on target host
- Workflow: Repository-first backend development with VPS deployment only after local quality gates (CLAUDE.md 14.3)

---

## Goal

Build the backend runtime skeleton and canonical SQLite schema so the API service boots deterministically from
repository code and is deployable to the VPS without direct VPS-side source authoring.

---

## Scope

### File Inventory

| File | Action | Responsibility |
| ---- | ------ | -------------- |
| `requirements.txt` | Modify | Pin the backend dependency set required for FastAPI, SQLite, auth, APNS, testing, and structured logging. |
| `app/__init__.py` | Create | Define the FastAPI app factory, route registration shell, startup initialization, and health endpoint wiring. |
| `app/__main__.py` | Create | Provide the executable module entrypoint that starts Uvicorn on `127.0.0.1:8001`. |
| `app/config.py` | Create | Implement typed settings loading via `pydantic-settings` for runtime, auth, and storage configuration. |
| `app/db.py` | Create | Manage aiosqlite lifecycle, enforce WAL mode, and initialize schema and indexes from Design Doc 7.2. |
| `app/models.py` | Create | Define base Pydantic models and shared typed primitives consumed by route modules. |
| `start.sh` | Create | Load environment variables and run the backend module using the project virtual environment. |
| `.env.example` | Create | Document required environment keys for local validation and VPS deployment bootstrap. |
| `scripts/protocol-zero.sh` | Modify | Keep repository protocol scanning aligned with backend file patterns and exclusions. |
| `scripts/check-em-dashes.sh` | Modify | Keep typographic lint exclusions aligned with backend source and generated artifacts. |

### Integration Points

**requirements.txt**

- Imports from: None
- Imported by: Local `uv` install flows, CI quality jobs, VPS deployment bootstrap
- State reads: None
- State writes: None

**app/**init**.py**

- Imports from: `app/config.py`, `app/db.py`, `app/routes/__init__.py` (registered once routes exist)
- Imported by: `app/__main__.py`, test harnesses
- State reads: Runtime settings from `Settings`
- State writes: FastAPI app state references for DB connection management

**app/**main**.py**

- Imports from: `app/__init__.py`
- Imported by: `python -m app`, `start.sh`, systemd service command
- State reads: Host and port settings
- State writes: None

**app/config.py**

- Imports from: None
- Imported by: `app/__init__.py`, `app/db.py`, `app/auth.py`, route modules
- State reads: Environment variables loaded from process environment
- State writes: None

**app/db.py**

- Imports from: `app/config.py`
- Imported by: `app/__init__.py`, `app/routes/content.py`, `app/routes/signatures.py`, `app/routes/devices.py`,
  `app/auth.py`
- State reads: Database path and SQLite pragmas from settings
- State writes: Database schema objects (`content`, `signatures`, `sync_log`, `device_tokens`, `api_keys`,
  `admin_sessions`) and indexes

**app/models.py**

- Imports from: None
- Imported by: Route modules and endpoint tests
- State reads: None
- State writes: None

**start.sh**

- Imports from: `.env` runtime file and Python module `app`
- Imported by: `/etc/systemd/system/exhibit-a.service`
- State reads: Environment variables from `/opt/exhibit-a/.env`
- State writes: Process environment for Uvicorn execution

**.env.example**

- Imports from: None
- Imported by: Local setup workflow and VPS bootstrap copy
- State reads: None
- State writes: None

**scripts/protocol-zero.sh**

- Imports from: None
- Imported by: CI jobs, local pre-commit hooks, manual validation flow
- State reads: Repository file tree and commit message input
- State writes: Exit status only

**scripts/check-em-dashes.sh**

- Imports from: None
- Imported by: CI jobs, local pre-commit hooks, manual validation flow
- State reads: Repository file tree
- State writes: Exit status only

---

## Out of Scope

- App-facing endpoint behavior (`/content`, `/signatures`, `/sync`, `/device-tokens`) and response-envelope compliance
  (owned by E0.2).
- Bearer token verification, signer identity enforcement, and 401/400 auth error paths (owned by E0.3).
- VPS runtime control changes (`systemctl`, Caddy reload, firewall operations) (approval-gated operational work in E0.3
  per CLAUDE.md 14.5).
- Admin panel routes, templates, and APNS send flow (Phase 1 scope).
- iOS client integration, local mobile cache behavior, and BGAppRefresh sync behavior (Phase 2+ scope).

---

## Definition of Done

- [ ] `python -m app` starts the API process bound to `127.0.0.1:8001` from repository code.
- [ ] `GET /health` returns HTTP 200 with body `{"status":"ok"}` after service startup.
- [ ] Database initialization creates all six tables and all required indexes exactly matching Design Doc 7.2.
- [ ] SQLite runs in WAL mode and persists the database file at the configured path.
- [ ] Runtime settings resolve from environment variables through `pydantic-settings` without hardcoded secrets.
- [ ] `ruff format --check .`, `ruff check .`, and `mypy --strict .` pass after scaffold creation.
- [ ] `scripts/protocol-zero.sh` exits 0 on a clean repository snapshot.
- [ ] `scripts/check-em-dashes.sh` exits 0 on a clean repository snapshot.
- [ ] Deployment artifact set is generated in-repo and is ready for `scp` to `/opt/exhibit-a/` without direct VPS code
  edits.

---

## Implementation Notes

Implement schema and indexes exactly from Design Doc 7.2, including `UNIQUE(content_id, signer)` on signatures and
explicit `CHECK` constraints for enum-like fields. Initialize WAL mode in the DB bootstrap path before serving requests.
Keep the app factory and startup deterministic: load typed settings, open DB connection, run bootstrap, register
routers, expose `/health`. Treat this epic as repository-only source construction; deploy only after quality gates pass,
then copy artifacts to VPS using the CLAUDE.md 14.3 flow (`scp` after local validation), not direct source authoring on
VPS.
