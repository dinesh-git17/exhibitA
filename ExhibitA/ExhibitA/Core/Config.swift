import Foundation

enum Config {
    // MARK: - Signer Identity

    static let signerIdentity: String = {
        guard let value = Bundle.main.infoDictionary?["SIGNER_IDENTITY"] as? String,
              !value.isEmpty,
              !value.hasPrefix("$(")
        else {
            let message = "SIGNER_IDENTITY not configured. Copy Config/*.xcconfig.example to *.xcconfig and set values."
            preconditionFailure(message)
        }
        return value
    }()

    // MARK: - API Key

    static let apiKey: String = {
        guard let value = Bundle.main.infoDictionary?["API_KEY"] as? String,
              !value.isEmpty,
              !value.hasPrefix("$(")
        else {
            let message = "API_KEY not configured. Copy Config/*.xcconfig.example to *.xcconfig and set values."
            preconditionFailure(message)
        }
        return value
    }()

    // MARK: - Base URL

    static let apiBaseURL: URL = {
        guard let raw = Bundle.main.infoDictionary?["API_BASE_URL"] as? String,
              !raw.isEmpty,
              !raw.hasPrefix("$("),
              let url = URL(string: raw)
        else {
            let message = "API_BASE_URL not configured or invalid. "
                + "Copy Config/*.xcconfig.example to *.xcconfig and set values."
            preconditionFailure(message)
        }
        return url
    }()
}
