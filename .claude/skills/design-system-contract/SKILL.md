---
name: design-system-contract
description: Enforce Exhibit A's project-wide visual design contract with deterministic PASS/REJECT validation and structured diagnostics. Use when creating, editing, reviewing, refactoring, or approving any SwiftUI/UIKit UI code, theme tokens, component styles, typography, spacing, dark mode behavior, or visual assets. Triggers on design-system checks, token enforcement, visual QA, and pull-request validation for styling changes.
---

# Design System Contract

Strict contract enforcement. No advisory mode. Reject every violating change.

## Doctrine

All visual styling flows through semantic tokens. Views never contain raw design decisions. Inline styling, visual drift, and token bypasses are architectural violations.

## Canonical Token Architecture

Project must expose a `Theme` struct with semantic namespaces and token-only access:

```swift
struct Theme {
    enum Colors {
        static let backgroundPrimary = Color(light: "#F2EFEA", dark: "#1E1B16")
        static let warmInk = Color(light: "#2C2118", dark: "#E8E4DF")
        static let fadedInk = Color(light: "#8C7B6B", dark: "#A89882")
        static let goldLeaf = Color(light: "#CBB674", dark: "#CBB674")
        static let dustyRose = Color(light: "#DCA1A1", dark: "#E0B5A8")
        static let sealBurgundy = Color(light: "#800020", dark: "#C4526A")
        static let shadowWarm = Color(light: "#2C2118", dark: "#2C2118")
    }

    enum Typography {
        static let headerDisplay: FontToken // Cormorant Garamond
        static let bodyReading: FontToken   // Crimson Pro
    }

    enum Spacing {
        static let x1: CGFloat = 4
        static let x2: CGFloat = 8
        static let x3: CGFloat = 12
        static let x4: CGFloat = 16
    }
}
```

Color tokens must use paired light/dark constructors:

```swift
Color(light: "...", dark: "...")
```

## Validation

Run:

```bash
python3 .claude/skills/design-system-contract/scripts/validate_design_system_contract.py --root . --format json
```

- Exit code `0` + zero violations = `PASS`.
- Non-zero exit code = `REJECT`.
- Never waive or downgrade a rule.

## Contract Rules

### Baseline

| Rule | Constraint |
|------|-----------|
| DSC000 | Swift source files must exist |

### Token Architecture

| Rule | Constraint |
|------|-----------|
| DSC001 | `Theme` struct with token namespaces must exist |
| DSC002 | Theme color tokens must use `Color(light: ..., dark: ...)` |
| DSC003 | Required tokens must exist: `goldLeaf`, `dustyRose`, `sealBurgundy`, `warmInk`, `fadedInk`, `shadowWarm` |

### Typography

| Rule | Constraint |
|------|-----------|
| DSC005 | Header typography tokens must use `Cormorant Garamond` |
| DSC006 | Body typography tokens must use `Crimson Pro` |
| DSC007 | Fonts must be bundled in app metadata (`UIAppFonts`) |

### Spacing

| Rule | Constraint |
|------|-----------|
| DSC008 | `Theme.Spacing` must use a 4pt base scale |
| DSC009 | Views must not use inline numeric spacing or padding values |

### View Styling Discipline

| Rule | Constraint |
|------|-----------|
| DSC004 | Views must not declare inline colors, hex literals, or raw color APIs |
| DSC010 | Raw font-size APIs are forbidden in views (`.font(.system(size:))`, `Font.custom(...)`) |
| DSC011 | Views must consume semantic typography tokens (`Theme.Typography.*`) |

### Surface and Texture

| Rule | Constraint |
|------|-----------|
| DSC012 | Paper texture may only be applied with `PaperTexture` modifier |
| DSC023 | Paper texture must provide warm-noise adaptation for dark mode |

### Shadows and Dividers

| Rule | Constraint |
|------|-----------|
| DSC013 | Shadows must use warm token values; gray/black drop shadows are forbidden |
| DSC014 | Default SwiftUI `Divider()` is forbidden; dividers must use `goldLeaf` token |

### Component Styling

| Rule | Constraint |
|------|-----------|
| DSC015 | Stamp components must use `dustyRose`, uppercase treatment, tracking, and thin rounded border; alarm red forbidden |
| DSC016 | Wax seal components must use `sealBurgundy` and subtle emboss shadow |
| DSC017 | Wax seal usage is limited to cover and home screens |
| DSC018 | Signature styling must use `goldLeaf` lines, `warmInk` names, and `fadedInk` italic titles |

### Dark Mode

| Rule | Constraint |
|------|-----------|
| DSC019 | Dark-mode background must include `#1E1B16`; pure black backgrounds are forbidden |

### Token Traceability

| Rule | Constraint |
|------|-----------|
| DSC020 | Component files must declare `// DESIGN_TOKEN: Theme.<Namespace>.<token>` markers resolving to existing tokens |

### Contrast Compliance

| Rule | Constraint |
|------|-----------|
| DSC021 | Contrast checks require parseable hex values for semantic text/background tokens |
| DSC022 | WCAG AA contrast must pass: 4.5:1 body text, 3.0:1 large text |

Reference: `references/design-token-contrast-baseline.md`

## Output

Emit this exact structure:

```json
{
  "contract": "design-system-contract",
  "verdict": "PASS | REJECT",
  "summary": {
    "files_scanned": 0,
    "rules_checked": 24,
    "violations": 0
  },
  "violations": [
    {
      "rule_id": "DSC000",
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
