import SwiftUI

struct ThoughtDetailView: View {
    let id: String
    let client: ExhibitAClient
    @Environment(AppState.self) private var appState

    private var thought: ContentItem? {
        appState.cachedContent.first { $0.id == id }
    }

    var body: some View {
        ZStack {
            Theme.Colors.Background.reading
                .ignoresSafeArea()

            if let thought {
                readerContent(thought)
            }
        }
        .paperNoise()
        .toolbarBackground(Theme.Colors.Background.reading, for: .navigationBar)
        .toolbarBackground(.visible, for: .navigationBar)
        .navigationBarTitleDisplayMode(.inline)
        .onAppear { markAsRead() }
    }

    // MARK: - Reader Content

    private func readerContent(_ thought: ContentItem) -> some View {
        ScrollViewReader { proxy in
            ScrollView {
                VStack(spacing: 0) {
                    Text(formattedDateTime(for: thought))
                        .font(Theme.Typography.metadata)
                        .foregroundStyle(Theme.Colors.Text.muted)

                    Text(thought.body)
                        .font(Theme.Typography.contractBody)
                        .foregroundStyle(Theme.Colors.Text.reading)
                        .lineSpacing(Self.bodyLineSpacing)
                        .multilineTextAlignment(.center)
                        .fixedSize(horizontal: false, vertical: true)
                        .padding(.top, Theme.Spacing.lg)

                    responseSection(thought)
                        .padding(.top, Theme.Spacing.lg)
                        .id("response")
                }
                .padding(.horizontal, Theme.Spacing.xl)
                .padding(.vertical, Theme.Spacing.xxl)
                .frame(maxWidth: .infinity)
            }
            .scrollDismissesKeyboard(.interactively)
            .onReceive(NotificationCenter.default.publisher(for: UIResponder.keyboardWillShowNotification)) { _ in
                withAnimation(.easeOut(duration: 0.3)) {
                    proxy.scrollTo("response", anchor: .bottom)
                }
            }
        }
    }

    // MARK: - Response Section

    @ViewBuilder
    private func responseSection(_ thought: ContentItem) -> some View {
        let responses = appState.commentsForContent(thought.id)
        let hasMyComment = appState.comment(
            forContentId: thought.id,
            signer: Config.signerIdentity
        ) != nil

        if !responses.isEmpty || !hasMyComment {
            VStack(spacing: Theme.Spacing.md) {
                Rectangle()
                    .fill(Theme.Colors.Accent.gold.opacity(0.3))
                    .frame(height: Theme.Dividers.hairline)
                    .accessibilityHidden(true)

                ForEach(responses) { comment in
                    ResponseOnRecordView(comment: comment)
                }

                if !hasMyComment {
                    CommentComposeView(contentId: thought.id, client: client)
                }
            }
            .multilineTextAlignment(.center)
        }
    }

    // MARK: - Typography

    private static let bodyFontSize: CGFloat = 18
    private static let naturalLineHeightRatio: CGFloat = 1.2
    private static let bodyLineSpacing = bodyFontSize * (Theme.LineHeight.reading - naturalLineHeightRatio)

    // MARK: - Formatting

    private func formattedDateTime(for thought: ContentItem) -> String {
        thought.createdAt.formatted(
            .dateTime.month(.wide).day().year().hour().minute(),
        )
    }

    // MARK: - State

    private func markAsRead() {
        guard !appState.hasBeenSeen(id) else { return }
        appState.markSeen(id)
    }

}

// MARK: - Previews

#Preview("Thought Detail") {
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
                from: DateComponents(year: 2_026, month: 3, day: 1, hour: 23, minute: 42),
            ) ?? .now,
            updatedAt: Calendar.current.date(
                from: DateComponents(year: 2_026, month: 3, day: 1, hour: 23, minute: 42),
            ) ?? .now,
        ),
    ])

    NavigationStack {
        ThoughtDetailView(id: "thought-1", client: ExhibitAClient(baseURL: URL(string: "https://localhost")!))
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
                from: DateComponents(year: 2_026, month: 2, day: 1, hour: 22, minute: 15),
            ) ?? .now,
            updatedAt: Calendar.current.date(
                from: DateComponents(year: 2_026, month: 2, day: 1, hour: 22, minute: 15),
            ) ?? .now,
        ),
    ])

    NavigationStack {
        ThoughtDetailView(id: "thought-1", client: ExhibitAClient(baseURL: URL(string: "https://localhost")!))
    }
    .environment(state)
    .environment(Router())
    .preferredColorScheme(.dark)
}

#Preview("Long Content") {
    let state = AppState()
    let _ = state.updateCachedContent([
        ContentItem(
            id: "thought-1",
            type: .thought,
            title: nil,
            subtitle: nil,
            body: """
            Morning. This is your daily reminder that you're under contractual obligation \
            to have a good day.

            Per Article 7, Section 3 of our agreement, good days are defined as: days where \
            you smile at least once, eat something that makes you happy, and remember that \
            someone out there is thinking about you.

            Failure to comply will result in additional love letters, unsolicited compliments, \
            and a formal petition for more time together.

            Consider yourself served.
            """,
            articleNumber: nil,
            classification: nil,
            sectionOrder: 46,
            requiresSignature: false,
            createdAt: Calendar.current.date(
                from: DateComponents(year: 2_026, month: 2, day: 27, hour: 8, minute: 15),
            ) ?? .now,
            updatedAt: Calendar.current.date(
                from: DateComponents(year: 2_026, month: 2, day: 27, hour: 8, minute: 15),
            ) ?? .now,
        ),
    ])

    NavigationStack {
        ThoughtDetailView(id: "thought-1", client: ExhibitAClient(baseURL: URL(string: "https://localhost")!))
    }
    .environment(state)
    .environment(Router())
}

#Preview("Markdown Literal") {
    let state = AppState()
    let _ = state.updateCachedContent([
        ContentItem(
            id: "thought-1",
            type: .thought,
            title: nil,
            subtitle: nil,
            body: "Note: **this is not bold** and _this is not italic_. Just plain text.",
            articleNumber: nil,
            classification: nil,
            sectionOrder: 5,
            requiresSignature: false,
            createdAt: Calendar.current.date(
                from: DateComponents(year: 2_026, month: 1, day: 10, hour: 15, minute: 0),
            ) ?? .now,
            updatedAt: Calendar.current.date(
                from: DateComponents(year: 2_026, month: 1, day: 10, hour: 15, minute: 0),
            ) ?? .now,
        ),
    ])

    NavigationStack {
        ThoughtDetailView(id: "thought-1", client: ExhibitAClient(baseURL: URL(string: "https://localhost")!))
    }
    .environment(state)
    .environment(Router())
}
