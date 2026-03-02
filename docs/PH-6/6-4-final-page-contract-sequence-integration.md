# E6.4: Build Final Page and Contract Sequence Integration

**Phase:** 6 - Contract Book and Signatures
**Class:** Feature
**Design Doc Reference:** 3.1, 3.8, 6.2, 6.3, 8.1
**Dependencies:**

- Phase 4: Filed Letters (phase exit criteria met).
- Phase 5: Sealed Thoughts (phase exit criteria met).
- E2.2: Define Design System Color and Typography Tokens (reading-surface and final-page typography tokens are
  available).
- E2.3: Implement AppState, Router, and Navigation Shell (contract-book route state container is available).
- E2.4: Build API Client, KeychainService, and Content Cache (contract and signature data is available from cache-backed
  state).
- E6.1: Build Contract Book Page Curl, Cover, and TOC (book-sequence framework is available).
- E6.2: Implement Contract Article Pagination Engine (article page groups and signature-page slots are available).
- E6.3: Build Signature Block and PencilKit Signing Flow (signature persistence behavior is available before terminal
  page rendering).
- Asset: None (no new static assets are required).
- Service: Contract-book page assembler accepts terminal page entries supplied by feature views.
- Service: AppState-backed signature state persistence is available for pre-final-page continuity.

---

## Goal

Build the contract closing page so "In Witness Whereof" copy renders as the terminal page after all article and
signature-page groups.

---

## Scope

### File Inventory

| File | Action | Responsibility |
| ---- | ------ | -------------- |
| `ExhibitA/ExhibitA/Features/Contract/FinalPageView.swift` | Create | Implement the final legal-closing page view with required copy, tokenized typography, and terminal contract-book sequence semantics. |

### Integration Points

**ExhibitA/ExhibitA/Features/Contract/FinalPageView.swift**

- Imports from: `ExhibitA/ExhibitA/Design/Theme.swift`, `ExhibitA/ExhibitA/App/AppState.swift`
- Imported by: `ExhibitA/ExhibitA/Features/Contract/ContractBookView.swift`
- State reads: Contract-book completion context required to position the final page after article groups
- State writes: None

---

## Out of Scope

- Page-curl wrapper mechanics, cover composition, and table-of-contents interactions (owned by E6.1).
- Article-body pagination logic and per-article footer numbering (owned by E6.2).
- Signature capture, signer-line gating, and upload mechanics (owned by E6.3).
- Push deep links, launch/background sync orchestration, and offline upload queue behavior (owned by Phase 7 epics E7.1
  and E7.2).
- Sound effects, haptic triggers, and transition polish (owned by Phase 8 epics E8.1 and E8.2).
- Backend implementation or VPS deployment execution (backend work remains repository-first and deployed only after
  local validation gates pass).

---

## Definition of Done

- [ ] FinalPageView renders the `IN WITNESS WHEREOF` heading and full closing copy from the design specification.
- [ ] FinalPageView renders closing-signature copy including `Dinesh & Carolina` and `Est. 2025` in tokenized legal
  style.
- [ ] FinalPageView renders on `background.reading` with contract typography tokens and no decorative ornaments.
- [ ] Contract-book sequence places FinalPageView after cover, TOC, and all article/signature-page groups.
- [ ] Reopening the contract book preserves prior signature state on preceding pages while FinalPageView remains the
  terminal page.
- [ ] Contract-book sequence still renders a valid terminal FinalPageView when contract article data is empty or
  temporarily unavailable.
- [ ] FinalPageView introduces no interactive controls that alter signature or content state.

---

## Implementation Notes

Use Design Doc 3.8 as the authoritative source for the final-page text and tone, and Design Doc 3.1 for page-sequence
ordering constraints. Use tokenized styles from Design Doc 6.2 and 6.3; do not introduce new visual primitives. Keep
this epic constrained to terminal-page composition and sequence integration semantics only. Treat backend data lifecycle
as upstream context governed by repository-first workflow: backend changes are authored and validated in-repo before any
VPS deployment operations.
