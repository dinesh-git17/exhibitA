import SwiftUI

struct CoverPageView: View {
    let filedDate: Date?

    var body: some View {
        coverContent
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background {
                Theme.Colors.Background.reading.ignoresSafeArea()
            }
            .paperNoise()
    }

    // MARK: - Content

    private var coverContent: some View {
        VStack(spacing: 0) {
            Spacer(minLength: Theme.Spacing.xl)

            titleBlock
                .padding(.bottom, Theme.Spacing.xxl)

            partiesBlock
                .padding(.bottom, Theme.Spacing.xl)

            caseBlock
                .padding(.bottom, Theme.Spacing.xl)

            quoteBlock
                .padding(.bottom, Theme.Spacing.lg)

            MonogramView(fontSize: 40)

            Spacer(minLength: Theme.Spacing.xl)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding(.horizontal, Theme.Spacing.readingHorizontal)
    }

    // MARK: - Title

    private var titleBlock: some View {
        VStack(spacing: Theme.Spacing.xs) {
            Text("THE OFFICIAL & LEGALLY")
            Text("BINDING LOVE CONTRACT")
        }
        .font(Theme.Typography.screenTitle)
        .foregroundStyle(Theme.Colors.Text.primary)
        .multilineTextAlignment(.center)
        .accessibilityElement(children: .combine)
        .accessibilityAddTraits(.isHeader)
    }

    // MARK: - Parties

    private var partiesBlock: some View {
        VStack(spacing: Theme.Spacing.sm) {
            Text("Between the Parties:")
                .font(Theme.Typography.metadata)
                .foregroundStyle(Theme.Colors.Text.muted)

            partyEntry("DINESH DAWONAUTH", role: "The Boyfriend")

            Text("\u{2014} and \u{2014}")
                .font(Theme.Typography.legalPreamble)
                .foregroundStyle(Theme.Colors.Text.muted)

            partyEntry("CAROLINA LOMBARDO", role: "The Girlfriend")
        }
        .multilineTextAlignment(.center)
        .accessibilityElement(children: .combine)
    }

    private func partyEntry(_ name: String, role: String) -> some View {
        VStack(spacing: Theme.Spacing.xs) {
            Text(name)
                .font(Theme.Typography.articleTitle)
                .foregroundStyle(Theme.Colors.Text.primary)
            Text("(\"\(role)\")")
                .font(Theme.Typography.metadata)
                .foregroundStyle(Theme.Colors.Text.secondary)
        }
    }

    // MARK: - Case Details

    private var caseBlock: some View {
        VStack(spacing: Theme.Spacing.xs) {
            Text("Case No. CD-2025-0126")
            Text("Filed: \(filedDateDisplay)")
            Text("Jurisdiction: The Supreme Court of Us")
        }
        .font(Theme.Typography.metadata)
        .foregroundStyle(Theme.Colors.Text.muted)
        .multilineTextAlignment(.center)
        .accessibilityElement(children: .combine)
    }

    private var filedDateDisplay: String {
        guard let date = filedDate else {
            return "Awaiting filing"
        }
        return date.formatted(.dateTime.month(.wide).day().year())
    }

    // MARK: - Quote

    private var quoteBlock: some View {
        VStack(spacing: Theme.Spacing.xs) {
            Text("\"No refunds. No exchanges.")
            Text("All sales are final.\"")
        }
        .font(Theme.Typography.pullQuote)
        .foregroundStyle(Theme.Colors.Text.secondary)
        .multilineTextAlignment(.center)
        .accessibilityElement(children: .combine)
    }
}

// MARK: - Previews

#Preview("Cover Page") {
    CoverPageView(
        filedDate: Calendar.current.date(
            from: DateComponents(year: 2025, month: 2, day: 14)
        )
    )
}

#Preview("Cover - No Date") {
    CoverPageView(filedDate: nil)
}

#Preview("Cover - Dark Mode") {
    CoverPageView(
        filedDate: Calendar.current.date(
            from: DateComponents(year: 2025, month: 2, day: 14)
        )
    )
    .preferredColorScheme(.dark)
}
