import SwiftUI

struct SettingsView: View {
    @Environment(SoundService.self) private var soundService: SoundService?

    var body: some View {
        VStack(spacing: 0) {
            headerSection

            Divider()
                .frame(height: Theme.Dividers.hairline)
                .overlay(Theme.Colors.Border.separator)
                .padding(.horizontal, Theme.Spacing.lg)

            if let service = soundService {
                soundSection(service)
            }

            Spacer(minLength: 0)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Theme.Colors.Background.primary, ignoresSafeAreaEdges: .all)
        .navigationTitle("Settings")
        .navigationBarTitleDisplayMode(.inline)
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
