import SwiftUI

struct ResponseOnRecordView: View {
    let comment: CommentRecord

    private static let bodyFontSize: CGFloat = 18
    private static let naturalLineHeightRatio: CGFloat = 1.2
    private static let bodyLineSpacing = bodyFontSize * (Theme.LineHeight.reading - naturalLineHeightRatio)

    var body: some View {
        VStack(alignment: .leading, spacing: Theme.Spacing.sm) {
            Text("RESPONSE ON RECORD")
                .font(Theme.Typography.label)
                .foregroundStyle(Theme.Colors.Text.secondary)
                .tracking(1.5)

            Text(signerLabel)
                .font(Theme.Typography.metadata)
                .foregroundStyle(Theme.Colors.Text.muted)

            Text(comment.body)
                .font(Theme.Typography.contractBody)
                .foregroundStyle(Theme.Colors.Text.reading)
                .lineSpacing(Self.bodyLineSpacing)
                .fixedSize(horizontal: false, vertical: true)

            Text(dateLabel)
                .font(Theme.Typography.metadata)
                .foregroundStyle(Theme.Colors.Text.muted)
        }
    }

    private var signerLabel: String {
        comment.signer == Config.signerIdentity ? "Your response" : "Their response"
    }

    private var dateLabel: String {
        "Filed: \(comment.createdAt.formatted(.dateTime.month(.wide).day().year()))"
    }
}
