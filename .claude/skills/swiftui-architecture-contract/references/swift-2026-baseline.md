# Swift 6.2 + SwiftUI Baseline (Research Snapshot)

Use this file as normative context for the contract rules.

## Language + Concurrency Sources

- Swift 6.2 release post: `https://www.swift.org/blog/announcing-swift-6.2/`
- Default actor isolation article: `https://www.swift.org/documentation/articles/default-actor-isolation-in-swift-6-2.html`
- SE-0466 (control default actor isolation): `https://raw.githubusercontent.com/swiftlang/swift-evolution/main/proposals/0466-control-default-actor-isolation.md`
- SE-0461 (async function isolation): `https://raw.githubusercontent.com/swiftlang/swift-evolution/main/proposals/0461-async-function-isolation.md`
- SE-0470 (global-actor isolated conformances): `https://raw.githubusercontent.com/swiftlang/swift-evolution/main/proposals/0470-isolated-conformances.md`

## SwiftUI Architecture + Observation Sources

- WWDC24 "What's new in SwiftUI": `https://developer.apple.com/videos/play/wwdc2024/10144/`
- WWDC23 "Discover Observation in SwiftUI": `https://developer.apple.com/videos/play/wwdc2023/10149/`
- WWDC25 "Optimize SwiftUI performance with Instruments": `https://developer.apple.com/videos/play/wwdc2025/306/`
- SwiftUI `EnvironmentValues`: `https://developer.apple.com/documentation/swiftui/environmentvalues/`
- Apple sample app (`NavigationPath` and model-driven navigation): `https://github.com/apple/sample-food-truck`
- SwiftUI previews in Xcode: `https://developer.apple.com/documentation/swiftui/previews-in-xcode`

## Contract-Oriented Findings

- Swift 6.2 supports approachable concurrency and project-level default actor isolation.
- Async isolation behavior is now explicit and must be configured intentionally.
- Observation tracks property access and updates only dependents that read changed values.
- SwiftUI navigation is model-driven and supports type-safe routing with route values.
- Environment keys are the first-class mechanism for dependency flow through the view tree.
- Modern preview workflows emphasize lightweight, isolated mock data.
