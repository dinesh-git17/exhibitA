# E1.2: Build Admin Content Templates and Styling

**Phase:** 1 - Admin Panel **Class:** Infrastructure **Design Doc Reference:** 9.4, 9.5, 9.8, 9.9, 10.9, 14.3
**Dependencies:**

- Phase 1: Admin Panel (E1.1 route and session deliverable available)
- E1.1: Implement Admin Routes, Session Auth, and APNS Push (admin endpoints and base template shell exist)
- Asset: HTMX 2.x script artifact is available for static serving under `app/static/`
- Service: Jinja2 template rendering pipeline is available in FastAPI runtime
- Service: repository-first deployment path is available (`scp` from local repository to VPS per CLAUDE.md 14.3)

---

## Goal

Build the admin content-management UI templates and styling so contracts, letters, and thoughts can be listed, created,
edited, and deleted through typed forms with dynamic behavior.

---

## Scope

### File Inventory

| File | Action | Responsibility |
| ---- | ------ | -------------- |
| `app/templates/content_list.html` | Create | Implement grouped content list view with per-row metadata, edit action, and delete action entry points. |
| `app/templates/content_form.html` | Create | Implement adaptive create/edit form for contract, letter, and thought fields with type-specific controls. |
| `app/templates/components/content_row.html` | Create | Implement reusable row partial for list rendering of title/preview, type, position, and action controls. |
| `app/static/admin.css` | Create | Implement admin visual styling aligned with legal-warm aesthetic and readable form/list hierarchy. |
| `app/static/htmx.min.js` | Create | Provide HTMX runtime script for server-rendered dynamic interactions without a frontend build toolchain. |

### Integration Points

**app/templates/content_list.html**

- Imports from: `app/templates/base.html`, `app/templates/components/content_row.html`
- Imported by: `app/routes/admin.py`
- State reads: Grouped content collections, ordering metadata, and pagination/filter context
- State writes: None

**app/templates/content_form.html**

- Imports from: `app/templates/base.html`
- Imported by: `app/routes/admin.py`
- State reads: Content type, existing item payload for edit, validation errors, and select-option lists
- State writes: None

**app/templates/components/content_row.html**

- Imports from: None
- Imported by: `app/templates/content_list.html`
- State reads: Row-level content record fields and action URLs
- State writes: None

**app/static/admin.css**

- Imports from: None
- Imported by: `app/templates/base.html`
- State reads: None
- State writes: None

**app/static/htmx.min.js**

- Imports from: None
- Imported by: `app/templates/base.html`, `app/templates/content_form.html`
- State reads: DOM attributes (`hx-*`) emitted by templates
- State writes: Browser DOM updates via HTMX swaps

---

## Out of Scope

- Admin route business logic, session creation, and APNS send orchestration in Python modules (owned by E1.1).
- Additional backend API endpoints or schema changes for app-facing routes (owned by Phase 0 and not part of admin
  template scope).
- iOS UI rendering and any Swift-side form or content management workflows (Phase 2+ scope).
- Advanced frontend toolchains, bundlers, or client-rendered SPA behavior (explicitly excluded by Design Doc 9.1 stack
  constraints).
- Animation tuning, micro-interaction polish, and non-blocking visual refinements beyond functional admin usability
  (deferred to later polish cycles).

---

## Definition of Done

- [ ] `/admin/content` renders contracts, letters, and thoughts in separate grouped sections with visible title/preview,
  date, and position fields.
- [ ] Content rows render through `content_row.html` and expose functional edit and delete action links for each item.
- [ ] Contract form renders `article_number`, `title`, `body`, `requires_signature`, and `position` fields when type is
  `contract`.
- [ ] Letter form renders `title`, `subtitle`, `classification`, `body`, and `position` fields with all nine
  classifications from Design Doc 9.4.
- [ ] Thought form renders a minimal body input plus `position` and displays a live character count indicator.
- [ ] Edit form mode pre-populates all existing values for the selected content record.
- [ ] Delete interaction requires an explicit confirmation step before submission.
- [ ] HTMX-driven markdown preview updates the letter preview region on body input keyup events.
- [ ] Admin styles apply warm legal presentation while preserving readable hierarchy for list rows, form controls, and
  validation states.
- [ ] Template and static assets are authored in-repo and validated locally before VPS sync/deploy promotion.

---

## Implementation Notes

Match field coverage exactly to Design Doc 9.4 and do not collapse type-specific fields into a generic unchecked
payload. Keep template structure aligned with Design Doc 9.8 file map and ensure `content_row.html` is reused by list
rendering to avoid duplicated row markup. Serve HTMX as a static asset and use server-rendered partial swaps for dynamic
behavior, consistent with the no-build-step admin architecture in Design Doc 9.1. Preserve repository-first workflow by
implementing and validating template/static changes in this repository first, then deploying the resulting artifacts to
VPS through the approved copy flow in CLAUDE.md 14.3.
