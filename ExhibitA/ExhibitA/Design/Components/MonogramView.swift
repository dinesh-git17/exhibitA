import SwiftUI

/// Reusable `EA` monogram rendered in New York Bold with accent styling.
struct MonogramView: View {
    private let fontSize: CGFloat

    private static let monogram = "EA"
    private static let defaultFontSize: CGFloat = 28

    init(fontSize: CGFloat = Self.defaultFontSize) {
        self.fontSize = fontSize
    }

    var body: some View {
        Text(Self.monogram)
            .font(.system(size: fontSize, weight: .bold, design: .serif))
            .foregroundStyle(Theme.Colors.Accent.primary)
            .accessibilityLabel("Exhibit A")
    }
}

// MARK: - Previews

#Preview("Default") {
    MonogramView()
        .padding()
}

#Preview("Large") {
    MonogramView(fontSize: 48)
        .padding()
}

#Preview("Dark Mode") {
    MonogramView()
        .padding()
        .preferredColorScheme(.dark)
}
