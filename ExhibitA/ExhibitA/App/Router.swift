import SwiftUI

/// Observable router managing navigation state via NavigationPath.
/// Design Doc reference: S8.2.
@Observable final class Router {
    var path = NavigationPath()

    enum Route: Hashable {
        case contractBook
        case lettersList
        case thoughtsList
        case letterDetail(id: String)
        case thoughtDetail(id: String)
    }

    func navigate(to route: Route) {
        path.append(route)
    }

    func pop() {
        guard !path.isEmpty else { return }
        path.removeLast()
    }

    func popToRoot() {
        path.removeLast(path.count)
    }
}
