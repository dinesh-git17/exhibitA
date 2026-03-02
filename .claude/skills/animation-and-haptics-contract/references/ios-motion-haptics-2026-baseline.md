# iOS Motion + Haptics Baseline (2026)

This baseline captures the external platform direction used to author the contract rules.

## Motion Intent and Accessibility

- Apple HIG transitions guidance emphasizes continuity, hierarchy, and reducing motion when requested.
- Reduced motion must be honored by providing less or no animation where possible.
- SwiftUI exposes `@Environment(\.accessibilityReduceMotion)` for per-view adaptation.

## SwiftUI Animation System

- WWDC guidance on spring updates introduced perceptual tuning through `duration` and `bounce`.
- Contract rule design requires explicit parameters to avoid hidden defaults and drift.
- Contract constrains product language to explicit spring/ease families with fixed durations.

## Haptics Pairing Principles

- Apple HIG haptics guidance emphasizes consistent, meaningful haptic responses and avoiding novelty-only feedback.
- Haptics should reinforce clear UX events and align with visual state changes.

## Audio for Short UI Feedback

- AVFAudio docs for `AVAudioPlayer.prepareToPlay()` note preloading behavior for lower startup latency.
- Contract requires optional, user-toggleable UI sounds and forbids SystemSoundID paths.

## Performance Direction

- Apple performance talks target consistent frame delivery at display refresh rates and responsive main-thread behavior.
- Contract encodes a minimum 60fps target for page-curl flows and bans blocking delay calls in motion/haptic paths.

## Source Links

- Apple HIG transitions: https://developer.apple.com/design/human-interface-guidelines/transitions
- Apple HIG playing haptics: https://developer.apple.com/design/human-interface-guidelines/playing-haptics
- SwiftUI withAnimation reference: https://developer.apple.com/documentation/swiftui/withanimation%28_%3A_%3A%29
- WWDC23 spring animation updates: https://developer.apple.com/videos/play/wwdc2023/10156/
- EnvironmentValues.accessibilityReduceMotion: https://developer.apple.com/documentation/swiftui/environmentvalues/accessibilityreducemotion
- AVAudioPlayer.prepareToPlay(): https://developer.apple.com/documentation/avfaudio/avaudioplayer/1388508-preparetoplay
- UIPageViewController transition style: https://developer.apple.com/documentation/uikit/uipageviewcontroller/transitionstyle-swift.enum/pagecurl
- Apple responsiveness guidance: https://developer.apple.com/documentation/xcode/improving-app-responsiveness
