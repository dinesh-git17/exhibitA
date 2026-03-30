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
    private var isSyncing = false

    init(client: ExhibitAClient, cache: ContentCache, appState: AppState) {
        self.client = client
        self.cache = cache
        self.appState = appState
    }

    // MARK: - Sync

    func performFullSync() async {
        let start = ContinuousClock.now
        logger.info("Full sync started")

        let allContent: [ContentItem]
        do {
            allContent = try await client.fetchContent()
        } catch {
            logger.error("Full sync fetch failed: \(error)")
            await hydrateFilings()
            return
        }

        do {
            if !allContent.isEmpty {
                try await cache.save(allContent)
            }
        } catch {
            logger.error("Full sync cache write failed: \(error)")
        }

        appState.updateCachedContent(allContent)
        appState.lastSyncAt = .now

        await hydrateSignatures(content: allContent)
        await hydrateComments(content: allContent)
        await hydrateFilings()

        let elapsed = ContinuousClock.now - start
        logger.info("Full sync complete: \(allContent.count) items in \(elapsed)")
    }

    func performSync() async {
        guard !isSyncing else {
            logger.debug("Sync already in progress, skipping")
            return
        }
        isSyncing = true
        defer { isSyncing = false }

        let start = ContinuousClock.now
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
            let allContent = await cache.loadAll()
            appState.updateCachedContent(allContent)
            await hydrateSignatures(content: allContent)
            await hydrateFilings()
            let elapsed = ContinuousClock.now - start
            logger.debug("Delta sync (no changes) in \(elapsed)")
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
        appState.lastSyncAt = .now

        await hydrateSignatures(content: allContent)
        await hydrateComments(content: allContent)
        await hydrateFilings()

        let elapsed = ContinuousClock.now - start
        logger.debug("Delta sync: \(fetched.count) updated, \(idsToDelete.count) deleted in \(elapsed)")
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

    private static let maxConcurrentFetches = 3

    // MARK: - Signature Hydration

    private func hydrateSignatures(content: [ContentItem]) async {
        let signable = content.filter { $0.requiresSignature }
        guard !signable.isEmpty else { return }

        let signatureCache = SignatureCache()

        var allRecords: [(String, [SignatureRecord])] = []
        await withTaskGroup(of: (String, [SignatureRecord])?.self) { group in
            for item in signable {
                group.addTask {
                    guard let records = try? await self.client.fetchSignatures(contentId: item.id)
                    else { return nil }
                    return (item.id, records)
                }
            }
            for await result in group {
                if let result { allRecords.append(result) }
            }
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

        var downloads: [(contentId: String, record: SignatureRecord)] = []
        for (contentId, records) in allRecords {
            for record in records {
                let onDisk = await signatureCache.exists(
                    contentId: contentId,
                    signer: record.signer
                )
                if !onDisk {
                    downloads.append((contentId, record))
                }
            }
        }

        guard !downloads.isEmpty else {
            logger.debug("Signature hydration: all PNGs on disk, 0 downloads")
            return
        }

        let start = ContinuousClock.now
        logger.debug("Downloading \(downloads.count) missing signature PNGs")

        await withTaskGroup(of: Void.self) { group in
            var active = 0
            for download in downloads {
                if active >= Self.maxConcurrentFetches {
                    await group.next()
                    active -= 1
                }
                active += 1
                group.addTask {
                    do {
                        let imageData = try await self.client.fetchSignatureImage(
                            signatureId: download.record.id
                        )
                        try await signatureCache.save(
                            png: imageData,
                            contentId: download.contentId,
                            signer: download.record.signer
                        )
                        await MainActor.run {
                            self.appState.signalSignatureImageAvailable()
                        }
                        self.logger.debug("Downloaded signature: \(download.contentId)_\(download.record.signer)")
                    } catch {
                        self.logger.error(
                            "Signature image download failed for \(download.contentId)_\(download.record.signer): \(error)"
                        )
                    }
                }
            }
        }

        let elapsed = ContinuousClock.now - start
        logger.debug("Signature hydration: \(downloads.count) downloaded in \(elapsed)")
    }

    // MARK: - Filing Hydration

    private func hydrateFilings() async {
        do {
            let filings = try await client.fetchFilings()
            appState.updateCachedFilings(filings)
        } catch {
            logger.error("Filing hydration failed: \(error)")
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
