# iOS Testing Baseline (2026)

Use this baseline to keep `testing-contract` aligned with current platform/tooling behavior.

## iOS Testing Findings (2024+)

- Swift Testing is Apple's modern test framework direction, with macro-based `@Test` and suite-based organization.
- Swift Testing runs tests in parallel by default and randomizes order, so tests must not depend on execution order or shared mutable state.
- Swift Testing supports traits, including time-limit traits, which provide a deterministic mechanism for runtime ceilings.
- Point-Free SnapshotTesting 1.17+ introduced Swift Testing integration with `@Suite(.snapshots(record: .failed))`.
- Point-Free recommends scoped recording with `withSnapshotTesting(record:diffTool:)` and has deprecated global `isRecording` mutation patterns.
- SnapshotTesting notes simulator/device consistency requirements; snapshot assertions must avoid environment drift.
- For networking isolation in Apple platforms, custom `URLProtocol` + `URLSessionConfiguration.protocolClasses` remains the deterministic stubbing pattern.

## Operational Implications for This Contract

- Enforce snapshot naming and coverage matrices in code, not docs.
- Fail fast when non-deterministic data (`Date`, randomness, environment lookups) appears in snapshot tests.
- Reject PRs that alter Swift feature code without accompanying test deltas.
- Require explicit runtime limits and coverage evidence to keep CI latency and confidence bounded.

## Source Index

- Apple WWDC24 "Meet Swift Testing": https://developer.apple.com/videos/play/wwdc2024/10179/
- Apple WWDC24 "Go further with Swift Testing": https://developer.apple.com/videos/play/wwdc2024/10195/
- Swift Testing repository: https://github.com/swiftlang/swift-testing
- Point-Free SnapshotTesting repository: https://github.com/pointfreeco/swift-snapshot-testing
- Point-Free SnapshotTesting 1.17 announcement: https://www.pointfree.co/blog/posts/146-swift-testing-support-for-snapshottesting
