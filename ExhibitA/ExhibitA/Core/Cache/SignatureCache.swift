import Foundation
import os

/// Persists signature PNG data in Application Support (survives iOS cache purges).
/// Files named {contentId}_{signer}.png for deterministic lookup.
actor SignatureCache {
    private let directory: URL
    private let logger = Logger(subsystem: "dev.dineshd.exhibita", category: "cache.signatures")

    // MARK: - Initialization

    init() {
        let appSupport = FileManager.default.urls(
            for: .applicationSupportDirectory,
            in: .userDomainMask
        )[0]
        directory = appSupport.appending(path: "exhibita/signatures")
    }

    /// Migrate PNGs from the legacy Caches location if present.
    func migrateFromCachesIfNeeded() {
        let caches = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask)[0]
        let legacy = caches.appending(path: "signatures")
        let manager = FileManager.default

        guard manager.fileExists(atPath: legacy.path()) else { return }

        do {
            try ensureDirectory()
            let files = try manager.contentsOfDirectory(atPath: legacy.path())
            for file in files where file.hasSuffix(".png") {
                let src = legacy.appending(path: file)
                let dst = directory.appending(path: file)
                if !manager.fileExists(atPath: dst.path()) {
                    try manager.copyItem(at: src, to: dst)
                }
            }
            try manager.removeItem(at: legacy)
            logger.debug("Migrated signature PNGs from Caches to Application Support")
        } catch {
            logger.warning("Signature cache migration failed: \(error)")
        }
    }

    // MARK: - Write

    func save(png: Data, contentId: String, signer: String) throws {
        guard !png.isEmpty else { return }
        try ensureDirectory()
        let fileURL = fileURL(contentId: contentId, signer: signer)
        try png.write(to: fileURL, options: .atomic)
    }

    // MARK: - Read

    func load(contentId: String, signer: String) -> Data? {
        let url = fileURL(contentId: contentId, signer: signer)
        do {
            let data = try Data(contentsOf: url)
            return data.isEmpty ? nil : data
        } catch {
            return nil
        }
    }

    // MARK: - Delete

    func remove(contentId: String, signer: String) {
        let url = fileURL(contentId: contentId, signer: signer)
        try? FileManager.default.removeItem(at: url)
    }

    func removeAll() {
        try? FileManager.default.removeItem(at: directory)
    }

    // MARK: - Private

    private func fileURL(contentId: String, signer: String) -> URL {
        directory.appending(path: "\(contentId)_\(signer).png")
    }

    private func ensureDirectory() throws {
        let manager = FileManager.default
        if !manager.fileExists(atPath: directory.path()) {
            try manager.createDirectory(at: directory, withIntermediateDirectories: true)
        }
    }
}
