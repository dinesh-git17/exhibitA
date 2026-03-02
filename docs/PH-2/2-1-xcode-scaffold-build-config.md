# E2.1: Scaffold Xcode Project and Build Configuration

**Phase:** 2 - iOS Foundation **Class:** Infrastructure **Design Doc Reference:** 8.1, 10.1, 10.7, 10.9, 14.3
**Dependencies:**

- Phase 1: Admin Panel (exit criteria met)
- E1.1: Implement Admin Routes, Session Auth, and APNS Push (backend admin and push foundation available)
- E1.2: Build Admin Content Templates and Styling (phase gate complete)
- Asset: iOS 26 SDK and Xcode 26+ are available on local development machine
- Service: backend API service at `exhibita.dineshd.dev` is available through repository-first deployment from prior
  phases
- Service: code signing and TestFlight entitlements are available via active Apple Developer account

---

## Goal

Scaffold the iOS project shell and build configuration so Exhibit A compiles on iOS 26 and exposes signer/API key
build-time configuration with Liquid Glass suppression defaults.

---

## Scope

### File Inventory

| File | Action | Responsibility |
| ---- | ------ | -------------- |
| `ExhibitA/ExhibitA.xcodeproj/project.pbxproj` | Create | Define project targets, build settings, source groups, and iOS 26 deployment configuration. |
| `ExhibitA/ExhibitA/App/ExhibitAApp.swift` | Create | Implement app entrypoint shell and root scene bootstrapping for the SwiftUI app lifecycle. |
| `ExhibitA/ExhibitA/Core/Config.swift` | Create | Implement typed runtime config surface for base URL, signer identity, and API key ingestion from build settings. |
| `ExhibitA/.swiftlint.yml` | Create | Define SwiftLint policy for project-local lint execution and CI validation. |
| `ExhibitA/.swiftformat` | Create | Define SwiftFormat policy for deterministic source formatting. |

### Integration Points

**ExhibitA/ExhibitA.xcodeproj/project.pbxproj**

- Imports from: None
- Imported by: Xcode build system, SwiftPM resolver, CI build jobs
- State reads: Build settings, xcconfig values, signing configuration
- State writes: None

**ExhibitA/ExhibitA/App/ExhibitAApp.swift**

- Imports from: `ExhibitA/ExhibitA/Core/Config.swift`
- Imported by: iOS app target executable
- State reads: App-level configuration values and launch-time environment
- State writes: Root app lifecycle state ownership

**ExhibitA/ExhibitA/Core/Config.swift**

- Imports from: None
- Imported by: `ExhibitA/ExhibitA/App/ExhibitAApp.swift`, networking and feature modules in later epics
- State reads: Build configuration entries (`SIGNER_IDENTITY`, `API_KEY`, base URL)
- State writes: None

**ExhibitA/.swiftlint.yml**

- Imports from: None
- Imported by: SwiftLint CLI and CI workflows
- State reads: File inclusion and exclusion patterns under `ExhibitA/`
- State writes: None

**ExhibitA/.swiftformat**

- Imports from: None
- Imported by: SwiftFormat CLI and local formatting workflow
- State reads: Swift source files in project scope
- State writes: None

---

## Out of Scope

- Design token definitions, typography roles, and paper noise generator implementation (owned by E2.2).
- Observable state container and navigation route implementation (owned by E2.3).
- API client, keychain wrapper, and local cache implementation (owned by E2.4).
- Shared reusable UI component library (`MonogramView`, `UnreadBadge`, labels) (owned by E2.5).
- Backend deployment or VPS runtime operations (`scp`, systemd, Caddy) (already delivered in backend phases and not part
  of iOS scaffold scope).

---

## Definition of Done

- [ ] Xcode opens `ExhibitA/ExhibitA.xcodeproj` and resolves the project graph without project-file errors.
- [ ] iOS target deployment setting is pinned to iOS 26 and simulator build succeeds.
- [ ] `ExhibitAApp` launches to a valid SwiftUI root scene without runtime crash.
- [ ] `Config` resolves signer identity and API key from build settings rather than hardcoded literals.
- [ ] SwiftLint runs using `ExhibitA/.swiftlint.yml` and reports no configuration errors.
- [ ] SwiftFormat runs using `ExhibitA/.swiftformat` and reports no configuration errors.
- [ ] Liquid Glass suppression defaults are present in the app shell so no translucent glass surfaces appear by default.
- [ ] Project bootstrap is performed entirely in repository files with no direct VPS source authoring.

---

## Implementation Notes

Structure files and module folders exactly as Design Doc 8.1 defines to avoid path drift before later phase epics layer
features on top. Keep Liquid Glass suppression at the app-shell level per Design Doc 10.1 so all subsequent feature
screens inherit opaque baseline surfaces. Read signer identity and API key from build settings per Design Doc 10.7 and
never hardcode secrets or identities in Swift sources. Treat this epic as local iOS foundation work; backend dependency
is consumed via previously deployed repository-first backend artifacts, not by editing VPS code directly.
