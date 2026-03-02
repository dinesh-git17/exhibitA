# E1.1: Implement Admin Routes, Session Auth, and APNS Push

**Phase:** 1 - Admin Panel **Class:** Infrastructure **Design Doc Reference:** 9.1, 9.2, 9.3, 9.5, 9.6, 9.7, 9.8, 10.7,
14.3 **Dependencies:**

- Phase 0: Backend Foundation (exit criteria met)
- E0.1: Scaffold Backend Runtime and SQLite Schema (app factory, schema, and runtime are operational)
- E0.2: Implement Content, Signature, and Sync APIs (content and device token tables are actively used)
- E0.3: Enforce Auth and Production Deployment Controls (Bearer auth and deployment controls already established)
- Asset: APNS P8 credentials and IDs are present in deployment environment variables (`APNS_KEY_ID`, `APNS_TEAM_ID`,
  `APNS_KEY_PATH`)
- Service: `device_tokens` registration interface is available for push targets (`POST /device-tokens`)
- Service: repository-first deployment path is available (`scp` from local repo artifacts to `/opt/exhibit-a/` per
  CLAUDE.md 14.3)

---

## Goal

Implement the authenticated admin backend and core admin templates so content can be managed through `/admin` and new
filings trigger APNS notifications without blocking CRUD completion.

---

## Scope

### File Inventory

| File | Action | Responsibility |
| ---- | ------ | -------------- |
| `app/routes/admin.py` | Create | Implement admin login, session validation, dashboard, content CRUD, reorder handling, and push-trigger wiring. |
| `app/apns.py` | Create | Implement APNS client with JWT token auth and typed send interface for contract, letter, and thought push copy. |
| `app/templates/base.html` | Create | Define the shared admin layout shell with navigation region, flash region, and authenticated page container. |
| `app/templates/login.html` | Create | Implement API key login page for session creation at `/admin/login`. |
| `app/templates/dashboard.html` | Create | Implement dashboard summary view with content counts, signature counts, quick actions, and recent filings section. |
| `app/templates/components/nav.html` | Create | Implement reusable admin navigation component for dashboard and content views. |
| `app/templates/components/flash.html` | Create | Implement reusable success and error flash component for admin actions. |

### Integration Points

**app/routes/admin.py**

- Imports from: `app/db.py`, `app/config.py`, `app/models.py`, `app/apns.py`, `app/auth.py`
- Imported by: `app/routes/__init__.py`, `app/__init__.py`
- State reads: `api_keys`, `admin_sessions`, `content`, `signatures`, `sync_log`, `device_tokens`
- State writes: `admin_sessions`, `content`, `sync_log`

**app/apns.py**

- Imports from: `app/config.py`
- Imported by: `app/routes/admin.py`
- State reads: APNS credentials and target device tokens
- State writes: None

**app/templates/base.html**

- Imports from: `app/templates/components/nav.html`, `app/templates/components/flash.html`
- Imported by: `app/templates/login.html`, `app/templates/dashboard.html`, `app/templates/content_list.html`,
  `app/templates/content_form.html`
- State reads: Template context values for auth/session and flash messages
- State writes: None

**app/templates/login.html**

- Imports from: `app/templates/base.html`
- Imported by: `app/routes/admin.py`
- State reads: Login error state and csrf/session context values
- State writes: None

**app/templates/dashboard.html**

- Imports from: `app/templates/base.html`
- Imported by: `app/routes/admin.py`
- State reads: Content counts, signature counts, and recent filing rows
- State writes: None

**app/templates/components/nav.html**

- Imports from: None
- Imported by: `app/templates/base.html`
- State reads: Active route and session-authenticated user context
- State writes: None

**app/templates/components/flash.html**

- Imports from: None
- Imported by: `app/templates/base.html`
- State reads: Flash message queue entries and severity
- State writes: None

---

## Out of Scope

- Content list and content form templates for per-type rendering (`content_list.html`, `content_form.html`,
  `content_row.html`) (owned by E1.2).
- Admin CSS and HTMX static integration for dynamic form behavior (owned by E1.2).
- App-facing API schema changes for `/content`, `/signatures`, `/sync`, or `/device-tokens` (owned by Phase 0 epics).
- iOS push registration, deep-link routing, and unread badge reactions after notification receipt (owned by Phase 7).
- VPS runtime control operations such as `systemctl` restart or Caddy reload (operational step outside this repository
  planning artifact per CLAUDE.md 14.5).

---

## Definition of Done

- [ ] `GET /admin` returns an HTTP redirect to `/admin/login` when no valid admin session cookie is present.
- [ ] `POST /admin/login` creates a persisted session row in `admin_sessions` and redirects to `/admin` when the API key
  is valid.
- [ ] Session cookie emitted by login has `HttpOnly`, `Secure`, and `SameSite=Strict` attributes with a seven-day
  expiration window.
- [ ] Invalid API key submission to `/admin/login` returns an authentication failure view and does not create a session
  row.
- [ ] Authenticated dashboard renders contract, letter, thought, and signature counts plus recent filings data.
- [ ] Admin CRUD handlers create, update, reorder, and delete content rows while writing corresponding `sync_log`
  entries.
- [ ] Content creation through admin handlers invokes APNS send with the notification title/body mapped by content type
  from Design Doc 9.6.
- [ ] APNS send failures are logged and surfaced as non-blocking flash warnings while content creation still returns
  success.
- [ ] All route and APNS logic is authored in repository files and validated locally before any VPS sync/deploy action.
- [ ] `ruff format --check .`, `ruff check .`, `mypy --strict .`, and `pytest` pass for the admin backend changeset.

---

## Implementation Notes

Implement session auth exactly as Design Doc 9.2 specifies: API key login, SQLite-backed `admin_sessions`, and strict
cookie flags. Keep admin route ownership centralized in `app/routes/admin.py` per Design Doc 9.8 and avoid splitting
CRUD logic across unrelated modules. Build APNS notification copy strictly from Design Doc 9.6 and emit push after
successful content persistence and sync-log write to preserve data-first sequencing. Do all code authoring and
validation locally in this repository, then promote to VPS using the repository-first flow in CLAUDE.md 14.3; do not
frame this epic as direct source coding on the VPS.
