---
name: pencilkit-signature-contract
description: Enforce Exhibit A's PencilKit signature capture contract with deterministic PASS/REJECT validation and structured rejection diagnostics. Use when creating, editing, reviewing, refactoring, or testing Swift/SwiftUI code for signature capture UI, PKCanvasView integration, export/cropping pipelines, upload persistence, and fallback behavior when PencilKit is unavailable.
---

# PencilKit Signature Contract

Strict contract enforcement. No advisory mode. Reject every violating change.

## Doctrine

Signature capture must feel deliberate, intimate, and production-grade — a focused capture surface, not a sketch canvas.

## Validation

Run:

```bash
python3 .claude/skills/pencilkit-signature-contract/scripts/validate_pencilkit_signature_contract.py --root . --format json
```

- Exit code `0` + zero violations = `PASS`.
- Non-zero exit code = `REJECT`.
- Never waive or downgrade a rule.

Scans all `*.swift` files under `--root`, excluding build and dependency directories.

## Contract Rules

### Canvas Bridge

| Rule | Constraint |
|------|-----------|
| PSC000 | Swift source files must exist |
| PSC001 | Signature capture must use `PKCanvasView` bridged via `UIViewRepresentable` |

### Inking

| Rule | Constraint |
|------|-----------|
| PSC002 | Required tool: `PKInkingTool(.pen, color: UIColor(named: "warmInk")!, width: 2.5)` |
| PSC003 | Pencil and marker tools forbidden for signature capture |
| PSC004 | Canvas background must use warm cream `#FBF7F0` paper tone |

### Canvas Configuration

| Rule | Constraint |
|------|-----------|
| PSC005 | `isRulerActive` must be disabled |
| PSC006 | Tool picker must remain disabled |
| PSC007 | Input policy must be `drawingPolicy = .anyInput` |

### Export Pipeline

| Rule | Constraint |
|------|-----------|
| PSC008 | Export rendering must use `UIScreen.main.scale` |
| PSC009 | Export must crop to `PKDrawing.bounds` with ~8pt padding |
| PSC010 | Exporting full canvas bounds forbidden |
| PSC011 | Export must use `UIImage.pngData()` |
| PSC012 | PNG byte-size gate must enforce `< 50KB` and crop before encoding |

### UX Behavior

| Rule | Constraint |
|------|-----------|
| PSC013 | Clear action must confirm when non-empty and dismiss immediately when empty |
| PSC014 | Signature guide line must be centered, `goldLeaf`, `0.5pt` |
| PSC015 | Undo/redo gesture paths must be explicitly disabled |
| PSC016 | Canvas emptiness must sync back to SwiftUI through `@Binding isEmpty` |

### Post-Upload and Safety

| Rule | Constraint |
|------|-----------|
| PSC017 | Uploaded signatures must become immutable |
| PSC018 | PencilKit usage must be guarded with `#if canImport(PencilKit)` and graceful fallback |

Reference: `references/pencilkit-2026-baseline.md`

## Output

Emit this exact structure:

```json
{
  "contract": "pencilkit-signature-contract",
  "verdict": "PASS | REJECT",
  "summary": {
    "files_scanned": 0,
    "rules_checked": 19,
    "violations": 0
  },
  "violations": [
    {
      "rule_id": "PSC000",
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
