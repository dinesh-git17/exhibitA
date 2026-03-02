# E7.1: Implement Sync Engine Background Refresh Push Handling

**Phase:** 7 - Sync, Push, and Offline **Class:** Integration **Design Doc Reference:** 7.4, 8.2, 9.6, 9.7, 10.2, 10.3,
15.3 **Dependencies:**

- Phase 6: Contract Book and Signatures (phase exit criteria met)
- E0.2: Implement content, signature, sync, and device-token API endpoints (`GET /sync` and `POST /device-tokens` are
  available)
- E2.1: Scaffold Xcode project with build configuration (`ExhibitAApp.swift` app entry is present for lifecycle
  integration)
- E2.3: Implement AppState, Router, and navigation shell (`last_sync_at`, unread state, and route navigation contracts
  are available)
- E2.4: Build API client, KeychainService, and content cache (authenticated sync requests and cache writes are
  available)
- E6.4: Create final page and wire contract state integration (feature surfaces already consume cached content and
  signature state)
- Asset: Notification payload `route` field contract is available for deep-link routing from backend push events
- Service: `BGTaskScheduler` and `BGAppRefreshTask` APIs are available for background refresh orchestration
- Service: `UNUserNotificationCenter` and APNS device-token registration APIs are available for push enrollment

---

## Goal

Implement launch sync, background refresh, and push routing so content deltas, unread state, and deep-link navigation
stay consistent without manual user refresh.

---

## Scope

### File Inventory

| File | Action | Responsibility |
| ---- | ------ | -------------- |
| `ExhibitA/ExhibitA/Core/Sync/SyncService.swift` | Create | Implement sync-on-launch and background sync orchestration that fetches `/sync` deltas, refreshes cached content, and updates unread/sync state. |
| `ExhibitA/ExhibitA/App/ExhibitAApp.swift` | Modify | Wire app lifecycle hooks for BG task registration/scheduling, push authorization/token registration, and notification deep-link routing into Router. |

### Integration Points

**ExhibitA/ExhibitA/Core/Sync/SyncService.swift**

- Imports from: `ExhibitA/ExhibitA/Core/API/ExhibitAClient.swift`, `ExhibitA/ExhibitA/Core/Cache/ContentCache.swift`,
  `ExhibitA/ExhibitA/App/AppState.swift`, `ExhibitA/ExhibitA/Core/Config.swift`
- Imported by: `ExhibitA/ExhibitA/App/ExhibitAApp.swift`
- State reads: AppState `last_sync_at`, seen-content ID state, cached content snapshot
- State writes: AppState `last_sync_at`, unread-content state, refreshed cached content metadata

**ExhibitA/ExhibitA/App/ExhibitAApp.swift**

- Imports from: `ExhibitA/ExhibitA/App/AppState.swift`, `ExhibitA/ExhibitA/App/Router.swift`,
  `ExhibitA/ExhibitA/Core/Sync/SyncService.swift`
- Imported by: None (`@main` app entry)
- State reads: App lifecycle phase, Router route payload mapping, AppState sync readiness
- State writes: Router navigation path on push deep link, AppState sync state via SyncService invocation

---

## Out of Scope

- Offline signature-upload queue durability and retry semantics (owned by E7.2).
- Signature capture UX, local optimistic signature render, and contract-book interaction flows (owned by Phase 6 epics
  E6.1 to E6.4).
- Audio, haptics, and animation polish behavior after sync or push events (owned by Phase 8 epics E8.1 and E8.2).
- Backend endpoint implementation changes for sync/device token APIs (owned by Phase 0 epic E0.2 and already delivered
  via repository-first backend workflow).
- VPS operational tasks such as systemd restart, Caddy edits, or firewall actions (out of scope for this iOS integration
  epic and approval-gated by governance).

---

## Definition of Done

- [ ] App launch executes sync flow that calls `GET /sync?since=` using the persisted `last_sync_at` value.
- [ ] Sync engine fetches changed content entities from returned delta IDs and writes updated records to local content
  cache.
- [ ] Sync success updates `last_sync_at` in AppState and persists it so the next launch uses the new timestamp.
- [ ] `BGAppRefreshTask` identifier registers at app startup and schedules future background refresh execution.
- [ ] Background refresh executes the same sync code path as foreground launch and updates cache/unread state on
  success.
- [ ] First-launch notification enrollment requests authorization and registers device token with `POST /device-tokens`
  using signer identity.
- [ ] Push payloads containing a `route` field map to Router destinations and navigate to the corresponding content
  screen.
- [ ] New content discovered through sync updates unread badge state based on unseen content IDs.
- [ ] Sync failures preserve the previous cached snapshot and do not crash or block app startup.

---

## Implementation Notes

Use Design Doc 7.4 as the source of truth for sync sequencing (`last_sync_at` read, delta fetch, cache update, timestamp
write). Register BG tasks in `ExhibitAApp` and route all sync execution through `SyncService` to avoid duplicated logic
between foreground and background flows. Use Design Doc 9.6/9.7 push mechanics for token registration and deep-link
payload handling, and Router contracts from Design Doc 8.2 for navigation resolution. Keep this epic iOS-only; backend
sync/device-token services are prerequisite repository-authored artifacts from Phase 0 and are not modified here.
