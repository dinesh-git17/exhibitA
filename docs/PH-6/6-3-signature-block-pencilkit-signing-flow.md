# E6.3: Build Signature Block and PencilKit Signing Flow

**Phase:** 6 - Contract Book and Signatures **Class:** Feature **Design Doc Reference:** 3.7, 6.5, 8.4, 10.3, 10.7
**Dependencies:**

- Phase 4: Filed Letters (phase exit criteria met).
- Phase 5: Sealed Thoughts (phase exit criteria met).
- E2.1: Scaffold Xcode Project and Build Configuration (`Config.signerIdentity` build-time identity is available).
- E2.2: Define Design System Color and Typography Tokens (signature colors, typography, and line styling tokens are
  available).
- E2.4: Build API Client, KeychainService, and Content Cache (`POST /signatures` client path and local signature cache
  are available).
- E6.1: Build Contract Book Page Curl, Cover, and TOC (contract-book page host is available).
- E6.2: Implement Contract Article Pagination Engine (article-level signature-page slot is available per contract).
- Asset: None (no bundled signature assets are required).
- Service: `ExhibitAClient` signature-upload interface is available for `POST /signatures`.
- Service: `SignatureCache` PNG persistence interface is available for optimistic local writes.
- Service: `Config.signerIdentity` is available for signer-line tap gating.

---

## Goal

Build the contract signature interaction so unsigned lines, signer-restricted PencilKit capture, local persistence, and
API upload execute as one end-to-end flow.

---

## Scope

### File Inventory

| File | Action | Responsibility |
| ---- | ------ | -------------- |
| `ExhibitA/ExhibitA/Features/Contract/SignatureBlockView.swift` | Create | Implement signed/unsigned line rendering, signer-gated interaction, signature image placement, and signed-date display behavior. |
| `ExhibitA/ExhibitA/Features/Contract/SignaturePadView.swift` | Create | Implement PencilKit capture sheet, clear/sign actions, PNG export, optimistic cache write, and upload trigger integration. |

### Integration Points

**ExhibitA/ExhibitA/Features/Contract/SignatureBlockView.swift**

- Imports from: `ExhibitA/ExhibitA/Design/Theme.swift`, `ExhibitA/ExhibitA/App/AppState.swift`,
  `ExhibitA/ExhibitA/Core/Config.swift`, `ExhibitA/ExhibitA/Features/Contract/SignaturePadView.swift`
- Imported by: `ExhibitA/ExhibitA/Features/Contract/ContractPageView.swift`
- State reads: Current contract content ID, persisted signature state by signer, and build signer identity
- State writes: Local signature-state updates after successful or duplicate-resolved sign operations

**ExhibitA/ExhibitA/Features/Contract/SignaturePadView.swift**

- Imports from: `ExhibitA/ExhibitA/Design/Theme.swift`, `ExhibitA/ExhibitA/Core/API/ExhibitAClient.swift`,
  `ExhibitA/ExhibitA/Core/Cache/SignatureCache.swift`, `ExhibitA/ExhibitA/Core/Config.swift`
- Imported by: `ExhibitA/ExhibitA/Features/Contract/SignatureBlockView.swift`
- State reads: Active `content_id`, active signer identity, and existing drawing buffer state
- State writes: Exported PNG bytes to signature cache, upload-request trigger state, and signed timestamp on success

---

## Out of Scope

- Book-shell page-curl container, cover, and TOC behaviors (owned by E6.1).
- Contract clause pagination and page-number rendering mechanics (owned by E6.2).
- Final "In Witness Whereof" page composition and terminal-sequence behavior (owned by E6.4).
- Background retry queue orchestration for offline signature upload recovery (owned by Phase 7 epic E7.2).
- Haptic feedback and signature-placement animation polish (owned by Phase 8 epic E8.2).
- Backend endpoint changes, schema migrations, and VPS-side authoring/deployment work (backend changes remain
  repository-first and deploy-after-validation).

---

## Definition of Done

- [ ] Unsigned signature lines render dotted affordances with `Tap to sign` labels in contract signature blocks.
- [ ] Only the signer line matching `Config.signerIdentity` is tappable in unsigned state.
- [ ] Tapping an eligible unsigned line presents `SignaturePadView` as a half-sheet capture surface.
- [ ] PencilKit canvas initializes with `drawingPolicy = .anyInput`, tool picker disabled, and pen tool color/width
  matching design constraints.
- [ ] Selecting `Clear` removes all in-canvas strokes without dismissing the sheet.
- [ ] Selecting `Sign` exports PNG bytes and writes the image to `SignatureCache` before network upload begins.
- [ ] Signature upload request calls `POST /signatures` with contract `content_id`, signer value, and PNG payload.
- [ ] Successful upload marks the signer state as signed, stores the signed timestamp, and makes the line
  non-interactive.
- [ ] Signed signature rendering displays persisted PNG imagery with 1-3 degree random rotation and date metadata below.
- [ ] Duplicate-sign conflicts resolve to existing signed state without enabling re-sign.

---

## Implementation Notes

Implement this flow exactly from Design Doc 3.7 and 8.4: tap line, capture via PencilKit, export PNG, optimistic local
persist, and API submission. Use Design Doc 6.5 for signature-area visual treatment and Design Doc 10.7 for signer
identity semantics. Keep signature immutability strict: once signed, interaction is blocked. Defer background retry
queue or network-recovery orchestration to Phase 7. Maintain repository-first architecture language for backend
references; deployment to VPS remains a post-validation operation and is not implemented inside this iOS feature epic.
