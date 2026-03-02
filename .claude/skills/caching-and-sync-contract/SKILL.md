---
name: caching-and-sync-contract
description: Enforce Exhibit A's offline-first caching and sync architecture contract with deterministic PASS/REJECT validation and structured rejection diagnostics. Use when creating, editing, reviewing, refactoring, or testing Swift iOS code for cache persistence, sync orchestration, optimistic UI, upload flows, launch hydration, unread tracking, rollback behavior, and cache invalidation logic.
---

# Caching and Sync Contract

Strict contract enforcement. No advisory mode. Reject every violating change.

## Doctrine

Local cache is authoritative. Network is synchronization only. UI must never depend on network availability for initial state.

## Required Markers

Place these exact marker comments near the corresponding implementation paths. The validator checks them for deterministic contract traceability:

```swift
// CACHE-CONTRACT: local-cache-authoritative
// CACHE-CONTRACT: network-sync-only
// CACHE-CONTRACT: launch-cache-hydration
// CACHE-CONTRACT: cache-write-atomic-temp-rename
// CACHE-CONTRACT: signatures-optimistic-background-upload
// CACHE-CONTRACT: rollback-retain-cache-show-retry
// CACHE-CONTRACT: invalidate-on-sync-response-only
// CACHE-CONTRACT: launch-latency-under-300ms
// CACHE-CONTRACT: network-background-only
// CACHE-CONTRACT: no-launch-spinner-if-cache
```

## Validation

Run:

```bash
python3 .claude/skills/caching-and-sync-contract/scripts/validate_caching_sync_contract.py --root . --format json
```

- Exit code `0` + zero violations = `PASS`.
- Non-zero exit code = `REJECT`.
- Never waive, downgrade, or reinterpret a rule.

Scans all `*.swift` files under `--root`, excluding build and dependency directories.

## Contract Rules

### Doctrine

| Rule | Constraint |
|------|-----------|
| CSC001 | All required `CACHE-CONTRACT` doctrine markers must exist |

### Cache Persistence

| Rule | Constraint |
|------|-----------|
| CSC002 | Content cache must persist as JSON in app documents directory and hydrate on launch |
| CSC003 | Cache read/write path must be actor-isolated |
| CSC004 | Cache writes must be atomic via temp file plus rename/replace |

### Signature Storage

| Rule | Constraint |
|------|-----------|
| CSC005 | Signature PNG persistence must use content-addressable naming: `{content_id}_{signer}.png` |
| CSC009 | Optimistic UI must place signatures in cache before upload starts |
| CSC010 | Signature upload path must be background-only |

### Sync State Machine

| Rule | Constraint |
|------|-----------|
| CSC006 | `SyncState` must define `.idle`, `.syncing`, `.completed(Date)`, `.failed(Error)` |
| CSC007 | `last_sync_at` must be stored through `UserDefaults` |
| CSC008 | Sync requests must include incremental `since` parameter |

### Failure Resilience

| Rule | Constraint |
|------|-----------|
| CSC011 | Upload failure must set a retry indicator |
| CSC012 | Upload failure must not remove cached signature/content entries |

### Launch Performance

| Rule | Constraint |
|------|-----------|
| CSC013 | Launch cache display target must be declared at or below `300ms` |
| CSC019 | Launch spinner gating on generic loading flags forbidden when cache exists |

### Background Execution

| Rule | Constraint |
|------|-----------|
| CSC014 | Network execution for sync/upload must be configured for background operation |
| CSC020 | UI/main-thread blocking network patterns forbidden |

### Unread Tracking

| Rule | Constraint |
|------|-----------|
| CSC015 | Unread tracking must persist `Set<UUID>` through `UserDefaults` |
| CSC016 | New content not in unread set must drive unread badge logic |

### Cache Invalidation

| Rule | Constraint |
|------|-----------|
| CSC017 | Cache invalidation must be explicitly tied to sync response handling |
| CSC018 | Time-based cache invalidation forbidden |

Reference: `references/offline-first-ios-baseline.md`

## Output

Emit this exact structure:

```json
{
  "contract": "caching-and-sync-contract",
  "verdict": "PASS | REJECT",
  "summary": {
    "files_scanned": 0,
    "rules_checked": 20,
    "violations": 0
  },
  "violations": [
    {
      "rule_id": "CSC000",
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
