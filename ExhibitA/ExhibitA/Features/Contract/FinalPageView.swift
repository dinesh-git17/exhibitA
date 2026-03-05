import SwiftUI

struct FinalPageView: View {
    private static let bodyLineSpacing: CGFloat = 18 * (Theme.LineHeight.reading - 1.0)

    var body: some View {
        VStack(spacing: 0) {
            Spacer(minLength: Theme.Spacing.xl)

            headingBlock
                .padding(.bottom, Theme.Spacing.xxl)

            bodyBlock
                .padding(.bottom, Theme.Spacing.xxl)

            closingBlock

            Spacer(minLength: Theme.Spacing.xl)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding(.horizontal, Theme.Spacing.readingHorizontal)
        .background {
            Theme.Colors.Background.reading.ignoresSafeArea()
        }
        .paperNoise()
    }

    // MARK: - Heading

    private var headingBlock: some View {
        Text("IN WITNESS WHEREOF")
            .font(Theme.Typography.screenTitle)
            .foregroundStyle(Theme.Colors.Text.primary)
            .tracking(1.5)
            .multilineTextAlignment(.center)
            .accessibilityAddTraits(.isHeader)
    }

    // MARK: - Body

    private var bodyBlock: some View {
        VStack(spacing: Theme.Spacing.paragraphSpacing) {
            Text("The Parties have executed this Agreement as of the date first written above, with full knowledge that they are stuck with each other.")
                .lineSpacing(Self.bodyLineSpacing)

            Text("This contract shall remain in effect in perpetuity, through every chapter still to come, and all the moments still waiting to be shared.")
                .lineSpacing(Self.bodyLineSpacing)
        }
        .font(Theme.Typography.contractBody)
        .foregroundStyle(Theme.Colors.Text.reading)
        .multilineTextAlignment(.center)
        .accessibilityElement(children: .combine)
    }

    // MARK: - Closing

    private var closingBlock: some View {
        VStack(spacing: Theme.Spacing.md) {
            Text("With all my love and legal obligation,")
                .font(Theme.Typography.legalPreamble)
                .foregroundStyle(Theme.Colors.Text.secondary)

            VStack(spacing: Theme.Spacing.xs) {
                Text("Dinesh & Carolina")
                    .font(Theme.Typography.sectionMarker)
                    .foregroundStyle(Theme.Colors.Text.primary)

                Text("Est. 2025")
                    .font(Theme.Typography.metadata)
                    .foregroundStyle(Theme.Colors.Text.muted)
            }
        }
        .multilineTextAlignment(.center)
        .accessibilityElement(children: .combine)
        .accessibilityLabel("With all love and legal obligation, Dinesh and Carolina, established 2025")
    }
}

// MARK: - Previews

#Preview("Final Page") {
    FinalPageView()
}

#Preview("Dark Mode") {
    FinalPageView()
        .preferredColorScheme(.dark)
}
