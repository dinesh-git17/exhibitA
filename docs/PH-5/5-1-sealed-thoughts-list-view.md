# E5.1: Build Sealed Thoughts List View

**Phase:** 5 - Sealed Thoughts **Class:** Feature **Design Doc Reference:** 5.1, 6.2, 6.3, 8.1, 10.5 **Dependencies:**

- Phase 3: Home Screen (phase exit criteria met and thoughts route is reachable from Home).
- E2.2: Define Design System Color and Typography Tokens (thought list colors, typography, spacing, and separator tokens
  are available).
- E2.3: Implement AppState, Router, and Navigation Shell (route contract and unread-state container are available).
- E2.4: Build API Client, KeychainService, and Content Cache (cached thought content is available to the feature layer).
- E2.5: Create Shared UI Components (`UnreadBadge` is available for unread row indicators).
- E3.1: Build Home Screen Filing Cabinet Navigation (Home card routing to the thoughts surface is implemented).
- Asset: None (no new static assets are required for this epic).
- Service: `Router.navigate(to: .thoughtDetail(id:))` is available for row navigation.
- Service: AppState-backed thought collection is available from cached content hydration.

---

## Goal

Build the Sealed Thoughts list screen so classified memoranda rows, unread indicators, ordering, and navigation to
detail are fully functional.

---

## Scope

### File Inventory

| File | Action | Responsibility |
| ---- | ------ | -------------- |
| `ExhibitA/ExhibitA/Features/Thoughts/ThoughtListView.swift` | Create | Implement the complete thought list layout, row rendering, unread badge display, and router-based detail navigation specified for Phase 5. |

### Integration Points

**ExhibitA/ExhibitA/Features/Thoughts/ThoughtListView.swift**

- Imports from: `ExhibitA/ExhibitA/Design/Theme.swift`, `ExhibitA/ExhibitA/Design/Components/UnreadBadge.swift`,
  `ExhibitA/ExhibitA/App/AppState.swift`, `ExhibitA/ExhibitA/App/Router.swift`
- Imported by: `ExhibitA/ExhibitA/App/ExhibitAApp.swift` (navigation destination), Home-screen navigation flow
- State reads: AppState thought collection, unread-thought state, and section ordering metadata
- State writes: Router navigation path mutations through `navigate(to:)` on row tap

---

## Out of Scope

- Thought detail reader composition, centered typography, and read-surface layout (owned by E5.2).
- Filed Letters list/detail behavior and markdown rendering (owned by Phase 4 epics E4.1 and E4.2).
- Contract page-curl flow, article pagination, and signature capture behavior (owned by Phase 6 epics E6.1 to E6.4).
- Background sync, push-triggered data refresh, and unread-state refresh from `/sync` (owned by Phase 7 epic E7.1).
- Sound effects, haptics, parallax, and animation polish work (owned by Phase 8 epics E8.1 and E8.2).
- Backend endpoint changes, VPS editing, or deployment operations (backend phases are repository-first and deployed
  after local validation via SCP per governance).

---

## Definition of Done

- [ ] Thought list screen renders header text `CLASSIFIED MEMORANDA` and subtitle `For Authorized Eyes Only` on launch.
- [ ] Each list row renders memo identifier, formatted date-time metadata, and 2-3 line preview text from cached thought
  body content.
- [ ] Thought rows are ordered by `section_order` descending so newest memoranda appear first.
- [ ] Hairline separators render at 0.5pt using the `border.separator` token between thought rows.
- [ ] `UnreadBadge` renders only for unread thought rows and remains hidden for read rows.
- [ ] Tapping a thought row navigates through Router to `.thoughtDetail(id:)` for the tapped memo.
- [ ] Screen renders safely with zero thought items, preserving header and showing no runtime crashes or layout breaks.
- [ ] All colors and typography in the list view resolve through `Theme` tokens without hardcoded literals.

---

## Implementation Notes

Implement this view as a pure feature surface that consumes already-hydrated AppState content; do not initiate network
fetches from `ThoughtListView`. Use Design Doc 5.1 for copy and row composition, and Design Doc 6.2/6.3 token values for
palette and typography. Keep this epic constrained to a single file and route-to-detail behavior only; read-state
mutation on detail display belongs to E5.2. Maintain repository-first workflow boundaries: any backend change needed by
future phases must be authored in-repo first and deployed to the VPS only after quality gates pass.
