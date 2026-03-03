import SwiftUI

/// Pulsing unread indicator dot with a 2-second breathing animation cycle.
struct UnreadBadge: View {
    let isUnread: Bool

    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @ScaledMetric(relativeTo: .caption) private var dotSize: CGFloat = 8

    private static let phaseDuration: TimeInterval = 1.0
    private static let expandedScale: CGFloat = 1.15
    private static let restingOpacity = 0.8

    private enum PulsePhase: CaseIterable {
        case resting, expanded
    }

    var body: some View {
        if isUnread {
            Circle()
                .fill(Theme.Colors.Accent.primary)
                .frame(width: dotSize, height: dotSize)
                .phaseAnimator(
                    PulsePhase.allCases,
                    content: { view, phase in
                        view
                            .scaleEffect(scaleFor(phase))
                            .opacity(opacityFor(phase))
                    },
                    animation: { _ in
                        reduceMotion
                            ? nil
                            : .easeInOut(duration: Self.phaseDuration)
                    },
                )
                .accessibilityLabel("Unread")
        }
    }

    // MARK: - Animation Values

    private func scaleFor(_ phase: PulsePhase) -> CGFloat {
        guard !reduceMotion else { return 1.0 }
        return phase == .expanded ? Self.expandedScale : 1.0
    }

    private func opacityFor(_ phase: PulsePhase) -> Double {
        guard !reduceMotion else { return 1.0 }
        return phase == .expanded ? 1.0 : Self.restingOpacity
    }
}

// MARK: - Previews

#Preview("Unread") {
    UnreadBadge(isUnread: true)
        .padding()
}

#Preview("Read") {
    UnreadBadge(isUnread: false)
        .padding()
}

#Preview("Dark Mode") {
    UnreadBadge(isUnread: true)
        .padding()
        .preferredColorScheme(.dark)
}
