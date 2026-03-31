import os
import SwiftUI
import UIKit
import UserNotifications

@main
struct ExhibitAApp: App {
    @UIApplicationDelegateAdaptor private var appDelegate: AppDelegate
    @State private var appState: AppState
    @State private var router = Router()
    @Environment(\.scenePhase) private var scenePhase

    private let syncService: SyncService
    private let client: ExhibitAClient
    private let cache: ContentCache
    private let uploadQueue: UploadQueue
    private let commentUploadQueue: CommentUploadQueue
    private let soundService: SoundService

    init() {
        let state = AppState()
        let apiClient = ExhibitAClient(baseURL: Config.apiBaseURL)
        let contentCache = ContentCache()

        _appState = State(initialValue: state)
        client = apiClient
        cache = contentCache
        syncService = SyncService(client: apiClient, cache: contentCache, appState: state)
        uploadQueue = UploadQueue(
            client: apiClient,
            signatureCache: SignatureCache(),
            appState: state
        )
        commentUploadQueue = CommentUploadQueue(
            client: apiClient,
            appState: state
        )

        soundService = SoundService()

        KeychainService.seedAPIKeyIfNeeded(Config.apiKey)
        Self.suppressLiquidGlass()
    }

    var body: some Scene {
        WindowGroup {
            NavigationStack(path: $router.path) {
                HomeView(
                    onRefresh: { [syncService, uploadQueue, commentUploadQueue] in
                        await syncService.performSync()
                        await uploadQueue.processQueue()
                        await commentUploadQueue.processQueue()
                    },
                    onForceSync: { [syncService] in
                        await syncService.performFullSync()
                    }
                )
                    .navigationDestination(for: Router.Route.self) { route in
                        switch route {
                        case .contractBook:
                            ContractBookView()
                        case .lettersList:
                            LetterListView()
                        case .thoughtsList:
                            ThoughtListView()
                        case let .letterDetail(id):
                            LetterDetailView(id: id, client: client)
                        case let .thoughtDetail(id):
                            ThoughtDetailView(id: id, client: client)
                        case .filingsList:
                            FilingListView(client: client)
                        case let .filingDetail(id):
                            FilingDetailView(id: id, client: client)
                        case .filingCompose:
                            FilingComposeView(client: client)
                        }
                    }
            }
            .environment(appState)
            .environment(router)
            .environment(uploadQueue)
            .environment(commentUploadQueue)
            .environment(soundService)
            .task { await handleLaunch() }
            .onChange(of: scenePhase) { _, phase in
                if phase == .background {
                    syncService.scheduleBackgroundRefresh()
                }
                if phase == .active {
                    Task {
                        await syncService.performSync()
                        await uploadQueue.processQueue()
                        await commentUploadQueue.processQueue()
                    }
                }
            }
        }
        .backgroundTask(.appRefresh(SyncService.backgroundTaskIdentifier)) {
            await syncService.performSync()
            await syncService.scheduleBackgroundRefresh()
        }
    }

    // MARK: - Launch

    private func handleLaunch() async {
        appDelegate.onDeviceToken = { [client] tokenData in
            let hex = tokenData.map { String(format: "%02x", $0) }.joined()
            Task {
                _ = try? await client.registerDeviceToken(
                    token: hex,
                    signer: Config.signerIdentity
                )
            }
        }

        appDelegate.onNotificationRoute = { [client, appState, router, syncService, cache] payload in
            let route = payload.route
            guard !route.isEmpty else { return }
            let segments = route.split(separator: "/", maxSplits: 1)
            let kind = segments.first.map(String.init)
            let entityId = segments.count > 1 ? String(segments[1]) : nil

            if let kind, let entityId {
                switch kind {
                case "filing":
                    if let dict = payload.filingDict,
                       let filing = Filing.from(pushPayload: dict) {
                        await MainActor.run { appState.cacheFiling(filing) }
                    }
                case "letter", "thought":
                    if let dict = payload.contentDict,
                       let item = ContentItem.from(pushPayload: dict) {
                        await MainActor.run { appState.cacheContentItem(item) }
                        try? await cache.save(item)
                    }
                default:
                    break
                }
            }

            if let destination = Router.Route.from(pushRoute: route) {
                await MainActor.run {
                    router.popToRoot()
                    router.navigate(to: destination)
                }
            }

            if let kind, let entityId {
                switch kind {
                case "filing":
                    do {
                        let filing = try await client.fetchFiling(id: entityId)
                        await MainActor.run { appState.cacheFiling(filing) }
                    } catch {
                        await MainActor.run { appState.markEntityFetchFailed(entityId) }
                    }
                case "letter", "thought":
                    do {
                        let item = try await client.fetchContentItem(id: entityId)
                        await MainActor.run { appState.cacheContentItem(item) }
                        try? await cache.save(item)
                    } catch {
                        await MainActor.run { appState.markEntityFetchFailed(entityId) }
                    }
                    if let comments = try? await client.fetchComments(contentId: entityId) {
                        await MainActor.run {
                            for comment in comments { appState.cacheComment(comment) }
                        }
                    }
                    await MainActor.run { appState.setCommentsLoaded(for: entityId) }
                default:
                    break
                }
            }

            await syncService.performSync()
        }

        appDelegate.onForegroundNotification = { [syncService] in
            Task { await syncService.performSync() }
        }

        appDelegate.flushBufferedToken()

        await SignatureCache().migrateFromCachesIfNeeded()

        let cached = await cache.loadAll()
        appState.updateCachedContent(cached)

        if cached.isEmpty {
            appState.lastSyncAt = nil
        }

        appDelegate.flushBufferedRoute()

        await syncService.performSync()
        syncService.scheduleBackgroundRefresh()

        await uploadQueue.processQueue()
        uploadQueue.startMonitoring()

        await commentUploadQueue.processQueue()
        commentUploadQueue.startMonitoring()

        await enrollPushNotifications()
    }

    // MARK: - Push Enrollment

    private func enrollPushNotifications() async {
        let center = UNUserNotificationCenter.current()
        do {
            let granted = try await center.requestAuthorization(options: [.alert, .sound, .badge])
            guard granted else { return }
        } catch {
            return
        }
        UIApplication.shared.registerForRemoteNotifications()
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

// MARK: - App Delegate

struct NotificationPayload: Sendable {
    let route: String
    let contentDict: [String: String]?
    let filingDict: [String: String]?

    init(userInfo: [AnyHashable: Any]) {
        route = userInfo["route"] as? String ?? ""

        if let raw = userInfo["content"] as? [String: Any] {
            var flat: [String: String] = [:]
            for (key, value) in raw {
                if let boolVal = value as? Bool {
                    flat[key] = boolVal ? "true" : "false"
                } else if let intVal = value as? Int {
                    flat[key] = String(intVal)
                } else if let strVal = value as? String {
                    flat[key] = strVal
                }
            }
            contentDict = flat
        } else {
            contentDict = nil
        }

        if let raw = userInfo["filing"] as? [String: Any] {
            var flat: [String: String] = [:]
            for (key, value) in raw {
                if let boolVal = value as? Bool {
                    flat[key] = boolVal ? "true" : "false"
                } else if let intVal = value as? Int {
                    flat[key] = String(intVal)
                } else if let strVal = value as? String {
                    flat[key] = strVal
                }
            }
            filingDict = flat
        } else {
            filingDict = nil
        }
    }
}

final class AppDelegate: NSObject, UIApplicationDelegate, UNUserNotificationCenterDelegate {
    var onDeviceToken: ((Data) -> Void)?
    var onNotificationRoute: ((NotificationPayload) async -> Void)?
    var onForegroundNotification: (() -> Void)?
    private var bufferedToken: Data?
    private var bufferedPayload: NotificationPayload?

    func application(
        _ application: UIApplication,
        didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]? = nil
    ) -> Bool {
        UNUserNotificationCenter.current().delegate = self
        return true
    }

    func application(
        _ application: UIApplication,
        didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data
    ) {
        if let handler = onDeviceToken {
            handler(deviceToken)
        } else {
            bufferedToken = deviceToken
        }
    }

    func application(
        _ application: UIApplication,
        didFailToRegisterForRemoteNotificationsWithError error: Error
    ) {
        Logger(subsystem: "dev.dineshd.exhibita", category: "push")
            .error("Push registration failed: \(error)")
    }

    func flushBufferedToken() {
        guard let token = bufferedToken, let handler = onDeviceToken else { return }
        handler(token)
        bufferedToken = nil
    }

    // MARK: - UNUserNotificationCenterDelegate

    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        didReceive response: UNNotificationResponse
    ) async {
        let userInfo = response.notification.request.content.userInfo
        guard userInfo["route"] is String else { return }
        let payload = NotificationPayload(userInfo: userInfo)
        if let handler = onNotificationRoute {
            await handler(payload)
        } else {
            bufferedPayload = payload
        }
    }

    func flushBufferedRoute() {
        guard let payload = bufferedPayload, let handler = onNotificationRoute else { return }
        Task { await handler(payload) }
        bufferedPayload = nil
    }

    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification
    ) async -> UNNotificationPresentationOptions {
        onForegroundNotification?()
        return [.banner, .sound]
    }
}
