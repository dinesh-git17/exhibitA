# E6.1: Build Contract Book Page Curl, Cover, and TOC

**Phase:** 6 - Contract Book and Signatures **Class:** Feature **Design Doc Reference:** 3.1, 3.2, 3.3, 6.2, 6.3, 8.1,
8.3 **Dependencies:**

- Phase 4: Filed Letters (phase exit criteria met).
- Phase 5: Sealed Thoughts (phase exit criteria met).
- E2.2: Define Design System Color and Typography Tokens (contract surfaces, typography roles, separators, and shadows
  are available).
- E2.3: Implement AppState, Router, and Navigation Shell (contract-book route and navigation shell are available).
- E2.4: Build API Client, KeychainService, and Content Cache (contract content payloads are available for rendering).
- E2.5: Create Shared UI Components (`MonogramView` is available for cover-page branding).
- E4.2: Build Letter Detail Reader with Markdown Rendering (reading-surface conventions are validated and reusable).
- E5.2: Build Sealed Thought Detail View (paper-noise reading composition is validated and reusable).
- Asset: None (no new static assets are required).
- Service: `Router.navigate(to: .contractBook)` destination wiring is available from the app shell.
- Service: `UIPageViewController` `.pageCurl` runtime support is available on iOS 26+.

---

## Goal

Build the contract-book shell so page-curl navigation, legal cover page, and tappable table of contents function as one
cohesive entry surface.

---

## Scope

### File Inventory

| File | Action | Responsibility |
| ---- | ------ | -------------- |
| `ExhibitA/ExhibitA/Features/Contract/ContractBookView.swift` | Create | Implement the SwiftUI wrapper around `UIPageViewController` with coordinator-driven page ordering, swipe transitions, and TOC jump handling. |
| `ExhibitA/ExhibitA/Features/Contract/CoverPageView.swift` | Create | Implement the full legal cover page composition with required copy, party metadata, case details, and monogram styling. |
| `ExhibitA/ExhibitA/Features/Contract/TOCPageView.swift` | Create | Implement the table of contents layout with dotted leaders, page-number metadata, and tap-to-jump actions for article entries. |

### Integration Points

**ExhibitA/ExhibitA/Features/Contract/ContractBookView.swift**

- Imports from: `ExhibitA/ExhibitA/App/AppState.swift`, `ExhibitA/ExhibitA/App/Router.swift`,
  `ExhibitA/ExhibitA/Features/Contract/CoverPageView.swift`, `ExhibitA/ExhibitA/Features/Contract/TOCPageView.swift`
- Imported by: `ExhibitA/ExhibitA/App/ExhibitAApp.swift` (contract-book route destination)
- State reads: Contract article collection and current-page context from AppState-backed feature state
- State writes: Current page index and route-driven navigation state for in-book jumps

**ExhibitA/ExhibitA/Features/Contract/CoverPageView.swift**

- Imports from: `ExhibitA/ExhibitA/Design/Theme.swift`, `ExhibitA/ExhibitA/Design/Components/MonogramView.swift`
- Imported by: `ExhibitA/ExhibitA/Features/Contract/ContractBookView.swift`
- State reads: Filed date display value passed from contract-book composition
- State writes: None

**ExhibitA/ExhibitA/Features/Contract/TOCPageView.swift**

- Imports from: `ExhibitA/ExhibitA/Design/Theme.swift`
- Imported by: `ExhibitA/ExhibitA/Features/Contract/ContractBookView.swift`
- State reads: Ordered article titles, numbers, and resolved in-book target indexes
- State writes: Selected TOC destination index through tap callbacks

---

## Out of Scope

- Dynamic clause pagination and per-article text-splitting rules (owned by E6.2).
- Signature line states, PencilKit sheet presentation, and signature upload behavior (owned by E6.3).
- Final closing page content and terminal book-sequence composition (owned by E6.4).
- Push deep linking, launch-time sync deltas, and background refresh orchestration (owned by Phase 7 epic E7.1).
- Sound, haptic, and animation polish on page transitions (owned by Phase 8 epics E8.1 and E8.2).
- Backend endpoint implementation and VPS-side coding operations (repository-first backend authoring remains outside
  this iOS feature epic).

---

## Definition of Done

- [ ] ContractBookView renders a `UIPageViewController` with `.pageCurl` transition style on contract-book route launch.
- [ ] Swipe gestures advance and reverse pages with coordinator-managed state updates across the book sequence.
- [ ] Cover page renders legal title, party names, case number, filed date placeholder, jurisdiction line, quote, and
  `EA` monogram using contract token styles.
- [ ] TOC page renders all available contract articles with dotted leaders and page-number metadata in legal-brief
  format.
- [ ] Tapping a TOC entry navigates to the first page for the selected article inside the same `UIPageViewController`
  session.
- [ ] Current page tracking updates after both swipe navigation and TOC jump navigation actions.
- [ ] Contract-book shell renders safely when article collection is empty, preserving cover and TOC without runtime
  crashes.
- [ ] Cover and TOC views resolve colors and typography through `Theme` tokens without hardcoded visual literals.

---

## Implementation Notes

Use Design Doc 3.1 to enforce the canonical page sequence contract (`Cover -> TOC -> Articles -> Final Page`) and Design
Doc 8.3 for the exact `UIPageViewController` wrapper pattern. Use Design Doc 3.2 and 3.3 as the source of truth for
cover and TOC copy structure. Keep this epic restricted to book-shell composition and navigation mechanics; content
pagination and signature behavior are intentionally deferred to E6.2 and E6.3. Preserve repository-first workflow
language in all planning notes: backend changes remain authored and validated in-repo before any VPS deployment step.
