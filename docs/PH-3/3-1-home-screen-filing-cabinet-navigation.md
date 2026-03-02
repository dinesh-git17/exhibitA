# E3.1: Build Home Screen Filing Cabinet Navigation

**Phase:** 3 - Home Screen **Class:** Feature **Design Doc Reference:** 2.1, 6.2, 6.3, 7.4, 8.2 **Dependencies:**

- Phase 2: iOS Foundation (phase exit criteria met)
- E2.2: Define Design System Color and Typography Tokens (all color, typography, spacing, and shadow tokens available)
- E2.3: Implement AppState, Router, and Navigation Shell (home route hosting and navigation contract available)
- E2.4: Build API Client, KeychainService, and Content Cache (cached content available for card counts)
- E2.5: Create Shared UI Components (MonogramView and UnreadBadge available)
- Asset: SF Symbols `book.closed`, `envelope`, and `lock.fill` are available in iOS 26 runtime
- Service: `Router.navigate(to:)` and `NavigationPath` destination handling are available from the app shell
- Service: UserDefaults-backed unread state is available through AppState

---

## Goal

Build the filing-cabinet home screen so header, entry cards, unread indicators, and card navigation are fully functional
on all supported iPhone sizes.

---

## Scope

### File Inventory

| File | Action | Responsibility |
| ---- | ------ | -------------- |
| `ExhibitA/ExhibitA/Features/Home/HomeView.swift` | Create | Implement the complete Home screen layout, data binding, unread badge rendering, and router-driven card navigation defined for Phase 3. |

### Integration Points

**ExhibitA/ExhibitA/Features/Home/HomeView.swift**

- Imports from: `ExhibitA/ExhibitA/Design/Theme.swift`, `ExhibitA/ExhibitA/Design/Components/MonogramView.swift`,
  `ExhibitA/ExhibitA/Design/Components/UnreadBadge.swift`, `ExhibitA/ExhibitA/App/AppState.swift`,
  `ExhibitA/ExhibitA/App/Router.swift`
- Imported by: `ExhibitA/ExhibitA/App/ExhibitAApp.swift`
- State reads: AppState content counts per section, AppState unread state per section
- State writes: Router navigation path mutations through `navigate(to:)` when cards are tapped

---

## Out of Scope

- Filed Letters list and detail screens (owned by Phase 4 epics E4.1 and E4.2).
- Sealed Thoughts list and detail screens (owned by Phase 5 epics E5.1 and E5.2).
- Contract page-curl reader, pagination, and signature capture flows (owned by Phase 6 epics E6.1 to E6.4).
- Background sync execution, push registration, and unread-state refresh from `/sync` (owned by Phase 7 epic E7.1).
- Sound effects, haptic feedback, and card parallax polish (owned by Phase 8 epics E8.1 and E8.2).
- Backend API implementation, VPS runtime changes, and deployment steps (completed in repository-first backend phases
  before VPS deployment in Phases 0 and 1).

---

## Definition of Done

- [ ] Home screen renders on launch with the filing-cabinet structure on `background.primary` using the Phase 2 theme
  tokens.
- [ ] Header renders `EXHIBIT A` in New York Bold 34pt, subtitle `Case No. DC-2025-0214 | Dinesh & Carolina` in SF Pro
  Text 14pt, and `EA` monogram centered below subtitle.
- [ ] Three entry cards render with the exact labels and subtitles from Design Doc 2.1 and show SF Symbols
  `book.closed`, `envelope`, and `lock.fill` with tokenized accent colors.
- [ ] Entry cards render on `background.secondary` with 12pt continuous corners and warm layered shadow values from
  Design Doc 6.2.
- [ ] Filed Letters and Sealed Thoughts cards display live item counts derived from current AppState content for their
  section types.
- [ ] Entry cards are not rendered as a uniform grid and present variable heights based on subtitle and metadata
  content.
- [ ] Unread badge renders only for sections marked unread in AppState and remains hidden for sections with no unread
  content.
- [ ] Tapping each card mutates router navigation state and routes to the correct destination for Contract, Letters, and
  Thoughts sections.
- [ ] Footer legal text renders at the bottom in New York Regular Italic 13pt with `text.muted` and remains visible
  without overlap on iPhone SE and iPhone 16 Pro Max layouts.

---

## Implementation Notes

Use Design Doc 2.1 as the source of truth for exact strings, card copy, and section semantics. Use token values from
Design Doc 6.2 and typography roles from 6.3; do not hardcode raw colors or font literals in HomeView. Consume unread
and count state from AppState rather than performing network fetches from the Home view. Drive navigation through Router
contracts established in the Phase 2 foundation so Home remains a pure feature surface. Keep this epic repository-local
to iOS code; no direct VPS coding is part of this phase.
