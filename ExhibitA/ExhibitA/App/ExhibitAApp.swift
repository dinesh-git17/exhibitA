import SwiftUI
import UIKit

@main
struct ExhibitAApp: App {
    @State private var appState = AppState()
    @State private var router = Router()

    init() {
        KeychainService.seedAPIKeyIfNeeded(Config.apiKey)
        Self.suppressLiquidGlass()
    }

    var body: some Scene {
        WindowGroup {
            NavigationStack(path: $router.path) {
                Theme.Colors.Background.primary
                    .ignoresSafeArea()
                    .navigationDestination(for: Router.Route.self) { route in
                        switch route {
                        case .contractBook:
                            Text("Contract Book")
                        case let .letterDetail(id):
                            Text("Letter \(id)")
                        case let .thoughtDetail(id):
                            Text("Thought \(id)")
                        }
                    }
            }
            .environment(appState)
            .environment(router)
        }
    }

    // MARK: - Liquid Glass Suppression

    private static func suppressLiquidGlass() {
        let bg = Theme.UIColors.backgroundPrimary

        let navAppearance = UINavigationBarAppearance()
        navAppearance.configureWithOpaqueBackground()
        navAppearance.backgroundColor = bg
        UINavigationBar.appearance().standardAppearance = navAppearance
        UINavigationBar.appearance().scrollEdgeAppearance = navAppearance
        UINavigationBar.appearance().compactAppearance = navAppearance

        let tabAppearance = UITabBarAppearance()
        tabAppearance.configureWithOpaqueBackground()
        tabAppearance.backgroundColor = bg
        UITabBar.appearance().standardAppearance = tabAppearance
        UITabBar.appearance().scrollEdgeAppearance = tabAppearance

        let toolbarAppearance = UIToolbarAppearance()
        toolbarAppearance.configureWithOpaqueBackground()
        toolbarAppearance.backgroundColor = bg
        UIToolbar.appearance().standardAppearance = toolbarAppearance
        UIToolbar.appearance().scrollEdgeAppearance = toolbarAppearance
    }
}
