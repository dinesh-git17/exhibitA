# E8.1: Add Sound Service and Settings Toggle

**Phase:** 8 - Sound, Haptics, and Animation Polish
**Class:** Integration
**Design Doc Reference:** 6.8, 8.1, 10.5
**Dependencies:**

- Phase 7: Sync, Push, and Offline (phase exit criteria met).
- E2.3: Implement AppState, Router, and Navigation Shell (shared state patterns and environment injection contracts are
  available).
- E2.5: Create Shared UI Components (home-surface component conventions are established for consistent settings UI
  integration).
- E6.1: Build Contract Book Page Curl, Cover, and TOC (contract-book interaction points that emit page-turn events are
  available to consume sound cues).
- E6.3: Build Signature Block and PencilKit Signing Flow (signature-confirmation interaction points are available to
  consume sound cues).
- E7.1: Implement Sync Engine, Background Refresh, and Push Notification Handling (new-content sync trigger exists for
  notification-chime event emission).
- Asset: Runtime audio resources for `page_turn`, `signature_placed`, and `new_content_chime` are present in the iOS
  app bundle.
- Service: UserDefaults persistence interface is available for global sound on/off preference.

---

## Goal

Implement centralized sound playback and persisted sound preferences so page-turn, signature, and new-content cues are
uniformly controlled across the app.

---

## Scope

### File Inventory

| File | Action | Responsibility |
| ---- | ------ | -------------- |
| `ExhibitA/ExhibitA/Core/SoundService.swift` | Create | Implement a single sound service that resolves named cues, enforces global enablement state, and exposes deterministic play APIs for feature surfaces. |
| `ExhibitA/ExhibitA/Features/Home/SettingsView.swift` | Create | Implement a settings view that exposes the global sound toggle and persists user preference for all sound cues. |

### Integration Points

**ExhibitA/ExhibitA/Core/SoundService.swift**

- Imports from: Foundation and AVFoundation runtime interfaces, app configuration/state container conventions
- Imported by: `ExhibitA/ExhibitA/Features/Contract/ContractBookView.swift`,
  `ExhibitA/ExhibitA/Features/Contract/SignaturePadView.swift`, sync/push handling integration points, and
  `ExhibitA/ExhibitA/Features/Home/SettingsView.swift`
- State reads: Persisted sound-enabled preference key from UserDefaults
- State writes: Persisted sound-enabled preference key updates and in-memory playback state

**ExhibitA/ExhibitA/Features/Home/SettingsView.swift**

- Imports from: `ExhibitA/ExhibitA/Core/SoundService.swift`, `ExhibitA/ExhibitA/Design/Theme.swift`
- Imported by: Home-surface presentation flow (wired by E8.2 view integration epic)
- State reads: Current global sound preference state from SoundService
- State writes: Global sound preference toggles through SoundService API

---

## Out of Scope

- HomeView gear-button presentation wiring and settings-entry animation behavior (owned by E8.2, which modifies
  `HomeView.swift`).
- Haptic trigger wiring and motion timing behavior in contract and home views (owned by E8.2).
- Audio-trigger call-site wiring in feature views (owned by E8.2; E8.1 only provides service contracts).
- Backend implementation changes, VPS authoring, or deployment operations (backend remains repository-first and deploys
  after local repository validation).
- Audio mastering, asset redesign, or replacement of cue files (deferred content/polish work outside this integration
  slice).

---

## Definition of Done

- [ ] SoundService exposes named cue playback APIs for page-turn, signature-placed, and new-content events.
- [ ] SoundService blocks cue playback when global sound preference is disabled.
- [ ] SoundService persists sound preference changes in UserDefaults and restores them on app relaunch.
- [ ] SoundService initializes default sound preference as enabled on first launch.
- [ ] SettingsView renders a deterministic sound on/off control bound to SoundService preference state.
- [ ] Toggling SettingsView sound control updates persisted preference and immediately affects SoundService playback
  eligibility.
- [ ] SettingsView renders safely when SoundService state is unavailable, without runtime crash.

---

## Implementation Notes

Use Design Doc 6.8 as the authoritative contract for the three sound cues and persisted toggle semantics. Keep
SoundService as the single playback authority so feature views do not duplicate player setup logic. Persist preference
through a single UserDefaults key and expose an explicit API for reads and writes; do not rely on scattered view-local
flags. Keep this epic strictly on service and settings-surface construction; interaction-site trigger wiring is deferred
to E8.2. Maintain repository-first workflow assumptions for any backend references: backend changes are authored in the
repository first, then deployed to VPS only after local quality gates pass.
