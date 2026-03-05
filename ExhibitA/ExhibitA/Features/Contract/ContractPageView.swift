import CoreText
import SwiftUI
import UIKit

// MARK: - Article Section

nonisolated enum ArticleSection: Sendable {
    case preamble(String)
    case agreement(String)
    case clause(String)
    case body(String)

    var text: String {
        switch self {
        case let .preamble(t), let .agreement(t), let .clause(t), let .body(t):
            t
        }
    }
}

// MARK: - Article Page

nonisolated struct ArticlePage: Identifiable, Sendable {
    let id: String
    let contentId: String
    let articleNumber: String?
    let articleTitle: String?
    let sections: [ArticleSection]
    let isFirstPage: Bool
    let isSignaturePage: Bool
    let pageNumber: Int
    let totalPages: Int
}

// MARK: - Contract Body Parser

nonisolated enum ContractBodyParser: Sendable {
    static func parse(_ body: String) -> [ArticleSection] {
        let cleaned = body.replacingOccurrences(of: "**", with: "")
        let paragraphs = cleaned
            .components(separatedBy: "\n\n")
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }

        return paragraphs.map(classify)
    }

    private static func classify(_ paragraph: String) -> ArticleSection {
        let trimmed = paragraph.trimmingCharacters(in: .whitespaces)
        let upper = trimmed.uppercased()

        if upper.hasPrefix("WHEREAS") || upper.hasPrefix("AND WHEREAS") {
            return .preamble(trimmed)
        }

        if upper.hasPrefix("NOW, THEREFORE") || upper.hasPrefix("NOW THEREFORE") {
            return .agreement(trimmed)
        }

        if trimmed.hasPrefix("\u{00A7}") {
            return .clause(trimmed)
        }

        return .body(trimmed)
    }
}

// MARK: - Measurement Fonts

@MainActor
private enum MeasurementFonts {
    static let contractBody: UIFont = serifFont(size: 18, weight: .regular)
    static let legalPreamble: UIFont = serifFont(size: 18, weight: .regular, italic: true)
    static let sectionMarker: UIFont = serifFont(size: 18, weight: .semibold)
    static let screenTitle: UIFont = serifFont(size: 28, weight: .bold)
    static let articleTitle: UIFont = serifFont(size: 24, weight: .semibold)

    private static func serifFont(
        size: CGFloat,
        weight: UIFont.Weight,
        italic: Bool = false,
    )
        -> UIFont
    {
        var descriptor = UIFont.systemFont(ofSize: size, weight: weight).fontDescriptor
        if let serif = descriptor.withDesign(.serif) {
            descriptor = serif
        }
        if italic, let italicDesc = descriptor.withSymbolicTraits(.traitItalic) {
            descriptor = italicDesc
        }
        return UIFont(descriptor: descriptor, size: size)
    }
}

// MARK: - Text Measurement

@MainActor
private enum TextMeasurement {
    private static let bodyFontSize: CGFloat = 18
    private static let naturalLineHeightRatio: CGFloat = 1.2
    static let bodyLineSpacing = bodyFontSize * (Theme.LineHeight.reading - naturalLineHeightRatio)

    static func height(
        for text: String,
        font: UIFont,
        width: CGFloat,
        lineSpacing: CGFloat = 0,
    )
        -> CGFloat
    {
        guard !text.isEmpty else { return 0 }

        let paragraphStyle = NSMutableParagraphStyle()
        paragraphStyle.lineSpacing = lineSpacing

        let attributes: [NSAttributedString.Key: Any] = [
            .font: font,
            .paragraphStyle: paragraphStyle,
        ]

        let attrString = NSAttributedString(string: text, attributes: attributes)
        let constraintSize = CGSize(width: width, height: .greatestFiniteMagnitude)
        let bounds = attrString.boundingRect(
            with: constraintSize,
            options: [.usesLineFragmentOrigin, .usesFontLeading],
            context: nil,
        )
        return ceil(bounds.height)
    }

    static func sectionHeight(_ section: ArticleSection, width: CGFloat) -> CGFloat {
        let font: UIFont = switch section {
        case .preamble:
            MeasurementFonts.legalPreamble
        case .agreement:
            MeasurementFonts.contractBody
        case .clause:
            MeasurementFonts.contractBody
        case .body:
            MeasurementFonts.contractBody
        }
        return height(for: section.text, font: font, width: width, lineSpacing: bodyLineSpacing)
    }

    static func headingHeight(
        articleNumber: String?,
        title: String?,
        width: CGFloat,
    )
        -> CGFloat
    {
        var total: CGFloat = 0

        if let number = articleNumber {
            total += height(for: number.uppercased(), font: MeasurementFonts.screenTitle, width: width)
        }

        if articleNumber != nil, title != nil {
            total += Theme.Spacing.md
        }

        if let title {
            total += height(
                for: title.uppercased(),
                font: MeasurementFonts.articleTitle,
                width: width,
            )
        }

        return total
    }
}

// MARK: - Contract Paginator

@MainActor
enum ContractPaginator {
    struct PageMetrics: Sendable {
        let contentWidth: CGFloat
        let bodyHeight: CGFloat
    }

    static func paginate(article: ContentItem, metrics: PageMetrics) -> [ArticlePage] {
        let sections = ContractBodyParser.parse(article.body)
        let width = metrics.contentWidth

        let headingHeight = TextMeasurement.headingHeight(
            articleNumber: article.articleNumber,
            title: article.title,
            width: width,
        )
        let headingBottomSpacing = Theme.Spacing.lg
        let firstPageAvailable = metrics.bodyHeight - headingHeight - headingBottomSpacing
        let sectionSpacing = Theme.Spacing.paragraphSpacing

        var pages: [[ArticleSection]] = []
        var currentPage: [ArticleSection] = []
        var currentHeight: CGFloat = 0
        var isFirstPage = true
        var availableHeight = max(firstPageAvailable, 50)

        for section in sections {
            let sectionH = TextMeasurement.sectionHeight(section, width: width)
            let spacingBefore: CGFloat = currentPage.isEmpty ? 0 : sectionSpacing
            let needed = spacingBefore + sectionH

            if !currentPage.isEmpty, currentHeight + needed > availableHeight {
                pages.append(currentPage)
                currentPage = [section]
                currentHeight = sectionH
                if isFirstPage {
                    isFirstPage = false
                    availableHeight = max(metrics.bodyHeight, 50)
                }
            } else {
                currentPage.append(section)
                currentHeight += needed
            }
        }

        if !currentPage.isEmpty {
            pages.append(currentPage)
        }

        if pages.isEmpty {
            pages.append([])
        }

        let totalPages = pages.count + 1
        let articleId = article.id
        var result: [ArticlePage] = []

        for (index, pageSections) in pages.enumerated() {
            result.append(ArticlePage(
                id: "\(articleId)-body-\(index)",
                contentId: articleId,
                articleNumber: article.articleNumber,
                articleTitle: article.title,
                sections: pageSections,
                isFirstPage: index == 0,
                isSignaturePage: false,
                pageNumber: index + 1,
                totalPages: totalPages,
            ))
        }

        result.append(ArticlePage(
            id: "\(articleId)-signature",
            contentId: articleId,
            articleNumber: article.articleNumber,
            articleTitle: article.title,
            sections: [],
            isFirstPage: false,
            isSignaturePage: true,
            pageNumber: totalPages,
            totalPages: totalPages,
        ))

        return result
    }

    static func computeMetrics() -> PageMetrics {
        let windowScene = UIApplication.shared.connectedScenes
            .compactMap { $0 as? UIWindowScene }
            .first
        let fallbackBounds = CGRect(x: 0, y: 0, width: 393, height: 852)
        let screen = windowScene?.screen.bounds ?? fallbackBounds
        let safeArea = windowScene?.keyWindow?.safeAreaInsets ?? .zero

        let contentWidth = screen.width - 2 * Theme.Spacing.readingHorizontal

        let topPadding = Theme.Spacing.lg
        let bottomPadding = Theme.Spacing.md
        let footerArea: CGFloat = 32

        let safeAreaHeight = screen.height - safeArea.top - safeArea.bottom
        let bodyHeight = safeAreaHeight - topPadding - bottomPadding - footerArea

        return PageMetrics(
            contentWidth: max(contentWidth, 100),
            bodyHeight: max(bodyHeight, 100),
        )
    }
}

// MARK: - Contract Page View

struct ContractPageView: View {
    let page: ArticlePage

    private static let bodyFontSize: CGFloat = 18
    private static let bodyLineSpacing = bodyFontSize * (Theme.LineHeight.reading - 1.2)

    var body: some View {
        VStack(spacing: 0) {
            if page.isSignaturePage {
                signatureSlotContent
            } else {
                articleBodyContent
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding(.horizontal, Theme.Spacing.readingHorizontal)
        .background {
            Theme.Colors.Background.reading.ignoresSafeArea()
        }
        .paperNoise()
    }

    // MARK: - Article Body Content

    private var articleBodyContent: some View {
        VStack(spacing: 0) {
            Spacer().frame(height: Theme.Spacing.lg)

            if page.isFirstPage {
                headingBlock
                    .padding(.bottom, Theme.Spacing.lg)
            }

            sectionsBlock

            Spacer(minLength: Theme.Spacing.sm)

            footerBlock
                .padding(.bottom, Theme.Spacing.md)
        }
    }

    // MARK: - Heading

    private var headingBlock: some View {
        VStack(spacing: Theme.Spacing.md) {
            if let number = page.articleNumber {
                Text(number.uppercased())
                    .font(Theme.Typography.screenTitle)
                    .foregroundStyle(Theme.Colors.Text.primary)
                    .multilineTextAlignment(.center)
                    .accessibilityAddTraits(.isHeader)
            }
            if let title = page.articleTitle {
                Text(title.uppercased())
                    .font(Theme.Typography.articleTitle)
                    .foregroundStyle(Theme.Colors.Text.primary)
                    .multilineTextAlignment(.center)
            }
        }
        .frame(maxWidth: .infinity)
        .accessibilityElement(children: .combine)
    }

    // MARK: - Sections

    private var sectionsBlock: some View {
        VStack(alignment: .leading, spacing: Theme.Spacing.paragraphSpacing) {
            if page.sections.isEmpty, page.isFirstPage {
                Text("No content filed.")
                    .font(Theme.Typography.metadata)
                    .foregroundStyle(Theme.Colors.Text.muted)
                    .frame(maxWidth: .infinity, alignment: .center)
            } else {
                ForEach(Array(page.sections.enumerated()), id: \.offset) { _, section in
                    sectionView(section)
                }
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    @ViewBuilder
    private func sectionView(_ section: ArticleSection) -> some View {
        switch section {
        case let .preamble(text):
            Text(text)
                .font(Theme.Typography.legalPreamble)
                .foregroundStyle(Theme.Colors.Text.secondary)
                .lineSpacing(Self.bodyLineSpacing)
                .fixedSize(horizontal: false, vertical: true)

        case let .agreement(text):
            Text(text)
                .font(Theme.Typography.contractBody)
                .foregroundStyle(Theme.Colors.Text.reading)
                .lineSpacing(Self.bodyLineSpacing)
                .fixedSize(horizontal: false, vertical: true)

        case let .clause(text):
            styledClause(text)
                .lineSpacing(Self.bodyLineSpacing)
                .fixedSize(horizontal: false, vertical: true)

        case let .body(text):
            Text(text)
                .font(Theme.Typography.contractBody)
                .foregroundStyle(Theme.Colors.Text.reading)
                .lineSpacing(Self.bodyLineSpacing)
                .fixedSize(horizontal: false, vertical: true)
        }
    }

    private func styledClause(_ text: String) -> Text {
        guard let spaceIndex = text.firstIndex(where: { $0.isWhitespace }) else {
            return Text(text)
                .font(Theme.Typography.sectionMarker)
                .foregroundStyle(Theme.Colors.Accent.primary)
        }

        let marker = String(text[text.startIndex ..< spaceIndex])
        let rest = String(text[spaceIndex...]).trimmingCharacters(in: .whitespaces)

        var styled = AttributedString(marker + "  ")
        styled.font = Theme.Typography.sectionMarker
        styled.foregroundColor = Theme.Colors.Accent.primary

        var body = AttributedString(rest)
        body.font = Theme.Typography.contractBody
        body.foregroundColor = Theme.Colors.Text.reading

        styled.append(body)
        return Text(styled)
    }

    // MARK: - Footer

    private var footerBlock: some View {
        Group {
            if let number = page.articleNumber {
                Text("\(number) \u{2014} \(page.pageNumber) of \(page.totalPages)")
                    .font(Theme.Typography.pageNumber)
                    .foregroundStyle(Theme.Colors.Text.muted)
            }
        }
        .frame(maxWidth: .infinity, alignment: .center)
        .accessibilityLabel(footerAccessibilityLabel)
    }

    private var footerAccessibilityLabel: String {
        let article = page.articleNumber ?? "Article"
        return "\(article), page \(page.pageNumber) of \(page.totalPages)"
    }

    // MARK: - Signature Slot

    private var signatureSlotContent: some View {
        VStack(spacing: 0) {
            Spacer()

            SignatureBlockView(contentId: page.contentId)

            Spacer()

            footerBlock
                .padding(.bottom, Theme.Spacing.md)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

// MARK: - Previews

private enum PreviewContent {
    static let shortBody = """
    WHEREAS, the Parties acknowledge that this Agreement was not entered into lightly, \
    casually, or for temporary amusement, but instead arose from real affection, deep \
    attachment, and a bond that has grown into something meaningful and serious;

    NOW, THEREFORE, the Parties hereby establish that Forever shall mean a love intended \
    to last, a bond entered into seriously, and a promise that the Girlfriend is not being \
    loved only for the present moment, but for all the moments still to come.
    """

    static let longBody = """
    WHEREAS, the Girlfriend has expressed, on no fewer than forty-seven (47) documented \
    occasions, a preference for snacks of the sweet, salty, and surprise me variety;

    AND WHEREAS, the Boyfriend has demonstrated a pattern of arriving with said snacks \
    unprompted, thereby establishing precedent;

    AND WHEREAS, snack procurement is recognized under this Agreement as an act of love, \
    not a logistical inconvenience;

    NOW, THEREFORE, the Parties agree to the following terms regarding snack obligations:

    \u{00A7}3.1  The Boyfriend shall maintain a reasonable inventory of the Girlfriend's \
    preferred snacks at all times. Reasonable shall be defined as more than zero.

    \u{00A7}3.2  The phrase I'm not hungry shall not be interpreted literally and the \
    Boyfriend shall procure snacks regardless.

    \u{00A7}3.3  Failure to comply with the above shall constitute a Minor Infraction \
    under Schedule B of this Agreement.

    \u{00A7}3.4  In the event of a dispute regarding snack preferences, the Girlfriend's \
    craving at the time of request shall be considered the final authority.

    \u{00A7}3.5  Emergency snack runs may be initiated at any hour and shall not be \
    subject to the Boyfriend's claims of tiredness, distance, or weather conditions.

    \u{00A7}3.6  The Boyfriend acknowledges that snack sharing is a privilege, not a right, \
    and that taking the last piece without offering it first constitutes a breach of trust.

    \u{00A7}3.7  All snack-related disputes shall be resolved in favor of the Girlfriend \
    unless the Boyfriend presents compelling evidence of a superior snack option.
    """

    static func article(
        id: String = "art-preview",
        title: String = "Snack Procurement Obligations",
        number: String = "Article III",
        body: String = longBody,
        order: Int = 3,
    )
        -> ContentItem
    {
        ContentItem(
            id: id,
            type: .contract,
            title: title,
            subtitle: nil,
            body: body,
            articleNumber: number,
            classification: nil,
            sectionOrder: order,
            requiresSignature: true,
            createdAt: Calendar.current.date(
                from: DateComponents(year: 2_025, month: 2, day: 14),
            ) ?? .now,
            updatedAt: Calendar.current.date(
                from: DateComponents(year: 2_025, month: 2, day: 14),
            ) ?? .now,
        )
    }
}

#Preview("Body Page - First") {
    let article = PreviewContent.article()
    let metrics = ContractPaginator.computeMetrics()
    let pages = ContractPaginator.paginate(article: article, metrics: metrics)
    if let first = pages.first {
        ContractPageView(page: first)
    }
}

#Preview("Body Page - Short Article") {
    let article = PreviewContent.article(
        title: "Definition of Forever",
        number: "Article I",
        body: PreviewContent.shortBody,
        order: 1,
    )
    let metrics = ContractPaginator.computeMetrics()
    let pages = ContractPaginator.paginate(article: article, metrics: metrics)
    if let first = pages.first {
        ContractPageView(page: first)
    }
}

#Preview("Signature Page") {
    let article = PreviewContent.article()
    let metrics = ContractPaginator.computeMetrics()
    let pages = ContractPaginator.paginate(article: article, metrics: metrics)
    if let last = pages.last {
        ContractPageView(page: last)
            .environment(AppState())
    }
}

#Preview("Empty Body") {
    let article = PreviewContent.article(body: "", order: 1)
    let metrics = ContractPaginator.computeMetrics()
    let pages = ContractPaginator.paginate(article: article, metrics: metrics)
    if let first = pages.first {
        ContractPageView(page: first)
    }
}

#Preview("Dark Mode") {
    let article = PreviewContent.article()
    let metrics = ContractPaginator.computeMetrics()
    let pages = ContractPaginator.paginate(article: article, metrics: metrics)
    ContractPageView(page: pages[0])
        .preferredColorScheme(.dark)
}
