import SwiftUI

struct HomeView: View {
    @Environment(AppState.self) private var appState
    @Environment(Router.self) private var router
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    var onRefresh: (() async -> Void)?
    var onForceSync: (() async -> Void)?
    @State private var showSettings = false

    var body: some View {
        VStack(spacing: 0) {
            headerSection

            headerSeparator
                .padding(.vertical, Theme.Spacing.md)

            Spacer(minLength: 0)

            cardSection

            Spacer(minLength: 0)

            footerSection
                .padding(.bottom, Theme.Spacing.md)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .overlay(alignment: .topTrailing) { settingsButton }
        .sheet(isPresented: $showSettings) {
            NavigationStack {
                SettingsView(onRefresh: onRefresh, onForceSync: onForceSync)
            }
        }
        .background(Theme.Colors.Background.primary, ignoresSafeAreaEdges: .all)
        .toolbar(.hidden, for: .navigationBar)
    }

    // MARK: - Settings

    private var settingsButton: some View {
        Button { showSettings = true } label: {
            Image(systemName: "gearshape")
                .font(.system(size: Theme.Sizing.settingsButtonIcon, weight: .regular))
                .foregroundStyle(Theme.Colors.Text.muted)
                .frame(
                    width: Theme.Sizing.settingsButton,
                    height: Theme.Sizing.settingsButton
                )
                .background(
                    Circle()
                        .fill(Theme.Colors.Background.secondary)
                )
                .overlay(
                    Circle()
                        .strokeBorder(
                            Theme.Colors.Border.separator,
                            lineWidth: Theme.Dividers.hairline
                        )
                )
                .contentShape(Circle())
        }
        .buttonStyle(SettingsPressStyle(reduceMotion: reduceMotion))
        .padding(.top, Theme.Spacing.xxl)
        .padding(.trailing, Theme.Spacing.lg)
        .accessibilityLabel("Settings")
    }

    // MARK: - Header

    private var sealView: some View {
        MonogramView(fontSize: Theme.Sizing.sealMonogramFont)
            .frame(
                width: Theme.Sizing.sealDiameter,
                height: Theme.Sizing.sealDiameter
            )
            .background(
                Circle()
                    .strokeBorder(
                        Theme.Colors.Accent.goldLeaf,
                        lineWidth: Theme.Sizing.sealBorderWidth
                    )
            )
            .background(
                Circle()
                    .strokeBorder(
                        Theme.Colors.Accent.goldLeaf.opacity(0.35),
                        lineWidth: 1
                    )
                    .padding(-Theme.Sizing.sealOuterRingInset)
            )
            .shadow(
                color: Theme.Shadows.seal[0].color,
                radius: Theme.Shadows.seal[0].radius,
                x: Theme.Shadows.seal[0].x,
                y: Theme.Shadows.seal[0].y
            )
            .shadow(
                color: Theme.Shadows.seal[1].color,
                radius: Theme.Shadows.seal[1].radius,
                x: Theme.Shadows.seal[1].x,
                y: Theme.Shadows.seal[1].y
            )
            .shadow(
                color: Theme.Shadows.seal[2].color,
                radius: Theme.Shadows.seal[2].radius,
                x: Theme.Shadows.seal[2].x,
                y: Theme.Shadows.seal[2].y
            )
            .accessibilityLabel("Exhibit A seal")
    }

    private var headerSection: some View {
        VStack(spacing: Theme.Spacing.sm) {
            sealView
                .padding(.bottom, Theme.Spacing.xs)

            Text("EXHIBIT A")
                .font(Theme.Typography.appTitle)
                .foregroundStyle(Theme.Colors.Text.primary)
                .tracking(0.5)

            Text("Case No. CD-2025-0126 | Dinesh & Carolina")
                .font(Theme.Typography.metadata)
                .foregroundStyle(Theme.Colors.Text.muted)
        }
        .padding(.top, Theme.Spacing.xxl)
        .accessibilityElement(children: .combine)
    }

    // MARK: - Separators

    private var headerSeparator: some View {
        Rectangle()
            .fill(Theme.Colors.Accent.goldLeaf)
            .frame(
                width: Theme.Sizing.headerSeparatorWidth,
                height: Theme.Dividers.hairline
            )
    }

    // MARK: - Cards

    private var cardSection: some View {
        VStack(spacing: Theme.Spacing.md) {
            FilingCabinetCard(
                sectionName: "The Contract",
                label: "The Binding Agreement",
                subtitle: "Governing Terms & Conditions of This Relationship",
                symbolName: "book.closed",
                symbolColor: Theme.Colors.Accent.primary,
                unreadCount: appState.unreadCount(ofType: .contract),
                reduceMotion: reduceMotion
            ) {
                router.navigate(to: .contractBook)
            }

            FilingCabinetCard(
                sectionName: "Filed Letters",
                label: "Correspondence on Record",
                subtitle: "\(contentCount(ofType: .letter)) letters filed",
                symbolName: "envelope",
                symbolColor: Theme.Colors.Accent.soft,
                unreadCount: appState.unreadCount(ofType: .letter),
                reduceMotion: reduceMotion
            ) {
                router.navigate(to: .lettersList)
            }

            FilingCabinetCard(
                sectionName: "Sealed Thoughts",
                label: "Classified Memoranda",
                subtitle: "\(contentCount(ofType: .thought)) memoranda on file",
                symbolName: "lock.fill",
                symbolColor: Theme.Colors.Accent.primary,
                unreadCount: appState.unreadCount(ofType: .thought),
                reduceMotion: reduceMotion
            ) {
                router.navigate(to: .thoughtsList)
            }

            FilingCabinetCard(
                sectionName: "Motions & Objections",
                label: "Court Proceedings",
                subtitle: filingsSubtitle,
                symbolName: "scroll",
                symbolColor: Theme.Colors.Accent.warm,
                unreadCount: appState.pendingFilingsCount(),
                reduceMotion: reduceMotion
            ) {
                router.navigate(to: .filingsList)
            }
        }
        .padding(.horizontal, Theme.Spacing.lg)
    }

    // MARK: - Footer

    private var footerSection: some View {
        VStack(spacing: Theme.Spacing.md) {
            Rectangle()
                .fill(Theme.Colors.Accent.goldLeaf)
                .frame(
                    width: Theme.Sizing.footerSeparatorWidth,
                    height: Theme.Dividers.hairline
                )

            Text("This document is the property of Dinesh & Carolina. Unauthorized access will be prosecuted to the fullest extent of love.")
                .font(Theme.Typography.footerLegal)
                .foregroundStyle(Theme.Colors.Text.muted)
                .multilineTextAlignment(.center)
                .fixedSize(horizontal: false, vertical: true)
                .padding(.horizontal, Theme.Spacing.xl)
        }
    }

    // MARK: - State Derivation

    private func contentCount(ofType type: ContentType) -> Int {
        appState.cachedContent.filter { $0.type == type }.count
    }

    private var filingsSubtitle: String {
        let pending = appState.pendingFilingsCount()
        if pending > 0 {
            return "\(pending) pending ruling"
        }
        let total = appState.filingCount()
        return "\(total) filings on record"
    }
}

// MARK: - Filing Cabinet Card

private struct FilingCabinetCard: View {
    let sectionName: String
    let label: String
    let subtitle: String
    let symbolName: String
    let symbolColor: Color
    let unreadCount: Int
    let reduceMotion: Bool
    let action: () -> Void

    private static let cornerRadius: CGFloat = 12
    private static let iconContainerOpacity = 0.12
    private static let pillBackgroundOpacity = 0.10
    private static let chevronOpacity = 0.5
    private static let maxDisplayCount = 9

    var body: some View {
        Button(action: action) {
            ZStack(alignment: .topTrailing) {
                HStack(alignment: .center, spacing: Theme.Spacing.md) {
                    iconContainer

                    VStack(alignment: .leading, spacing: Theme.Spacing.xs) {
                        Text(sectionName.uppercased())
                            .font(Theme.Typography.label)
                            .foregroundStyle(Theme.Colors.Text.secondary)
                            .tracking(1.5)

                        Text(label)
                            .font(Theme.Typography.sectionMarker)
                            .foregroundStyle(Theme.Colors.Text.primary)

                        Text(subtitle)
                            .font(Theme.Typography.metadata)
                            .foregroundStyle(Theme.Colors.Text.muted)
                    }

                    Spacer(minLength: 0)

                    chevron
                }
                .padding(Theme.Spacing.md)

                if unreadCount > 0 {
                    pillBadge
                        .padding(.top, Theme.Spacing.sm)
                        .padding(.trailing, Theme.Spacing.sm)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Theme.Colors.Background.secondary)
            .clipShape(.rect(cornerRadius: Self.cornerRadius, style: .continuous))
            .shadow(
                color: Theme.Shadows.card[0].color,
                radius: Theme.Shadows.card[0].radius,
                x: Theme.Shadows.card[0].x,
                y: Theme.Shadows.card[0].y
            )
            .shadow(
                color: Theme.Shadows.card[1].color,
                radius: Theme.Shadows.card[1].radius,
                x: Theme.Shadows.card[1].x,
                y: Theme.Shadows.card[1].y
            )
            .shadow(
                color: Theme.Shadows.card[2].color,
                radius: Theme.Shadows.card[2].radius,
                x: Theme.Shadows.card[2].x,
                y: Theme.Shadows.card[2].y
            )
            .overlay(
                RoundedRectangle(cornerRadius: Self.cornerRadius, style: .continuous)
                    .strokeBorder(
                        Theme.Colors.Accent.primary.opacity(0.07),
                        lineWidth: 1
                    )
            )
        }
        .buttonStyle(CardPressStyle(reduceMotion: reduceMotion))
        .accessibilityLabel(accessibilityText)
        .accessibilityHint(subtitle)
    }

    // MARK: - Subviews

    private var iconContainer: some View {
        Image(systemName: symbolName)
            .symbolRenderingMode(.hierarchical)
            .font(.system(size: Theme.Sizing.cardIconSymbol, weight: .medium))
            .foregroundStyle(symbolColor)
            .frame(
                width: Theme.Sizing.cardIconContainer,
                height: Theme.Sizing.cardIconContainer
            )
            .background(
                RoundedRectangle(
                    cornerRadius: Theme.Sizing.cardIconCornerRadius,
                    style: .continuous
                )
                .fill(symbolColor.opacity(Self.iconContainerOpacity))
            )
            .accessibilityHidden(true)
    }

    private var pillBadge: some View {
        Text(badgeLabel)
            .font(Theme.Typography.pillBadge)
            .foregroundStyle(symbolColor)
            .padding(.horizontal, Theme.Spacing.sm)
            .padding(.vertical, Theme.Spacing.xs)
            .background(
                Capsule()
                    .fill(symbolColor.opacity(Self.pillBackgroundOpacity))
            )
    }

    private var chevron: some View {
        Image(systemName: "chevron.right")
            .font(.system(size: Theme.Sizing.cardChevron, weight: .medium))
            .foregroundStyle(Theme.Colors.Text.secondary.opacity(Self.chevronOpacity))
            .accessibilityHidden(true)
    }

    // MARK: - Derived Values

    private var badgeLabel: String {
        unreadCount > Self.maxDisplayCount
            ? "\(Self.maxDisplayCount)+ NEW"
            : "\(unreadCount) NEW"
    }

    private var accessibilityText: String {
        if unreadCount > 0 {
            let countText = unreadCount > Self.maxDisplayCount
                ? "more than \(Self.maxDisplayCount)"
                : "\(unreadCount)"
            return "\(sectionName), \(label), \(countText) new"
        }
        return "\(sectionName), \(label)"
    }
}

// MARK: - Button Styles

private struct CardPressStyle: ButtonStyle {
    let reduceMotion: Bool

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .scaleEffect(configuration.isPressed && !reduceMotion ? 0.97 : 1.0)
            .opacity(configuration.isPressed ? 0.85 : 1.0)
            .animation(
                .spring(duration: 0.35, bounce: 0.25),
                value: configuration.isPressed
            )
    }
}

private struct SettingsPressStyle: ButtonStyle {
    let reduceMotion: Bool

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .scaleEffect(configuration.isPressed && !reduceMotion ? 0.92 : 1.0)
            .opacity(configuration.isPressed ? 0.7 : 1.0)
            .animation(
                .spring(duration: 0.3, bounce: 0.2),
                value: configuration.isPressed
            )
    }
}

// MARK: - Previews

#Preview("Home") {
    NavigationStack {
        HomeView()
    }
    .environment(AppState())
    .environment(Router())
}

#Preview("Dark Mode") {
    NavigationStack {
        HomeView()
    }
    .environment(AppState())
    .environment(Router())
    .preferredColorScheme(.dark)
}
