# PencilKit 2026 Baseline

Target: high-fidelity signature capture in SwiftUI with deterministic quality controls.

## PencilKit + SwiftUI Baseline

- Bridge UIKit `PKCanvasView` into SwiftUI with `UIViewRepresentable` (`makeUIView`, `updateUIView`).
- Configure drawing input policy explicitly; support finger interaction for inclusive input (`drawingPolicy = .anyInput`).
- Use `PKDrawing.dataRepresentation()` for persistence and `PKDrawing.image(from:scale:)` for rendered export.
- Render export with display scale (`UIScreen.main.scale`), crop to drawing bounds, and avoid full-canvas export.

Source:
- https://developer.apple.com/documentation/swiftui/uiviewrepresentable
- https://developer.apple.com/documentation/pencilkit/adopting-pencilkit-for-ios
- https://developer.apple.com/documentation/pencilkit/pkdrawing-swift.struct/datarepresentation()
- https://developer.apple.com/documentation/pencilkit/pkdrawing-swift.struct/image%28from%3Ascale%3A%29

## Rendering and PNG Output Baseline

- Use `UIGraphicsImageRenderer` with explicit scale to preserve Retina output consistency.
- Encode signature assets with `UIImage.pngData()` after crop/downscale decisions.
- Keep byte budget deterministic (target `< 50KB`) via crop-first, padding discipline, and size checks.

Source:
- https://developer.apple.com/documentation/uikit/uigraphicsimagerenderer
- https://developer.apple.com/documentation/uikit/uigraphicsimagerendererformat
- https://developer.apple.com/documentation/uikit/uiimage/pngdata%28%29

## Defensive Availability and Accessibility Baseline

- Guard framework usage with conditional compilation (`#if canImport(PencilKit)`), with a non-PencilKit fallback path.
- Follow custom-control accessibility fundamentals: explicit labels, values, hints, and state updates.

Source:
- https://docs.swift.org/swift-book/documentation/the-swift-programming-language/statements/#Conditional-Compilation-Block
- https://developer.apple.com/documentation/accessibility/enhancing-the-accessibility-of-your-swiftui-app
