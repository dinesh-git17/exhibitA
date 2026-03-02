# E2.2: Define Design Tokens and Paper Noise System

**Phase:** 2 - iOS Foundation **Class:** Infrastructure **Design Doc Reference:** 6.1, 6.2, 6.3, 6.4, 6.7, 8.1
**Dependencies:**

- Phase 2: iOS Foundation (`E2.1` scaffold completed)
- E2.1: Scaffold Xcode Project and Build Configuration (project and target shell available)
- Asset: complete light and dark color token tables from Design Doc 6.2
- Service: SwiftUI rendering pipeline and dynamic color switching are available in iOS 26 runtime
- Service: runtime environment supports programmatic paper-noise generation (no bitmap dependency)

---

## Goal

Define the full Exhibit A design token layer and runtime paper-noise utility so all subsequent SwiftUI features consume
a single canonical visual system.

---

## Scope

### File Inventory

| File | Action | Responsibility |
| ---- | ------ | -------------- |
| `ExhibitA/ExhibitA/Design/Theme.swift` | Create | Define all color tokens, typography roles, spacing constants, and shadow constants for light and dark mode. |
| `ExhibitA/ExhibitA/Design/PaperNoise.swift` | Create | Implement programmatic paper-noise generation surface utility matching design opacity and turbulence constraints. |
| `ExhibitA/ExhibitA/Resources/Assets.xcassets` | Create | Provide asset-catalog color entries and resource hooks required for preview-safe token usage. |

### Integration Points

**ExhibitA/ExhibitA/Design/Theme.swift**

- Imports from: None
- Imported by: home, contract, letters, thoughts, and shared component modules in later phases
- State reads: Current color scheme and dynamic type context
- State writes: None

**ExhibitA/ExhibitA/Design/PaperNoise.swift**

- Imports from: `ExhibitA/ExhibitA/Design/Theme.swift`
- Imported by: reading surfaces in letters, thoughts, and contract flows in later phases
- State reads: Color scheme and configured opacity levels
- State writes: None

**ExhibitA/ExhibitA/Resources/Assets.xcassets**

- Imports from: None
- Imported by: `Theme.swift` and Xcode preview/runtime color resolution
- State reads: None
- State writes: None

---

## Out of Scope

- App routing, unread state, and `@Observable` state container implementation (owned by E2.3).
- API networking, keychain, and disk cache layers (owned by E2.4).
- Shared UI component construction using tokens (`MonogramView`, badges, labels) (owned by E2.5).
- Screen-level feature composition for home, letters, thoughts, and contract views (Phase 3+ feature scope).
- Sound, haptic, and animation wiring polish behavior (Phase 8 integration scope).

---

## Definition of Done

- [ ] All 13 light-mode color tokens from Design Doc 6.2 are defined in `Theme.swift` and are callable by semantic token
  name.
- [ ] All 10 dark-mode color tokens from Design Doc 6.2 are defined and switch automatically with system color scheme.
- [ ] Typography roles in `Theme.swift` map to the full role set from Design Doc 6.3 with expected font families,
  weights, and baseline sizes.
- [ ] Spacing and shadow constants in `Theme.swift` match the 8pt grid and warm layered shadow model from Design Doc
  6.4.
- [ ] `PaperNoise` renders programmatic texture using configured turbulence/octave behavior and no bitmap texture asset.
- [ ] Paper-noise opacity follows design constraints (3-5% light mode and 2-3% dark mode).
- [ ] `Assets.xcassets` contains token-aligned color resources required for preview-safe and runtime-safe access.
- [ ] Downstream SwiftUI view modules can import `Theme` and resolve tokens without redefining visual constants.

---

## Implementation Notes

Use Design Doc 6.2 token names verbatim so subsequent epics can depend on stable semantic identifiers. Apply typography
and spacing constants from Design Doc 6.3 and 6.4 exactly, including New York/SF role separation and warm shadow values.
Keep paper texture generation runtime-driven per Design Doc 6.4 and 6.7; do not introduce bitmap paper assets. Treat
`Theme.swift` as the canonical visual source so later UI epics do not reintroduce hardcoded color/spacing values.
