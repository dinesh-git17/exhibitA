import Foundation
import Network
import os

@Observable final class CommentUploadQueue {
    private let client: ExhibitAClient
    private let appState: AppState
    private let logger = Logger(subsystem: "dev.dineshd.exhibita", category: "comment-upload")

    private var pendingJobs: [CommentUploadJob] = []
    private var isProcessing = false
    private var pathMonitor: NWPathMonitor?

    private static let storageDirectory: URL = {
        let appSupport = FileManager.default.urls(
            for: .applicationSupportDirectory,
            in: .userDomainMask
        )[0]
        return appSupport.appending(path: "comment-upload-queue")
    }()

    private static let storageURL: URL = {
        storageDirectory.appending(path: "pending.json")
    }()

    // MARK: - Initialization

    init(client: ExhibitAClient, appState: AppState) {
        self.client = client
        self.appState = appState
        loadPersistedJobs()
    }

    // MARK: - Public API

    func enqueue(contentId: String, signer: String, body: String) {
        let job = CommentUploadJob(
            id: UUID().uuidString,
            contentId: contentId,
            signer: signer,
            body: body,
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

        var remaining: [CommentUploadJob] = []

        for job in pendingJobs {
            let outcome = await attemptUpload(job)
            switch outcome {
            case .success(let record):
                appState.cacheComment(record)
            case .duplicate:
                break
            case .permanentFailure:
                logger.warning(
                    "Dropping unrecoverable comment upload: \(job.contentId)_\(job.signer)"
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
            queue: DispatchQueue(label: "dev.dineshd.exhibita.comment-upload.monitor")
        )
    }

    func stopMonitoring() {
        pathMonitor?.cancel()
        pathMonitor = nil
    }

    // MARK: - Upload Execution

    private enum UploadOutcome {
        case success(CommentRecord)
        case duplicate
        case permanentFailure
        case transient
    }

    private func attemptUpload(_ job: CommentUploadJob) async -> UploadOutcome {
        do {
            let record = try await client.createComment(
                contentId: job.contentId,
                signer: job.signer,
                body: job.body
            )
            return .success(record)
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
            pendingJobs = try JSONDecoder().decode([CommentUploadJob].self, from: data)
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
            logger.error("Failed to persist comment upload queue: \(error)")
        }
    }
}

// MARK: - Upload Job

extension CommentUploadQueue {
    nonisolated struct CommentUploadJob: Codable, Sendable {
        let id: String
        let contentId: String
        let signer: String
        let body: String
        let enqueuedAt: Date
    }
}
