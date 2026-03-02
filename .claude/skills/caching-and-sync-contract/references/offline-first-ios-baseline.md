# Offline-First iOS Baseline (2026)

## Sources

- Offline-first architecture with local source-of-truth and queued writes: https://developer.android.com/topic/architecture/data-layer/offline-first
- iOS app responsiveness thresholds (avoid long main-thread work): https://developer.apple.com/documentation/Xcode/improving-app-responsiveness
- Apple launch-time guidance (first frame target and startup discipline): https://developer.apple.com/videos/play/wwdc2019/423/
- Background networking (`URLSessionConfiguration.background`): https://developer.apple.com/documentation/foundation/urlsessionconfiguration/1411521-background
- Atomic persistence semantics (`Data.write(..., .atomic)`): https://developer.apple.com/documentation/foundation/nsdata/write%28tofile%3Aatomically%3A%29
- UserDefaults scope and lightweight preference storage guidance: https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/UserDefaults/AboutPreferenceDomains/AboutPreferenceDomains.html
- CloudKit sync engine state serialization patterns: https://developer.apple.com/videos/play/wwdc2023/10188/
- URL cache disk+memory behavior for cached resources: https://developer.apple.com/documentation/foundation/urlcache

## Architecture Decisions Locked By This Skill

1. Keep local cache as authoritative source of truth for UI reads.
2. Run network as synchronization pipeline only; no launch-time dependency.
3. Persist cache and signature assets to disk for offline continuity.
4. Enforce atomic writes to avoid partial/corrupt cache files.
5. Maintain explicit sync state machine and incremental sync cursor (`since` / last sync token).
6. Keep uploads and sync in background paths.
7. Preserve cached content on sync/upload failure and expose retry state.
8. Keep launch rendering bounded by a strict cache-first performance target.
9. Use UserDefaults for lightweight scalar/set state and file storage for durable content payloads.
10. Forbid time-based cache eviction; invalidate only from explicit sync responses.
