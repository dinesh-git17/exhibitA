import SwiftUI
import UIKit

struct FilingComposeView: View {
    let client: ExhibitAClient

    @Environment(AppState.self) private var appState
    @Environment(Router.self) private var router

    @State private var selectedType: FilingType = .motion
    @State private var title = ""
    @State private var filingBody = ""

    private static let cornerRadius: CGFloat = 12

    var body: some View {
        ZStack {
            Theme.Colors.Background.reading
                .ignoresSafeArea()

            ScrollView {
                VStack(alignment: .leading, spacing: Theme.Spacing.lg) {
                    typePicker

                    templateSection

                    composeSection

                    submitButton
                }
                .padding(.horizontal, Theme.Spacing.readingHorizontal)
                .padding(.vertical, Theme.Spacing.lg)
            }
            .scrollDismissesKeyboard(.interactively)
        }
        .toolbarBackground(Theme.Colors.Background.reading, for: .navigationBar)
        .toolbarBackground(.visible, for: .navigationBar)
        .navigationBarTitleDisplayMode(.inline)
        .navigationTitle("File a Motion")
    }

    // MARK: - Type Picker

    private var typePicker: some View {
        VStack(alignment: .leading, spacing: Theme.Spacing.sm) {
            Text("FILING TYPE")
                .font(Theme.Typography.label)
                .foregroundStyle(Theme.Colors.Text.secondary)
                .tracking(1.5)

            Picker("Filing Type", selection: $selectedType) {
                Text("Motion").tag(FilingType.motion)
                Text("Objection").tag(FilingType.objection)
                Text("Emergency").tag(FilingType.emergencyOrder)
            }
            .pickerStyle(.segmented)
        }
    }

    // MARK: - Templates

    private var templateSection: some View {
        VStack(alignment: .leading, spacing: Theme.Spacing.sm) {
            Text("QUICK TEMPLATES")
                .font(Theme.Typography.label)
                .foregroundStyle(Theme.Colors.Text.secondary)
                .tracking(1.5)

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: Theme.Spacing.sm) {
                    ForEach(
                        Array(FilingTemplateStore.templates(for: selectedType).enumerated()),
                        id: \.offset
                    ) { _, template in
                        templateChip(template)
                    }
                }
            }
        }
    }

    private func templateChip(_ template: FilingTemplate) -> some View {
        Button {
            title = template.title
            filingBody = template.body
        } label: {
            Text(template.title)
                .font(Theme.Typography.metadata)
                .foregroundStyle(Theme.Colors.Text.reading)
                .lineLimit(2)
                .multilineTextAlignment(.leading)
                .padding(.horizontal, Theme.Spacing.md)
                .padding(.vertical, Theme.Spacing.sm)
                .frame(width: 200, alignment: .leading)
                .background(Theme.Colors.Background.secondary)
                .clipShape(.rect(cornerRadius: 8, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: 8, style: .continuous)
                        .strokeBorder(Theme.Colors.Border.separator, lineWidth: Theme.Dividers.hairline)
                )
        }
        .buttonStyle(.plain)
    }

    // MARK: - Compose Fields

    private var composeSection: some View {
        VStack(alignment: .leading, spacing: Theme.Spacing.sm) {
            Text("YOUR FILING")
                .font(Theme.Typography.label)
                .foregroundStyle(Theme.Colors.Text.secondary)
                .tracking(1.5)

            VStack(alignment: .leading, spacing: 0) {
                TextField("Title of your filing...", text: $title)
                    .font(Theme.Typography.articleTitle)
                    .foregroundStyle(Theme.Colors.Text.primary)
                    .padding(.horizontal, Theme.Spacing.md)
                    .padding(.top, Theme.Spacing.md)
                    .padding(.bottom, Theme.Spacing.sm)

                Rectangle()
                    .fill(Theme.Colors.Border.separator)
                    .frame(height: Theme.Dividers.hairline)
                    .padding(.horizontal, Theme.Spacing.md)

                TextField("State your case...", text: $filingBody, axis: .vertical)
                    .font(Theme.Typography.contractBody)
                    .foregroundStyle(Theme.Colors.Text.reading)
                    .lineLimit(4...8)
                    .padding(.horizontal, Theme.Spacing.md)
                    .padding(.top, Theme.Spacing.sm)
                    .padding(.bottom, Theme.Spacing.md)
            }
            .background(Theme.Colors.Background.secondary)
            .clipShape(.rect(cornerRadius: Self.cornerRadius, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: Self.cornerRadius, style: .continuous)
                    .strokeBorder(Theme.Colors.Border.separator, lineWidth: Theme.Dividers.hairline)
            )
        }
    }

    // MARK: - Submit

    private var submitButton: some View {
        Button {
            submit()
        } label: {
            Text(submitLabel)
                .font(Theme.Typography.label)
                .foregroundStyle(
                    isValid
                        ? Theme.Colors.Background.reading
                        : Theme.Colors.Text.muted
                )
                .frame(maxWidth: .infinity)
                .padding(.vertical, Theme.Spacing.md)
                .background(
                    isValid
                        ? Theme.Colors.Accent.warm
                        : Theme.Colors.Background.tertiary
                )
                .clipShape(.rect(cornerRadius: Self.cornerRadius, style: .continuous))
        }
        .disabled(!isValid)
    }

    // MARK: - Helpers

    private var trimmedTitle: String {
        title.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private var trimmedBody: String {
        filingBody.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private var isValid: Bool {
        !trimmedTitle.isEmpty && !trimmedBody.isEmpty
    }

    private var submitLabel: String {
        switch selectedType {
        case .motion: "File Motion"
        case .objection: "File Objection"
        case .emergencyOrder: "File Emergency Order"
        }
    }

    private func submit() {
        guard isValid else { return }

        let type = selectedType
        let filedBy = Config.signerIdentity
        let submitTitle = trimmedTitle
        let submitBody = trimmedBody
        let tempId = UUID().uuidString

        let optimistic = Filing(
            id: tempId,
            filingType: type,
            filedBy: filedBy,
            title: submitTitle,
            body: submitBody,
            ruling: nil,
            rulingReason: nil,
            ruledBy: nil,
            ruledAt: nil,
            createdAt: .now,
            updatedAt: .now
        )
        appState.cacheFiling(optimistic)
        UIImpactFeedbackGenerator(style: .medium).impactOccurred()
        router.pop()

        Task {
            do {
                let filing = try await client.createFiling(
                    type: type,
                    filedBy: filedBy,
                    title: submitTitle,
                    body: submitBody
                )
                await MainActor.run { appState.cacheFiling(filing) }
            } catch {
                await MainActor.run {
                    appState.removeFiling(id: tempId)
                }
            }
        }
    }
}
