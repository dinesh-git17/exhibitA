<!--
  Exhibit A -- Pull Request Template
  Reference: CLAUDE.md S4, S12, S16
  Title format: type(scope): imperative description (max 70 chars)
  Valid types: feat | fix | refactor | test | chore | docs
  Valid scopes: contract-book, letters, thoughts, signatures, sync,
                admin, api, theme, auth, push, infra, scripts, ci
-->

## Summary

<!-- What changed and why. Not a restatement of the diff. -->
<!-- Link the design doc section if implementing a specified behavior. -->

## Design Doc Alignment

<!-- Which section(s) of docs/exhibit-a-design-doc.md does this implement or modify? -->
<!-- If this deviates from the design doc, declare the deviation and rationale. -->

- **Section(s):** <!-- e.g., S8.1 (iOS Content Model), S7.3 (Sync Strategy) -->
- **Deviation:** None | <!-- describe deviation and justification -->

## Surfaces Affected

<!-- Check every surface this PR touches. A change touching multiple surfaces
     requires extra scrutiny for deployment ordering and contract compatibility. -->

- [ ] iOS app (SwiftUI)
- [ ] Backend API (FastAPI)
- [ ] Admin panel (Jinja2 / HTMX)
- [ ] Database schema (SQLite)
- [ ] Sync / offline behavior
- [ ] Signature flow (PencilKit / upload)
- [ ] Push notifications (APNS)
- [ ] Infrastructure / deployment (Caddy, systemd, Litestream)
- [ ] CI / GitHub Actions
- [ ] Scripts or tooling

## Risk Assessment

<!-- What could break? Which failure modes did you consider? -->
<!-- For cross-surface changes, describe deployment ordering requirements. -->

| Dimension | Impact |
|-----------|--------|
| **Blast radius** | <!-- e.g., "Signature upload only" or "All content sync paths" --> |
| **Failure mode** | <!-- e.g., "Silent data loss" / "Visible error state" / "Crash" --> |
| **Rollback** | <!-- e.g., "Revert safe, no migration" / "Requires DB rollback" --> |
| **Offline impact** | <!-- e.g., "None" / "Cached data format changes" --> |

## Schema & API Contract Changes

<!-- If no schema or API changes, write "None" and delete the table. -->

| Surface | Endpoint / Table | Change | Breaking |
|---------|------------------|--------|----------|
| <!-- Backend / iOS --> | <!-- e.g., POST /signatures --> | <!-- e.g., Added deviceId param --> | Yes / No |

## iOS Compatibility

<!-- Delete this section if the PR does not touch iOS code. -->

- **Minimum target:** iOS 26
- **Concurrency:** <!-- @MainActor, Sendable, async/await compliance notes -->
- **State management:** <!-- @Observable, no ObservableObject -->
- **Liquid Glass:** <!-- Suppressed where required per design doc S6 -->
- **Offline behavior:** <!-- How does this work without network? -->

## Admin & Content Flow

<!-- Delete this section if the PR does not touch admin panel or content pipeline. -->

- **Content types affected:** <!-- contract / letter / thought / none -->
- **Admin form changes:** <!-- New fields, validation, HTMX partials -->
- **APNS trigger impact:** <!-- Does this change when/how push fires? -->
- **Sync log impact:** <!-- New entity_type, changed action semantics? -->

## Migration & Rollout

<!-- Delete this section if no migration, data transformation, or phased rollout. -->

- **Database migration:** <!-- SQL script path or "None" -->
- **Data backfill:** <!-- Required? Script path? -->
- **Deployment order:** <!-- e.g., "Backend first (migration), then iOS" -->
- **Feature flag:** <!-- If gated, name the flag and default state -->
- **Litestream:** <!-- Any impact on backup/restore? -->

## Observability

<!-- Delete this section if no logging, monitoring, or structured output changes. -->

- **Logging changes:** <!-- New structlog fields, changed log levels -->
- **Health check:** <!-- /health endpoint affected? -->
- **Error codes:** <!-- New error codes added to the envelope? -->

## Testing

<!-- How was this verified? Be specific. -->

- **Device / OS:** <!-- e.g., iPhone 16 Pro / iOS 26 beta 1 -->
- **Scenarios verified:**
  - <!-- e.g., "Created contract via admin, verified sync on iOS" -->
  - <!-- e.g., "Signed contract offline, confirmed retry on reconnect" -->
- **Tests added/modified:** <!-- file paths -->
- **Edge cases covered:** <!-- e.g., "Empty body", "Duplicate signature 409" -->

<details>
<summary>Screenshots / Recordings</summary>

<!-- Attach screenshots or screen recordings for any UI change.
     For non-visual changes, write "N/A" and collapse this section. -->

N/A

</details>

## Checklist

<!-- All boxes must be checked before merge. -->

### Code Quality

- [ ] Code compiles and runs without errors or warnings
- [ ] No hardcoded secrets, API keys, or credentials
- [ ] No dead code, stubs, or placeholder comments
- [ ] No `print()` / `NSLog()` debugging statements in committed code
- [ ] No force unwraps without inline justification
- [ ] No magic numbers (named constants used)
- [ ] No em dashes (U+2014) or smart quotes in source files

### Standards Compliance

- [ ] Conventional Commits format on all commits: `type(scope): description`
- [ ] PR title follows S16.1: `type(scope): imperative description` (max 70 chars)
- [ ] Design doc compliance verified for architectural decisions
- [ ] Applicable skills from S5.1 consulted and constraints followed

### Linting & Verification

- [ ] `./scripts/protocol-zero.sh` exits 0
- [ ] `./scripts/check-em-dashes.sh` exits 0
- [ ] **Swift:** SwiftLint and SwiftFormat report clean (if iOS files changed)
- [ ] **Python:** `ruff format --check .` passes (if backend files changed)
- [ ] **Python:** `ruff check .` passes (if backend files changed)
- [ ] **Python:** `mypy --strict .` passes (if backend files changed)

### Testing

- [ ] Existing tests pass
- [ ] New tests added for logic-bearing changes
- [ ] No real network calls in tests (mocked/stubbed)
- [ ] No sleep-based synchronization in tests
