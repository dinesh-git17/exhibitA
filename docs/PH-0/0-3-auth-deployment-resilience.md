# E0.3: Enforce Auth and Production Deployment Controls

**Phase:** 0 - Backend Foundation **Class:** Infrastructure **Design Doc Reference:** 7.1, 7.3, 7.3.2, 10.7, 10.8, 14.2,
14.3, 15.1, 16.1 **Dependencies:**

- Phase 0: Backend Foundation (`E0.1` and `E0.2` deliverables completed)
- E0.1: Scaffold Backend Runtime and SQLite Schema (app factory, DB access, key tables exist)
- E0.2: Implement Content, Signature, and Sync APIs (all app-facing routes are present)
- Asset: Hashed API keys for `dinesh` and `carolina` seeded in `api_keys`
- Service: DNS `exhibita.dineshd.dev` resolves to `157.180.94.145` and Caddy is available on VPS
- Service: systemd available for `exhibit-a.service` lifecycle management
- Service: Backblaze B2 credentials available for Litestream replication

---

## Goal

Enforce Bearer authentication and codify production deployment controls so only authorized requests reach app-facing
endpoints and the backend runs with recoverable HTTPS-backed operations on the VPS.

---

## Scope

### File Inventory

| File | Action | Responsibility |
| ---- | ------ | -------------- |
| `app/auth.py` | Create | Implement API-key Bearer authentication, constant-time key validation, and signer-identity enforcement helpers. |
| `litestream.yml` | Create | Define SQLite WAL replication configuration from `/opt/exhibit-a/data/exhibit-a.db` to Backblaze B2. |
| `deploy/caddy/exhibita.Caddyfile` | Create | Version-control the Caddy site block for `exhibita.dineshd.dev` reverse proxy and TLS behavior. |
| `deploy/systemd/exhibit-a.service` | Create | Version-control the systemd unit that runs `/opt/exhibit-a/start.sh` with restart policy and correct working directory. |

### Integration Points

**app/auth.py**

- Imports from: `app/db.py`, `app/config.py`
- Imported by: `app/routes/content.py`, `app/routes/signatures.py`, `app/routes/devices.py`, `app/__init__.py`
- State reads: `api_keys` table rows and signer identity tied to each key hash
- State writes: None

**litestream.yml**

- Imports from: Environment variables loaded by runtime (`LITESTREAM_*` values)
- Imported by: Litestream process/service on VPS
- State reads: SQLite WAL at `/opt/exhibit-a/data/exhibit-a.db`
- State writes: Replicated WAL snapshots and index metadata in Backblaze B2

**deploy/caddy/exhibita.Caddyfile**

- Imports from: None
- Imported by: `/etc/caddy/Caddyfile` deployment step (copied/merged from repo artifact)
- State reads: Incoming HTTPS requests for `exhibita.dineshd.dev`
- State writes: Reverse-proxied traffic to `127.0.0.1:8001` and access logs

**deploy/systemd/exhibit-a.service**

- Imports from: `start.sh` runtime entrypoint
- Imported by: `/etc/systemd/system/exhibit-a.service` deployment step (copied from repo artifact)
- State reads: `/opt/exhibit-a/.env` and `/opt/exhibit-a/.venv`
- State writes: Process lifecycle state managed by systemd

---

## Out of Scope

- Endpoint payload shape changes or additional app-facing route creation (owned by E0.2).
- Admin login, session cookie handling, and web content CRUD workflows (Phase 1 scope).
- iOS push permission prompts, token submission UX, and deep-link handling (Phase 2 and Phase 7 scope).
- Contract rendering and signature capture UI behavior in SwiftUI/PencilKit (Phase 6 scope).
- Horizontal scaling, multi-worker tuning, or database sharding strategy (not required for two-user capacity profile in
  Design Doc 14).

---

## Definition of Done

- [x] Every app-facing request without an `Authorization: Bearer` header returns HTTP 401 with error code
  `UNAUTHORIZED`.
- [x] Requests with invalid Bearer keys return HTTP 401 with the standard error envelope.
- [x] Requests with valid Bearer keys resolve the signer identity as either `dinesh` or `carolina`.
- [x] `POST /signatures` returns HTTP 400 with `INVALID_SIGNER` when payload signer does not match authenticated signer.
- [x] Authentication checks compare keys using constant-time verification against stored key hashes.
- [x] `deploy/caddy/exhibita.Caddyfile` proxies `exhibita.dineshd.dev` to `127.0.0.1:8001` and keeps HTTPS enabled.
- [x] `deploy/systemd/exhibit-a.service` defines `WorkingDirectory=/opt/exhibit-a`, `ExecStart=/opt/exhibit-a/start.sh`,
  `Restart=always`, and `RestartSec=5`.
- [x] `litestream.yml` replicates `/opt/exhibit-a/data/exhibit-a.db` WAL frames to Backblaze B2 with a replication lag
  target under 60 seconds.
- [x] Deployment executes repository-first: artifacts are authored and validated in this repository, then copied to VPS
  paths; no direct VPS-side source coding is used.
- [x] Production process restart recovers API availability within 5 seconds after simulated process exit.

---

## Implementation Notes

Keep auth logic centralized in `app/auth.py` and consume it from routes as a shared dependency to avoid divergent
authorization behavior across endpoints. Match Design Doc 10.7 exactly: hashed API keys, constant-time comparison, and
signer mismatch rejection on signature writes. Treat Caddy and systemd definitions as repository-owned templates
(`deploy/`) and apply them to VPS only after branch validation and explicit operational approval, consistent with
CLAUDE.md 14.3 and 14.5. Configure Litestream strictly around the SQLite path and B2 destination so restore objectives
from Design Doc 10.8 and 15.3 remain achievable.
