# Error Handling Reliability Baseline

## Purpose

Map modern reliability and UX expectations to deterministic contract checks for Exhibit A.

## Enforcement Principles

1. Treat recoverable failures as product states, not exceptional dead-ends.
2. Enforce deterministic output (`PASS`/`REJECT`) with machine-readable violations.
3. Reject technical leakage in user-facing copy.
4. Require explicit recovery affordances for every surfaced error state.
5. Block crash-prone constructs in production paths.

## Research-Aligned Baselines

1. Apple guidance supports connectivity-aware retry and avoiding unnecessary preflight failures (`waitsForConnectivity`, adaptive network handling).
2. Apple loading guidance supports content-shaped placeholders/skeletons over generic loading waits.
3. Swift error modeling favors explicit error typing and controlled handling paths.
4. VoiceOver and writing guidance require clear, concise, user-centered messaging instead of developer diagnostics.

## Rule Mapping

- `EHC001-EHC006`: Connectivity/offline failure behavior and sync retry doctrine.
- `EHC007-EHC009`: Empty/loading state UX quality gates.
- `EHC010-EHC011` and `EHC016`: Typed errors and exhaustive handling requirements.
- `EHC012-EHC013` and `EHC017-EHC018`: Tone, recovery, and human-centered messaging constraints.
- `EHC014-EHC015`: Crash prevention and production safety constraints.
