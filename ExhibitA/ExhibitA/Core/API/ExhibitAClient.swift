import Foundation
import os

/// Authenticated API client for the Exhibit A backend.
/// All requests include Bearer token auth sourced from KeychainService.
/// All stored properties are immutable; URLSession is thread-safe.
final class ExhibitAClient: @unchecked Sendable {
    private let session: URLSession
    private let baseURL: URL
    private let decoder: JSONDecoder
    private let encoder: JSONEncoder
    private let dateFormatter: DateFormatter
    private let logger = Logger(subsystem: "dev.dineshd.exhibita", category: "api")

    private static let requestTimeout: TimeInterval = 30

    // MARK: - Initialization

    init(baseURL: URL, session: URLSession = .shared) {
        self.baseURL = baseURL
        self.session = session

        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd HH:mm:ss"
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = TimeZone(identifier: "UTC")
        dateFormatter = formatter

        let fractionalFormatter = DateFormatter()
        fractionalFormatter.dateFormat = "yyyy-MM-dd HH:mm:ss.SSSSSS"
        fractionalFormatter.locale = Locale(identifier: "en_US_POSIX")
        fractionalFormatter.timeZone = TimeZone(identifier: "UTC")

        let dec = JSONDecoder()
        dec.keyDecodingStrategy = .convertFromSnakeCase
        dec.dateDecodingStrategy = .custom { decoder in
            let container = try decoder.singleValueContainer()
            let string = try container.decode(String.self)
            let cleaned = string.replacingOccurrences(of: "T", with: " ")
                .replacingOccurrences(of: "+00:00", with: "")
                .replacingOccurrences(of: "Z", with: "")
            if let date = formatter.date(from: cleaned) { return date }
            if let date = fractionalFormatter.date(from: cleaned) { return date }
            throw DecodingError.dataCorruptedError(
                in: container,
                debugDescription: "Unrecognized date format: \(string)"
            )
        }
        decoder = dec

        let enc = JSONEncoder()
        enc.keyEncodingStrategy = .convertToSnakeCase
        enc.dateEncodingStrategy = .formatted(formatter)
        encoder = enc
    }

    // MARK: - Content

    func fetchContent(
        type: ContentType? = nil,
        since: Date? = nil,
    )
        async throws(APIError) -> [ContentItem]
    {
        var queryItems: [URLQueryItem] = []
        if let type {
            queryItems.append(URLQueryItem(name: "type", value: type.rawValue))
        }
        if let since {
            queryItems.append(URLQueryItem(name: "since", value: dateFormatter.string(from: since)))
        }

        let request = try makeAuthenticatedRequest(path: "/content", queryItems: queryItems)
        let (data, response) = try await performRequest(request)
        try validateStatus(response, data: data)
        let envelope: ContentListResponse = try decode(from: data)
        return envelope.items
    }

    func fetchContentItem(id: String) async throws(APIError) -> ContentItem {
        let request = try makeAuthenticatedRequest(path: "/content/\(id)")
        let (data, response) = try await performRequest(request)
        try validateStatus(response, data: data)
        return try decode(from: data)
    }

    func fetchContentBatch(ids: [String]) async throws(APIError) -> [ContentItem] {
        guard !ids.isEmpty else { return [] }
        var request = try makeAuthenticatedRequest(path: "/content/batch", method: "POST")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: ["ids": ids])
        } catch {
            throw .decodingFailure(context: "batch request encoding")
        }
        let (data, response) = try await performRequest(request)
        try validateStatus(response, data: data)
        let envelope: ContentListResponse = try decode(from: data)
        return envelope.items
    }

    // MARK: - Signatures

    func fetchSignatures(contentId: String) async throws(APIError) -> [SignatureRecord] {
        let request = try makeAuthenticatedRequest(path: "/content/\(contentId)/signatures")
        let (data, response) = try await performRequest(request)
        try validateStatus(response, data: data)
        return try decode(from: data)
    }

    func fetchSignatureImage(signatureId: String) async throws(APIError) -> Data {
        let request = try makeAuthenticatedRequest(path: "/signatures/\(signatureId)/image")
        let (data, response) = try await performRequest(request)
        try validateStatus(response, data: data)
        return data
    }

    func uploadSignature(
        contentId: String,
        signer: String,
        png: Data,
    )
        async throws(APIError) -> SignatureRecord
    {
        let boundary = UUID().uuidString
        var request = try makeAuthenticatedRequest(path: "/signatures", method: "POST")
        request.setValue(
            "multipart/form-data; boundary=\(boundary)",
            forHTTPHeaderField: "Content-Type",
        )
        request.httpBody = buildMultipartBody(
            fields: [
                (name: "content_id", value: contentId),
                (name: "signer", value: signer),
            ],
            fileField: "image",
            fileName: "signature.png",
            fileContentType: "image/png",
            fileData: png,
            boundary: boundary,
        )

        let (data, response) = try await performRequest(request)
        try validateStatus(response, data: data)
        return try decode(from: data)
    }

    // MARK: - Comments

    func fetchComments(contentId: String) async throws(APIError) -> [CommentRecord] {
        let request = try makeAuthenticatedRequest(path: "/content/\(contentId)/comments")
        let (data, response) = try await performRequest(request)
        try validateStatus(response, data: data)
        return try decode(from: data)
    }

    func createComment(
        contentId: String,
        signer: String,
        body: String,
    )
        async throws(APIError) -> CommentRecord
    {
        var request = try makeAuthenticatedRequest(path: "/comments", method: "POST")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let payload = CommentCreateRequest(contentId: contentId, signer: signer, body: body)
        do {
            request.httpBody = try encoder.encode(payload)
        } catch {
            throw .decodingFailure(context: "CommentCreateRequest encoding")
        }

        let (data, response) = try await performRequest(request)
        try validateStatus(response, data: data)
        return try decode(from: data)
    }

    // MARK: - Filings

    func fetchFilings() async throws(APIError) -> [Filing] {
        let request = try makeAuthenticatedRequest(path: "/filings")
        let (data, response) = try await performRequest(request)
        try validateStatus(response, data: data)
        let envelope: FilingListResponse = try decode(from: data)
        return envelope.items
    }

    func fetchFiling(id: String) async throws(APIError) -> Filing {
        let request = try makeAuthenticatedRequest(path: "/filings/\(id)")
        let (data, response) = try await performRequest(request)
        try validateStatus(response, data: data)
        return try decode(from: data)
    }

    func createFiling(
        type: FilingType,
        filedBy: String,
        title: String,
        body: String
    ) async throws(APIError) -> Filing {
        var request = try makeAuthenticatedRequest(path: "/filings", method: "POST")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let payload = FilingCreateRequest(
            filingType: type,
            filedBy: filedBy,
            title: title,
            body: body
        )
        do {
            request.httpBody = try encoder.encode(payload)
        } catch {
            throw .decodingFailure(context: "FilingCreateRequest encoding")
        }

        let (data, response) = try await performRequest(request)
        try validateStatus(response, data: data)
        return try decode(from: data)
    }

    func createRuling(
        filingId: String,
        ruling: RulingVerdict,
        reason: String,
        ruledBy: String
    ) async throws(APIError) -> Filing {
        var request = try makeAuthenticatedRequest(
            path: "/filings/\(filingId)/ruling",
            method: "POST"
        )
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let payload = RulingCreateRequest(
            ruling: ruling,
            rulingReason: reason,
            ruledBy: ruledBy
        )
        do {
            request.httpBody = try encoder.encode(payload)
        } catch {
            throw .decodingFailure(context: "RulingCreateRequest encoding")
        }

        let (data, response) = try await performRequest(request)
        try validateStatus(response, data: data)
        return try decode(from: data)
    }

    // MARK: - Sync

    func fetchSyncChanges(since: Date? = nil) async throws(APIError) -> [SyncEntry] {
        var queryItems: [URLQueryItem] = []
        if let since {
            queryItems.append(URLQueryItem(name: "since", value: dateFormatter.string(from: since)))
        }

        let request = try makeAuthenticatedRequest(path: "/sync", queryItems: queryItems)
        let (data, response) = try await performRequest(request)
        try validateStatus(response, data: data)
        let envelope: SyncResponse = try decode(from: data)
        return envelope.changes
    }

    // MARK: - Device Token

    func registerDeviceToken(
        token: String,
        signer: String,
    )
        async throws(APIError) -> DeviceTokenResponse
    {
        var request = try makeAuthenticatedRequest(path: "/device-tokens", method: "POST")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body = DeviceTokenRequest(signer: signer, token: token)
        do {
            request.httpBody = try encoder.encode(body)
        } catch {
            throw .decodingFailure(context: "DeviceTokenRequest encoding")
        }

        let (data, response) = try await performRequest(request)
        try validateStatus(response, data: data)
        return try decode(from: data)
    }

    // MARK: - Request Building

    private func makeURL(
        path: String,
        queryItems: [URLQueryItem] = [],
    )
        throws(APIError) -> URL
    {
        var components = URLComponents()
        components.scheme = baseURL.scheme
        components.host = baseURL.host()
        components.port = baseURL.port
        components.path = path

        if !queryItems.isEmpty {
            components.queryItems = queryItems
        }

        guard let url = components.url else {
            throw .invalidConfiguration("Failed to construct URL for path: \(path)")
        }
        return url
    }

    private func makeAuthenticatedRequest(
        path: String,
        method: String = "GET",
        queryItems: [URLQueryItem] = [],
    )
        throws(APIError) -> URLRequest
    {
        let apiKey: String
        do {
            apiKey = try KeychainService.retrieveAPIKey()
        } catch {
            throw .missingCredentials
        }

        let url = try makeURL(path: path, queryItems: queryItems)
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.timeoutInterval = Self.requestTimeout
        request.setValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        return request
    }

    // MARK: - Request Execution

    private func performRequest(
        _ request: URLRequest,
    )
        async throws(APIError) -> (Data, HTTPURLResponse)
    {
        logger.debug("API \(request.httpMethod ?? "GET") \(request.url?.path() ?? "")")

        let data: Data
        let response: URLResponse
        do {
            (data, response) = try await session.data(for: request)
        } catch let urlError as URLError {
            logger.error("Network failure: \(urlError.code.rawValue)")
            throw .networkFailure(urlError)
        } catch {
            throw .networkFailure(URLError(.unknown))
        }

        guard let httpResponse = response as? HTTPURLResponse else {
            throw .invalidResponse
        }

        logger.debug("API response: \(httpResponse.statusCode)")
        return (data, httpResponse)
    }

    // MARK: - Response Handling

    private func validateStatus(
        _ response: HTTPURLResponse,
        data: Data,
    )
        throws(APIError)
    {
        let status = response.statusCode
        guard (200 ..< 300).contains(status) else {
            let envelope = try? decoder.decode(APIErrorEnvelope.self, from: data)
            throw .httpFailure(
                statusCode: status,
                errorCode: envelope?.error.code,
                message: envelope?.error.message,
            )
        }
    }

    private func decode<T: Decodable>(from data: Data) throws(APIError) -> T {
        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            let context = String(describing: T.self)
            logger.error("Decoding failed for \(context)")
            throw .decodingFailure(context: context)
        }
    }

    // MARK: - Multipart Encoding

    private func buildMultipartBody(
        fields: [(name: String, value: String)],
        fileField: String,
        fileName: String,
        fileContentType: String,
        fileData: Data,
        boundary: String,
    )
        -> Data
    {
        var body = Data()

        for field in fields {
            body.append(Data("--\(boundary)\r\n".utf8))
            body.append(Data("Content-Disposition: form-data; name=\"\(field.name)\"\r\n\r\n".utf8))
            body.append(Data("\(field.value)\r\n".utf8))
        }

        body.append(Data("--\(boundary)\r\n".utf8))
        body.append(
            Data("Content-Disposition: form-data; name=\"\(fileField)\"; filename=\"\(fileName)\"\r\n".utf8),
        )
        body.append(Data("Content-Type: \(fileContentType)\r\n\r\n".utf8))
        body.append(fileData)
        body.append(Data("\r\n--\(boundary)--\r\n".utf8))

        return body
    }
}
