import SwiftUI

struct LetterDetailView: View {
    let id: String
    let client: ExhibitAClient
    @Environment(AppState.self) private var appState

    private var letter: ContentItem? {
        appState.cachedContent.first { $0.id == id }
    }

    var body: some View {
        ZStack {
            Theme.Colors.Background.reading
                .ignoresSafeArea()

            if let letter {
                readerContent(letter)
            } else if appState.failedEntityIDs.contains(id) {
                entityErrorView
            } else {
                letterSkeleton
            }
        }
        .paperNoise()
        .toolbarBackground(Theme.Colors.Background.reading, for: .navigationBar)
        .toolbarBackground(.visible, for: .navigationBar)
        .navigationBarTitleDisplayMode(.inline)
        .onAppear { markAsRead() }
        .task { await startSkeletonTimeout() }
    }

    // MARK: - Reader Content

    private func readerContent(_ letter: ContentItem) -> some View {
        ScrollViewReader { proxy in
            ScrollView {
                VStack(alignment: .leading, spacing: 0) {
                    headerSection(letter)

                    separator
                        .padding(.top, Theme.Spacing.md)

                    bodySection(letter)
                        .padding(.top, Theme.Spacing.lg)

                    footerSection(letter)
                        .padding(.top, Theme.Spacing.xxl)

                    responseSection(letter)
                        .padding(.top, Theme.Spacing.lg)
                        .padding(.bottom, Theme.Spacing.xl)
                        .id("response")
                }
                .padding(.horizontal, Theme.Spacing.readingHorizontal)
                .padding(.top, Theme.Spacing.xl)
            }
            .scrollDismissesKeyboard(.interactively)
            .onReceive(NotificationCenter.default.publisher(for: UIResponder.keyboardWillShowNotification)) { _ in
                withAnimation(.easeOut(duration: 0.3)) {
                    proxy.scrollTo("response", anchor: .bottom)
                }
            }
        }
    }

    // MARK: - Header

    private func headerSection(_ letter: ContentItem) -> some View {
        VStack(alignment: .leading, spacing: Theme.Spacing.sm) {
            Text(exhibitIdentifier(for: letter))
                .font(Theme.Typography.label)
                .foregroundStyle(Theme.Colors.Text.secondary)
                .tracking(1.5)

            if let title = letter.title {
                Text(title)
                    .font(Theme.Typography.articleTitle)
                    .foregroundStyle(Theme.Colors.Text.primary)
                    .fixedSize(horizontal: false, vertical: true)
            }

            Text(filedDateText(for: letter))
                .font(Theme.Typography.metadata)
                .foregroundStyle(Theme.Colors.Text.muted)

            if let classification = letter.classification {
                ClassificationLabel(classification)
            }
        }
        .accessibilityElement(children: .combine)
    }

    // MARK: - Body

    private func bodySection(_ letter: ContentItem) -> some View {
        let paragraphs = letter.body
            .components(separatedBy: "\n\n")
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }

        return VStack(alignment: .leading, spacing: Theme.Spacing.paragraphSpacing) {
            ForEach(Array(paragraphs.enumerated()), id: \.offset) { _, paragraph in
                Text(styledMarkdown(paragraph))
                    .lineSpacing(Self.bodyLineSpacing)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
    }

    // MARK: - Footer

    private func footerSection(_ letter: ContentItem) -> some View {
        Text(footerText(for: letter))
            .font(Theme.Typography.footerLegal)
            .foregroundStyle(Theme.Colors.Text.muted)
            .frame(maxWidth: .infinity, alignment: .leading)
    }

    // MARK: - Separator

    private var separator: some View {
        Rectangle()
            .fill(Theme.Colors.Border.separator)
            .frame(height: Theme.Dividers.hairline)
            .accessibilityHidden(true)
    }

    // MARK: - Response Section

    @ViewBuilder
    private func responseSection(_ letter: ContentItem) -> some View {
        let responses = appState.commentsForContent(letter.id)
        let commentsLoaded = appState.areCommentsLoaded(for: letter.id)
        let hasMyComment = appState.comment(
            forContentId: letter.id,
            signer: Config.signerIdentity
        ) != nil

        if !commentsLoaded {
            VStack(alignment: .leading, spacing: Theme.Spacing.md) {
                goldSeparator
                SkeletonBlock(height: 14)
                SkeletonBlock(width: 180, height: 14)
            }
        } else if !responses.isEmpty || !hasMyComment {
            VStack(alignment: .leading, spacing: Theme.Spacing.md) {
                goldSeparator

                ForEach(responses) { comment in
                    ResponseOnRecordView(comment: comment)
                }

                if !hasMyComment {
                    CommentComposeView(contentId: letter.id, client: client)
                }
            }
        }
    }

    private var goldSeparator: some View {
        Rectangle()
            .fill(Theme.Colors.Accent.gold.opacity(0.3))
            .frame(height: Theme.Dividers.hairline)
            .accessibilityHidden(true)
    }

    // MARK: - Markdown Rendering

    private static let bodyFontSize: CGFloat = 18
    /// Approximate default line-height ratio for digital serif typefaces.
    private static let naturalLineHeightRatio: CGFloat = 1.2
    private static let bodyLineSpacing = bodyFontSize * (Theme.LineHeight.reading - naturalLineHeightRatio)

    private func styledMarkdown(_ source: String) -> AttributedString {
        var result: AttributedString
        do {
            result = try AttributedString(
                markdown: source,
                options: .init(interpretedSyntax: .inlineOnlyPreservingWhitespace)
            )
        } catch {
            result = AttributedString(source)
        }
        result.font = Theme.Typography.contractBody
        result.foregroundColor = Theme.Colors.Text.reading
        return result
    }

    // MARK: - Formatting

    private func exhibitIdentifier(for letter: ContentItem) -> String {
        "EXHIBIT L-\(String(format: "%03d", letter.sectionOrder))"
    }

    private func filedDateText(for letter: ContentItem) -> String {
        "Filed: \(letter.createdAt.formatted(.dateTime.month(.wide).day().year()))"
    }

    private func footerText(for letter: ContentItem) -> String {
        "Filed with love, \(letter.createdAt.formatted(.dateTime.month(.wide).day().year()))"
    }

    // MARK: - Skeleton

    private var letterSkeleton: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                SkeletonBlock(width: 100, height: 12)
                SkeletonBlock(height: 20)
                    .padding(.top, Theme.Spacing.sm)
                SkeletonBlock(width: 180, height: 20)
                    .padding(.top, Theme.Spacing.xs)
                SkeletonBlock(width: 140, height: 12)
                    .padding(.top, Theme.Spacing.sm)

                Rectangle()
                    .fill(Theme.Colors.Border.separator)
                    .frame(height: Theme.Dividers.hairline)
                    .padding(.top, Theme.Spacing.md)

                VStack(alignment: .leading, spacing: Theme.Spacing.sm) {
                    SkeletonBlock(height: 14)
                    SkeletonBlock(height: 14)
                    SkeletonBlock(width: 260, height: 14)
                    SkeletonBlock(height: 14)
                        .padding(.top, Theme.Spacing.sm)
                    SkeletonBlock(height: 14)
                    SkeletonBlock(width: 200, height: 14)
                }
                .padding(.top, Theme.Spacing.lg)

                SkeletonBlock(width: 180, height: 12)
                    .padding(.top, Theme.Spacing.xxl)
            }
            .padding(.horizontal, Theme.Spacing.readingHorizontal)
            .padding(.top, Theme.Spacing.xl)
        }
    }

    // MARK: - Error State

    private var entityErrorView: some View {
        VStack(spacing: Theme.Spacing.md) {
            Image(systemName: "exclamationmark.triangle")
                .font(.system(size: 32))
                .foregroundStyle(Theme.Colors.Text.muted)

            Text("This letter could not be retrieved.")
                .font(Theme.Typography.metadata)
                .foregroundStyle(Theme.Colors.Text.secondary)
                .multilineTextAlignment(.center)

            Button {
                appState.clearEntityFetchFailure(id)
            } label: {
                Text("Try Again")
                    .font(Theme.Typography.label)
                    .foregroundStyle(Theme.Colors.Accent.warm)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    // MARK: - State

    private static let skeletonTimeoutSeconds = 10

    private func startSkeletonTimeout() async {
        try? await Task.sleep(for: .seconds(Self.skeletonTimeoutSeconds))
        if letter == nil && !appState.failedEntityIDs.contains(id) {
            appState.markEntityFetchFailed(id)
        }
    }

    private func markAsRead() {
        guard !appState.hasBeenSeen(id) else { return }
        appState.markSeen(id)
    }

}

// MARK: - Previews

#Preview("Letter Detail") {
    let state = AppState()
    let _ = state.updateCachedContent([
        ContentItem(
            id: "letter-1",
            type: .letter,
            title: "Closing Arguments for Why You're Perfect",
            subtitle: "On the Matter of Perfection",
            body: """
            Let the record show that on this day, the court finds **overwhelming evidence** \
            of perfection in the defendant.

            The prosecution presents the following exhibits: your laugh when you think \
            nobody is listening, the way you *always* remember the small things, and your \
            inexplicable ability to make even Monday mornings feel bearable.

            Furthermore, the court notes that no reasonable person could deny the warmth \
            you bring to every room you enter. This is not hyperbole. This is **documented fact**.

            In closing, the court rules unanimously and without reservation: you are, \
            and have always been, perfect.
            """,
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
    ])

    NavigationStack {
        LetterDetailView(id: "letter-1", client: ExhibitAClient(baseURL: URL(string: "https://localhost")!))
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
            title: "Motion to Appreciate All the Small Things",
            subtitle: "On the Matter of Gratitude",
            body: """
            I hereby submit this motion to formally recognize and appreciate \
            the *small things* you do every day.

            **Exhibit A:** The way you leave little notes in unexpected places. \
            **Exhibit B:** Your patience when I forget things. \
            **Exhibit C:** The coffee you make without being asked.

            The defense rests, overwhelmed by evidence of thoughtfulness.
            """,
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
    ])

    NavigationStack {
        LetterDetailView(id: "letter-1", client: ExhibitAClient(baseURL: URL(string: "https://localhost")!))
    }
    .environment(state)
    .environment(Router())
    .preferredColorScheme(.dark)
}

#Preview("Long Content") {
    let state = AppState()
    let _ = state.updateCachedContent([
        ContentItem(
            id: "letter-1",
            type: .letter,
            title: "Emergency Motion Regarding Missing Goodnight Texts",
            subtitle: "On the Matter of Communication",
            body: """
            The plaintiff brings this emergency motion before the court to address a \
            matter of **urgent importance**: the recent and alarming decline in goodnight \
            text frequency.

            *Whereas* the established precedent (hereinafter "The Early Days") set a \
            standard of nightly communication that included, but was not limited to, \
            sweet messages, voice notes, and the occasional heart emoji.

            *Whereas* the defendant has, in recent weeks, allowed the frequency of said \
            communications to diminish to levels the court finds unacceptable.

            The plaintiff respectfully requests the following relief:

            **Count I:** An immediate restoration of nightly goodnight texts, to be \
            delivered no later than 11:59 PM local time.

            **Count II:** A formal acknowledgment that goodnight texts are not optional \
            but rather a *fundamental right* within this relationship.

            **Count III:** Retroactive goodnight texts for all missed evenings, to be \
            delivered in a single, heartfelt message.

            The plaintiff notes that failure to comply with this motion may result in \
            **additional filings**, including but not limited to a Motion for Increased \
            Heart Emojis and a Petition for More Spontaneous Compliments.

            The court is further advised that the plaintiff reserves the right to amend \
            this motion at any time, particularly if the defendant's response includes \
            an especially good goodnight text that renders further legal action unnecessary.

            Respectfully submitted with love and mild exasperation.
            """,
            articleNumber: nil,
            classification: "Emergency Filing",
            sectionOrder: 1,
            requiresSignature: false,
            createdAt: Calendar.current.date(
                from: DateComponents(year: 2026, month: 2, day: 1)
            ) ?? .now,
            updatedAt: Calendar.current.date(
                from: DateComponents(year: 2026, month: 2, day: 1)
            ) ?? .now
        ),
    ])

    NavigationStack {
        LetterDetailView(id: "letter-1", client: ExhibitAClient(baseURL: URL(string: "https://localhost")!))
    }
    .environment(state)
    .environment(Router())
}
