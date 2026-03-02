import SwiftUI
import UIKit

@main
struct ExhibitAApp: App {
    init() {
        Self.suppressLiquidGlass()
    }

    var body: some Scene {
        WindowGroup {
            Color(uiColor: AppDefaults.opaqueBackground)
                .ignoresSafeArea()
        }
    }

    // MARK: - Liquid Glass Suppression

    private static func suppressLiquidGlass() {
        let navAppearance = UINavigationBarAppearance()
        navAppearance.configureWithOpaqueBackground()
        navAppearance.backgroundColor = AppDefaults.opaqueBackground
        UINavigationBar.appearance().standardAppearance = navAppearance
        UINavigationBar.appearance().scrollEdgeAppearance = navAppearance
        UINavigationBar.appearance().compactAppearance = navAppearance

        let tabAppearance = UITabBarAppearance()
        tabAppearance.configureWithOpaqueBackground()
        tabAppearance.backgroundColor = AppDefaults.opaqueBackground
        UITabBar.appearance().standardAppearance = tabAppearance
        UITabBar.appearance().scrollEdgeAppearance = tabAppearance

        let toolbarAppearance = UIToolbarAppearance()
        toolbarAppearance.configureWithOpaqueBackground()
        toolbarAppearance.backgroundColor = AppDefaults.opaqueBackground
        UIToolbar.appearance().standardAppearance = toolbarAppearance
        UIToolbar.appearance().scrollEdgeAppearance = toolbarAppearance
    }
}

// MARK: - App Shell Defaults

/// Minimal color constants for Liquid Glass suppression at the app shell level.
/// Replaced by Theme tokens in E2.2 when the design system is implemented.
private enum AppDefaults {
    /// Warm ivory #F2EFEA -- design doc S6.2 background.primary
    static let opaqueBackground = UIColor(
        red: 242.0 / 255.0,
        green: 239.0 / 255.0,
        blue: 234.0 / 255.0,
        alpha: 1.0,
    )
}
