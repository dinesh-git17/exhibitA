import SwiftUI
import UIKit

struct FilingDetailView: View {
    let id: String
    let client: ExhibitAClient

    @Environment(AppState.self) private var appState
    @Environment(SoundService.self) private var soundService: SoundService?

    @State private var selectedVerdict: RulingVerdict?
    @State private var rulingReason = ""

    private static let bodyFontSize: CGFloat = 18
    private static let bodyLineSpacing = bodyFontSize * (Theme.LineHeight.reading - 1.2)

    private var filing: Filing? {
        appState.cachedFilings.first { $0.id == id }
    }

    private var canRule: Bool {
        guard let filing else { return false }
        return filing.ruling == nil && Config.signerIdentity != filing.filedBy
    }

    var body: some View {
        ZStack {
            Theme.Colors.Background.reading
                .ignoresSafeArea()

            if let filing {
                readerContent(filing)
            } else if appState.failedEntityIDs.contains(id) {
                entityErrorView
            } else {
                filingSkeleton
            }
        }
        .paperNoise()
        .toolbarBackground(Theme.Colors.Background.reading, for: .navigationBar)
        .toolbarBackground(.visible, for: .navigationBar)
        .navigationBarTitleDisplayMode(.inline)
        .onAppear {
            if let filing { appState.markSeen(filing.id) }
        }
        .task { await startSkeletonTimeout() }
    }

    private func readerContent(_ filing: Filing) -> some View {
        ScrollViewReader { proxy in
            ScrollView {
                VStack(alignment: .leading, spacing: 0) {
                    headerSection(filing)
                        .padding(.bottom, Theme.Spacing.lg)

                    bodySection(filing)
                        .padding(.bottom, Theme.Spacing.xl)

                    if let ruling = filing.ruling {
                        rulingSection(filing, verdict: ruling)
                    } else if canRule {
                        rulingComposeSection(filing)
                            .id("ruling")
                    }
                }
                .padding(.horizontal, Theme.Spacing.readingHorizontal)
                .padding(.vertical, Theme.Spacing.xl)
            }
            .scrollDismissesKeyboard(.interactively)
            .onReceive(NotificationCenter.default.publisher(for: UIResponder.keyboardWillShowNotification)) { _ in
                withAnimation(.easeOut(duration: 0.3)) {
                    proxy.scrollTo("ruling", anchor: .bottom)
                }
            }
        }
    }

    // MARK: - Header

    private func headerSection(_ filing: Filing) -> some View {
        VStack(alignment: .leading, spacing: Theme.Spacing.sm) {
            Text(filing.filingType.displayLabel)
                .font(Theme.Typography.label)
                .foregroundStyle(Theme.Colors.Accent.warm)
                .tracking(1.5)

            Text(filing.title)
                .font(Theme.Typography.articleTitle)
                .foregroundStyle(Theme.Colors.Text.primary)
                .fixedSize(horizontal: false, vertical: true)

            Text(filedByText(filing))
                .font(Theme.Typography.metadata)
                .foregroundStyle(Theme.Colors.Text.muted)
        }
    }

    // MARK: - Body

    private func bodySection(_ filing: Filing) -> some View {
        let paragraphs = filing.body.split(separator: "\n\n", omittingEmptySubsequences: true)
        return VStack(alignment: .leading, spacing: Theme.Spacing.readingHorizontal) {
            ForEach(Array(paragraphs.enumerated()), id: \.offset) { _, paragraph in
                Text(String(paragraph))
                    .font(Theme.Typography.contractBody)
                    .foregroundStyle(Theme.Colors.Text.reading)
                    .lineSpacing(Self.bodyLineSpacing)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
    }

    // MARK: - Ruling Display

    private func rulingSection(_ filing: Filing, verdict: RulingVerdict) -> some View {
        VStack(spacing: Theme.Spacing.lg) {
            goldSeparator

            RulingStampView(verdict: verdict)
                .frame(maxWidth: .infinity)
                .padding(.vertical, Theme.Spacing.md)

            VStack(alignment: .leading, spacing: Theme.Spacing.sm) {
                Text("THE COURT'S REASONING")
                    .font(Theme.Typography.label)
                    .foregroundStyle(Theme.Colors.Text.secondary)
                    .tracking(1.5)

                if let reason = filing.rulingReason {
                    Text(reason)
                        .font(Theme.Typography.contractBody)
                        .foregroundStyle(Theme.Colors.Text.reading)
                        .lineSpacing(Self.bodyLineSpacing)
                        .fixedSize(horizontal: false, vertical: true)
                }

                if let ruledAt = filing.ruledAt {
                    Text("Ruled: \(ruledAt.formatted(.dateTime.month(.wide).day().year()))")
                        .font(Theme.Typography.metadata)
                        .foregroundStyle(Theme.Colors.Text.muted)
                        .padding(.top, Theme.Spacing.xs)
                }
            }
        }
    }

    // MARK: - Ruling Compose

    private func rulingComposeSection(_ filing: Filing) -> some View {
        let verdicts = availableVerdicts(for: filing.filingType)
        return VStack(alignment: .leading, spacing: Theme.Spacing.md) {
            goldSeparator

            Text("ISSUE RULING")
                .font(Theme.Typography.label)
                .foregroundStyle(Theme.Colors.Text.secondary)
                .tracking(1.5)

            HStack(spacing: Theme.Spacing.md) {
                ForEach(verdicts, id: \.self) { verdict in
                    verdictButton(verdict)
                }
            }

            VStack(alignment: .leading, spacing: 0) {
                TextField("The court's reasoning...", text: $rulingReason, axis: .vertical)
                    .font(Theme.Typography.contractBody)
                    .foregroundStyle(Theme.Colors.Text.reading)
                    .lineLimit(3...8)
                    .padding(.horizontal, Theme.Spacing.md)
                    .padding(.top, Theme.Spacing.md)
                    .padding(.bottom, Theme.Spacing.sm)

                HStack {
                    Spacer()
                    Button {
                        submitRuling()
                    } label: {
                        Text("Issue Ruling")
                            .font(Theme.Typography.label)
                            .foregroundStyle(
                                isRulingValid
                                    ? Theme.Colors.Background.reading
                                    : Theme.Colors.Text.muted
                            )
                            .padding(.horizontal, Theme.Spacing.md)
                            .padding(.vertical, Theme.Spacing.sm)
                            .background(
                                isRulingValid
                                    ? Theme.Colors.Accent.warm
                                    : Theme.Colors.Background.tertiary
                            )
                            .clipShape(.rect(cornerRadius: 8, style: .continuous))
                    }
                    .disabled(!isRulingValid)
                }
                .padding(.horizontal, Theme.Spacing.md)
                .padding(.bottom, Theme.Spacing.md)
            }
            .background(Theme.Colors.Background.secondary)
            .clipShape(.rect(cornerRadius: 12, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .strokeBorder(Theme.Colors.Border.separator, lineWidth: Theme.Dividers.hairline)
            )
        }
    }

    private func verdictButton(_ verdict: RulingVerdict) -> some View {
        Button {
            selectedVerdict = verdict
        } label: {
            Text(verdict.rawValue.uppercased())
                .font(Theme.Typography.label)
                .foregroundStyle(
                    selectedVerdict == verdict
                        ? Theme.Colors.Background.reading
                        : verdict.displayColor
                )
                .tracking(1.0)
                .padding(.horizontal, Theme.Spacing.md)
                .padding(.vertical, Theme.Spacing.sm)
                .frame(maxWidth: .infinity)
                .background(
                    selectedVerdict == verdict
                        ? verdict.displayColor
                        : Theme.Colors.Background.secondary
                )
                .clipShape(.rect(cornerRadius: 8, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: 8, style: .continuous)
                        .strokeBorder(verdict.displayColor, lineWidth: 1)
                )
        }
        .buttonStyle(.plain)
    }

    // MARK: - Helpers

    private var goldSeparator: some View {
        Rectangle()
            .fill(Theme.Colors.Accent.gold.opacity(0.3))
            .frame(height: Theme.Dividers.hairline)
            .padding(.bottom, Theme.Spacing.sm)
    }

    private var isRulingValid: Bool {
        selectedVerdict != nil
            && !rulingReason.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    private func availableVerdicts(for type: FilingType) -> [RulingVerdict] {
        switch type {
        case .objection:
            [.sustained, .overruled]
        case .motion, .emergencyOrder:
            [.granted, .denied]
        }
    }

    private func filedByText(_ filing: Filing) -> String {
        let name = filing.filedBy == Config.signerIdentity ? "You" : filing.filedBy.capitalized
        let date = filing.createdAt.formatted(.dateTime.month(.wide).day().year())
        return "Filed by \(name) \u{2014} \(date)"
    }

    // MARK: - Skeleton

    private var filingSkeleton: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                SkeletonBlock(width: 80, height: 12)
                SkeletonBlock(height: 20)
                    .padding(.top, Theme.Spacing.sm)
                SkeletonBlock(width: 160, height: 12)
                    .padding(.top, Theme.Spacing.sm)
                    .padding(.bottom, Theme.Spacing.lg)

                VStack(alignment: .leading, spacing: Theme.Spacing.sm) {
                    SkeletonBlock(height: 14)
                    SkeletonBlock(height: 14)
                    SkeletonBlock(width: 240, height: 14)
                    SkeletonBlock(height: 14)
                        .padding(.top, Theme.Spacing.sm)
                    SkeletonBlock(width: 200, height: 14)
                }
                .padding(.bottom, Theme.Spacing.xl)

                Rectangle()
                    .fill(Theme.Colors.Accent.gold.opacity(0.3))
                    .frame(height: Theme.Dividers.hairline)
            }
            .padding(.horizontal, Theme.Spacing.readingHorizontal)
            .padding(.vertical, Theme.Spacing.xl)
        }
    }

    // MARK: - Error State

    private var entityErrorView: some View {
        VStack(spacing: Theme.Spacing.md) {
            Image(systemName: "exclamationmark.triangle")
                .font(.system(size: 32))
                .foregroundStyle(Theme.Colors.Text.muted)

            Text("This filing could not be retrieved.")
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

    private static let skeletonTimeoutSeconds = 10

    private func startSkeletonTimeout() async {
        try? await Task.sleep(for: .seconds(Self.skeletonTimeoutSeconds))
        if filing == nil && !appState.failedEntityIDs.contains(id) {
            appState.markEntityFetchFailed(id)
        }
    }

    private func submitRuling() {
        guard let verdict = selectedVerdict, isRulingValid, let filing else { return }

        let filingId = id
        let reason = rulingReason.trimmingCharacters(in: .whitespacesAndNewlines)
        let ruledBy = Config.signerIdentity

        let optimistic = Filing(
            id: filing.id,
            filingType: filing.filingType,
            filedBy: filing.filedBy,
            title: filing.title,
            body: filing.body,
            ruling: verdict,
            rulingReason: reason,
            ruledBy: ruledBy,
            ruledAt: .now,
            createdAt: filing.createdAt,
            updatedAt: .now
        )
        appState.cacheFiling(optimistic)
        UIImpactFeedbackGenerator(style: .medium).impactOccurred()
        soundService?.play(.signaturePlaced)

        Task {
            do {
                let updated = try await client.createRuling(
                    filingId: filingId,
                    ruling: verdict,
                    reason: reason,
                    ruledBy: ruledBy
                )
                await MainActor.run { appState.cacheFiling(updated) }
            } catch {
                await MainActor.run { appState.cacheFiling(filing) }
            }
        }
    }
}
