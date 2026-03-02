---
name: swift-concurrency-contract
description: Enforce Exhibit A's strict Swift 6.2 concurrency contract with deterministic PASS/REJECT validation and structured violation output. Use when creating, editing, reviewing, or refactoring any SwiftUI, networking, caching, sync/export, actor, or async code. Triggers on pull-request validation, concurrency audits, Swift 6.2 migration, and architecture contract checks.
---

# Swift Concurrency Contract

Strict contract enforcement. No advisory mode. Reject every violating change.

## Doctrine

Start single-threaded. Add concurrency only when necessary, measurable, and explicit.

## Justification Markers

Every concurrency escape hatch requires a measured justification comment within the preceding three lines:

```swift
// CONCURRENCY-JUSTIFICATION: <measured reason and expected benefit>
```

`Task.detached` additionally requires:

```swift
// DETACHED-REASON: <why structured concurrency cannot be used>
```

Rules SCC006 and SCC007 enforce these markers.

## Validation

Run:

```bash
python3 .claude/skills/swift-concurrency-contract/scripts/validate_concurrency_contract.py --root . --format json
```

- Exit code `0` + zero violations = `PASS`.
- Non-zero exit code = `REJECT`.
- Never waive, downgrade, or reinterpret a rule.

Scans all `*.swift` files and `Package.swift` under `--root`, excluding build and dependency directories.

## Contract Rules

### Swift 6.2 Baseline

| Rule | Constraint |
|------|-----------|
| SCC001 | `Package.swift` must set `.defaultIsolation(MainActor.self)` |
| SCC002 | `Package.swift` must enable `NonisolatedNonsendingByDefault` |
| SCC003 | `Package.swift` must enable `InferIsolatedConformances` |

### Prohibited Legacy Concurrency

| Rule | Constraint |
|------|-----------|
| SCC004 | `DispatchQueue`, `DispatchGroup`, `DispatchSemaphore`, `OperationQueue`, and related GCD primitives forbidden |
| SCC005 | `import Combine` forbidden for async workflow design |

### Intentional Concurrency Enforcement

| Rule | Constraint |
|------|-----------|
| SCC006 | `Task.detached` forbidden unless both `CONCURRENCY-JUSTIFICATION` and `DETACHED-REASON` markers present |
| SCC007 | `Task {}`, `async let`, `TaskGroup`, `@concurrent` require `CONCURRENCY-JUSTIFICATION` marker |
| SCC008 | `@concurrent` allowed only for network, image, cache, export, sync, or background I/O contexts |
| SCC009 | Background/export/sync/cache/image async functions must be explicitly `@concurrent` |

### Async Safety and Cancellation

| Rule | Constraint |
|------|-----------|
| SCC010 | `async throws` functions with throwing async calls must include explicit `do/catch` |
| SCC011 | Lifecycle-bound async work in views must use `.task {}`; async `onAppear` forbidden |
| SCC012 | Multiple `Task {}` fan-out must use `withTaskGroup`/`withThrowingTaskGroup` |
| SCC013 | Network requests must be wrapped in `withTaskCancellationHandler` |

### Actor and Main-Thread Safety

| Rule | Constraint |
|------|-----------|
| SCC014 | Blocking I/O or sleep APIs on main-actor-isolated code forbidden |
| SCC015 | Actor protocol conformances in extensions must declare explicit isolation |

Reference: `references/swift-6-2-concurrency-baseline.md` for Swift 6.2 rationale.

## Output

Return this structure after every validation run:

```json
{
  "contract": "swift-concurrency-contract",
  "verdict": "PASS | REJECT",
  "summary": {
    "files_scanned": 0,
    "rules_checked": 15,
    "violations": 0
  },
  "violations": [
    {
      "rule_id": "SCC000",
      "title": "...",
      "rejection": "REJECT: ...",
      "file": "path/to/file.swift",
      "line": 1,
      "snippet": "offending code"
    }
  ]
}
```

If `verdict` is `REJECT`, approval is blocked until all violations are resolved.
