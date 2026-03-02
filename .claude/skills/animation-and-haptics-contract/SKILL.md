---
name: animation-and-haptics-contract
description: Enforce Exhibit A's project-wide animation, motion, haptics, and UI sound contract with deterministic PASS/REJECT validation. Use when creating, editing, reviewing, refactoring, or testing Swift/SwiftUI/UIKit code that defines animations, transitions, page curl flows, haptic feedback, reduced-motion behavior, or short UI sounds.
---

# Animation and Haptics Contract

Strict contract enforcement. No advisory mode. Reject every violating change.

## Doctrine

Motion is intentional, parameterized, and accessibility-aware. Haptics are paired with visual feedback and never arbitrary. Animations are product language, not decoration.

## Required Product Constants

Define these exact constants in project motion tokens:

```swift
static let signaturePlacementSpring = Animation.spring(duration: 0.5, bounce: 0.15)
static let screenTransitionEaseOut = Animation.easeOut(duration: 0.35)
static let unreadBadgePulseEaseInOut = Animation.easeInOut(duration: 1.0)
```

## Validation

Run:

```bash
python3 .claude/skills/animation-and-haptics-contract/scripts/validate_animation_and_haptics_contract.py --root . --format json
```

- Exit code `0` + zero violations = `PASS`.
- Non-zero exit code = `REJECT`.
- Never waive or downgrade a rule.

Scans all `*.swift` files under `--root`, excluding build and dependency directories.

## Contract Rules

### Animation API Discipline

| Rule | Constraint |
|------|-----------|
| AHC000 | Swift source files must exist |
| AHC001 | `Animation.default`, `.animation(.default)`, and `withAnimation(.default)` forbidden |
| AHC002 | Implicit `.animation(...)` modifier forbidden |
| AHC003 | `withAnimation(...)` must use approved curves only: `.spring(...)`, `.easeOut(...)`, `.easeInOut(...)` |
| AHC004 | Every spring animation must explicitly set `duration` and `bounce` |
| AHC005 | Every ease animation must explicitly set `duration` |
| AHC006 | Canonical motion constants must exist with exact parameter values |

### Page Curl and Signature Motion

| Rule | Constraint |
|------|-----------|
| AHC007 | Page curl must use `UIPageViewController(transitionStyle: .pageCurl, ...)` |
| AHC008 | Page curl path must explicitly target 60fps rendering |
| AHC009 | Signature placement must use `.spring(duration: 0.5, bounce: 0.15)` |
| AHC010 | Signature placement scale animation must include `0.95 -> 1.0` |

### Transition and Badge Language

| Rule | Constraint |
|------|-----------|
| AHC011 | Screen transition animation must use `.easeOut(duration: 0.35)` |
| AHC012 | Screen transitions must be fade-only (`.transition(.opacity)`); move/slide/scale/push forbidden |
| AHC013 | Unread badge pulse must use repeating `.easeInOut(duration: 1.0)` |
| AHC014 | Unread badge pulse must animate opacity `0.4 -> 1.0` |

### Accessibility

| Rule | Constraint |
|------|-----------|
| AHC015 | Global reduced-motion support must wire `@Environment(\.accessibilityReduceMotion)` |
| AHC016 | Every animated file must branch on reduced-motion state |
| AHC017 | Reduced-motion branch must provide an instant, non-animated fallback path |

### Haptics

| Rule | Constraint |
|------|-----------|
| AHC018 | Project must define haptic UX events (`signaturePlaced`, `pageCurlComplete`, `contentUnlockedFirstTime`) |
| AHC019 | `signaturePlaced` must map to `UIImpactFeedbackGenerator(style: .medium)` |
| AHC020 | `pageCurlComplete` must map to `UIImpactFeedbackGenerator(style: .light)` |
| AHC021 | `contentUnlockedFirstTime` must map to `UINotificationFeedbackGenerator().notificationOccurred(.success)` |
| AHC022 | Haptics must not be delayed (`asyncAfter`, `Task.sleep`, `sleep`) relative to visual state change |
| AHC023 | Haptic generator usage must flow through event mapping, not arbitrary direct calls |

### Audio and Responsiveness

| Rule | Constraint |
|------|-----------|
| AHC024 | UI sounds must be optional and toggleable via `UserDefaults` |
| AHC025 | UI sounds must use `AVAudioPlayer` and preload with `prepareToPlay()` |
| AHC026 | `SystemSoundID` and AudioServices system-sound APIs forbidden |
| AHC027 | Motion/haptic code must not block interaction responsiveness (no blocking sleep calls) |

Reference: `references/ios-motion-haptics-2026-baseline.md`

## Output

Emit this exact structure:

```json
{
  "contract": "animation-and-haptics-contract",
  "verdict": "PASS | REJECT",
  "summary": {
    "files_scanned": 0,
    "rules_checked": 28,
    "violations": 0
  },
  "violations": [
    {
      "rule_id": "AHC000",
      "title": "...",
      "rejection": "REJECT: ...",
      "file": "path/to/file.swift",
      "line": 1,
      "snippet": "offending code"
    }
  ]
}
```

If `verdict` is `REJECT`, block approval until all violations are resolved.
