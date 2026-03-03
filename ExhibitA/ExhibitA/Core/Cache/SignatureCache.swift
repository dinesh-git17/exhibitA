import Foundation
import os

/// Persists signature PNG data in the app caches directory.
/// Files named {contentId}_{signer}.png for deterministic lookup.
actor SignatureCache {
    private let directory: URL
    private let logger = Logger(subsystem: "dev.dineshd.exhibita", category: "cache.signatures")

    // MARK: - Initialization

    init() {
        let caches = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask)[0]
        directory = caches.appending(path: "signatures")
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
