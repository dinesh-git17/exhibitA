import SwiftUI
import UIKit

struct CommentComposeView: View {
    let contentId: String
    let client: ExhibitAClient

    @Environment(AppState.self) private var appState
    @Environment(CommentUploadQueue.self) private var commentQueue

    @State private var commentText = ""
    @State private var isSubmitting = false

    private static let cornerRadius: CGFloat = 12

    var body: some View {
        VStack(alignment: .leading, spacing: Theme.Spacing.sm) {
            Text("FILE A RESPONSE")
                .font(Theme.Typography.label)
                .foregroundStyle(Theme.Colors.Text.secondary)
                .tracking(1.5)

            VStack(alignment: .leading, spacing: 0) {
                TextField("Your response on record...", text: $commentText, axis: .vertical)
                    .font(Theme.Typography.contractBody)
                    .foregroundStyle(Theme.Colors.Text.reading)
                    .lineLimit(3...8)
                    .padding(.horizontal, Theme.Spacing.md)
                    .padding(.top, Theme.Spacing.md)
                    .padding(.bottom, Theme.Spacing.sm)
                    .disabled(isSubmitting)

                HStack {
                    Spacer()
                    Button {
                        Task { await submit() }
                    } label: {
                        Text("File Response")
                            .font(Theme.Typography.label)
                            .foregroundStyle(
                                trimmedBody.isEmpty || isSubmitting
                                    ? Theme.Colors.Text.muted
                                    : Theme.Colors.Background.reading
                            )
                            .padding(.horizontal, Theme.Spacing.md)
                            .padding(.vertical, Theme.Spacing.sm)
                            .background(
                                trimmedBody.isEmpty || isSubmitting
                                    ? Theme.Colors.Background.tertiary
                                    : Theme.Colors.Accent.warm
                            )
                            .clipShape(.rect(cornerRadius: 8, style: .continuous))
                    }
                    .disabled(trimmedBody.isEmpty || isSubmitting)
                }
                .padding(.horizontal, Theme.Spacing.md)
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

    private var trimmedBody: String {
        commentText.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private func submit() async {
        guard !trimmedBody.isEmpty else { return }
        isSubmitting = true
        defer { isSubmitting = false }

        let text = trimmedBody

        do {
            let record = try await client.createComment(
                contentId: contentId,
                signer: Config.signerIdentity,
                body: text
            )
            appState.cacheComment(record)
            UIImpactFeedbackGenerator(style: .medium).impactOccurred()
        } catch let error as APIError {
            if case .httpFailure(statusCode: 409, _, _) = error {
                return
            }
            commentQueue.enqueue(
                contentId: contentId,
                signer: Config.signerIdentity,
                body: text
            )
            appState.cacheComment(CommentRecord(
                id: UUID().uuidString,
                contentId: contentId,
                signer: Config.signerIdentity,
                body: text,
                createdAt: .now
            ))
        }
    }
}
