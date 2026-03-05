import AVFoundation
import os

/// Centralized sound playback authority for all UI cues.
/// Manages a global sound-enabled preference persisted in UserDefaults
/// and exposes named cue APIs consumed by feature surfaces.
@Observable final class SoundService {

    // MARK: - Cue Definitions

    enum Cue: String {
        case pageTurn = "page_turn"
        case signaturePlaced = "signature_placed"
    }

    // MARK: - Sound Preference

    var isSoundEnabled: Bool {
        didSet { defaults.set(isSoundEnabled, forKey: StorageKey.soundEnabled) }
    }

    // MARK: - Private State

    private let defaults: UserDefaults
    private var players: [Cue: AVAudioPlayer] = [:]
    private let logger = Logger(
        subsystem: "dev.dineshd.exhibita",
        category: "sound-service"
    )

    // MARK: - Initialization

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        defaults.register(defaults: [StorageKey.soundEnabled: true])
        isSoundEnabled = defaults.bool(forKey: StorageKey.soundEnabled)
        preparePlayers()
    }

    // MARK: - Playback

    func play(_ cue: Cue) {
        guard isSoundEnabled else { return }
        guard let player = players[cue] else { return }
        player.currentTime = 0
        player.play()
    }

    // MARK: - Player Setup

    private func preparePlayers() {
        for cue in [Cue.pageTurn, .signaturePlaced] {
            guard let url = Bundle.main.url(
                forResource: cue.rawValue,
                withExtension: "caf"
            ) else {
                logger.info("Audio asset not found: \(cue.rawValue).caf")
                continue
            }
            do {
                let player = try AVAudioPlayer(contentsOf: url)
                player.prepareToPlay()
                players[cue] = player
            } catch {
                logger.error(
                    "Failed to initialize player for \(cue.rawValue): \(error)"
                )
            }
        }
    }
}

// MARK: - Storage Keys

private enum StorageKey {
    static let soundEnabled = "exhibit_a_sound_enabled"
}
