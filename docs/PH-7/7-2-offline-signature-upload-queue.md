# E7.2: Implement Offline Signature Upload Queue

**Phase:** 7 - Sync, Push, and Offline **Class:** Integration **Design Doc Reference:** 7.4, 8.4, 10.3, 15.3
**Dependencies:**

- Phase 6: Contract Book and Signatures (phase exit criteria met)
- E0.2: Implement content, signature, sync, and device-token API endpoints (`POST /signatures` conflict and success
  responses are available)
- E2.4: Build API client, KeychainService, and content cache (authenticated signature upload surface and local PNG cache
  are available)
- E6.3: Build signature block and PencilKit signing flow (offline local save and optimistic signature state are already
  implemented)
- E6.4: Create final page and wire contract state integration (signature persistence path is integrated with cached
  contract state)
- Asset: Cached signature PNG artifacts are available from `SignatureCache` for queued upload payload construction
- Service: Background `URLSession` APIs are available for resilient upload retry when connectivity returns
- Service: Persistent local storage is available for queued upload records across app relaunch

---

## Goal

Implement a persistent background upload queue so signatures captured offline are retried automatically and reconciled
with server conflict/success outcomes.

---

## Scope

### File Inventory

| File | Action | Responsibility |
| ---- | ------ | -------------- |
| `ExhibitA/ExhibitA/Core/Sync/UploadQueue.swift` | Create | Implement queue persistence, background upload dispatch, retry behavior, and server-response reconciliation for signature upload jobs. |

### Integration Points

**ExhibitA/ExhibitA/Core/Sync/UploadQueue.swift**

- Imports from: `ExhibitA/ExhibitA/Core/API/ExhibitAClient.swift`, `ExhibitA/ExhibitA/Core/Cache/SignatureCache.swift`,
  `ExhibitA/ExhibitA/Core/Config.swift`, `ExhibitA/ExhibitA/App/AppState.swift`
- Imported by: `ExhibitA/ExhibitA/Features/Contract/SignaturePadView.swift`,
  `ExhibitA/ExhibitA/Features/Contract/SignatureBlockView.swift`
- State reads: Pending upload records, cached signature image references, signer identity, existing `signed_at` metadata
- State writes: Pending upload queue persistence, queued-item removal on terminal outcomes, local `signed_at`
  reconciliation after successful upload

---

## Out of Scope

- Sync-on-launch, BG refresh registration, push authorization, and deep-link routing (owned by E7.1).
- PencilKit drawing interactions and signature-pad UI behavior (owned by Phase 6 epic E6.3).
- Contract-book pagination, cover/TOC/final-page rendering, and non-upload contract navigation logic (owned by Phase 6
  epics E6.1, E6.2, and E6.4).
- Server-side upload endpoint semantics, authentication middleware, and response-schema changes (owned by backend Phase
  0 epics and not modified in this epic).
- VPS deployment operations or direct remote coding workflows (backend remains repository-first and deployed to VPS
  after local validation).
- Sound/haptic/motion polish attached to signature outcomes (owned by Phase 8 epics E8.1 and E8.2).

---

## Definition of Done

- [ ] Queue stores pending signature upload jobs durably so queued items remain after app termination and relaunch.
- [ ] Offline signature submission enqueues an upload job without blocking the signature confirmation UI path.
- [ ] Background `URLSession` processing retries queued uploads automatically when network connectivity is restored.
- [ ] Successful signature upload removes the corresponding queue entry and persists returned `signed_at` metadata
  locally.
- [ ] Server `409` duplicate responses remove the queued job and preserve existing local signed state without surfacing
  an error banner.
- [ ] Transient network or transport failures keep the job queued for later retry instead of dropping upload intent.
- [ ] Queue processing executes asynchronously and does not block main-thread interaction on contract screens.

---

## Implementation Notes

Use Design Doc 10.3 for offline-first behavior: local signature persistence is immediate, and network upload is eventual
through background retry. Treat the queue as the source of pending-upload truth and persist entries before dispatch so
retries survive process death. Reconcile server outcomes exactly per Design Doc 7.4 and endpoint behavior in 7.3.2
(`409` conflict is terminal, not a retry condition). Keep this epic constrained to upload queue infrastructure; push
sync and deep-link lifecycle wiring remain in E7.1.
