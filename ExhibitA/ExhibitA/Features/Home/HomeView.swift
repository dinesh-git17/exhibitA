import SwiftUI

struct HomeView: View {
    @Environment(AppState.self) private var appState
    @Environment(Router.self) private var router
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    var onRefresh: (() async -> Void)?
    @State private var showSettings = false

    var body: some View {
        GeometryReader { proxy in
            ScrollView {
                VStack(spacing: 0) {
                    headerSection
                        .padding(.bottom, Theme.Spacing.xl)

                    cardSection

                    Spacer(minLength: 0)

                    footerSection
                        .padding(.top, Theme.Spacing.xl)
                        .padding(.bottom, Theme.Spacing.lg)
                }
                .frame(minHeight: proxy.size.height)
            }
            .scrollBounceBehavior(.basedOnSize)
        }
        .overlay(alignment: .topTrailing) { settingsButton }
        .sheet(isPresented: $showSettings) {
            NavigationStack {
                SettingsView(onRefresh: onRefresh)
            }
        }
        .background(Theme.Colors.Background.primary, ignoresSafeAreaEdges: .all)
        .toolbar(.hidden, for: .navigationBar)
    }

    // MARK: - Settings

    private var settingsButton: some View {
        Button { showSettings = true } label: {
            Image(systemName: "gearshape")
                .font(.system(size: 20, weight: .regular))
                .foregroundStyle(Theme.Colors.Text.muted)
                .padding(Theme.Spacing.sm)
                .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .padding(.top, Theme.Spacing.xxl)
        .padding(.trailing, Theme.Spacing.lg)
        .accessibilityLabel("Settings")
    }

    // MARK: - Header

    private var headerSection: some View {
        VStack(spacing: Theme.Spacing.sm) {
            Text("EXHIBIT A")
                .font(Theme.Typography.appTitle)
                .foregroundStyle(Theme.Colors.Text.primary)
                .tracking(0.5)

            Text("Case No. CD-2025-0126 | Dinesh & Carolina")
                .font(Theme.Typography.metadata)
                .foregroundStyle(Theme.Colors.Text.muted)

            MonogramView()
                .padding(.top, Theme.Spacing.xs)
        }
        .padding(.top, Theme.Spacing.xxl)
        .accessibilityElement(children: .combine)
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
                isUnread: hasUnreadContent(ofType: .contract)
            ) {
                router.navigate(to: .contractBook)
            }
            .cardParallax(reduceMotion: reduceMotion)

            FilingCabinetCard(
                sectionName: "Filed Letters",
                label: "Correspondence on Record",
                subtitle: "\(contentCount(ofType: .letter)) letters filed",
                symbolName: "envelope",
                symbolColor: Theme.Colors.Accent.soft,
                isUnread: hasUnreadContent(ofType: .letter)
            ) {
                router.navigate(to: .lettersList)
            }
            .cardParallax(reduceMotion: reduceMotion)

            FilingCabinetCard(
                sectionName: "Sealed Thoughts",
                label: "Classified Memoranda",
                subtitle: "\(contentCount(ofType: .thought)) memoranda on file",
                symbolName: "lock.fill",
                symbolColor: Theme.Colors.Accent.primary,
                isUnread: hasUnreadContent(ofType: .thought)
            ) {
                router.navigate(to: .thoughtsList)
            }
            .cardParallax(reduceMotion: reduceMotion)

            FilingCabinetCard(
                sectionName: "Motions & Objections",
                label: "Court Proceedings",
                subtitle: filingsSubtitle,
                symbolName: "scroll",
                symbolColor: Theme.Colors.Accent.warm,
                isUnread: appState.hasUnruledFilings()
            ) {
                router.navigate(to: .filingsList)
            }
            .cardParallax(reduceMotion: reduceMotion)
        }
        .padding(.horizontal, Theme.Spacing.lg)
    }

    // MARK: - Footer

    private var footerSection: some View {
        Text("This document is the property of Dinesh & Carolina. Unauthorized access will be prosecuted to the fullest extent of love.")
            .font(Theme.Typography.footerLegal)
            .foregroundStyle(Theme.Colors.Text.muted)
            .multilineTextAlignment(.center)
            .fixedSize(horizontal: false, vertical: true)
            .padding(.horizontal, Theme.Spacing.xl)
    }

    // MARK: - State Derivation

    private func contentCount(ofType type: ContentType) -> Int {
        appState.cachedContent.filter { $0.type == type }.count
    }

    private func hasUnreadContent(ofType type: ContentType) -> Bool {
        appState.cachedContent
            .filter { $0.type == type }
            .contains { !appState.hasBeenSeen($0.id) }
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

// MARK: - Card Parallax

private extension View {
    func cardParallax(reduceMotion: Bool) -> some View {
        scrollTransition(.animated(.easeInOut(duration: 0.3))) { content, phase in
            content
                .offset(y: reduceMotion ? 0 : phase.value * 6)
                .scaleEffect(reduceMotion ? 1 : 1 - abs(phase.value) * 0.02)
        }
    }
}

// MARK: - Filing Cabinet Card

private struct FilingCabinetCard: View {
    let sectionName: String
    let label: String
    let subtitle: String
    let symbolName: String
    let symbolColor: Color
    let isUnread: Bool
    let action: () -> Void

    private static let cornerRadius: CGFloat = 12
    private static let iconSize: CGFloat = 24

    var body: some View {
        Button(action: action) {
            HStack(alignment: .top, spacing: Theme.Spacing.md) {
                Image(systemName: symbolName)
                    .symbolRenderingMode(.hierarchical)
                    .font(.system(size: Self.iconSize, weight: .medium))
                    .foregroundStyle(symbolColor)
                    .frame(width: 32)
                    .accessibilityHidden(true)

                VStack(alignment: .leading, spacing: Theme.Spacing.xs) {
                    Text(sectionName.uppercased())
                        .font(Theme.Typography.label)
                        .foregroundStyle(Theme.Colors.Text.secondary)
                        .tracking(1.5)

                    Text(label)
                        .font(Theme.Typography.sectionMarker)
                        .foregroundStyle(Theme.Colors.Text.primary)
                        .fixedSize(horizontal: false, vertical: true)

                    Text(subtitle)
                        .font(Theme.Typography.metadata)
                        .foregroundStyle(Theme.Colors.Text.muted)
                        .fixedSize(horizontal: false, vertical: true)
                }

                Spacer(minLength: 0)

                UnreadBadge(isUnread: isUnread)
            }
            .padding(Theme.Spacing.md)
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
        .buttonStyle(CardPressStyle())
        .accessibilityLabel(accessibilityText)
        .accessibilityHint(subtitle)
    }

    private var accessibilityText: String {
        isUnread
            ? "\(sectionName), \(label), unread content"
            : "\(sectionName), \(label)"
    }
}

// MARK: - Card Press Style

private struct CardPressStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .opacity(configuration.isPressed ? 0.85 : 1.0)
            .animation(.easeInOut(duration: 0.15), value: configuration.isPressed)
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
