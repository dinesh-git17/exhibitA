---
name: testing-contract
description: Enforce Exhibit A's project-wide testing contract with deterministic PASS/REJECT validation and structured rejection diagnostics. Use when creating, editing, reviewing, refactoring, or validating Swift/SwiftUI features, tests, snapshot suites, networking tests, integration tests, and CI coverage/performance gates.
---

# Testing Contract

Strict contract enforcement. No advisory mode. Reject every violating change.

## Doctrine

Tests are required, deterministic, fast, and architecture-aware.

## Deterministic Evidence Conventions

- Name snapshots with `snapshot::<target>::<mode>::<type>`.
  - `<mode>`: `light` or `dark`
  - `<type>`: `body` or `accessibility3`
- Keep snapshot assertions in unit-test targets only.
- Represent integration flow coverage with explicit markers in the integration test:
  - `INTEGRATION-CONTRACT: seed-server-data`
  - `INTEGRATION-CONTRACT: app-syncs`
  - `INTEGRATION-CONTRACT: content-appears`
  - `INTEGRATION-CONTRACT: signature-uploads`
  - `INTEGRATION-CONTRACT: server-confirms`
- Store networking fixtures as recorded responses (for example `Tests/Fixtures/*.json`) and never hit live endpoints.

## Validation

Run:

```bash
python3 .claude/skills/testing-contract/scripts/validate_testing_contract.py --root . --base-ref origin/main --format json
```

- Exit code `0` + zero violations = `PASS`.
- Non-zero exit code = `REJECT`.
- Never waive or downgrade a rule.

Scans all `*.swift` files under `--root`, excluding build and dependency directories.

## Contract Rules

### Baseline

| Rule | Constraint |
|------|-----------|
| TTC000 | Swift test files must exist |

### Snapshot Infrastructure

| Rule | Constraint |
|------|-----------|
| TTC001 | Point-Free SnapshotTesting dependency must be pinned to version `1.17+` |
| TTC002 | Swift Testing snapshot integration must use `@Suite(.snapshots(record: .failed))` |
| TTC003 | Snapshot config must use scoped `withSnapshotTesting(record:diffTool:)` |
| TTC004 | Global `isRecording` flags are forbidden |
| TTC005 | Snapshot tests are forbidden in UI test targets |

### Snapshot Coverage and Determinism

| Rule | Constraint |
|------|-----------|
| TTC006 | Required snapshot targets and variants must exist (light/dark x body/accessibility3): cover page, table of contents, article page, signature block unsigned, signature block signed, letter detail, thought detail |
| TTC007 | Snapshot data must be deterministic (no dates, randomness, or environment-dependent values) |

### ViewModel Testing

| Rule | Constraint |
|------|-----------|
| TTC008 | Every `ViewModel` type must have unit tests |
| TTC009 | Unit tests must use Swift Testing `@Test`; XCTestCase-only tests are forbidden |
| TTC010 | `@MainActor` ViewModels require `@MainActor` tests |

### Networking Isolation

| Rule | Constraint |
|------|-----------|
| TTC011 | Networking tests must stub transport with `URLProtocol` |
| TTC012 | Networking tests must use recorded response fixtures |
| TTC013 | Tests must never call real servers |

### Signature Export

| Rule | Constraint |
|------|-----------|
| TTC014 | Signature export tests must assert non-empty PNG output |
| TTC015 | Signature export tests must assert PNG payload under 50KB |
| TTC016 | Signature export tests must assert crop to drawing bounds before encoding |

### Integration Flow

| Rule | Constraint |
|------|-----------|
| TTC017 | Integration tests must cover seed/sync/content/upload/confirm flow |

### CI Gates

| Rule | Constraint |
|------|-----------|
| TTC018 | Every `@Test` must enforce a time limit of 2 seconds or less |
| TTC019 | Coverage evidence must exist and report at least 85% |
| TTC020 | PR diff introducing Swift functionality must include test changes |

### Dependency Mocking

| Rule | Constraint |
|------|-----------|
| TTC021 | Tests must mock dependencies via protocols, never concrete production types |

Reference: `references/ios-testing-baseline.md`

## Output

Emit this exact structure:

```json
{
  "contract": "testing-contract",
  "verdict": "PASS | REJECT",
  "summary": {
    "files_scanned": 0,
    "rules_checked": 22,
    "violations": 0
  },
  "violations": [
    {
      "rule_id": "TTC000",
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
