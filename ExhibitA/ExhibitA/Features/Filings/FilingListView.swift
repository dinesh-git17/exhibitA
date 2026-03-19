import SwiftUI

struct FilingListView: View {
    let client: ExhibitAClient

    @Environment(AppState.self) private var appState
    @Environment(Router.self) private var router

    private var filings: [Filing] {
        appState.cachedFilings.sorted { $0.createdAt > $1.createdAt }
    }

    var body: some View {
        ScrollView {
            LazyVStack(spacing: 0) {
                headerSection
                    .padding(.bottom, Theme.Spacing.lg)

                separator

                if filings.isEmpty {
                    emptyState
                } else {
                    ForEach(filings) { filing in
                        filingRow(filing)
                        separator
                    }
                }
            }
        }
        .background(Theme.Colors.Background.reading, ignoresSafeAreaEdges: .all)
        .toolbarBackground(Theme.Colors.Background.reading, for: .navigationBar)
        .toolbarBackground(.visible, for: .navigationBar)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            if Config.signerIdentity == "carolina" {
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        router.navigate(to: .filingCompose)
                    } label: {
                        Image(systemName: "plus")
                            .foregroundStyle(Theme.Colors.Accent.warm)
                    }
                    .accessibilityLabel("File new motion or objection")
                }
            }
        }
    }

    // MARK: - Header

    private var headerSection: some View {
        VStack(spacing: Theme.Spacing.sm) {
            Text("COURT PROCEEDINGS")
                .font(Theme.Typography.screenTitle)
                .foregroundStyle(Theme.Colors.Text.primary)
                .tracking(0.5)
                .multilineTextAlignment(.center)

            Text("Motions, Objections & Emergency Orders")
                .font(Theme.Typography.metadata)
                .foregroundStyle(Theme.Colors.Text.muted)
        }
        .padding(.top, Theme.Spacing.xl)
        .frame(maxWidth: .infinity)
        .accessibilityElement(children: .combine)
    }

    // MARK: - Empty State

    private var emptyState: some View {
        VStack(spacing: Theme.Spacing.md) {
            Text("No filings on record")
                .font(Theme.Typography.contractBody)
                .foregroundStyle(Theme.Colors.Text.muted)

            if Config.signerIdentity == "carolina" {
                Text("Tap + to file your first motion")
                    .font(Theme.Typography.metadata)
                    .foregroundStyle(Theme.Colors.Text.muted)
            }
        }
        .padding(.vertical, Theme.Spacing.xxl)
        .frame(maxWidth: .infinity)
    }

    // MARK: - Filing Row

    private func filingRow(_ filing: Filing) -> some View {
        Button {
            router.navigate(to: .filingDetail(id: filing.id))
        } label: {
            VStack(alignment: .leading, spacing: Theme.Spacing.sm) {
                HStack {
                    filingTypeBadge(filing.filingType)
                    Spacer(minLength: 0)
                    statusBadge(filing)
                }

                Text(filingIdentifier(filing))
                    .font(Theme.Typography.metadata)
                    .foregroundStyle(Theme.Colors.Text.muted)

                Text(filing.title)
                    .font(Theme.Typography.articleTitle)
                    .foregroundStyle(Theme.Colors.Text.primary)
                    .lineLimit(2)
                    .fixedSize(horizontal: false, vertical: true)
                    .multilineTextAlignment(.leading)

                Text(filedDateText(filing))
                    .font(Theme.Typography.metadata)
                    .foregroundStyle(Theme.Colors.Text.muted)
            }
            .padding(.horizontal, Theme.Spacing.readingHorizontal)
            .padding(.vertical, Theme.Spacing.md)
            .frame(maxWidth: .infinity, alignment: .leading)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .onAppear { appState.markSeen(filing.id) }
        .accessibilityHint("Opens filing detail")
    }

    // MARK: - Badges

    private func filingTypeBadge(_ type: FilingType) -> some View {
        Text(type.displayLabel)
            .font(Theme.Typography.label)
            .foregroundStyle(Theme.Colors.Accent.warm)
            .tracking(1.5)
    }

    private func statusBadge(_ filing: Filing) -> some View {
        Group {
            if let ruling = filing.ruling {
                Text(ruling.rawValue.uppercased())
                    .font(Theme.Typography.label)
                    .foregroundStyle(ruling.displayColor)
                    .tracking(1.0)
            } else {
                HStack(spacing: Theme.Spacing.xs) {
                    UnreadBadge(isUnread: !appState.hasBeenSeen(filing.id))
                    Text("PENDING")
                        .font(Theme.Typography.label)
                        .foregroundStyle(Theme.Colors.Text.muted)
                        .tracking(1.0)
                }
            }
        }
    }

    // MARK: - Separator

    private var separator: some View {
        Rectangle()
            .fill(Theme.Colors.Border.separator)
            .frame(height: Theme.Dividers.hairline)
            .accessibilityHidden(true)
    }

    // MARK: - Formatting

    private func filingIdentifier(_ filing: Filing) -> String {
        let index = filings.filter({ $0.filingType == filing.filingType })
            .sorted { $0.createdAt < $1.createdAt }
            .firstIndex(where: { $0.id == filing.id })
            .map { $0 + 1 } ?? 1
        let prefix = filing.filingType.identifierPrefix
        return "\(prefix)-\(String(format: "%03d", index))"
    }

    private func filedDateText(_ filing: Filing) -> String {
        "Filed: \(filing.createdAt.formatted(.dateTime.month(.wide).day().year()))"
    }
}

// MARK: - FilingType Display

extension FilingType {
    var displayLabel: String {
        switch self {
        case .motion: "MOTION"
        case .objection: "OBJECTION"
        case .emergencyOrder: "EMERGENCY ORDER"
        }
    }

    var identifierPrefix: String {
        switch self {
        case .motion: "MOTION"
        case .objection: "OBJECTION"
        case .emergencyOrder: "ORDER"
        }
    }
}

// MARK: - RulingVerdict Display

extension RulingVerdict {
    var displayColor: Color {
        switch self {
        case .granted, .sustained:
            Color(red: 0.2, green: 0.55, blue: 0.3)
        case .denied, .overruled:
            Theme.Colors.Accent.primary
        }
    }
}

// MARK: - Previews

#Preview("Filings") {
    let state = AppState()
    let _ = state.updateCachedFilings([
        Filing(
            id: "filing-1",
            filingType: .motion,
            filedBy: "carolina",
            title: "Motion to Extend FaceTime by 30 Minutes",
            body: "",
            ruling: .granted,
            rulingReason: "The court finds this request reasonable.",
            ruledBy: "dinesh",
            ruledAt: .now,
            createdAt: .now.addingTimeInterval(-86400),
            updatedAt: .now
        ),
        Filing(
            id: "filing-2",
            filingType: .objection,
            filedBy: "carolina",
            title: "Objection: Defendant Has Not Replied in 47 Minutes",
            body: "",
            ruling: nil,
            rulingReason: nil,
            ruledBy: nil,
            ruledAt: nil,
            createdAt: .now,
            updatedAt: .now
        ),
    ])

    NavigationStack {
        FilingListView(client: ExhibitAClient(baseURL: URL(string: "https://test")!))
    }
    .environment(state)
    .environment(Router())
}
