import SwiftUI
import UIKit

struct ContractBookView: View {
    @Environment(AppState.self) private var appState
    @Environment(Router.self) private var router

    private var articles: [ContentItem] {
        appState.cachedContent
            .filter { $0.type == .contract }
            .sorted { $0.sectionOrder < $1.sectionOrder }
    }

    private var filedDate: Date? {
        articles.first?.createdAt
    }

    var body: some View {
        PageCurlContainer(
            articles: articles,
            filedDate: filedDate,
            onBack: { router.pop() }
        )
        .ignoresSafeArea()
        .navigationBarBackButtonHidden()
        .toolbar(.hidden, for: .navigationBar)
    }
}

// MARK: - Page Curl Container

private struct PageCurlContainer: UIViewControllerRepresentable {
    let articles: [ContentItem]
    let filedDate: Date?
    let onBack: () -> Void

    func makeCoordinator() -> Coordinator {
        Coordinator()
    }

    func makeUIViewController(
        context: Context
    ) -> UIPageViewController {
        let pvc = UIPageViewController(
            transitionStyle: .pageCurl,
            navigationOrientation: .horizontal,
            options: [
                .spineLocation: NSNumber(
                    value: UIPageViewController.SpineLocation.min.rawValue
                ),
            ]
        )
        pvc.dataSource = context.coordinator
        pvc.delegate = context.coordinator
        pvc.isDoubleSided = false

        let readingBg = UIColor(named: "BackgroundReading") ?? .clear
        pvc.view.backgroundColor = readingBg

        let coordinator = context.coordinator
        coordinator.pageViewController = pvc
        coordinator.rebuild(
            articles: articles,
            filedDate: filedDate,
            onBack: onBack
        )

        if let first = coordinator.controller(at: 0) {
            pvc.setViewControllers(
                [first],
                direction: .forward,
                animated: false
            )
        }

        return pvc
    }

    func updateUIViewController(
        _ pvc: UIPageViewController,
        context: Context
    ) {
        let coordinator = context.coordinator
        let currentIDs = articles.map(\.id)
        guard coordinator.articleIDs != currentIDs else { return }

        coordinator.rebuild(
            articles: articles,
            filedDate: filedDate,
            onBack: onBack
        )
        let safeIndex = min(
            coordinator.currentIndex,
            max(coordinator.pageCount - 1, 0)
        )
        coordinator.currentIndex = safeIndex

        if let vc = coordinator.controller(at: safeIndex) {
            pvc.setViewControllers(
                [vc],
                direction: .forward,
                animated: false
            )
        }
    }

    // MARK: - Coordinator

    final class Coordinator: NSObject,
        UIPageViewControllerDataSource,
        UIPageViewControllerDelegate
    {
        weak var pageViewController: UIPageViewController?
        var currentIndex = 0
        private(set) var articleIDs: [String] = []
        private var controllers: [UIViewController] = []

        var pageCount: Int { controllers.count }

        // MARK: Build Pages

        func rebuild(
            articles: [ContentItem],
            filedDate: Date?,
            onBack: @escaping () -> Void
        ) {
            articleIDs = articles.map(\.id)
            controllers = []

            let cover = UIHostingController(
                rootView: CoverPageView(filedDate: filedDate, onBack: onBack)
            )
            controllers.append(cover)

            let toc = UIHostingController(
                rootView: TOCPageView(
                    articles: articles
                ) { [weak self] pageIndex in
                    self?.jumpTo(pageIndex)
                }
            )
            controllers.append(toc)

            for article in articles {
                let page = UIHostingController(
                    rootView: ArticlePageView(article: article)
                )
                controllers.append(page)
            }

            let readingBg = UIColor(named: "BackgroundReading") ?? .clear
            for controller in controllers {
                controller.view.backgroundColor = readingBg
            }
        }

        func controller(at index: Int) -> UIViewController? {
            guard index >= 0, index < controllers.count else {
                return nil
            }
            return controllers[index]
        }

        // MARK: Jump

        func jumpTo(_ index: Int) {
            guard index >= 0,
                  index < controllers.count,
                  index != currentIndex,
                  let pvc = pageViewController
            else { return }

            let direction: UIPageViewController.NavigationDirection =
                index > currentIndex ? .forward : .reverse
            currentIndex = index
            pvc.setViewControllers(
                [controllers[index]],
                direction: direction,
                animated: true
            )
        }

        // MARK: Data Source

        func pageViewController(
            _ pageViewController: UIPageViewController,
            viewControllerBefore viewController: UIViewController
        ) -> UIViewController? {
            guard let index = controllers.firstIndex(of: viewController),
                  index > 0
            else { return nil }
            return controllers[index - 1]
        }

        func pageViewController(
            _ pageViewController: UIPageViewController,
            viewControllerAfter viewController: UIViewController
        ) -> UIViewController? {
            guard let index = controllers.firstIndex(of: viewController),
                  index < controllers.count - 1
            else { return nil }
            return controllers[index + 1]
        }

        // MARK: Delegate

        func pageViewController(
            _ pageViewController: UIPageViewController,
            didFinishAnimating finished: Bool,
            previousViewControllers: [UIViewController],
            transitionCompleted completed: Bool
        ) {
            guard completed,
                  let visible = pageViewController.viewControllers?.first,
                  let index = controllers.firstIndex(of: visible)
            else { return }
            currentIndex = index
        }
    }
}

// MARK: - Article Page View

private struct ArticlePageView: View {
    let article: ContentItem

    var body: some View {
        VStack(spacing: Theme.Spacing.md) {
            Spacer()

            if let articleNumber = article.articleNumber {
                Text(articleNumber.uppercased())
                    .font(Theme.Typography.screenTitle)
                    .foregroundStyle(Theme.Colors.Text.primary)
                    .accessibilityAddTraits(.isHeader)
            }

            if let title = article.title {
                Text(title)
                    .font(Theme.Typography.articleTitle)
                    .foregroundStyle(Theme.Colors.Text.primary)
                    .multilineTextAlignment(.center)
            }

            Spacer()
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding(.horizontal, Theme.Spacing.readingHorizontal)
        .background {
            Theme.Colors.Background.reading.ignoresSafeArea()
        }
        .paperNoise()
    }
}

// MARK: - Previews

#Preview("Contract Book") {
    let state = AppState()
    let _ = state.updateCachedContent([
        ContentItem(
            id: "art-1",
            type: .contract,
            title: "Definition of Forever",
            subtitle: nil,
            body: "WHEREAS the parties have agreed to define forever...",
            articleNumber: "Article I",
            classification: nil,
            sectionOrder: 1,
            requiresSignature: true,
            createdAt: Calendar.current.date(
                from: DateComponents(year: 2025, month: 2, day: 14)
            ) ?? .now,
            updatedAt: Calendar.current.date(
                from: DateComponents(year: 2025, month: 2, day: 14)
            ) ?? .now
        ),
        ContentItem(
            id: "art-2",
            type: .contract,
            title: "Daily Reassurance Obligations",
            subtitle: nil,
            body: "WHEREAS the Boyfriend acknowledges...",
            articleNumber: "Article II",
            classification: nil,
            sectionOrder: 2,
            requiresSignature: true,
            createdAt: Calendar.current.date(
                from: DateComponents(year: 2025, month: 2, day: 14)
            ) ?? .now,
            updatedAt: Calendar.current.date(
                from: DateComponents(year: 2025, month: 2, day: 14)
            ) ?? .now
        ),
        ContentItem(
            id: "art-3",
            type: .contract,
            title: "Snack Procurement Obligations",
            subtitle: nil,
            body: "WHEREAS the Girlfriend has expressed...",
            articleNumber: "Article III",
            classification: nil,
            sectionOrder: 3,
            requiresSignature: true,
            createdAt: Calendar.current.date(
                from: DateComponents(year: 2025, month: 2, day: 14)
            ) ?? .now,
            updatedAt: Calendar.current.date(
                from: DateComponents(year: 2025, month: 2, day: 14)
            ) ?? .now
        ),
    ])

    NavigationStack {
        ContractBookView()
    }
    .environment(state)
    .environment(Router())
}

#Preview("Empty State") {
    NavigationStack {
        ContractBookView()
    }
    .environment(AppState())
    .environment(Router())
}

#Preview("Dark Mode") {
    let state = AppState()
    let _ = state.updateCachedContent([
        ContentItem(
            id: "art-1",
            type: .contract,
            title: "Definition of Forever",
            subtitle: nil,
            body: "WHEREAS the parties have agreed...",
            articleNumber: "Article I",
            classification: nil,
            sectionOrder: 1,
            requiresSignature: true,
            createdAt: Calendar.current.date(
                from: DateComponents(year: 2025, month: 2, day: 14)
            ) ?? .now,
            updatedAt: Calendar.current.date(
                from: DateComponents(year: 2025, month: 2, day: 14)
            ) ?? .now
        ),
    ])

    NavigationStack {
        ContractBookView()
    }
    .environment(state)
    .environment(Router())
    .preferredColorScheme(.dark)
}
