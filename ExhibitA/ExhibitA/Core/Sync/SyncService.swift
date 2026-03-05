import BackgroundTasks
import Foundation
import os

final class SyncService {

    static let backgroundTaskIdentifier = "com.exhibita.app.refresh"

    private static let refreshInterval: TimeInterval = 15 * 60

    private let client: ExhibitAClient
    private let cache: ContentCache
    private let appState: AppState
    private let logger = Logger(subsystem: "dev.dineshd.exhibita", category: "sync")

    init(client: ExhibitAClient, cache: ContentCache, appState: AppState) {
        self.client = client
        self.cache = cache
        self.appState = appState
    }

    // MARK: - Sync

    func performSync() async {
        let since = appState.lastSyncAt

        let changes: [SyncEntry]
        do {
            changes = try await client.fetchSyncChanges(since: since)
        } catch {
            logger.error("Sync delta fetch failed: \(error)")
            return
        }

        if changes.isEmpty {
            appState.lastSyncAt = .now
            return
        }

        var idsToFetch: Set<String> = []
        var idsToDelete: Set<String> = []

        for entry in changes where entry.entityType == "content" {
            switch entry.action {
            case .create, .update:
                idsToFetch.insert(entry.entityId)
                idsToDelete.remove(entry.entityId)
            case .delete:
                idsToDelete.insert(entry.entityId)
                idsToFetch.remove(entry.entityId)
            }
        }

        var fetched: [ContentItem] = []
        for id in idsToFetch {
            do {
                let item = try await client.fetchContentItem(id: id)
                fetched.append(item)
            } catch {
                logger.warning("Content fetch skipped for \(id): \(error)")
            }
        }

        do {
            if !fetched.isEmpty {
                try await cache.save(fetched)
            }
            for id in idsToDelete {
                await cache.remove(id: id)
            }
        } catch {
            logger.error("Cache write failed, preserving previous snapshot")
            return
        }

        let allContent = await cache.loadAll()
        appState.updateCachedContent(allContent)
        appState.lastSyncAt = .now

        logger.debug("Sync complete: \(fetched.count) updated, \(idsToDelete.count) deleted")
    }

    // MARK: - Background Refresh

    func scheduleBackgroundRefresh() {
        let request = BGAppRefreshTaskRequest(identifier: Self.backgroundTaskIdentifier)
        request.earliestBeginDate = Date(timeIntervalSinceNow: Self.refreshInterval)
        do {
            try BGTaskScheduler.shared.submit(request)
        } catch {
            logger.warning("Background refresh scheduling failed: \(error)")
        }
    }
}
