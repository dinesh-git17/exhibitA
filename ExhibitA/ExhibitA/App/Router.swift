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
        case filingsList
        case filingDetail(id: String)
        case filingCompose
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

extension Router.Route {
    static func from(pushRoute value: String) -> Router.Route? {
        let segments = value.split(separator: "/", maxSplits: 1)
        guard let kind = segments.first else { return nil }
        let id = segments.count > 1 ? String(segments[1]) : nil

        switch kind {
        case "contract":
            return .contractBook
        case "letter":
            return id.map { .letterDetail(id: $0) } ?? .lettersList
        case "thought":
            return id.map { .thoughtDetail(id: $0) } ?? .thoughtsList
        case "filing":
            return id.map { .filingDetail(id: $0) } ?? .filingsList
        default:
            return nil
        }
    }
}
