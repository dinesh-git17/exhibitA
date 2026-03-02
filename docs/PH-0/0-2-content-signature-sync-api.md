# E0.2: Implement Content, Signature, and Sync APIs

**Phase:** 0 - Backend Foundation **Class:** Infrastructure **Design Doc Reference:** 7.3, 7.3.1, 7.3.2, 7.3.3, 7.4,
10.7, 14.3 **Dependencies:**

- Phase 0: Backend Foundation (E0.1 runtime and schema complete)
- E0.1: Scaffold Backend Runtime and SQLite Schema (DB lifecycle and base models available)
- Service: SQLite schema from Design Doc 7.2 already initialized (`content`, `signatures`, `sync_log`, `device_tokens`)
- Workflow: Repository-first implementation and local validation before VPS deployment via `scp` (CLAUDE.md 14.3)

---

## Goal

Implement the app-facing content, signature, sync, and device-token APIs so the iOS client can fetch deltas, upload
signatures, and register for push delivery using stable response contracts.

---

## Scope

### File Inventory

| File | Action | Responsibility |
| ---- | ------ | -------------- |
| `app/routes/__init__.py` | Create | Register and expose the app-facing router modules under a deterministic route map. |
| `app/routes/content.py` | Create | Implement content read endpoints (`/content`, `/content/{id}`, `/content/{id}/signatures`) with filters and ordering rules. |
| `app/routes/signatures.py` | Create | Implement signature image retrieval and multipart signature upload with conflict handling and payload limits. |
| `app/routes/devices.py` | Create | Implement sync delta retrieval and APNS device-token registration endpoints. |

### Integration Points

**app/routes/**init**.py**

- Imports from: `app/routes/content.py`, `app/routes/signatures.py`, `app/routes/devices.py`
- Imported by: `app/__init__.py`
- State reads: None
- State writes: None

**app/routes/content.py**

- Imports from: `app/db.py`, `app/models.py`
- Imported by: `app/routes/__init__.py`
- State reads: Database rows from `content` and `signatures`
- State writes: None

**app/routes/signatures.py**

- Imports from: `app/db.py`, `app/models.py`
- Imported by: `app/routes/__init__.py`
- State reads: Existing signature rows and content ownership fields
- State writes: `signatures` table rows and corresponding `sync_log` rows for create events

**app/routes/devices.py**

- Imports from: `app/db.py`, `app/models.py`
- Imported by: `app/routes/__init__.py`
- State reads: `sync_log` rows ordered by timestamp
- State writes: `device_tokens` rows (insert or deduplicated update semantics)

---

## Out of Scope

- Bearer token parsing, API-key hash verification, and signer authorization enforcement (owned by E0.3).
- Caddy reverse-proxy setup, systemd service configuration, and Litestream replication rollout (owned by E0.3).
- Admin web UI routes, session cookies, and APNS send-on-create behavior (Phase 1 scope).
- iOS-side cache hydration, background refresh scheduling, and unread-badge logic (Phase 2 and Phase 7 scope).
- Contract rendering, page-curl behavior, and signature pad UX interactions (Phase 6 scope).

---

## Definition of Done

- [x] `GET /content` returns HTTP 200 with `{"items": [...]}` ordered by `type` and `section_order`.
- [x] `GET /content?type=contract` returns only `contract` records and preserves phase-defined ordering.
- [x] `GET /content?since=<ISO8601>` returns only records with `updated_at` strictly newer than the provided timestamp.
- [x] `GET /content/{id}` returns HTTP 200 for existing IDs and HTTP 404 with the standard error envelope for missing
  IDs.
- [x] `GET /content/{id}/signatures` returns signature metadata for that contract and no unrelated rows.
- [x] `GET /signatures/{id}/image` returns HTTP 200 with `Content-Type: image/png` for valid IDs.
- [x] `POST /signatures` accepts multipart PNG up to 1 MB and returns HTTP 201 with `id`, `content_id`, `signer`, and
  `signed_at`.
- [x] Duplicate signature submissions for the same `(content_id, signer)` return HTTP 409 with error code
  `ALREADY_SIGNED`.
- [x] `GET /sync?since=<ISO8601>` returns `{"changes": [...]}` ordered by `occurred_at` ascending.
- [x] `POST /device-tokens` persists the token with signer identity and returns HTTP 201 on successful registration.
- [x] Every non-2xx endpoint response uses the exact error envelope format from Design Doc 7.3.2.
- [x] Endpoint code is committed in-repo and promoted to VPS only through repository-first deployment flow (`scp` after
  local validation).

---

## Implementation Notes

Use Design Doc 7.3 as the API contract authority and avoid shape drift: response field names, required fields, and
status codes must match 7.3.1 through 7.3.3 exactly. Generate `sync_log` entries for all signature writes so delta sync
remains authoritative for iOS launch refresh (Design Doc 7.4). Enforce PNG payload size at request boundary before DB
writes. Keep route handlers deterministic and side-effect scoped to their own tables; do not implement auth behavior in
this epic, because auth and signer identity validation are introduced in E0.3.
