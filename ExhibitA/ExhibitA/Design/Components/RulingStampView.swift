import SwiftUI

struct RulingStampView: View {
    let verdict: RulingVerdict

    private static let rotationAngle: Double = -5
    private static let borderWidth: CGFloat = 3

    var body: some View {
        Text(spacedVerdict)
            .font(.system(size: 22, weight: .bold, design: .serif))
            .foregroundStyle(verdictColor.opacity(0.85))
            .tracking(4)
            .padding(.horizontal, Theme.Spacing.lg)
            .padding(.vertical, Theme.Spacing.sm)
            .overlay(
                RoundedRectangle(cornerRadius: 4, style: .continuous)
                    .strokeBorder(verdictColor.opacity(0.85), lineWidth: Self.borderWidth)
            )
            .background(verdictColor.opacity(0.08))
            .rotationEffect(.degrees(Self.rotationAngle))
    }

    private var spacedVerdict: String {
        verdict.rawValue.uppercased().map(String.init).joined(separator: " ")
    }

    private var verdictColor: Color {
        switch verdict {
        case .granted, .sustained:
            Color(red: 0.2, green: 0.55, blue: 0.3)
        case .denied, .overruled:
            Theme.Colors.Accent.primary
        }
    }
}

#Preview("Granted") {
    RulingStampView(verdict: .granted)
        .padding()
        .background(Theme.Colors.Background.reading)
}

#Preview("Denied") {
    RulingStampView(verdict: .denied)
        .padding()
        .background(Theme.Colors.Background.reading)
}

#Preview("Sustained") {
    RulingStampView(verdict: .sustained)
        .padding()
        .background(Theme.Colors.Background.reading)
}

#Preview("Overruled") {
    RulingStampView(verdict: .overruled)
        .padding()
        .background(Theme.Colors.Background.reading)
}
