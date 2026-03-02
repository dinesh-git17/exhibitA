# E6.2: Implement Contract Article Pagination Engine

**Phase:** 6 - Contract Book and Signatures **Class:** Feature **Design Doc Reference:** 3.4, 3.5, 3.6, 6.2, 6.3, 10.6
**Dependencies:**

- Phase 4: Filed Letters (phase exit criteria met).
- Phase 5: Sealed Thoughts (phase exit criteria met).
- E2.2: Define Design System Color and Typography Tokens (contract body typography, separators, and page-number styles
  are available).
- E2.4: Build API Client, KeychainService, and Content Cache (contract article body text is available from cache-backed
  data models).
- E6.1: Build Contract Book Page Curl, Cover, and TOC (book container and article page host integration points are
  available).
- Asset: None (no new static assets are required).
- Service: AppState-backed contract article payloads are available to the contract feature layer.
- Service: ContractBook page host exposes viewport constraints needed for pagination measurement.

---

## Goal

Implement dynamic article pagination so contract content splits at natural boundaries with per-article page numbering
and a terminal signature-page slot.

---

## Scope

### File Inventory

| File | Action | Responsibility |
| ---- | ------ | -------------- |
| `ExhibitA/ExhibitA/Features/Contract/ContractPageView.swift` | Create | Implement article text measurement, natural-break pagination output, per-page contract rendering styles, and per-article page-number formatting. |

### Integration Points

**ExhibitA/ExhibitA/Features/Contract/ContractPageView.swift**

- Imports from: `ExhibitA/ExhibitA/Design/Theme.swift`, `ExhibitA/ExhibitA/App/AppState.swift`
- Imported by: `ExhibitA/ExhibitA/Features/Contract/ContractBookView.swift`
- State reads: Article title, article body text, article number, and ordered clause content for the active contract item
- State writes: None

---

## Out of Scope

- Page-curl wrapper mechanics, cover page composition, and TOC tap navigation (owned by E6.1).
- Signature line rendering, signer gating, and PencilKit capture/upload flow (owned by E6.3).
- Final closing page composition and terminal-sequence copy rendering (owned by E6.4).
- Offline upload queue retries and sync-log reconciliation for signature submissions (owned by Phase 7 epic E7.2).
- Sound effects, haptics, and transition polish for contract interactions (owned by Phase 8 epics E8.1 and E8.2).
- Backend API behavior changes or VPS deployment tasks (backend lifecycle remains repository-first and
  deploy-after-merge).

---

## Definition of Done

- [ ] ContractPageView renders article heading, preamble, agreement text, and clause content using contract typography
  tokens from the design system.
- [ ] Pagination logic splits article content at natural boundaries between clauses, paragraphs, or preamble/agreement
  sections when measured content exceeds the current page viewport.
- [ ] Section markers render in `accent.primary` semibold styling and WHEREAS preambles render in `text.secondary`
  italic styling.
- [ ] Per-article page footer renders in `Article <n> -- <current> of <total>` format with SF Pro Text 12pt
  `text.muted`.
- [ ] Pagination output appends a terminal signature-page slot after article body pages for every article sequence.
- [ ] Short-article content that fits one body page still produces a distinct final signature-page slot.
- [ ] Pagination recomputation reflects article body edits without app restart when updated content is reloaded from
  state/cache.
- [ ] ContractPageView handles empty or malformed article body text with a safe fallback rendering path and no runtime
  crash.

---

## Implementation Notes

Use Design Doc 3.4 as the canonical specification for splitting behavior and terminal signature-page semantics. Use
Design Doc 3.5 for heading and clause formatting expectations, and Design Doc 10.6 to keep contract content plain-text
driven without markdown parsing. Keep this epic scoped to pagination and rendering logic in `ContractPageView` only; do
not add signature-capture behavior or route orchestration here. Preserve repository-first operational language whenever
backend dependencies are referenced: backend modifications are authored and validated in-repo before any VPS rollout.
