import Foundation
import Security

// MARK: - Keychain Error

nonisolated enum KeychainError: Error, Sendable {
    case unexpectedStatus(OSStatus)
    case itemNotFound
    case encodingFailed
}

// MARK: - Keychain Service

/// Secure credential storage backed by the iOS Keychain.
/// Uses kSecAttrAccessibleAfterFirstUnlock for background-safe access.
nonisolated enum KeychainService {
    private static let serviceName = "dev.dineshd.exhibita"
    private static let apiKeyAccount = "api_key"

    // MARK: - Public API

    static func saveAPIKey(_ key: String) throws(KeychainError) {
        guard let data = key.data(using: .utf8) else {
            throw .encodingFailed
        }

        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: serviceName,
            kSecAttrAccount as String: apiKeyAccount,
            kSecAttrAccessible as String: kSecAttrAccessibleAfterFirstUnlock,
            kSecValueData as String: data,
        ]

        let status = SecItemAdd(query as CFDictionary, nil)

        if status == errSecDuplicateItem {
            let searchQuery: [String: Any] = [
                kSecClass as String: kSecClassGenericPassword,
                kSecAttrService as String: serviceName,
                kSecAttrAccount as String: apiKeyAccount,
            ]
            let updateFields: [String: Any] = [kSecValueData as String: data]
            let updateStatus = SecItemUpdate(
                searchQuery as CFDictionary,
                updateFields as CFDictionary,
            )
            guard updateStatus == errSecSuccess else {
                throw .unexpectedStatus(updateStatus)
            }
        } else if status != errSecSuccess {
            throw .unexpectedStatus(status)
        }
    }

    static func retrieveAPIKey() throws(KeychainError) -> String {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: serviceName,
            kSecAttrAccount as String: apiKeyAccount,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne,
        ]

        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)

        if status == errSecItemNotFound {
            throw .itemNotFound
        }

        guard status == errSecSuccess,
              let data = result as? Data,
              let key = String(data: data, encoding: .utf8)
        else {
            throw .unexpectedStatus(status)
        }

        return key
    }

    static func deleteAPIKey() throws(KeychainError) {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: serviceName,
            kSecAttrAccount as String: apiKeyAccount,
        ]

        let status = SecItemDelete(query as CFDictionary)
        guard status == errSecSuccess || status == errSecItemNotFound else {
            throw .unexpectedStatus(status)
        }
    }

    /// Seeds the API key into the Keychain if not already present.
    /// Called once at app launch with the build-time injected key.
    static func seedAPIKeyIfNeeded(_ apiKey: String) {
        do {
            _ = try retrieveAPIKey()
        } catch KeychainError.itemNotFound {
            do {
                try saveAPIKey(apiKey)
            } catch {
                // Seed failure is non-fatal at launch; API calls will surface .missingCredentials
            }
        } catch {
            // Key already exists or transient keychain error; no action needed
        }
    }
}
