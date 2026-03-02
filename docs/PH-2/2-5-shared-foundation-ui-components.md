# E2.5: Create Shared Foundation UI Components

**Phase:** 2 - iOS Foundation **Class:** Infrastructure **Design Doc Reference:** 2.1, 6.2, 6.3, 8.1 **Dependencies:**

- Phase 2: iOS Foundation (`E2.1` and `E2.2` completed)
- E2.1: Scaffold Xcode Project and Build Configuration (component target and previews compile)
- E2.2: Define Design Tokens and Paper Noise System (canonical colors and typography available)
- Asset: Home-screen and metadata labeling semantics from Design Doc 2.1
- Service: SwiftUI previews are available for component validation

---

## Goal

Create the shared UI component primitives required by feature phases so monogram, labels, exhibit badges, and unread
indicators render consistently from centralized design tokens.

---

## Scope

### File Inventory

| File | Action | Responsibility |
| ---- | ------ | -------------- |
| `ExhibitA/ExhibitA/Design/Components/MonogramView.swift` | Create | Implement reusable `EA` monogram component with tokenized typography and accent styling. |
| `ExhibitA/ExhibitA/Design/Components/ClassificationLabel.swift` | Create | Implement reusable uppercase classification label component with tracking and tokenized typography. |
| `ExhibitA/ExhibitA/Design/Components/ExhibitBadge.swift` | Create | Implement reusable exhibit badge component for identifiers like `EXHIBIT L-001`. |
| `ExhibitA/ExhibitA/Design/Components/UnreadBadge.swift` | Create | Implement reusable unread dot indicator with gentle 2-second breathing animation cycle. |

### Integration Points

**ExhibitA/ExhibitA/Design/Components/MonogramView.swift**

- Imports from: `ExhibitA/ExhibitA/Design/Theme.swift`
- Imported by: home header and cover-page features in later phases
- State reads: Color scheme for token resolution
- State writes: None

**ExhibitA/ExhibitA/Design/Components/ClassificationLabel.swift**

- Imports from: `ExhibitA/ExhibitA/Design/Theme.swift`
- Imported by: letters list/detail and admin-adjacent metadata surfaces in later phases
- State reads: Color scheme for token resolution
- State writes: None

**ExhibitA/ExhibitA/Design/Components/ExhibitBadge.swift**

- Imports from: `ExhibitA/ExhibitA/Design/Theme.swift`
- Imported by: letters list/detail features in later phases
- State reads: Provided exhibit identifier string
- State writes: None

**ExhibitA/ExhibitA/Design/Components/UnreadBadge.swift**

- Imports from: `ExhibitA/ExhibitA/Design/Theme.swift`
- Imported by: home, letters, thoughts, and contract status surfaces in later phases
- State reads: unread boolean state and animation phase timing
- State writes: None

---

## Out of Scope

- Any screen-level layout implementation for home, letters, thoughts, or contract pages (Phase 3+ feature epics).
- Design-token creation or updates in `Theme.swift` (owned by E2.2).
- App-state unread logic and persistence behavior in `AppState` (owned by E2.3).
- Audio/haptic animation polish wiring beyond unread-dot breathing animation baseline (Phase 8 scope).
- Backend-driven badge state sync or push-response behaviors (Phase 7 integration scope).

---

## Definition of Done

- [ ] `MonogramView` renders `EA` using New York Bold and `accent.primary` token styling from the design system.
- [ ] `ClassificationLabel` renders uppercase text with `accent.soft` color and 2pt tracking.
- [ ] `ExhibitBadge` formats and displays exhibit identifiers in the expected uppercase badge style.
- [ ] `UnreadBadge` renders a token-colored dot and animates with a 2-second breathing pulse cycle.
- [ ] All four components compile and render in SwiftUI previews without requiring feature-module dependencies.
- [ ] Components import `Theme` tokens instead of hardcoded color or font literals.
- [ ] Components expose interfaces that are reusable by downstream feature views without per-screen forks.
- [ ] Unread badge animation can be disabled by input state when unread is false.

---

## Implementation Notes

Use the exact component intent from Design Doc 8.1 and style values from Design Doc 6.2 and 6.3 so downstream screens
consume consistent primitives. Keep component APIs narrow and reusable; each file should own one component concern only.
Implement unread-badge pulse timing to match the 2-second breathing cadence in Design Doc 2.1 while keeping other motion
polish deferred to Phase 8. Do not embed feature routing or data-fetch logic in component files.
