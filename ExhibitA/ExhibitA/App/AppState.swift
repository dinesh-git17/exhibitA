import Foundation

/// Observable app state managing sync timestamps and unread content tracking.
/// Design Doc references: S7.4, S10.5.
@Observable final class AppState {
    // MARK: - Sync State

    var lastSyncAt: Date? {
        didSet { defaults.set(lastSyncAt, forKey: StorageKey.lastSyncAt) }
    }

    // MARK: - Content

    private(set) var cachedContent: [ContentItem] = []

    // MARK: - Unread Tracking

    private(set) var seenContentIDs: Set<String> = [] {
        didSet { persistSeenContentIDs() }
    }

    // MARK: - Comment State

    private(set) var cachedComments: [String: CommentRecord] = [:] {
        didSet { persistComments() }
    }

    // MARK: - Signature State

    private(set) var signedSignatures: [String: Date] = [:] {
        didSet { persistSignedSignatures() }
    }

    // MARK: - Initialization

    private let defaults: UserDefaults

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        lastSyncAt = defaults.object(forKey: StorageKey.lastSyncAt) as? Date
        seenContentIDs = Self.loadSeenContentIDs(from: defaults)
        signedSignatures = Self.loadSignedSignatures(from: defaults)
        cachedComments = Self.loadComments(from: defaults)
    }

    // MARK: - Unread API

    func hasBeenSeen(_ contentID: String) -> Bool {
        seenContentIDs.contains(contentID)
    }

    func markSeen(_ contentID: String) {
        seenContentIDs.insert(contentID)
    }

    func updateCachedContent(_ items: [ContentItem]) {
        cachedContent = items
    }

    // MARK: - Comment API

    func commentsForContent(_ contentId: String) -> [CommentRecord] {
        cachedComments.values
            .filter { $0.contentId == contentId }
            .sorted { $0.createdAt < $1.createdAt }
    }

    func comment(forContentId contentId: String, signer: String) -> CommentRecord? {
        cachedComments[commentKey(contentId: contentId, signer: signer)]
    }

    func cacheComment(_ comment: CommentRecord) {
        cachedComments[commentKey(contentId: comment.contentId, signer: comment.signer)] = comment
    }

    private func commentKey(contentId: String, signer: String) -> String {
        "\(contentId)_\(signer)"
    }

    // MARK: - Signature API

    func isSigned(contentId: String, signer: String) -> Bool {
        signedSignatures[signatureKey(contentId: contentId, signer: signer)] != nil
    }

    func signedDate(contentId: String, signer: String) -> Date? {
        signedSignatures[signatureKey(contentId: contentId, signer: signer)]
    }

    func markSigned(contentId: String, signer: String, at date: Date) {
        signedSignatures[signatureKey(contentId: contentId, signer: signer)] = date
    }

    private func signatureKey(contentId: String, signer: String) -> String {
        "\(contentId)_\(signer)"
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

    private func persistComments() {
        guard let data = try? JSONEncoder().encode(cachedComments) else { return }
        defaults.set(data, forKey: StorageKey.cachedComments)
    }

    private static func loadComments(from defaults: UserDefaults) -> [String: CommentRecord] {
        guard let data = defaults.data(forKey: StorageKey.cachedComments),
              let decoded = try? JSONDecoder().decode([String: CommentRecord].self, from: data)
        else {
            return [:]
        }
        return decoded
    }

    private func persistSignedSignatures() {
        guard let data = try? JSONEncoder().encode(signedSignatures) else { return }
        defaults.set(data, forKey: StorageKey.signedSignatures)
    }

    private static func loadSignedSignatures(from defaults: UserDefaults) -> [String: Date] {
        guard let data = defaults.data(forKey: StorageKey.signedSignatures),
              let decoded = try? JSONDecoder().decode([String: Date].self, from: data)
        else {
            return [:]
        }
        return decoded
    }
}

private enum StorageKey {
    static let lastSyncAt = "exhibit_a_last_sync_at"
    static let seenContentIDs = "exhibit_a_seen_content_ids"
    static let signedSignatures = "exhibit_a_signed_signatures"
    static let cachedComments = "exhibit_a_cached_comments"
}
