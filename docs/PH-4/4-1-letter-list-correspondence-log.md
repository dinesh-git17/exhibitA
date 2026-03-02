# E4.1: Build Correspondence Log Letter List

**Phase:** 4 - Filed Letters **Class:** Feature **Design Doc Reference:** 4.1, 6.2, 6.3, 7.4, 8.2 **Dependencies:**

- Phase 3: Home Screen (phase exit criteria met)
- E3.1: Build Home Screen Filing Cabinet Navigation (letters route entry point available)
- E2.2: Define Design System Color and Typography Tokens (letter list token set available)
- E2.3: Implement AppState, Router, and Navigation Shell (route and unread state contracts available)
- E2.4: Build API Client, KeychainService, and Content Cache (cached `letter` records available)
- E2.5: Create Shared Foundation UI Components (`ExhibitBadge`, `ClassificationLabel`, and `UnreadBadge` available)
- Asset: SF Symbol rendering support is available in iOS 26 runtime for list-row iconography
- Service: Router route case `.letterDetail(id:)` is available for list-to-detail navigation
- Service: ContentCache read path for cached letters is available through AppState data flow

---

## Goal

Build the Filed Letters correspondence log list so cached letter records render with correct metadata, unread
indicators, and deterministic navigation into letter detail.

---

## Scope

### File Inventory

| File | Action | Responsibility |
| ---- | ------ | -------------- |
| `ExhibitA/ExhibitA/Features/Letters/LetterListView.swift` | Create | Implement the Filed Letters list screen with header, letter rows, unread indicators, ordering, and router navigation to letter detail. |

### Integration Points

**ExhibitA/ExhibitA/Features/Letters/LetterListView.swift**

- Imports from: `ExhibitA/ExhibitA/Design/Theme.swift`, `ExhibitA/ExhibitA/Design/Components/ExhibitBadge.swift`,
  `ExhibitA/ExhibitA/Design/Components/ClassificationLabel.swift`,
  `ExhibitA/ExhibitA/Design/Components/UnreadBadge.swift`, `ExhibitA/ExhibitA/App/AppState.swift`,
  `ExhibitA/ExhibitA/App/Router.swift`
- Imported by: `ExhibitA/ExhibitA/App/ExhibitAApp.swift` through `navigationDestination` wiring for letters
- State reads: AppState cached content filtered to `type == letter`, per-letter unread state, and list ordering fields
- State writes: Router navigation path through `navigate(to: .letterDetail(id:))`

---

## Out of Scope

- Letter detail rendering and markdown typography surface (owned by E4.2).
- Home card badge logic and section-count computation on the filing cabinet screen (owned by E3.1).
- Thought list and thought detail feature surfaces (owned by Phase 5 epics E5.1 and E5.2).
- Contract book, signature capture, and page-curl flows (owned by Phase 6 epics E6.1 to E6.4).
- Background sync refresh and push-triggered route handling (owned by Phase 7 epic E7.1).
- Sound, haptics, and motion polish beyond baseline unread indicator behavior (owned by Phase 8 epics E8.1 and E8.2).
- Backend API changes, VPS service operations, and deployment actions (completed in repository-first backend phases
  before VPS deployment).

---

## Definition of Done

- [ ] Letter list screen renders the header `CORRESPONDENCE ON RECORD` with subtitle `Dinesh & Carolina` when the
  letters route appears.
- [ ] Each rendered row displays exhibit identifier, quoted title, filed date, and classification label from the cached
  letter record.
- [ ] Rows render a 0.5pt separator using the `border.separator` token between adjacent entries.
- [ ] Unread indicator renders only for letter IDs that AppState marks as unread and remains hidden for read letters.
- [ ] Letter rows are ordered by `section_order` descending so the most recent filing appears first.
- [ ] Tapping a row pushes `.letterDetail(id:)` on Router navigation state with the tapped letter ID.
- [ ] List typography and colors use design tokens defined in Phase 2 and contain no hardcoded color literals.
- [ ] List layout renders without overlap or clipping on iPhone SE and iPhone 16 Pro Max viewport classes.

---

## Implementation Notes

Implement list structure exactly per Design Doc 4.1 and use tokenized styling from 6.2 and 6.3. Read letter records from
the Phase 2 cache/state pipeline rather than initiating network fetches in the view layer. Keep this epic constrained to
list behavior only; detail rendering belongs to E4.2. Route transitions must use the Router contract from Design Doc 8.2
and Phase 2 foundation epics. No backend or VPS modifications are part of this feature slice; backend remains
repository-authored and already deployed from earlier phases.
