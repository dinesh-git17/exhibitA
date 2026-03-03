import SwiftUI

/// Uppercase classification label with tracked typography and accent styling.
struct ClassificationLabel: View {
    private let text: String

    private static let tracking: CGFloat = 2

    init(_ text: String) {
        self.text = text
    }

    var body: some View {
        Text(text.uppercased())
            .font(Theme.Typography.label)
            .tracking(Self.tracking)
            .foregroundStyle(Theme.Colors.Accent.soft)
    }
}

// MARK: - Previews

#Preview("Letter") {
    ClassificationLabel("Letter")
        .padding()
}

#Preview("Thought") {
    ClassificationLabel("Sealed Thought")
        .padding()
}

#Preview("Dark Mode") {
    ClassificationLabel("Contract")
        .padding()
        .preferredColorScheme(.dark)
}
