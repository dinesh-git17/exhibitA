# E8.2: Wire Haptics, Sounds, and Animation Polish

**Phase:** 8 - Sound, Haptics, and Animation Polish
**Class:** Integration
**Design Doc Reference:** 2.1, 3.7, 6.6, 6.8, 8.3, 8.4
**Dependencies:**

- Phase 7: Sync, Push, and Offline (phase exit criteria met).
- E2.5: Create Shared UI Components (`UnreadBadge` animation baseline is available for timing alignment).
- E6.1: Build Contract Book Page Curl, Cover, and TOC (page-transition hooks are available in ContractBookView).
- E6.3: Build Signature Block and PencilKit Signing Flow (signature-confirmation and signed-state rendering are
  available for haptic/sound/motion wiring).
- E8.1: Add Sound Service and Settings Toggle (sound playback service and persisted preference are available).
- Asset: Contract/book interaction event surfaces in existing views are available and stable.
- Service: SoundService cue APIs are available for page-turn and signature/new-content audio playback.
- Service: UIKit haptics runtime (`UIImpactFeedbackGenerator`) is available on iOS 26+.

---

## Goal

Integrate sound triggers, haptic feedback, and motion polish into existing feature views so Phase 8 interaction quality
matches the design specification.

---

## Scope

### File Inventory

| File | Action | Responsibility |
| ---- | ------ | -------------- |
| `ExhibitA/ExhibitA/Features/Home/HomeView.swift` | Modify | Wire settings-entry access, card parallax behavior, and transition polish into the home surface while preserving existing navigation semantics. |
| `ExhibitA/ExhibitA/Features/Contract/ContractBookView.swift` | Modify | Wire page-turn sound triggers to contract page-transition lifecycle events and preserve existing page-curl behavior. |
| `ExhibitA/ExhibitA/Features/Contract/SignatureBlockView.swift` | Modify | Wire signature placement animation timing and final signed-state reveal behavior to match motion requirements. |
| `ExhibitA/ExhibitA/Features/Contract/SignaturePadView.swift` | Modify | Wire signature confirmation sound and medium-impact haptic feedback on successful sign completion events. |

### Integration Points

**ExhibitA/ExhibitA/Features/Home/HomeView.swift**

- Imports from: `ExhibitA/ExhibitA/Core/SoundService.swift`, `ExhibitA/ExhibitA/Features/Home/SettingsView.swift`,
  `ExhibitA/ExhibitA/Design/Theme.swift`, existing home navigation dependencies
- Imported by: `ExhibitA/ExhibitA/App/ExhibitAApp.swift`
- State reads: Home-view section state, unread indicator state, and global sound preference exposure for settings access
- State writes: Presentation state for SettingsView and animation-state updates for parallax/transition behavior

**ExhibitA/ExhibitA/Features/Contract/ContractBookView.swift**

- Imports from: `ExhibitA/ExhibitA/Core/SoundService.swift`, existing contract-book page controller wrappers
- Imported by: Contract-book route destination wiring
- State reads: Current page transition direction and page index transitions
- State writes: None

**ExhibitA/ExhibitA/Features/Contract/SignatureBlockView.swift**

- Imports from: existing signature state dependencies and animation timing utilities
- Imported by: `ExhibitA/ExhibitA/Features/Contract/ContractPageView.swift`
- State reads: Signature completion state and image availability state
- State writes: Animation-state transitions for signed-image reveal

**ExhibitA/ExhibitA/Features/Contract/SignaturePadView.swift**

- Imports from: `ExhibitA/ExhibitA/Core/SoundService.swift`, UIKit haptics runtime, existing signing-flow dependencies
- Imported by: `ExhibitA/ExhibitA/Features/Contract/SignatureBlockView.swift`
- State reads: Signature submission success/failure outcomes
- State writes: None

---

## Out of Scope

- SoundService core implementation and persisted preference model (owned by E8.1).
- New audio asset creation, replacement, or mastering changes (content pipeline work outside this phase scope).
- Offline upload retries and sync queue behavior for signatures (owned by Phase 7 epic E7.2).
- Additional backend APIs, VPS-side coding, or deployment orchestration (backend workflow remains repository-first then
  deploy via approved process).
- Design-token redefinition for colors/typography beyond Phase 8 interaction wiring needs (owned by earlier foundation
  epics).

---

## Definition of Done

- [ ] HomeView exposes settings access that presents SettingsView for global sound-toggle control.
- [ ] HomeView card surfaces apply subtle scroll parallax behavior without breaking card tap navigation.
- [ ] ContractBookView emits page-turn sound cues on page transitions only when SoundService preference allows playback.
- [ ] SignaturePadView emits medium-impact haptic feedback on successful signature confirmation.
- [ ] SignaturePadView emits signature-placed sound cue on successful signature confirmation when sounds are enabled.
- [ ] SignatureBlockView animates signed-image reveal with 0.5s ease timing and 0.95-to-1.0 scale transition.
- [ ] Navigation and route transitions use 0.3-0.4s fade behavior where specified, without hard-cut regressions.
- [ ] Unread badge breathing animation remains synchronized to a 2-second cycle after motion wiring changes.
- [ ] Modified views render without frame drops below 60fps on supported target devices during representative interactions.

---

## Implementation Notes

Use Design Doc 6.6 for motion timing requirements (screen fades, signature reveal, parallax, and 2-second unread
breathing cadence), Design Doc 6.8 for sound cue semantics, and Design Doc 3.7 for signature-confirmation interaction
expectations. Keep all wiring changes localized to the four PHASES-listed files to preserve phase-level file boundaries.
Use SoundService from E8.1 as the only sound trigger interface and avoid direct per-view playback setup. Keep haptic
trigger logic bound to successful sign completion events only. Preserve repository-first backend constraints in planning
language: backend code is authored in-repo first and deployed to VPS only after validation gates.
