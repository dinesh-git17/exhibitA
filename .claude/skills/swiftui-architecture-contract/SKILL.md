---
name: swiftui-architecture-contract
description: Enforce Exhibit A's non-negotiable SwiftUI architecture contract with deterministic pass/reject validation. Use when creating, editing, reviewing, or refactoring any SwiftUI code, project configuration, navigation flow, dependency injection, previews, or view-model layer. Triggers on SwiftUI architecture review, MVVM enforcement, Swift 6.2 concurrency compliance, and pull-request validation.
---

# SwiftUI Architecture Contract

Strict contract enforcement. No soft guidance. Reject any violating change.

## Preconditions

Before validation, confirm these prerequisites exist in the Swift source tree:

- `.../Views/...` directory (ARC024)
- `.../ViewModels/...` directory (ARC025)
- `.../Navigation/...` directory (ARC026)

Absence of any path is a contract violation.

## Screen Classification

A view type is a **screen** unless one of these exemptions applies:

- File path contains `Components/`.
- File contains marker comment: `ARCHITECTURE: display-only`.
- View name ends with: `Row`, `Cell`, `Badge`, `Chip`, `Button`, `Label`, `Icon`, `Card`, `Tile`.

All non-exempt screens must satisfy ARC011, ARC012, ARC013.

## Validation

Run:

```bash
python3 .claude/skills/swiftui-architecture-contract/scripts/validate_architecture_contract.py --root . --format json
```

- Non-zero exit code = `REJECT`.
- Zero exit code, zero violations = `PASS`.
- Never waive or downgrade a rule.

## Architecture Rules

### Observation (ban legacy patterns)

| Rule | Constraint |
|------|-----------|
| ARC001 | `ObservableObject` forbidden |
| ARC002 | `@StateObject` forbidden |
| ARC003 | `@ObservedObject` forbidden |
| ARC004 | `import Combine` forbidden in all files |

### Safety

| Rule | Constraint |
|------|-----------|
| ARC005 | Implicitly unwrapped optionals (`Type!`) forbidden |
| ARC006 | Force unwrap (`!`) forbidden |

### View-Model Layer

| Rule | Constraint |
|------|-----------|
| ARC007 | View-model files must import `Foundation` |
| ARC008 | View-model files may only import `Foundation` |
| ARC009 | Every `*ViewModel` must be `@Observable` |
| ARC010 | Async view-models must be `@MainActor` |
| ARC014 | `@State` cannot own non-view-model reference types |

### Screen Completeness

| Rule | Constraint |
|------|-----------|
| ARC011 | Every screen view requires a matching `*ViewModel` |
| ARC012 | Every screen must define `#Preview` |
| ARC013 | Previews must use mock/fixture data |

### Navigation

| Rule | Constraint |
|------|-----------|
| ARC015 | Imperative push/pop navigation APIs forbidden |
| ARC016 | `NavigationStack` requires `NavigationPath` + `Route` enum + type-safe destination |

### Dependency Injection

| Rule | Constraint |
|------|-----------|
| ARC017 | Custom `EnvironmentKey` + `EnvironmentValues` extension required |
| ARC018 | Screens must consume dependencies with `@Environment(\.key)` |

### Swift 6.2 Concurrency

| Rule | Constraint |
|------|-----------|
| ARC019 | Default main-actor isolation must be configured |
| ARC020 | `nonisolated(nonsending)` behavior must be configured |
| ARC021 | Actor-isolated protocol conformances must declare isolation explicitly |
| ARC022 | Explicit concurrency escape requires `@concurrent` |

### View Discipline

| Rule | Constraint |
|------|-----------|
| ARC023 | Business logic tokens in `body` forbidden |

### Project Structure

| Rule | Constraint |
|------|-----------|
| ARC024 | Project must contain `Views/` structure |
| ARC025 | Project must contain `ViewModels/` structure |
| ARC026 | Project must contain `Navigation/` structure |

Reference: `references/swift-2026-baseline.md` for Swift 6.2 concurrency rationale.

## Output

Return this structure after every validation run:

```json
{
  "contract": "swiftui-architecture-contract",
  "verdict": "PASS | REJECT",
  "summary": {
    "files_scanned": 0,
    "rules_checked": 0,
    "violations": 0
  },
  "violations": [
    {
      "rule_id": "ARC000",
      "title": "...",
      "rejection": "REJECT: ...",
      "file": "path/to/file.swift",
      "line": 1,
      "snippet": "offending code"
    }
  ]
}
```

If `verdict` is `REJECT`, do not approve the code. List all violations with rule IDs and rejection messages exactly as the validator produced them.
