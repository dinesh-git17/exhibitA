# E2.3: Implement AppState, Router, and Navigation Shell

**Phase:** 2 - iOS Foundation **Class:** Infrastructure **Design Doc Reference:** 8.2, 10.5, 7.4 **Dependencies:**

- Phase 2: iOS Foundation (`E2.1` scaffold completed)
- E2.1: Scaffold Xcode Project and Build Configuration (app target and root app entry exist)
- Asset: route contract (`contractBook`, `letterDetail(id:)`, `thoughtDetail(id:)`) from Design Doc 8.2
- Service: SwiftUI `NavigationStack` and `NavigationPath` APIs are available in iOS 26 runtime
- Service: local persistence store (`UserDefaults`) is available for `last_sync_at` and seen-ID tracking

---

## Goal

Implement the observable app state and navigation shell so root routing, sync-state persistence, and unread tracking are
centrally managed for all downstream feature screens.

---

## Scope

### File Inventory

| File | Action | Responsibility |
| ---- | ------ | -------------- |
| `ExhibitA/ExhibitA/App/AppState.swift` | Create | Implement `@Observable` app state with sync timestamp and unread tracking persistence primitives. |
| `ExhibitA/ExhibitA/App/Router.swift` | Create | Implement `@Observable` router with `NavigationPath`, route enum, and programmatic navigation API. |

### Integration Points

**ExhibitA/ExhibitA/App/AppState.swift**

- Imports from: `ExhibitA/ExhibitA/Core/Config.swift`
- Imported by: `ExhibitA/ExhibitA/App/ExhibitAApp.swift`, feature view modules, sync modules in later phases
- State reads: `UserDefaults` keys for `last_sync_at` and seen content IDs
- State writes: `UserDefaults` values for sync timestamp and seen content IDs

**ExhibitA/ExhibitA/App/Router.swift**

- Imports from: None
- Imported by: `ExhibitA/ExhibitA/App/ExhibitAApp.swift`, feature views, push/deep-link handlers in later phases
- State reads: Current `NavigationPath`
- State writes: `NavigationPath` mutations via route pushes/resets

---

## Out of Scope

- Visual token definitions and paper-noise rendering utilities (owned by E2.2).
- Network client, keychain auth storage, and disk cache implementation (owned by E2.4).
- Shared visual component implementation such as monogram and badges (owned by E2.5).
- Screen-specific feature rendering for home, letters, thoughts, and contract experiences (Phase 3+ feature scope).
- Push-notification registration and deep-link consumption runtime wiring (Phase 7 integration scope).

---

## Definition of Done

- [ ] `AppState` compiles as an `@Observable` type with explicit properties for sync timestamp and unread tracking
  state.
- [ ] `AppState` persists `last_sync_at` to `UserDefaults` and restores it on app relaunch.
- [ ] `AppState` persists seen content IDs to `UserDefaults` and restores them on app relaunch.
- [ ] `Router` compiles as an `@Observable` type exposing `NavigationPath` and route enum cases from Design Doc 8.2.
- [ ] Calling `router.navigate(to: .contractBook)` appends the corresponding route to navigation path state.
- [ ] App root shell can inject `AppState` and `Router` into environment without runtime type mismatch.
- [ ] Navigation shell supports destination routing contracts for contract, letter detail, and thought detail.
- [ ] Unread tracking API in `AppState` can answer whether a content ID is seen and can mark it as seen.

---

## Implementation Notes

Use Observation-native state management exactly as Design Doc 10.5 requires and avoid legacy `ObservableObject`
patterns. Keep route enum values aligned with Design Doc 8.2 so phase-3 and later views can consume a stable navigation
contract. Persist sync and seen-state values in `UserDefaults` as specified by Design Doc 7.4 to support launch-time
continuity across app sessions. Keep these files domain-focused and avoid embedding screen-specific rendering logic in
the state layer.
