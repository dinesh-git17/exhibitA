import Foundation

/// Observable app state managing sync timestamps and unread content tracking.
/// Design Doc references: S7.4, S10.5.
@Observable final class AppState {
    // MARK: - Sync State

    var lastSyncAt: Date? {
        didSet { defaults.set(lastSyncAt, forKey: StorageKey.lastSyncAt) }
    }

    // MARK: - Unread Tracking

    private(set) var seenContentIDs: Set<String> = [] {
        didSet { persistSeenContentIDs() }
    }

    // MARK: - Initialization

    private let defaults: UserDefaults

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        lastSyncAt = defaults.object(forKey: StorageKey.lastSyncAt) as? Date
        seenContentIDs = Self.loadSeenContentIDs(from: defaults)
    }

    // MARK: - Unread API

    func hasBeenSeen(_ contentID: String) -> Bool {
        seenContentIDs.contains(contentID)
    }

    func markSeen(_ contentID: String) {
        seenContentIDs.insert(contentID)
    }

    // MARK: - Persistence Helpers

    private func persistSeenContentIDs() {
        guard let data = try? JSONEncoder().encode(seenContentIDs) else { return }
        defaults.set(data, forKey: StorageKey.seenContentIDs)
    }

    private static func loadSeenContentIDs(from defaults: UserDefaults) -> Set<String> {
        guard let data = defaults.data(forKey: StorageKey.seenContentIDs),
              let decoded = try? JSONDecoder().decode(Set<String>.self, from: data)
        else {
            return []
        }
        return decoded
    }
}

private enum StorageKey {
    static let lastSyncAt = "exhibit_a_last_sync_at"
    static let seenContentIDs = "exhibit_a_seen_content_ids"
}
