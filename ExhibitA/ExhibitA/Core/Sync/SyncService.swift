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

    func performFullSync() async {
        let allContent: [ContentItem]
        do {
            allContent = try await client.fetchContent()
        } catch {
            logger.error("Full sync fetch failed: \(error)")
            return
        }

        await cache.removeAll()
        do {
            if !allContent.isEmpty {
                try await cache.save(allContent)
            }
        } catch {
            logger.error("Full sync cache write failed: \(error)")
            return
        }

        appState.updateCachedContent(allContent)
        await hydrateSignatures(content: allContent)
        await hydrateComments(content: allContent)
        appState.lastSyncAt = .now
    }

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
            let allContent = await cache.loadAll()
            appState.updateCachedContent(allContent)
            await hydrateSignatures(content: allContent)
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

        var fetched: [ContentItem]
        do {
            fetched = try await client.fetchContentBatch(ids: Array(idsToFetch))
        } catch {
            logger.warning("Batch fetch failed, falling back to parallel individual fetches: \(error)")
            fetched = await fetchIndividually(ids: idsToFetch)
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

        await hydrateSignatures(content: allContent)
        await hydrateComments(content: allContent)

        appState.lastSyncAt = .now

        logger.debug("Sync complete: \(fetched.count) updated, \(idsToDelete.count) deleted")
    }

    private func fetchIndividually(ids: Set<String>) async -> [ContentItem] {
        await withTaskGroup(of: ContentItem?.self) { group in
            for id in ids {
                group.addTask {
                    try? await self.client.fetchContentItem(id: id)
                }
            }
            var results: [ContentItem] = []
            for await item in group {
                if let item { results.append(item) }
            }
            return results
        }
    }

    // MARK: - Signature Hydration

    private func hydrateSignatures(content: [ContentItem]) async {
        let signable = content.filter { $0.requiresSignature }
        guard !signable.isEmpty else { return }

        let signatureCache = SignatureCache()

        let allRecords: [(String, [SignatureRecord])] = await withTaskGroup(
            of: (String, [SignatureRecord]).self
        ) { group in
            for item in signable {
                group.addTask {
                    let records = (try? await self.client.fetchSignatures(contentId: item.id)) ?? []
                    return (item.id, records)
                }
            }
            var results: [(String, [SignatureRecord])] = []
            for await result in group {
                results.append(result)
            }
            return results
        }

        for (contentId, records) in allRecords {
            for record in records {
                if !appState.isSigned(contentId: contentId, signer: record.signer) {
                    appState.markSigned(
                        contentId: contentId,
                        signer: record.signer,
                        at: record.signedAt
                    )
                }
            }
        }

        await withTaskGroup(of: Void.self) { group in
            for (contentId, records) in allRecords {
                for record in records {
                    group.addTask {
                        let cached = await signatureCache.load(
                            contentId: contentId,
                            signer: record.signer
                        )
                        guard cached == nil else { return }
                        if let imageData = try? await self.client.fetchSignatureImage(
                            signatureId: record.id
                        ) {
                            try? await signatureCache.save(
                                png: imageData,
                                contentId: contentId,
                                signer: record.signer
                            )
                        }
                    }
                }
            }
        }
    }

    // MARK: - Comment Hydration

    private func hydrateComments(content: [ContentItem]) async {
        let commentable = content.filter { $0.type == .letter || $0.type == .thought }
        guard !commentable.isEmpty else { return }

        await withTaskGroup(of: [CommentRecord].self) { group in
            for item in commentable {
                group.addTask {
                    (try? await self.client.fetchComments(contentId: item.id)) ?? []
                }
            }
            for await records in group {
                for record in records {
                    appState.cacheComment(record)
                }
            }
        }
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
