import Foundation
import Network
import os

@Observable final class UploadQueue {
    private let client: ExhibitAClient
    private let signatureCache: SignatureCache
    private let appState: AppState
    private let logger = Logger(subsystem: "dev.dineshd.exhibita", category: "upload-queue")

    private var pendingJobs: [UploadJob] = []
    private var isProcessing = false
    private var pathMonitor: NWPathMonitor?

    private static let storageDirectory: URL = {
        let appSupport = FileManager.default.urls(
            for: .applicationSupportDirectory,
            in: .userDomainMask
        )[0]
        return appSupport.appending(path: "upload-queue")
    }()

    private static let storageURL: URL = {
        storageDirectory.appending(path: "pending.json")
    }()

    // MARK: - Initialization

    init(client: ExhibitAClient, signatureCache: SignatureCache, appState: AppState) {
        self.client = client
        self.signatureCache = signatureCache
        self.appState = appState
        loadPersistedJobs()
    }

    // MARK: - Public API

    func enqueue(contentId: String, signer: String) {
        let job = UploadJob(
            id: UUID().uuidString,
            contentId: contentId,
            signer: signer,
            enqueuedAt: .now
        )
        pendingJobs.append(job)
        persistQueue()
        Task { await processQueue() }
    }

    func processQueue() async {
        guard !isProcessing, !pendingJobs.isEmpty else { return }
        isProcessing = true
        defer { isProcessing = false }

        var remaining: [UploadJob] = []

        for job in pendingJobs {
            let outcome = await attemptUpload(job)
            switch outcome {
            case .success(let signedAt):
                appState.markSigned(
                    contentId: job.contentId,
                    signer: job.signer,
                    at: signedAt
                )
            case .duplicate:
                break
            case .permanentFailure:
                logger.warning(
                    "Dropping unrecoverable upload: \(job.contentId)_\(job.signer)"
                )
            case .transient:
                remaining.append(job)
            }
        }

        pendingJobs = remaining
        persistQueue()
    }

    func startMonitoring() {
        guard pathMonitor == nil else { return }
        let monitor = NWPathMonitor()
        pathMonitor = monitor
        monitor.pathUpdateHandler = { [weak self] path in
            guard path.status == .satisfied else { return }
            Task { @MainActor in
                await self?.processQueue()
            }
        }
        monitor.start(
            queue: DispatchQueue(label: "dev.dineshd.exhibita.upload-queue.monitor")
        )
    }

    func stopMonitoring() {
        pathMonitor?.cancel()
        pathMonitor = nil
    }

    // MARK: - Upload Execution

    private enum UploadOutcome {
        case success(signedAt: Date)
        case duplicate
        case permanentFailure
        case transient
    }

    private func attemptUpload(_ job: UploadJob) async -> UploadOutcome {
        guard let pngData = await signatureCache.load(
            contentId: job.contentId,
            signer: job.signer
        ) else {
            return .permanentFailure
        }

        do {
            let record = try await client.uploadSignature(
                contentId: job.contentId,
                signer: job.signer,
                png: pngData
            )
            return .success(signedAt: record.signedAt)
        } catch {
            return classifyError(error)
        }
    }

    private func classifyError(_ error: APIError) -> UploadOutcome {
        switch error {
        case .httpFailure(statusCode: 409, errorCode: _, message: _):
            return .duplicate
        case .networkFailure:
            return .transient
        case .httpFailure(statusCode: let code, errorCode: _, message: _)
            where code >= 500:
            return .transient
        default:
            return .permanentFailure
        }
    }

    // MARK: - Persistence

    private func loadPersistedJobs() {
        do {
            let data = try Data(contentsOf: Self.storageURL)
            pendingJobs = try JSONDecoder().decode([UploadJob].self, from: data)
        } catch {
            pendingJobs = []
        }
    }

    private func persistQueue() {
        do {
            let manager = FileManager.default
            if !manager.fileExists(atPath: Self.storageDirectory.path()) {
                try manager.createDirectory(
                    at: Self.storageDirectory,
                    withIntermediateDirectories: true
                )
            }
            let data = try JSONEncoder().encode(pendingJobs)
            try data.write(to: Self.storageURL, options: .atomic)
        } catch {
            logger.error("Failed to persist upload queue: \(error)")
        }
    }
}

// MARK: - Upload Job

extension UploadQueue {
    nonisolated struct UploadJob: Codable, Sendable {
        let id: String
        let contentId: String
        let signer: String
        let enqueuedAt: Date
    }
}
