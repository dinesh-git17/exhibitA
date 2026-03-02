---
name: networking-layer-contract
description: Enforce Exhibit A's networking architecture contract with deterministic PASS/REJECT validation. Use when creating, editing, reviewing, refactoring, or testing Swift networking code, API clients, endpoint models, retry logic, upload queues, reachability handling, certificate pinning, and network-related test isolation.
---

# Networking Layer Contract

Strict contract enforcement. No advisory mode. Reject every violating change.

## Doctrine

Networking must be type-safe, actor-isolated, deterministic, and failure-aware.

## Validation

Run:

```bash
python3 .claude/skills/networking-layer-contract/scripts/validate_networking_contract.py --root . --format json
```

- Exit code `0` + zero violations = `PASS`.
- Non-zero exit code = `REJECT`.
- Never waive or downgrade a rule.

Scans all `*.swift` files under `--root`, excluding build and dependency directories.

## Contract Rules

### API Client Architecture

| Rule | Constraint |
|------|-----------|
| NLC001 | `APIClient` must be an `actor` |
| NLC002 | `APIClient` must conform to a protocol abstraction for mocking |
| NLC003 | Networking `class` types cannot hold mutable shared state |

### Request/Response Typing

| Rule | Constraint |
|------|-----------|
| NLC004 | `protocol Request` must declare `associatedtype Response: Decodable` |
| NLC016 | Strict Codable models only; no dynamic keys, `AnyCodable`, or `[String: Any]` |

### Transport

| Rule | Constraint |
|------|-----------|
| NLC005 | Completion-handler networking (`dataTask`/`uploadTask`/`downloadTask`) forbidden |
| NLC006 | URLSession usage must be async/await |
| NLC010 | URL construction must be enum-driven; raw URL strings forbidden |
| NLC014 | Every request must enforce a 15-second timeout |

### Resilience and Offline

| Rule | Constraint |
|------|-----------|
| NLC007 | Retry policy: exponential backoff, max 3 retries, retry only network or 5xx failures |
| NLC011 | Offline upload queue must persist JSON to disk |
| NLC012 | Connectivity-triggered retry must use `NWPathMonitor` |

### Security

| Rule | Constraint |
|------|-----------|
| NLC013 | Certificate pinning for `exhibita.dineshd.dev` required via `URLSessionDelegate` trust challenge |

### Error Handling

| Rule | Constraint |
|------|-----------|
| NLC015 | `APIError` must include: `.networkError(URLError)`, `.serverError(statusCode: Int, body: Data)`, `.decodingError(DecodingError)`, `.unauthorized`, `.notFound` |
| NLC017 | Silent error swallowing forbidden (`try?`, empty/opaque `catch`) |
| NLC018 | Network functions must return `Result<T, APIError>` or `throws(APIError)` |

### Logging

| Rule | Constraint |
|------|-----------|
| NLC008 | Networking logging must use `OSLog` `Logger(subsystem:category:)`, debug-gated |
| NLC009 | `print` and `debugPrint` forbidden |

### Test Isolation

| Rule | Constraint |
|------|-----------|
| NLC019 | Tests must not hit real servers; use mocks/stubs with `URLProtocol` |

Reference: `references/swift-networking-baseline.md`

## Output

Emit this exact structure:

```json
{
  "contract": "networking-layer-contract",
  "verdict": "PASS | REJECT",
  "summary": {
    "files_scanned": 0,
    "rules_checked": 19,
    "violations": 0
  },
  "violations": [
    {
      "rule_id": "NLC000",
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
