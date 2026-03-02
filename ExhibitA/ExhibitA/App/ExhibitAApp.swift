import SwiftUI
import UIKit

@main
struct ExhibitAApp: App {
    init() {
        Self.suppressLiquidGlass()
    }

    var body: some Scene {
        WindowGroup {
            Theme.Colors.Background.primary
                .ignoresSafeArea()
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
