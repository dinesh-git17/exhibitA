# E2.4: Build API Client, Keychain, and Local Cache

**Phase:** 2 - iOS Foundation **Class:** Infrastructure **Design Doc Reference:** 7.3, 7.3.1, 7.4, 8.1, 10.3, 10.7
**Dependencies:**

- Phase 2: iOS Foundation (`E2.1` scaffold completed)
- E2.1: Scaffold Xcode Project and Build Configuration (`Config` and app shell available)
- E0.2: Implement Content, Signature, and Sync APIs (endpoint contract and response envelopes are live)
- E0.3: Enforce Auth and Production Deployment Controls (Bearer token auth path is live)
- Asset: API response schemas from Design Doc 7.3.1 and error-envelope contract from Design Doc 7.3.2
- Service: backend deployment reachable at `exhibita.dineshd.dev`, promoted through repository-first backend workflow
- Service: iOS Keychain access with `kSecAttrAccessibleAfterFirstUnlock` is available

---

## Goal

Build the authenticated networking and offline storage layer so iOS can fetch backend content, store API credentials
securely, and cache content/signatures for offline-first behavior.

---

## Scope

### File Inventory

| File | Action | Responsibility |
| ---- | ------ | -------------- |
| `ExhibitA/ExhibitA/Core/API/ExhibitAClient.swift` | Create | Implement async API client methods for all phase-defined endpoints with Bearer auth support. |
| `ExhibitA/ExhibitA/Core/API/APIModels.swift` | Create | Define Codable request and response models aligned to backend schema contracts. |
| `ExhibitA/ExhibitA/Core/Cache/ContentCache.swift` | Create | Implement JSON file persistence and retrieval for content entities in the caches directory. |
| `ExhibitA/ExhibitA/Core/Cache/SignatureCache.swift` | Create | Implement PNG signature persistence and retrieval by signature/content identifier. |
| `ExhibitA/ExhibitA/Core/Security/KeychainService.swift` | Create | Implement secure API key store/retrieve/delete operations backed by iOS Keychain. |

### Integration Points

**ExhibitA/ExhibitA/Core/API/ExhibitAClient.swift**

- Imports from: `ExhibitA/ExhibitA/Core/API/APIModels.swift`, `ExhibitA/ExhibitA/Core/Security/KeychainService.swift`,
  `ExhibitA/ExhibitA/Core/Config.swift`
- Imported by: sync layer, feature data loaders, signature upload flow in later phases
- State reads: Keychain-stored API key and configured base URL
- State writes: None

**ExhibitA/ExhibitA/Core/API/APIModels.swift**

- Imports from: None
- Imported by: `ExhibitA/ExhibitA/Core/API/ExhibitAClient.swift`, cache modules
- State reads: None
- State writes: None

**ExhibitA/ExhibitA/Core/Cache/ContentCache.swift**

- Imports from: `ExhibitA/ExhibitA/Core/API/APIModels.swift`
- Imported by: sync service, feature data providers, app startup loaders in later phases
- State reads: Content JSON files in app caches directory
- State writes: Content JSON files in app caches directory

**ExhibitA/ExhibitA/Core/Cache/SignatureCache.swift**

- Imports from: None
- Imported by: signature flow and contract rendering modules in later phases
- State reads: Signature PNG files in app caches directory
- State writes: Signature PNG files in app caches directory

**ExhibitA/ExhibitA/Core/Security/KeychainService.swift**

- Imports from: None
- Imported by: `ExhibitA/ExhibitA/Core/API/ExhibitAClient.swift`, app setup in later phases
- State reads: Keychain item values for API credentials
- State writes: Keychain item values for API credentials

---

## Out of Scope

- App navigation shell and unread-state orchestration logic (owned by E2.3).
- Design token and paper-noise definition (owned by E2.2).
- Shared UI component rendering (`MonogramView`, `ClassificationLabel`, `UnreadBadge`) (owned by E2.5).
- Push registration workflows and background sync orchestration logic (Phase 7 integration scope).
- Backend endpoint evolution or VPS runtime reconfiguration (handled in backend phases via repository-first deploy
  flow).

---

## Definition of Done

- [ ] `ExhibitAClient` sends `Authorization: Bearer <key>` on authenticated requests using key material from
  `KeychainService`.
- [ ] `ExhibitAClient` exposes async methods for content listing/filtering, item fetch, signature image fetch, signature
  upload, sync fetch, and device-token registration.
- [ ] `APIModels` decode and encode payloads consistent with Design Doc 7.3.1 field names and types.
- [ ] `ContentCache` writes content entities to JSON files and restores the same entities without data loss.
- [ ] `SignatureCache` writes PNG data and restores PNG data by deterministic identifier lookup.
- [ ] `KeychainService` stores and retrieves API keys using `kSecAttrAccessibleAfterFirstUnlock` accessibility.
- [ ] API-layer errors surface typed failures for HTTP and decoding paths without exposing secret token data in logs.
- [ ] Local cache reads succeed without network connectivity after data has been cached once.

---

## Implementation Notes

Use backend contracts from Design Doc 7.3 as immutable schema references for model definitions and request builders.
Keep Keychain handling aligned with Design Doc 10.7, including `kSecAttrAccessibleAfterFirstUnlock` for background-safe
access, and never persist raw keys in user defaults or source files. Implement cache persistence as JSON/PNG files in
caches directory per Design Doc 10.3, avoiding CoreData/SwiftData introduction. Consume the already deployed backend
produced via repository-first backend phases; this epic does not redefine backend deployment behavior.
