import SwiftUI
import UserNotifications

struct SettingsView: View {
    @Environment(SoundService.self) private var soundService: SoundService?
    var onRefresh: (() async -> Void)?

    @State private var notificationsEnabled = true
    @State private var isRefreshing = false

    var body: some View {
        VStack(spacing: 0) {
            headerSection

            Divider()
                .frame(height: Theme.Dividers.hairline)
                .overlay(Theme.Colors.Border.separator)
                .padding(.horizontal, Theme.Spacing.lg)

            if !notificationsEnabled {
                notificationSection

                sectionDivider
            }

            if let service = soundService {
                soundSection(service)

                sectionDivider
            }

            refreshSection

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
            openNotificationSettings()
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

                    Text("Get notified when new content is filed")
                        .font(Theme.Typography.metadata)
                        .foregroundStyle(Theme.Colors.Text.muted)
                }

                Spacer(minLength: 0)

                Image(systemName: "arrow.up.right")
                    .font(.system(size: 14, weight: .medium))
                    .foregroundStyle(Theme.Colors.Text.muted)
            }
            .padding(.horizontal, Theme.Spacing.lg)
            .padding(.vertical, Theme.Spacing.md)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .accessibilityLabel("Enable Notifications")
        .accessibilityHint("Opens system notification settings")
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

    // MARK: - Helpers

    private func checkNotificationStatus() async {
        let settings = await UNUserNotificationCenter.current().notificationSettings()
        notificationsEnabled = settings.authorizationStatus == .authorized
    }

    private func openNotificationSettings() {
        guard let url = URL(string: UIApplication.openSettingsURLString) else { return }
        UIApplication.shared.open(url)
    }
}

// MARK: - Previews

#Preview("Settings") {
    NavigationStack {
        SettingsView()
    }
    .environment(SoundService())
}

#Preview("Dark Mode") {
    NavigationStack {
        SettingsView()
    }
    .environment(SoundService())
    .preferredColorScheme(.dark)
}

#Preview("No Service") {
    NavigationStack {
        SettingsView()
    }
}
