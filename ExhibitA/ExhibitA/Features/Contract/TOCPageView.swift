import SwiftUI
import UIKit

struct TOCPageView: View {
    let articles: [ContentItem]
    var articlePageIndices: [Int] = []
    let onSelectArticle: (Int) -> Void

    private static let tocPageOffset = 2

    @MainActor
    private static var topSafeAreaInset: CGFloat {
        UIApplication.shared.connectedScenes
            .compactMap { $0 as? UIWindowScene }
            .first?.keyWindow?.safeAreaInsets.top ?? 0
    }

    var body: some View {
        GeometryReader { geometry in
            ScrollView {
                tocContent
                    .frame(minHeight: geometry.size.height)
            }
        }
        .background {
            Theme.Colors.Background.reading.ignoresSafeArea()
        }
        .paperNoise()
    }

    // MARK: - Content

    private var tocContent: some View {
        VStack(alignment: .leading, spacing: 0) {
            headerSection
                .padding(.bottom, Theme.Spacing.lg)

            separator

            if articles.isEmpty {
                emptyState
                    .padding(.top, Theme.Spacing.xl)
            } else {
                articleEntries
                    .padding(.top, Theme.Spacing.md)
            }

            Spacer(minLength: Theme.Spacing.xxl)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.horizontal, Theme.Spacing.readingHorizontal)
        .padding(.top, Self.topSafeAreaInset + Theme.Spacing.md)
    }

    // MARK: - Header

    private var headerSection: some View {
        Text("TABLE OF CONTENTS")
            .font(Theme.Typography.screenTitle)
            .foregroundStyle(Theme.Colors.Text.primary)
            .tracking(1.5)
            .frame(maxWidth: .infinity, alignment: .center)
            .accessibilityAddTraits(.isHeader)
    }

    // MARK: - Entries

    private var articleEntries: some View {
        VStack(alignment: .leading, spacing: Theme.Spacing.md) {
            ForEach(
                Array(articles.enumerated()),
                id: \.element.id
            ) { index, article in
                articleRow(article, index: index)

                if index < articles.count - 1 {
                    separator
                }
            }
        }
    }

    private func articleRow(
        _ article: ContentItem,
        index: Int
    ) -> some View {
        let pageIndex = index < articlePageIndices.count
            ? articlePageIndices[index]
            : index + Self.tocPageOffset
        let displayPage = pageIndex + 1

        return Button {
            onSelectArticle(pageIndex)
        } label: {
            VStack(alignment: .leading, spacing: Theme.Spacing.xs) {
                if let articleNumber = article.articleNumber {
                    Text(articleNumber.uppercased())
                        .font(Theme.Typography.label)
                        .foregroundStyle(Theme.Colors.Text.secondary)
                        .tracking(1.5)
                }

                HStack(spacing: 0) {
                    Text(article.title ?? "Untitled")
                        .font(Theme.Typography.contractBody)
                        .foregroundStyle(Theme.Colors.Text.primary)
                        .lineLimit(1)

                    Spacer(minLength: Theme.Spacing.sm)
                        .overlay {
                            DottedLeader()
                                .fill(Theme.Colors.Text.muted)
                        }

                    Text("\(displayPage)")
                        .font(Theme.Typography.pageNumber)
                        .foregroundStyle(Theme.Colors.Text.muted)
                        .monospacedDigit()
                        .fixedSize()
                }
            }
            .padding(.vertical, Theme.Spacing.sm)
            .frame(maxWidth: .infinity, alignment: .leading)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .accessibilityLabel(
            "\(article.articleNumber ?? ""), \(article.title ?? "Untitled"), page \(displayPage)"
        )
        .accessibilityHint("Jumps to article")
    }

    // MARK: - Empty State

    private var emptyState: some View {
        Text("No articles filed.")
            .font(Theme.Typography.metadata)
            .foregroundStyle(Theme.Colors.Text.muted)
            .frame(maxWidth: .infinity, alignment: .center)
    }

    // MARK: - Separator

    private var separator: some View {
        Rectangle()
            .fill(Theme.Colors.Border.separator)
            .frame(height: Theme.Dividers.hairline)
            .accessibilityHidden(true)
    }
}

// MARK: - Dotted Leader

private struct DottedLeader: Shape {
    private static let dotDiameter: CGFloat = 1.5
    private static let dotSpacing: CGFloat = 5

    nonisolated func path(in rect: CGRect) -> Path {
        var path = Path()
        let y = rect.maxY - 4
        var x = Self.dotSpacing
        while x < rect.width {
            path.addEllipse(in: CGRect(
                x: x - Self.dotDiameter / 2,
                y: y - Self.dotDiameter / 2,
                width: Self.dotDiameter,
                height: Self.dotDiameter
            ))
            x += Self.dotSpacing
        }
        return path
    }
}

// MARK: - Previews

#Preview("TOC") {
    TOCPageView(
        articles: PreviewData.sampleArticles,
        onSelectArticle: { _ in }
    )
}

#Preview("TOC - Empty") {
    TOCPageView(
        articles: [],
        onSelectArticle: { _ in }
    )
}

#Preview("TOC - Dark Mode") {
    TOCPageView(
        articles: PreviewData.sampleArticles,
        onSelectArticle: { _ in }
    )
    .preferredColorScheme(.dark)
}

// MARK: - Preview Data

private enum PreviewData {
    static let sampleArticles: [ContentItem] = [
        ContentItem(
            id: "art-1",
            type: .contract,
            title: "Definition of Forever",
            subtitle: nil,
            body: "",
            articleNumber: "Article I",
            classification: nil,
            sectionOrder: 1,
            requiresSignature: true,
            createdAt: .now,
            updatedAt: .now
        ),
        ContentItem(
            id: "art-2",
            type: .contract,
            title: "Daily Reassurance Obligations",
            subtitle: nil,
            body: "",
            articleNumber: "Article II",
            classification: nil,
            sectionOrder: 2,
            requiresSignature: true,
            createdAt: .now,
            updatedAt: .now
        ),
        ContentItem(
            id: "art-3",
            type: .contract,
            title: "Snack Procurement Obligations",
            subtitle: nil,
            body: "",
            articleNumber: "Article III",
            classification: nil,
            sectionOrder: 3,
            requiresSignature: true,
            createdAt: .now,
            updatedAt: .now
        ),
        ContentItem(
            id: "art-4",
            type: .contract,
            title: "Princess Treatment Provision",
            subtitle: nil,
            body: "",
            articleNumber: "Article IV",
            classification: nil,
            sectionOrder: 4,
            requiresSignature: true,
            createdAt: .now,
            updatedAt: .now
        ),
        ContentItem(
            id: "art-5",
            type: .contract,
            title: "Comfort in Times of Distress",
            subtitle: nil,
            body: "",
            articleNumber: "Article V",
            classification: nil,
            sectionOrder: 5,
            requiresSignature: true,
            createdAt: .now,
            updatedAt: .now
        ),
    ]
}
