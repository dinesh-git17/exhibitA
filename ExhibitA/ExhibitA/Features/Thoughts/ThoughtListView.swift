import SwiftUI

struct ThoughtListView: View {
    @Environment(AppState.self) private var appState
    @Environment(Router.self) private var router

    private var thoughts: [ContentItem] {
        appState.cachedContent
            .filter { $0.type == .thought }
            .sorted { $0.sectionOrder > $1.sectionOrder }
    }

    var body: some View {
        ScrollView {
            LazyVStack(spacing: 0) {
                headerSection
                    .padding(.bottom, Theme.Spacing.lg)

                separator

                ForEach(thoughts) { thought in
                    thoughtRow(thought)
                    separator
                }
            }
        }
        .background(Theme.Colors.Background.reading, ignoresSafeAreaEdges: .all)
        .toolbarBackground(Theme.Colors.Background.reading, for: .navigationBar)
        .toolbarBackground(.visible, for: .navigationBar)
        .navigationBarTitleDisplayMode(.inline)
    }

    // MARK: - Header

    private var headerSection: some View {
        VStack(spacing: Theme.Spacing.sm) {
            Text("CLASSIFIED MEMORANDA")
                .font(Theme.Typography.screenTitle)
                .foregroundStyle(Theme.Colors.Text.primary)
                .tracking(0.5)
                .multilineTextAlignment(.center)

            Text("For Authorized Eyes Only")
                .font(Theme.Typography.metadata)
                .foregroundStyle(Theme.Colors.Text.muted)
        }
        .padding(.top, Theme.Spacing.xl)
        .frame(maxWidth: .infinity)
        .accessibilityElement(children: .combine)
    }

    // MARK: - Thought Row

    private func thoughtRow(_ thought: ContentItem) -> some View {
        Button {
            router.navigate(to: .thoughtDetail(id: thought.id))
        } label: {
            VStack(alignment: .leading, spacing: Theme.Spacing.sm) {
                HStack {
                    Text(memoIdentifier(for: thought))
                        .font(Theme.Typography.label)
                        .foregroundStyle(Theme.Colors.Text.secondary)
                        .tracking(1.5)

                    Spacer(minLength: 0)

                    UnreadBadge(isUnread: !appState.hasBeenSeen(thought.id))
                }

                Text(formattedDateTime(for: thought))
                    .font(Theme.Typography.metadata)
                    .foregroundStyle(Theme.Colors.Text.muted)

                Text(previewText(for: thought))
                    .font(Theme.Typography.contractBody)
                    .foregroundStyle(Theme.Colors.Text.reading)
                    .lineLimit(3)
                    .multilineTextAlignment(.leading)
            }
            .padding(.horizontal, Theme.Spacing.readingHorizontal)
            .padding(.vertical, Theme.Spacing.md)
            .frame(maxWidth: .infinity, alignment: .leading)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .accessibilityHint("Opens sealed thought")
    }

    // MARK: - Separator

    private var separator: some View {
        Rectangle()
            .fill(Theme.Colors.Border.separator)
            .frame(height: Theme.Dividers.hairline)
            .accessibilityHidden(true)
    }

    // MARK: - Formatting

    private func memoIdentifier(for thought: ContentItem) -> String {
        "MEMO-\(String(format: "%03d", thought.sectionOrder))"
    }

    private func formattedDateTime(for thought: ContentItem) -> String {
        thought.createdAt.formatted(
            .dateTime.month(.wide).day().year().hour().minute()
        )
    }

    private func previewText(for thought: ContentItem) -> String {
        let trimmed = thought.body.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return "" }
        return trimmed
    }
}

// MARK: - Previews

#Preview("Thoughts") {
    let state = AppState()
    let _ = state.updateCachedContent([
        ContentItem(
            id: "thought-1",
            type: .thought,
            title: nil,
            subtitle: nil,
            body: "Thought about you during my meeting today. Objection: you're distracting.",
            articleNumber: nil,
            classification: nil,
            sectionOrder: 47,
            requiresSignature: false,
            createdAt: Calendar.current.date(
                from: DateComponents(year: 2026, month: 3, day: 1, hour: 23, minute: 42)
            ) ?? .now,
            updatedAt: Calendar.current.date(
                from: DateComponents(year: 2026, month: 3, day: 1, hour: 23, minute: 42)
            ) ?? .now
        ),
        ContentItem(
            id: "thought-2",
            type: .thought,
            title: nil,
            subtitle: nil,
            body: "Morning. This is your daily reminder that you're under contractual obligation to have a good day.",
            articleNumber: nil,
            classification: nil,
            sectionOrder: 46,
            requiresSignature: false,
            createdAt: Calendar.current.date(
                from: DateComponents(year: 2026, month: 2, day: 27, hour: 8, minute: 15)
            ) ?? .now,
            updatedAt: Calendar.current.date(
                from: DateComponents(year: 2026, month: 2, day: 27, hour: 8, minute: 15)
            ) ?? .now
        ),
        ContentItem(
            id: "thought-3",
            type: .thought,
            title: nil,
            subtitle: nil,
            body: "Saw an otter video. Thought of you. Filing this as evidence.",
            articleNumber: nil,
            classification: nil,
            sectionOrder: 45,
            requiresSignature: false,
            createdAt: Calendar.current.date(
                from: DateComponents(year: 2026, month: 2, day: 25, hour: 14, minute: 30)
            ) ?? .now,
            updatedAt: Calendar.current.date(
                from: DateComponents(year: 2026, month: 2, day: 25, hour: 14, minute: 30)
            ) ?? .now
        ),
    ])
    let _ = state.markSeen("thought-2")

    NavigationStack {
        ThoughtListView()
    }
    .environment(state)
    .environment(Router())
}

#Preview("Dark Mode") {
    let state = AppState()
    let _ = state.updateCachedContent([
        ContentItem(
            id: "thought-1",
            type: .thought,
            title: nil,
            subtitle: nil,
            body: "Emergency filing: I miss you. This has been entered into the official record.",
            articleNumber: nil,
            classification: nil,
            sectionOrder: 12,
            requiresSignature: false,
            createdAt: Calendar.current.date(
                from: DateComponents(year: 2026, month: 2, day: 1, hour: 22, minute: 15)
            ) ?? .now,
            updatedAt: Calendar.current.date(
                from: DateComponents(year: 2026, month: 2, day: 1, hour: 22, minute: 15)
            ) ?? .now
        ),
        ContentItem(
            id: "thought-2",
            type: .thought,
            title: nil,
            subtitle: nil,
            body: "Note to self: her laugh should be classified as a controlled substance.",
            articleNumber: nil,
            classification: nil,
            sectionOrder: 11,
            requiresSignature: false,
            createdAt: Calendar.current.date(
                from: DateComponents(year: 2026, month: 1, day: 20, hour: 9, minute: 30)
            ) ?? .now,
            updatedAt: Calendar.current.date(
                from: DateComponents(year: 2026, month: 1, day: 20, hour: 9, minute: 30)
            ) ?? .now
        ),
    ])

    NavigationStack {
        ThoughtListView()
    }
    .environment(state)
    .environment(Router())
    .preferredColorScheme(.dark)
}

#Preview("Empty") {
    NavigationStack {
        ThoughtListView()
    }
    .environment(AppState())
    .environment(Router())
}
