import SwiftUI
import UserNotifications

struct SettingsView: View {
    @Environment(AppState.self) private var appState
    @Environment(SoundService.self) private var soundService: SoundService?
    var onRefresh: (() async -> Void)?
    var onForceSync: (() async -> Void)?

    @State private var notificationStatus: UNAuthorizationStatus = .authorized
    @State private var isRefreshing = false
    @State private var isForceSyncing = false
    @State private var didMarkAllRead = false

    var body: some View {
        VStack(spacing: 0) {
            headerSection

            Divider()
                .frame(height: Theme.Dividers.hairline)
                .overlay(Theme.Colors.Border.separator)
                .padding(.horizontal, Theme.Spacing.lg)

            if notificationStatus != .authorized {
                notificationSection

                sectionDivider
            }

            if let service = soundService {
                soundSection(service)

                sectionDivider
            }

            markAllReadSection

            sectionDivider

            refreshSection

            if onForceSync != nil {
                sectionDivider
                forceSyncSection
            }

            Spacer(minLength: 0)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Theme.Colors.Background.primary, ignoresSafeAreaEdges: .all)
        .navigationTitle("Settings")
        .navigationBarTitleDisplayMode(.inline)
        .task { await checkNotificationStatus() }
    }

    private var sectionDivider: some View {
        Divider()
            .frame(height: Theme.Dividers.hairline)
            .overlay(Theme.Colors.Border.separator)
            .padding(.horizontal, Theme.Spacing.lg)
    }

    // MARK: - Header

    private var headerSection: some View {
        Text("PREFERENCES")
            .font(Theme.Typography.label)
            .foregroundStyle(Theme.Colors.Text.secondary)
            .tracking(1.5)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.horizontal, Theme.Spacing.lg)
            .padding(.top, Theme.Spacing.lg)
            .padding(.bottom, Theme.Spacing.md)
    }

    // MARK: - Notifications

    private var notificationSection: some View {
        Button {
            Task { await handleNotificationAction() }
        } label: {
            HStack(spacing: Theme.Spacing.sm) {
                Image(systemName: "bell.slash.fill")
                    .font(.system(size: 18, weight: .medium))
                    .foregroundStyle(Theme.Colors.Accent.warm)
                    .frame(width: 24)
                    .accessibilityHidden(true)

                VStack(alignment: .leading, spacing: Theme.Spacing.xs) {
                    Text("Enable Notifications")
                        .font(Theme.Typography.sectionMarker)
                        .foregroundStyle(Theme.Colors.Text.primary)

                    Text(notificationSubtitle)
                        .font(Theme.Typography.metadata)
                        .foregroundStyle(Theme.Colors.Text.muted)
                }

                Spacer(minLength: 0)

                if notificationStatus == .denied {
                    Image(systemName: "arrow.up.right")
                        .font(.system(size: 14, weight: .medium))
                        .foregroundStyle(Theme.Colors.Text.muted)
                }
            }
            .padding(.horizontal, Theme.Spacing.lg)
            .padding(.vertical, Theme.Spacing.md)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .accessibilityLabel("Enable Notifications")
        .accessibilityHint(
            notificationStatus == .denied
                ? "Opens system notification settings"
                : "Request notification permission"
        )
    }

    private var notificationSubtitle: String {
        notificationStatus == .denied
            ? "Notifications were denied. Tap to open Settings."
            : "Get notified when new content is filed"
    }

    // MARK: - Sound Toggle

    private func soundSection(_ service: SoundService) -> some View {
        @Bindable var service = service
        return Toggle(isOn: $service.isSoundEnabled) {
            HStack(spacing: Theme.Spacing.sm) {
                Image(systemName: service.isSoundEnabled
                    ? "speaker.wave.2.fill"
                    : "speaker.slash.fill")
                    .font(.system(size: 18, weight: .medium))
                    .foregroundStyle(Theme.Colors.Accent.primary)
                    .frame(width: 24)
                    .accessibilityHidden(true)

                VStack(alignment: .leading, spacing: Theme.Spacing.xs) {
                    Text("Sound Effects")
                        .font(Theme.Typography.sectionMarker)
                        .foregroundStyle(Theme.Colors.Text.primary)

                    Text("Page turns, signatures, and notifications")
                        .font(Theme.Typography.metadata)
                        .foregroundStyle(Theme.Colors.Text.muted)
                }
            }
        }
        .tint(Theme.Colors.Accent.primary)
        .padding(.horizontal, Theme.Spacing.lg)
        .padding(.vertical, Theme.Spacing.md)
        .accessibilityLabel("Sound Effects")
        .accessibilityValue(service.isSoundEnabled ? "On" : "Off")
        .accessibilityHint("Toggle sound effects for page turns, signatures, and notifications")
    }

    // MARK: - Mark All Read

    private var markAllReadSection: some View {
        Button {
            guard !didMarkAllRead else { return }
            appState.markAllContentSeen()
            didMarkAllRead = true
        } label: {
            HStack(spacing: Theme.Spacing.sm) {
                Image(systemName: didMarkAllRead ? "checkmark.circle.fill" : "eye")
                    .font(.system(size: 18, weight: .medium))
                    .foregroundStyle(
                        didMarkAllRead
                            ? Theme.Colors.Accent.warm
                            : Theme.Colors.Accent.primary
                    )
                    .frame(width: 24)
                    .accessibilityHidden(true)

                VStack(alignment: .leading, spacing: Theme.Spacing.xs) {
                    Text("Mark All as Read")
                        .font(Theme.Typography.sectionMarker)
                        .foregroundStyle(Theme.Colors.Text.primary)

                    Text(
                        didMarkAllRead
                            ? "All content marked as read"
                            : "Dismiss all unread badges"
                    )
                    .font(Theme.Typography.metadata)
                    .foregroundStyle(Theme.Colors.Text.muted)
                }

                Spacer(minLength: 0)
            }
            .padding(.horizontal, Theme.Spacing.lg)
            .padding(.vertical, Theme.Spacing.md)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .disabled(didMarkAllRead)
        .accessibilityLabel("Mark All as Read")
        .accessibilityHint(
            didMarkAllRead
                ? "All content already marked as read"
                : "Marks all letters, thoughts, and contract articles as read"
        )
    }

    // MARK: - Refresh

    private var refreshSection: some View {
        Button {
            guard !isRefreshing else { return }
            Task {
                isRefreshing = true
                await onRefresh?()
                isRefreshing = false
            }
        } label: {
            HStack(spacing: Theme.Spacing.sm) {
                Group {
                    if isRefreshing {
                        ProgressView()
                            .controlSize(.small)
                    } else {
                        Image(systemName: "arrow.clockwise")
                            .font(.system(size: 18, weight: .medium))
                    }
                }
                .foregroundStyle(Theme.Colors.Accent.primary)
                .frame(width: 24)
                .accessibilityHidden(true)

                VStack(alignment: .leading, spacing: Theme.Spacing.xs) {
                    Text("Refresh Content")
                        .font(Theme.Typography.sectionMarker)
                        .foregroundStyle(Theme.Colors.Text.primary)

                    Text(isRefreshing ? "Syncing..." : "Check for new letters, thoughts, and updates")
                        .font(Theme.Typography.metadata)
                        .foregroundStyle(Theme.Colors.Text.muted)
                }

                Spacer(minLength: 0)
            }
            .padding(.horizontal, Theme.Spacing.lg)
            .padding(.vertical, Theme.Spacing.md)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .disabled(isRefreshing)
        .accessibilityLabel("Refresh Content")
        .accessibilityHint(isRefreshing ? "Syncing in progress" : "Fetches the latest content from the server")
    }

    // MARK: - Force Sync

    private var forceSyncSection: some View {
        Button {
            guard !isForceSyncing else { return }
            Task {
                isForceSyncing = true
                await onForceSync?()
                isForceSyncing = false
            }
        } label: {
            HStack(spacing: Theme.Spacing.sm) {
                Group {
                    if isForceSyncing {
                        ProgressView()
                            .controlSize(.small)
                    } else {
                        Image(systemName: "arrow.triangle.2.circlepath")
                            .font(.system(size: 18, weight: .medium))
                    }
                }
                .foregroundStyle(Theme.Colors.Text.muted)
                .frame(width: 24)
                .accessibilityHidden(true)

                VStack(alignment: .leading, spacing: Theme.Spacing.xs) {
                    Text("Force Full Sync")
                        .font(Theme.Typography.sectionMarker)
                        .foregroundStyle(Theme.Colors.Text.primary)

                    Text(
                        isForceSyncing
                            ? "Running full sync..."
                            : "Re-download all content and signatures"
                    )
                    .font(Theme.Typography.metadata)
                    .foregroundStyle(Theme.Colors.Text.muted)
                }

                Spacer(minLength: 0)
            }
            .padding(.horizontal, Theme.Spacing.lg)
            .padding(.vertical, Theme.Spacing.md)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .disabled(isForceSyncing)
        .accessibilityLabel("Force Full Sync")
        .accessibilityHint(
            isForceSyncing
                ? "Full sync in progress"
                : "Re-downloads everything from the server"
        )
    }

    // MARK: - Helpers

    private func checkNotificationStatus() async {
        let settings = await UNUserNotificationCenter.current().notificationSettings()
        notificationStatus = settings.authorizationStatus
    }

    private func handleNotificationAction() async {
        if notificationStatus == .notDetermined {
            let center = UNUserNotificationCenter.current()
            let granted = (try? await center.requestAuthorization(options: [.alert, .sound, .badge])) ?? false
            if granted {
                UIApplication.shared.registerForRemoteNotifications()
            }
            await checkNotificationStatus()
        } else {
            guard let url = URL(string: UIApplication.openSettingsURLString) else { return }
            await UIApplication.shared.open(url)
        }
    }
}

// MARK: - Previews

#Preview("Settings") {
    NavigationStack {
        SettingsView()
    }
    .environment(AppState())
    .environment(SoundService())
}

#Preview("Dark Mode") {
    NavigationStack {
        SettingsView()
    }
    .environment(AppState())
    .environment(SoundService())
    .preferredColorScheme(.dark)
}

#Preview("No Service") {
    NavigationStack {
        SettingsView()
    }
    .environment(AppState())
}
