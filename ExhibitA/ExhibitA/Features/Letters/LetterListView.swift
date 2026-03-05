import SwiftUI

struct LetterListView: View {
    @Environment(AppState.self) private var appState
    @Environment(Router.self) private var router

    private var letters: [ContentItem] {
        appState.cachedContent
            .filter { $0.type == .letter }
            .sorted { $0.sectionOrder > $1.sectionOrder }
    }

    var body: some View {
        ScrollView {
            LazyVStack(spacing: 0) {
                headerSection
                    .padding(.bottom, Theme.Spacing.lg)

                separator

                ForEach(letters) { letter in
                    letterRow(letter)
                    separator
                }
            }
        }
        .background(Theme.Colors.Background.primary, ignoresSafeAreaEdges: .all)
        .toolbarBackground(Theme.Colors.Background.primary, for: .navigationBar)
        .toolbarBackground(.visible, for: .navigationBar)
        .navigationBarTitleDisplayMode(.inline)
    }

    // MARK: - Header

    private var headerSection: some View {
        VStack(spacing: Theme.Spacing.sm) {
            Text("CORRESPONDENCE ON RECORD")
                .font(Theme.Typography.screenTitle)
                .foregroundStyle(Theme.Colors.Text.primary)
                .tracking(0.5)
                .multilineTextAlignment(.center)

            Text("Dinesh & Carolina")
                .font(Theme.Typography.metadata)
                .foregroundStyle(Theme.Colors.Text.muted)
        }
        .padding(.top, Theme.Spacing.xl)
        .frame(maxWidth: .infinity)
        .accessibilityElement(children: .combine)
    }

    // MARK: - Letter Row

    private func letterRow(_ letter: ContentItem) -> some View {
        Button {
            router.navigate(to: .letterDetail(id: letter.id))
        } label: {
            VStack(alignment: .leading, spacing: Theme.Spacing.sm) {
                HStack {
                    ExhibitBadge(exhibitIdentifier(for: letter))
                    Spacer(minLength: 0)
                    UnreadBadge(isUnread: !appState.hasBeenSeen(letter.id))
                }

                if let title = letter.title {
                    Text("\"\(title)\"")
                        .font(Theme.Typography.articleTitle)
                        .foregroundStyle(Theme.Colors.Text.primary)
                        .fixedSize(horizontal: false, vertical: true)
                        .multilineTextAlignment(.leading)
                }

                Text(filedDateText(for: letter))
                    .font(Theme.Typography.metadata)
                    .foregroundStyle(Theme.Colors.Text.muted)

                if let classification = letter.classification {
                    ClassificationLabel(classification)
                }
            }
            .padding(.horizontal, Theme.Spacing.readingHorizontal)
            .padding(.vertical, Theme.Spacing.md)
            .frame(maxWidth: .infinity, alignment: .leading)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .accessibilityHint("Opens letter detail")
    }

    // MARK: - Separator

    private var separator: some View {
        Rectangle()
            .fill(Theme.Colors.Border.separator)
            .frame(height: Theme.Dividers.hairline)
            .accessibilityHidden(true)
    }

    // MARK: - Formatting

    private func exhibitIdentifier(for letter: ContentItem) -> String {
        "EXHIBIT L-\(String(format: "%03d", letter.sectionOrder))"
    }

    private func filedDateText(for letter: ContentItem) -> String {
        "Filed: \(letter.createdAt.formatted(.dateTime.month(.wide).day().year()))"
    }
}

// MARK: - Previews

#Preview("Letters") {
    let state = AppState()
    let _ = state.updateCachedContent([
        ContentItem(
            id: "letter-1",
            type: .letter,
            title: "Closing Arguments for Why You're Perfect",
            subtitle: "On the Matter of Perfection",
            body: "",
            articleNumber: nil,
            classification: "Closing Statement",
            sectionOrder: 3,
            requiresSignature: false,
            createdAt: Calendar.current.date(
                from: DateComponents(year: 2026, month: 2, day: 14)
            ) ?? .now,
            updatedAt: Calendar.current.date(
                from: DateComponents(year: 2026, month: 2, day: 14)
            ) ?? .now
        ),
        ContentItem(
            id: "letter-2",
            type: .letter,
            title: "Motion to Appreciate All the Small Things",
            subtitle: "On the Matter of Gratitude",
            body: "",
            articleNumber: nil,
            classification: "Motion to Appreciate",
            sectionOrder: 2,
            requiresSignature: false,
            createdAt: Calendar.current.date(
                from: DateComponents(year: 2026, month: 1, day: 15)
            ) ?? .now,
            updatedAt: Calendar.current.date(
                from: DateComponents(year: 2026, month: 1, day: 15)
            ) ?? .now
        ),
        ContentItem(
            id: "letter-3",
            type: .letter,
            title: "Initial Filing of Affection",
            subtitle: "On the Matter of First Impressions",
            body: "",
            articleNumber: nil,
            classification: "Sincere",
            sectionOrder: 1,
            requiresSignature: false,
            createdAt: Calendar.current.date(
                from: DateComponents(year: 2025, month: 12, day: 1)
            ) ?? .now,
            updatedAt: Calendar.current.date(
                from: DateComponents(year: 2025, month: 12, day: 1)
            ) ?? .now
        ),
    ])
    let _ = state.markSeen("letter-2")

    NavigationStack {
        LetterListView()
    }
    .environment(state)
    .environment(Router())
}

#Preview("Dark Mode") {
    let state = AppState()
    let _ = state.updateCachedContent([
        ContentItem(
            id: "letter-1",
            type: .letter,
            title: "Emergency Motion Regarding Missing Goodnight Texts",
            subtitle: "On the Matter of Communication",
            body: "",
            articleNumber: nil,
            classification: "Emergency Filing",
            sectionOrder: 2,
            requiresSignature: false,
            createdAt: Calendar.current.date(
                from: DateComponents(year: 2026, month: 2, day: 1)
            ) ?? .now,
            updatedAt: Calendar.current.date(
                from: DateComponents(year: 2026, month: 2, day: 1)
            ) ?? .now
        ),
        ContentItem(
            id: "letter-2",
            type: .letter,
            title: "Addendum to Previous Declaration of Love",
            subtitle: "On the Matter of Amendments",
            body: "",
            articleNumber: nil,
            classification: "Addendum to Previous Affection",
            sectionOrder: 1,
            requiresSignature: false,
            createdAt: Calendar.current.date(
                from: DateComponents(year: 2026, month: 1, day: 20)
            ) ?? .now,
            updatedAt: Calendar.current.date(
                from: DateComponents(year: 2026, month: 1, day: 20)
            ) ?? .now
        ),
    ])

    NavigationStack {
        LetterListView()
    }
    .environment(state)
    .environment(Router())
    .preferredColorScheme(.dark)
}

#Preview("Empty") {
    NavigationStack {
        LetterListView()
    }
    .environment(AppState())
    .environment(Router())
}
