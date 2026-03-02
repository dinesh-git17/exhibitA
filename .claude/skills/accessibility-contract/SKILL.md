---
name: accessibility-contract
description: Enforce Exhibit A's project-wide iOS accessibility contract with deterministic PASS/REJECT validation and structured rejection diagnostics. Use when creating, editing, reviewing, refactoring, or testing SwiftUI/UIKit code, custom controls, signature flows, page curl navigation, dynamic type behavior, VoiceOver support, contrast handling, and UI accessibility tests.
---

# Accessibility Contract

Strict contract enforcement. No advisory mode. Reject every violating change.

## Doctrine

Accessibility is not an enhancement. It is a release requirement.

## Validation

Run:

```bash
python3 .claude/skills/accessibility-contract/scripts/validate_accessibility_contract.py --root . --format json
```

- Exit code `0` + zero violations = `PASS`.
- Non-zero exit code = `REJECT`.
- Never waive or downgrade a rule.

Scans all `*.swift` files under `--root`, excluding build and dependency directories.

## Contract Rules

### Baseline Compliance

| Rule | Constraint |
|------|-----------|
| ACC000 | Swift source files must exist |
| ACC001 | Project must explicitly declare WCAG 2.2 AA accessibility baseline |
| ACC002 | Every interactive element must provide a minimum 44x44pt touch target |

### VoiceOver Semantics

| Rule | Constraint |
|------|-----------|
| ACC003 | Interactive elements must provide VoiceOver labels |
| ACC004 | Interactive elements must provide VoiceOver hints |
| ACC005 | No image without either accessibilityLabel or accessibilityHidden |
| ACC006 | Custom components must expose accessibility metadata |
| ACC007 | Signature state announcements must use full contextual phrases |

### Navigation and Focus

| Rule | Constraint |
|------|-----------|
| ACC008 | Page curl gesture must provide VoiceOver alternative navigation |
| ACC009 | Rotor or gesture-based accessibility navigation must be implemented |
| ACC014 | After signature placement, focus must move to a confirmation element |
| ACC018 | Screens cannot be marked complete without VoiceOver verification evidence |

### Typography and Layout

| Rule | Constraint |
|------|-----------|
| ACC010 | Text must use semantic font styles; fixed-size typography is forbidden |
| ACC011 | Pagination must reflow correctly at large Dynamic Type sizes |

### Contrast and Decoration

| Rule | Constraint |
|------|-----------|
| ACC012 | Contrast architecture must enforce 4.5:1 body text, 3:1 large text, and custom palette validation |
| ACC013 | Decorative UI elements must be marked `.accessibilityHidden(true)` |

### Signature and Dynamic Content

| Rule | Constraint |
|------|-----------|
| ACC015 | Signature blocks must use `.accessibilityElement(children: .combine)` |
| ACC017 | Dynamic content changes must announce via `UIAccessibility.post(notification: .announcement, argument: ...)` |

### Testing and Release Gating

| Rule | Constraint |
|------|-----------|
| ACC016 | UI tests must execute `performA11yAudit()` before completion |

Reference: `references/ios-accessibility-2026-baseline.md`

## Output

Emit this exact structure:

```json
{
  "contract": "accessibility-contract",
  "verdict": "PASS | REJECT",
  "summary": {
    "files_scanned": 0,
    "rules_checked": 19,
    "violations": 0
  },
  "violations": [
    {
      "rule_id": "ACC000",
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
