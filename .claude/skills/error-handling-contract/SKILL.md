---
name: error-handling-contract
description: Enforce Exhibit A's user-facing error handling and failure UX contract with deterministic PASS/REJECT validation and structured rejection diagnostics. Use when creating, editing, reviewing, refactoring, or testing Swift/SwiftUI code that handles networking failures, sync behavior, loading/empty states, typed errors, recovery actions, user-facing error copy, and crash prevention paths.
---

# Error Handling Contract

Strict contract enforcement. No advisory mode. Reject every violating change.

## Doctrine

Errors must never feel technical. Failures must always feel recoverable. Prioritize Carolina's experience over implementation convenience in every failure path.

## Required Markers

Place these exact marker comments near the implementation paths they represent. The validator checks them for deterministic contract traceability:

```swift
// ERROR-CONTRACT: network-down-copy-the-court-is-in-recess
// ERROR-CONTRACT: network-down-retry-action
// ERROR-CONTRACT: network-down-paper-texture
// ERROR-CONTRACT: signature-failure-retain-local-signature
// ERROR-CONTRACT: signature-failure-sync-indicator-dustyRose-circular-arrow
// ERROR-CONTRACT: signature-failure-auto-retry-on-connectivity-restore
// ERROR-CONTRACT: sync-transient-silent-retry
// ERROR-CONTRACT: sync-ui-after-3-consecutive-failures
// ERROR-CONTRACT: empty-state-context-message-illustration
// ERROR-CONTRACT: primary-loading-skeleton-match-layout
// ERROR-CONTRACT: no-primary-spinner
// ERROR-CONTRACT: typed-error-enums-and-exhaustive-switches
// ERROR-CONTRACT: recovery-actions-retry-dismiss-cache
// ERROR-CONTRACT: user-copy-no-technical-leaks
// ERROR-CONTRACT: carolina-experience-priority
```

## Validation

Run:

```bash
python3 .claude/skills/error-handling-contract/scripts/validate_error_handling_contract.py --root . --format json
```

- Exit code `0` + zero violations = `PASS`.
- Non-zero exit code = `REJECT`.
- Never waive, downgrade, or reinterpret a rule.

Scans all `*.swift` files under `--root`, excluding build and dependency directories.

## Contract Rules

### Baseline

| Rule | Constraint |
|------|-----------|
| EHC000 | Swift source files must exist |

### Network-Down UX

| Rule | Constraint |
|------|-----------|
| EHC001 | All required `ERROR-CONTRACT` doctrine markers must exist |
| EHC002 | Network-down state must include exact copy `The court is in recess` and a retry action |
| EHC003 | Network-down state must use paper texture background |

### Signature Upload Failure

| Rule | Constraint |
|------|-----------|
| EHC004 | Signature upload failure must retain local signature and show dustyRose circular-arrow sync indicator |
| EHC005 | Signature upload failure must auto-retry on connectivity restoration |

### Sync Failure Strategy

| Rule | Constraint |
|------|-----------|
| EHC006 | Sync transient failures must retry silently; user-visible sync error appears only after 3 consecutive failures |

### Empty and Loading States

| Rule | Constraint |
|------|-----------|
| EHC007 | Empty states must never be blank; they must include contextual message and subtle illustration |
| EHC008 | Primary loading states must use skeleton layouts that match real content structure |
| EHC009 | Spinners (`ProgressView`) are forbidden on primary screens |

### Typed Errors and Exhaustive Handling

| Rule | Constraint |
|------|-----------|
| EHC010 | Throwing functions must use typed error enums (`throws(MyError)`) |
| EHC011 | Error handling switches must be exhaustive and default-free |
| EHC016 | Generic catches and silent swallowing (`try?`) are forbidden |

### Copy and Recovery Behavior

| Rule | Constraint |
|------|-----------|
| EHC012 | User-facing copy must never expose HTTP codes, system errors, or raw diagnostics |
| EHC013 | Error states must provide recovery paths (`retry`, `dismiss`, or cache fallback), and contract coverage must include all three categories |
| EHC017 | Error messaging must remain in character (example: `Filing error. Please try again.`) |
| EHC018 | Carolina-first failure UX priority must be explicit |

### Crash Prevention

| Rule | Constraint |
|------|-----------|
| EHC014 | Force unwraps (`!`), force casts (`as!`), force tries (`try!`), and IUOs are forbidden |
| EHC015 | `fatalError()` and `preconditionFailure()` are forbidden in production paths |

Reference: `references/error-handling-reliability-baseline.md`

## Output

Emit this exact structure:

```json
{
  "contract": "error-handling-contract",
  "verdict": "PASS | REJECT",
  "summary": {
    "files_scanned": 0,
    "rules_checked": 18,
    "violations": 0
  },
  "violations": [
    {
      "rule_id": "EHC000",
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
