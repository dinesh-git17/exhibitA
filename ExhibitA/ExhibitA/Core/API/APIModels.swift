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

// MARK: - Error Envelope

nonisolated struct APIErrorEnvelope: Decodable, Sendable {
    let error: APIErrorDetail
}

nonisolated struct APIErrorDetail: Decodable, Sendable {
    let code: String
    let message: String
}
