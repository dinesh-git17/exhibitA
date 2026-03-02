# E5.2: Build Sealed Thought Detail View

**Phase:** 5 - Sealed Thoughts **Class:** Feature **Design Doc Reference:** 5.2, 6.2, 6.3, 6.4, 10.6 **Dependencies:**

- Phase 3: Home Screen (phase exit criteria met and thoughts route is reachable).
- E2.2: Define Design System Color and Typography Tokens (`background.reading`, `text.reading`, `text.muted`, spacing
  and typography scales are available).
- E2.3: Implement AppState, Router, and Navigation Shell (`.thoughtDetail(id:)` route and shared state access are
  available).
- E2.4: Build API Client, KeychainService, and Content Cache (thought payloads and timestamps are available locally).
- E5.1: Build Sealed Thoughts List View (detail entry path from list rows is implemented for complete Phase 5 flow).
- Asset: None (no new static assets are required for this epic).
- Service: `PaperNoise` generator is available for warm reading-surface texture.
- Service: AppState unread-state persistence is available for clearing read status on view display.

---

## Goal

Build the Sealed Thought detail screen so plain-text memoranda render on the warm reading surface with required
typography, spacing, and read-state behavior.

---

## Scope

### File Inventory

| File | Action | Responsibility |
| ---- | ------ | -------------- |
| `ExhibitA/ExhibitA/Features/Thoughts/ThoughtDetailView.swift` | Create | Implement the complete thought detail reader, including metadata layout, centered plain-text rendering, and read-state update behavior for opened memoranda. |

### Integration Points

**ExhibitA/ExhibitA/Features/Thoughts/ThoughtDetailView.swift**

- Imports from: `ExhibitA/ExhibitA/Design/Theme.swift`, `ExhibitA/ExhibitA/Design/PaperNoise.swift`,
  `ExhibitA/ExhibitA/App/AppState.swift`, `ExhibitA/ExhibitA/App/Router.swift`
- Imported by: `ExhibitA/ExhibitA/App/ExhibitAApp.swift` (navigation destination for `.thoughtDetail(id:)`)
- State reads: Selected thought body content, selected thought timestamp, and current unread state for the selected ID
- State writes: AppState read/unread state mutation to mark the opened thought as read

---

## Out of Scope

- Thought-list row layout, row separators, row ordering, and row-level unread indicators (owned by E5.1).
- Markdown, attributed rendering, or rich-text parsing for thought body content (non-goal in Design Doc 5.2 and 10.6;
  thoughts are plain text only).
- Letters detail rendering and correspondence metadata treatment (owned by Phase 4 epic E4.2).
- Contract signature flows, page-curl interaction, and article pagination behavior (owned by Phase 6 epics E6.1 to
  E6.4).
- Push-triggered deep links, background sync refresh, and offline retry queue behavior (owned by Phase 7 epics E7.1 and
  E7.2).
- Haptics, sounds, and transition/parallax polish (owned by Phase 8 epics E8.1 and E8.2).
- Backend implementation or VPS-side coding/deployment activity (repository-first backend development and post-merge VPS
  deployment workflow remain unchanged).

---

## Definition of Done

- [ ] Detail screen renders on `background.reading` with paper-noise overlay applied from the shared noise generator.
- [ ] Date-time metadata renders above thought body in SF Pro Text 14pt using `text.muted`.
- [ ] Thought body renders as plain text in New York Regular 18pt using `text.reading`.
- [ ] Horizontal padding is 32pt and vertical padding is 48pt around the thought body container.
- [ ] Thought body text is centered in the detail composition with generous whitespace and no stamp or watermark
  elements.
- [ ] Markdown markers in thought text (for example `**text**` or `_text_`) render literally as plain characters and are
  not parsed into styled markdown output.
- [ ] Opening the detail view marks the selected thought as read in AppState so unread indicators clear on return to the
  list.
- [ ] Invalid or missing thought identifiers render a safe fallback state without application crash.

---

## Implementation Notes

Use Design Doc 5.2 as the source of truth for layout intent and Design Doc 6.2/6.3 for tokenized visual values. Keep the
renderer intentionally minimal: no markdown parser, no custom rich-text pipeline, and no extra controls beyond date
metadata plus body content. Apply `PaperNoise` at the same subtle intensity used by other reading surfaces to preserve
visual continuity without introducing decorative elements. Read-state mutation must happen when the detail appears so
the list badge state is accurate on back navigation. This epic is iOS-only and repository-local; it does not include any
VPS coding path.
