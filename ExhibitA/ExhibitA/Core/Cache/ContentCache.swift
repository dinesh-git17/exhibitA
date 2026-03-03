import Foundation
import os

/// Persists content entities as individual JSON files in the app caches directory.
/// One file per entity, named {id}.json, for granular offline-first reads and updates.
actor ContentCache {
    private let directory: URL
    private let encoder: JSONEncoder
    private let decoder: JSONDecoder
    private let logger = Logger(subsystem: "dev.dineshd.exhibita", category: "cache.content")

    // MARK: - Initialization

    init() {
        let caches = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask)[0]
        directory = caches.appending(path: "content")

        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd HH:mm:ss"
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = TimeZone(identifier: "UTC")

        let enc = JSONEncoder()
        enc.keyEncodingStrategy = .convertToSnakeCase
        enc.dateEncodingStrategy = .formatted(formatter)
        encoder = enc

        let dec = JSONDecoder()
        dec.keyDecodingStrategy = .convertFromSnakeCase
        dec.dateDecodingStrategy = .formatted(formatter)
        decoder = dec
    }

    // MARK: - Write

    func save(_ item: ContentItem) throws {
        try ensureDirectory()
        let data = try encoder.encode(item)
        let fileURL = directory.appending(path: "\(item.id).json")
        try data.write(to: fileURL, options: .atomic)
    }

    func save(_ items: [ContentItem]) throws {
        try ensureDirectory()
        for item in items {
            let data = try encoder.encode(item)
            let fileURL = directory.appending(path: "\(item.id).json")
            try data.write(to: fileURL, options: .atomic)
        }
    }

    // MARK: - Read

    func load(id: String) -> ContentItem? {
        let fileURL = directory.appending(path: "\(id).json")
        do {
            let data = try Data(contentsOf: fileURL)
            return try decoder.decode(ContentItem.self, from: data)
        } catch {
            return nil
        }
    }

    func loadAll() -> [ContentItem] {
        let manager = FileManager.default
        guard manager.fileExists(atPath: directory.path()) else { return [] }

        let files: [URL]
        do {
            files = try manager
                .contentsOfDirectory(at: directory, includingPropertiesForKeys: nil)
                .filter { $0.pathExtension == "json" }
        } catch {
            logger.error("Failed to list content cache directory")
            return []
        }

        var items: [ContentItem] = []
        for url in files {
            do {
                let data = try Data(contentsOf: url)
                let item = try decoder.decode(ContentItem.self, from: data)
                items.append(item)
            } catch {
                logger.warning("Skipped corrupt cache file: \(url.lastPathComponent)")
            }
        }
        return items
    }

    // MARK: - Delete

    func remove(id: String) {
        let fileURL = directory.appending(path: "\(id).json")
        try? FileManager.default.removeItem(at: fileURL)
    }

    func removeAll() {
        try? FileManager.default.removeItem(at: directory)
    }

    // MARK: - Private

    private func ensureDirectory() throws {
        let manager = FileManager.default
        if !manager.fileExists(atPath: directory.path()) {
            try manager.createDirectory(at: directory, withIntermediateDirectories: true)
        }
    }
}
