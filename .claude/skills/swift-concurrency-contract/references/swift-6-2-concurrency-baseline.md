# Swift 6.2 Concurrency Baseline (2026)

Use this baseline to justify the contract rules in `SKILL.md`.

## Platform Direction

- Swift 6.2 adds project-level default actor isolation controls, including `.defaultIsolation(MainActor.self)` for UI-first apps.
- Swift 6.2 introduces default behavior where nonisolated async functions run on the caller's actor (`NonisolatedNonsendingByDefault`).
- Swift 6.2 supports inferring actor-isolated conformances (`InferIsolatedConformances`) to reduce accidental nonisolated conformances.
- The modern direction is progressive concurrency adoption: start safe and simple, then add explicit concurrency boundaries where measurable benefit exists.

## SwiftUI Runtime Expectations

- Main actor is the default execution context for UI state and rendering.
- Lifecycle-bound asynchronous work belongs in `.task {}`.
- Intentional user-triggered fire-and-forget UI actions can use `Task {}`.
- Parallel fan-out work should use structured concurrency (`withTaskGroup` / `withThrowingTaskGroup`) rather than ad-hoc detached tasks.

## Cancellation Discipline

- Cancellation is cooperative and should be handled explicitly.
- Network work and navigation-bound work should include `withTaskCancellationHandler` to clean up side effects and stop work promptly.
- `Task.detached` should be treated as an exception path; justify it explicitly when structure cannot model the work.

## Isolation Guidance

- Keep UI models actor-isolated by default.
- Isolate background work explicitly with `@concurrent` only when true parallelism is required and measurable.
- Avoid mixing legacy async systems (GCD queues, callback chains, Combine-as-transport) with structured Swift concurrency.

## Primary Sources

- Swift.org blog: *Approachable Concurrency in Swift Packages*
- Swift Evolution SE-0461: *Run nonisolated async functions on the caller's actor by default*
- Swift Evolution SE-0466: *Control default actor isolation inference*
- Swift Evolution SE-0470: *Global-actor-isolated conformances*
- Apple Developer Documentation: `withTaskCancellationHandler(operation:onCancel:isolation:)`
- Apple Developer Documentation: `View.task(id:priority:_:)`
- Apple WWDC session: *Embracing Swift concurrency*
- Apple WWDC session: *Code-along: Elevate an app with Swift concurrency*
