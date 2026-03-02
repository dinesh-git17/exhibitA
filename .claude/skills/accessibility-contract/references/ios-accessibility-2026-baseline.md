# iOS Accessibility Baseline (2026)

This baseline captures the platform direction used to author the Accessibility Contract.

## WCAG 2.2 AA Mobile Thresholds

- WCAG 2.2 AA contrast minimums remain 4.5:1 for body text and 3:1 for large text.
- WCAG 2.2 adds Target Size (Minimum) at AA level (2.5.8) and reinforces touch target sizing expectations for mobile interfaces.

## Apple Accessibility Guidance (2024-present)

- Apple Human Interface Guidelines accessibility hub continues to center inclusive design and assistive technology support.
- Apple's accessibility updates include VoiceOver-focused guidance updates (March 2025 cycle).
- App Store accessibility criteria reinforce semantic labeling, larger text behavior, and sufficient contrast as measurable release criteria.

## VoiceOver in SwiftUI/UIKit Hybrids

- Custom controls must expose equivalent semantics through accessibility labels, hints, values, and traits.
- SwiftUI and UIKit paths both require explicit metadata for non-standard controls.
- For gesture-heavy interactions (like page curl), provide alternative accessible actions and rotor-adjustable navigation.

## Dynamic Type and Reflow

- Large text support requires semantic text styles and responsive layout reflow.
- Pagination and dense layouts must avoid clipping/truncation at accessibility sizes by switching to reflowed structures when needed.

## Focus Management

- SwiftUI focus management patterns use `@AccessibilityFocusState` and `.accessibilityFocused(...)` for deterministic handoff.
- UIKit focus transitions use `UIAccessibility.post(notification: .layoutChanged/.screenChanged, argument: ...)`.

## Automated Accessibility Testing

- Xcode UI testing supports automated accessibility audits (`performAccessibilityAudit(for:)`) for categories like hit region, contrast, and labels.
- Project contract requires wrapping this in `performA11yAudit()` and gating completion on passing audits.

## Contrast Validation for Custom Palettes

- Custom color systems must be validated against WCAG thresholds in both light and dark appearances.
- Accessibility Inspector and automated checks are expected for repeatable contrast validation.

## Source Links

- WCAG 2.2 Quick Reference: https://www.w3.org/WAI/WCAG22/quickref/
- WCAG 2.2 Understanding 1.4.3 Contrast (Minimum): https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html
- WCAG 2.2 Understanding 2.5.8 Target Size (Minimum): https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum
- Apple HIG Accessibility: https://developer.apple.com/design/human-interface-guidelines/accessibility
- App Store Accessibility Criteria - VoiceOver: https://developer.apple.com/help/app-store-connect/manage-app-accessibility/voiceover-evaluation-criteria
- App Store Accessibility Criteria - Larger Text: https://developer.apple.com/help/app-store-connect/manage-app-accessibility/larger-text-evaluation-criteria
- App Store Accessibility Criteria - Sufficient Contrast: https://developer.apple.com/help/app-store-connect/manage-app-accessibility/sufficient-contrast-evaluation-criteria
- SwiftUI accessibility focus state (WWDC23): https://developer.apple.com/videos/play/wwdc2023/10036/
- UIAccessibility notifications: https://developer.apple.com/documentation/uikit/uiaccessibility/post%28notification%3Aargument%3A%29
- Xcode accessibility audits (WWDC23): https://developer.apple.com/videos/play/wwdc2023/10037/
