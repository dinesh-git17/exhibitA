import SwiftUI

/// Formatted exhibit identifier badge with token-based border and surface styling.
struct ExhibitBadge: View {
    private let identifier: String

    private static let tracking: CGFloat = 1.5
    private static let cornerRadius: CGFloat = 4

    init(_ identifier: String) {
        self.identifier = identifier
    }

    var body: some View {
        Text(identifier.uppercased())
            .font(Theme.Typography.pageNumber)
            .tracking(Self.tracking)
            .foregroundStyle(Theme.Colors.Text.secondary)
            .padding(.horizontal, Theme.Spacing.sm)
            .padding(.vertical, Theme.Spacing.xs)
            .background(Theme.Colors.Background.tertiary)
            .clipShape(RoundedRectangle(cornerRadius: Self.cornerRadius))
            .overlay(
                RoundedRectangle(cornerRadius: Self.cornerRadius)
                    .strokeBorder(
                        Theme.Colors.Border.separator,
                        lineWidth: Theme.Dividers.hairline,
                    ),
            )
    }
}

// MARK: - Previews

#Preview("Letter") {
    ExhibitBadge("Exhibit L-001")
        .padding()
}

#Preview("Contract") {
    ExhibitBadge("Exhibit C-012")
        .padding()
}

#Preview("Dark Mode") {
    ExhibitBadge("Exhibit T-003")
        .padding()
        .preferredColorScheme(.dark)
}
