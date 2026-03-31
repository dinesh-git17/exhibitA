import Foundation

// MARK: - API Error

nonisolated enum APIError: Error, Sendable {
    case invalidConfiguration(String)
    case missingCredentials
    case networkFailure(URLError)
    case httpFailure(statusCode: Int, errorCode: String?, message: String?)
    case decodingFailure(context: String)
    case invalidResponse
}

// MARK: - Shared Enums

nonisolated enum ContentType: String, Codable, Sendable {
    case contract
    case letter
    case thought
}

nonisolated enum SyncAction: String, Decodable, Sendable {
    case create
    case update
    case delete
}

// MARK: - Content

nonisolated struct ContentItem: Codable, Sendable, Identifiable {
    let id: String
    let type: ContentType
    let title: String?
    let subtitle: String?
    let body: String
    let articleNumber: String?
    let classification: String?
    let sectionOrder: Int
    let requiresSignature: Bool
    let createdAt: Date
    let updatedAt: Date
}

nonisolated struct ContentListResponse: Decodable, Sendable {
    let items: [ContentItem]
}

// MARK: - Signatures

nonisolated struct SignatureRecord: Decodable, Sendable, Identifiable {
    let id: String
    let contentId: String
    let signer: String
    let signedAt: Date
}

// MARK: - Sync

nonisolated struct SyncEntry: Decodable, Sendable, Identifiable {
    let id: Int
    let entityType: String
    let entityId: String
    let action: SyncAction
    let occurredAt: Date
}

nonisolated struct SyncResponse: Decodable, Sendable {
    let changes: [SyncEntry]
}

// MARK: - Device Token

nonisolated struct DeviceTokenRequest: Encodable, Sendable {
    let signer: String
    let token: String
}

nonisolated struct DeviceTokenResponse: Decodable, Sendable {
    let id: String
    let signer: String
    let token: String
    let registeredAt: Date
}

// MARK: - Comments

nonisolated struct CommentRecord: Codable, Sendable, Identifiable {
    let id: String
    let contentId: String
    let signer: String
    let body: String
    let createdAt: Date
}

nonisolated struct CommentCreateRequest: Encodable, Sendable {
    let contentId: String
    let signer: String
    let body: String
}

// MARK: - Filings

nonisolated enum FilingType: String, Codable, Sendable {
    case motion
    case objection
    case emergencyOrder = "emergency_order"
}

nonisolated enum RulingVerdict: String, Codable, Sendable {
    case granted
    case denied
    case sustained
    case overruled
}

nonisolated struct Filing: Codable, Sendable, Identifiable {
    let id: String
    let filingType: FilingType
    let filedBy: String
    let title: String
    let body: String
    let ruling: RulingVerdict?
    let rulingReason: String?
    let ruledBy: String?
    let ruledAt: Date?
    let createdAt: Date
    let updatedAt: Date
}

nonisolated struct FilingListResponse: Decodable, Sendable {
    let items: [Filing]
}

nonisolated struct FilingCreateRequest: Encodable, Sendable {
    let filingType: FilingType
    let filedBy: String
    let title: String
    let body: String
}

nonisolated struct RulingCreateRequest: Encodable, Sendable {
    let ruling: RulingVerdict
    let rulingReason: String
    let ruledBy: String
}

// MARK: - Push Payload Factories

extension ContentItem {
    static let payloadDateFormatter: ISO8601DateFormatter = {
        let f = ISO8601DateFormatter()
        f.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return f
    }()

    static func parseDate(_ value: String?) -> Date? {
        guard let str = value else { return nil }
        return payloadDateFormatter.date(from: str)
            ?? ISO8601DateFormatter().date(from: str)
    }

    static func from(pushPayload dict: [String: String]) -> ContentItem? {
        guard let id = dict["id"],
              let typeRaw = dict["type"],
              let type = ContentType(rawValue: typeRaw),
              let body = dict["body"]
        else { return nil }

        let createdAt = parseDate(dict["created_at"]) ?? .now
        let sectionOrder = dict["section_order"].flatMap(Int.init) ?? 0
        let requiresSignature = dict["requires_signature"] == "true"

        return ContentItem(
            id: id,
            type: type,
            title: dict["title"],
            subtitle: dict["subtitle"],
            body: body,
            articleNumber: nil,
            classification: nil,
            sectionOrder: sectionOrder,
            requiresSignature: requiresSignature,
            createdAt: createdAt,
            updatedAt: createdAt
        )
    }
}

extension Filing {
    static func from(pushPayload dict: [String: String]) -> Filing? {
        guard let id = dict["id"],
              let typeRaw = dict["filing_type"],
              let filingType = FilingType(rawValue: typeRaw),
              let title = dict["title"],
              let body = dict["body"]
        else { return nil }

        let createdAt = ContentItem.parseDate(dict["created_at"]) ?? .now

        return Filing(
            id: id,
            filingType: filingType,
            filedBy: dict["filed_by"] ?? "",
            title: title,
            body: body,
            ruling: nil,
            rulingReason: nil,
            ruledBy: nil,
            ruledAt: nil,
            createdAt: createdAt,
            updatedAt: createdAt
        )
    }
}

// MARK: - Error Envelope

nonisolated struct APIErrorEnvelope: Decodable, Sendable {
    let error: APIErrorDetail
}

nonisolated struct APIErrorDetail: Decodable, Sendable {
    let code: String
    let message: String
}
