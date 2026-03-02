# E4.2: Build Letter Detail Markdown Reader

**Phase:** 4 - Filed Letters **Class:** Feature **Design Doc Reference:** 4.2, 6.2, 6.3, 6.4, 8.2, 10.6
**Dependencies:**

- Phase 3: Home Screen (phase exit criteria met)
- E3.1: Build Home Screen Filing Cabinet Navigation (letters route and navigation stack host available)
- E4.1: Build Correspondence Log Letter List (detail route invocation from list rows available)
- E2.2: Define Design System Color and Typography Tokens (reading-surface, spacing, and typography tokens available)
- E2.3: Implement AppState, Router, and Navigation Shell (detail route state and unread state mutation path available)
- E2.4: Build API Client, KeychainService, and Content Cache (cached letter bodies and metadata available for detail)
- E2.5: Create Shared Foundation UI Components (`ClassificationLabel` available for metadata rendering)
- Asset: Programmatic paper-noise renderer from `PaperNoise.swift` is available for reading-surface overlay
- Service: Foundation `AttributedString(markdown:)` parser is available for inline markdown rendering

---

## Goal

Build the letter detail reader so each filed letter renders as a warm full-screen markdown reading experience with
correct metadata, typography, and unread-state transition.

---

## Scope

### File Inventory

| File | Action | Responsibility |
| ---- | ------ | -------------- |
| `ExhibitA/ExhibitA/Features/Letters/LetterDetailView.swift` | Create | Implement the letter detail screen with reading-surface styling, markdown body rendering, metadata header, footer copy, and read-state transition behavior. |

### Integration Points

**ExhibitA/ExhibitA/Features/Letters/LetterDetailView.swift**

- Imports from: `ExhibitA/ExhibitA/Design/Theme.swift`, `ExhibitA/ExhibitA/Design/PaperNoise.swift`,
  `ExhibitA/ExhibitA/Design/Components/ClassificationLabel.swift`, `ExhibitA/ExhibitA/App/AppState.swift`,
  `ExhibitA/ExhibitA/App/Router.swift`
- Imported by: `ExhibitA/ExhibitA/App/ExhibitAApp.swift` via `navigationDestination`, and navigated from
  `LetterListView.swift`
- State reads: Selected letter metadata and body content by route ID, unread/read status for selected letter
- State writes: AppState read-state update for selected letter when detail view appears

---

## Out of Scope

- Letter list row layout, separators, and list ordering behavior (owned by E4.1).
- Thought reader and memorandum list experiences (owned by Phase 5 epics E5.1 and E5.2).
- Contract-book pagination, signature block, and PencilKit flows (owned by Phase 6 epics E6.1 to E6.4).
- Sync-engine refresh, push deep-link parsing, and background update orchestration (owned by Phase 7 epic E7.1).
- Audio cues, haptics, transition timing polish, and animation tuning (owned by Phase 8 epics E8.1 and E8.2).
- Markdown authoring workflows in admin panel and backend content CRUD behavior (owned by Phases 0 and 1
  repository-first backend work).
- VPS operational steps such as systemd or Caddy updates (not part of this iOS feature epic).

---

## Definition of Done

- [ ] Letter detail screen renders on `background.reading` with a visible programmatic paper-noise overlay when opened
  from a letter route.
- [ ] Header renders exhibit identifier, letter title, filed date, and classification metadata with the tokenized
  typography and colors defined for the reader.
- [ ] Classification metadata renders as plain text treatment without border or stamp styling.
- [ ] Letter body markdown parses through `AttributedString` and renders bold, italic, and paragraph breaks from stored
  body content.
- [ ] Body text renders with New York Regular 18pt styling, `text.reading` color, 1.48 line-height target, and 20-24pt
  horizontal margins.
- [ ] Footer renders `Filed with love, [date]` in SF Pro Text Regular Italic 13pt with `text.muted` styling.
- [ ] Long letter bodies scroll vertically without truncation and preserve metadata header and footer placement.
- [ ] Opening detail marks the selected letter as read in AppState so unread indicator state is cleared when returning
  to the list.

---

## Implementation Notes

Implement the reader structure directly from Design Doc 4.2 and enforce visual tokens from 6.2 and 6.3. Use
`AttributedString` markdown parsing as specified in 10.6 and avoid introducing third-party markdown libraries. Keep
paper texture generation tied to the existing Phase 2 `PaperNoise` primitive from 6.4, with no bitmap assets. Update
unread state through existing AppState contracts instead of adding parallel state stores. This epic is iOS-only and does
not include backend code changes or VPS deployment actions.
