# 2026 Platform Standards — Detailed Reference

## iOS Platform

### SwiftUI (2026)

- Production-ready for all new apps. ~70% of new apps use SwiftUI primary.
- UIKit remains necessary for: UIPageViewController (page curl), complex collection views,
  advanced gesture handling, PencilKit canvas hosting.
- Use UIViewRepresentable / UIViewControllerRepresentable to bridge UIKit into SwiftUI.
- Liquid Glass design system (iOS 26) adopts automatically on recompile.

### Observation Framework

- `@Observable` macro (iOS 17+) is the standard. Replaces `ObservableObject` + `@Published`.
- Fine-grained reactivity: only views reading a changed property re-render.
- Use `@State` for view-local ownership of `@Observable` classes.
- Use `@Environment` for dependency injection of shared models.
- Use `@Bindable` to create bindings from `@Observable` properties.
- Combine is NOT deprecated but narrowed to continuous event streams (debounce, throttle).
- TCA is appropriate for complex apps but unnecessary for Exhibit A's scale.

### Navigation

- `NavigationStack` + `NavigationPath` (iOS 16+). `NavigationView` is deprecated.
- Route enum pattern: `enum Route: Hashable { case detail(id: UUID), case settings }`.
- Router class marked `@Observable`, injected via `@Environment`.
- Deep linking via `NavigationPath` manipulation.

### Persistence

**SwiftData** (iOS 17+):

- Appropriate for simple flat models. SwiftUI-native with `@Query`.
- Known issues: memory problems with relationship `.count`, migration fragility,
  `@Query` Release-mode crashes (iOS 18.3), no group-by queries.
- Acceptable for Exhibit A's simple content + signature models.

**GRDB.swift**:

- Production-grade SQLite wrapper. `ValueObservation` for live SwiftUI queries.
- Better performance, fewer bugs, full SQL control.
- Recommended if SwiftData issues block development.

**JSON file caching**:

- Acceptable for read-mostly caching of small API responses.
- No query capability, no observation. Simplest possible approach.

### Rich Text

- Native `Text` markdown: bold, italic, code, links only. No headings, lists, tables.
- `AttributedString` (iOS 15+): More formatting, Markdown parsing built in.
- **Textual** (gonzalezreal): Successor to MarkdownUI. `InlineText` + `StructuredText`.
  Full markdown (headings, lists, code blocks, tables). Best pure-SwiftUI option.
- iOS 26 adds native `WebView` in SwiftUI (no UIViewRepresentable needed).

### Signature Capture

- PencilKit `PKCanvasView` is the standard. No meaningful alternatives.
- Set `drawingPolicy = .anyInput` for finger drawing support.
- Configure tool: `PKInkingTool(.pen, color: .black, width: 2)`.
- Disable tool picker for signature context.
- Export: `PKDrawing` → `UIImage` → PNG Data.
- Custom UIViewRepresentable wrapper: ~50-80 lines. Zero dependencies.

### Security

- Keychain for all secrets (tokens, API keys). AES-256-GCM, hardware-backed.
- `kSecAttrAccessibleAfterFirstUnlock` for tokens needed in background sync.
- iOS encrypts all data at rest by default (file-level, tied to device passcode).
- `FileProtectionType.complete` on sensitive files for extra protection.
- Certificate pinning: skip for TestFlight app. ATS enforces TLS 1.2+ already.
- No plaintext secrets in UserDefaults, plists, or bundle.

### Push Notifications

- APNs HTTP/2 provider API is the only supported path. Legacy binary protocol retired.
- Token-based (JWT) auth preferred: keys don't expire, single key for all apps.
- Device tokens can change — send latest on every app launch.
- Payload limit: 4KB.

### Background Work

- `BGAppRefreshTask`: ~30 seconds, for quick content refresh. iOS 13+.
- `BGProcessingTask`: Minutes, requires charging/idle. iOS 13+.
- `BGContinuedProcessingTask`: Until completion, user-initiated. iOS 26+ (new).
- Register handlers immediately at app launch.
- Scheduling is advisory — system determines actual timing.
- For time-critical sync, use silent push notifications as trigger.

### Package Management

- SPM is the universal standard. Integrated in Xcode, no external tools.
- CocoaPods Trunk becomes permanently read-only December 2, 2026.
- Carthage is effectively abandoned.
- Pin exact versions. Commit `Package.resolved` to source control.

### Linting & Formatting

- SwiftLint 0.58+: 200+ rules, 30% faster via SwiftSyntax optimizations.
- SwiftFormat (Nick Lockwood): auto-formatting complement to SwiftLint.
- Configure both via dotfiles at project root.

### Testing

- Swift Testing (WWDC 2024): `#expect()`, native async, parallel, parameterized.
- Use for all new unit tests and business logic.
- XCTest: retained for UI tests (`XCUITest`) and performance tests only.
- Both coexist in a single test target.
- Test ViewModels and logic, not SwiftUI view hierarchy.

### CI

- Xcode Cloud: 25 free hours/month with Apple Developer Program ($99/year).
- Zero config for signing, provisioning, TestFlight deployment.
- GitHub Actions: add only for non-Apple needs (backend CI, linting).

## Backend Platform

### FastAPI

- Version 0.128+, actively maintained. Pydantic v2 (Rust core) integrated.
- Native async. Automatic OpenAPI docs. Jinja2 template support built in.
- Deploy with Uvicorn (single worker for two-user load).

### SQLite (Server)

- SQLite renaissance in 2026. Appropriate for small server apps.
- WAL mode: concurrent reads + single writer. 500-1000+ writes/sec.
- Litestream: continuous WAL replication to S3. Zero-downtime backups.
- `aiosqlite`: async wrapper for FastAPI integration.

### Auth Patterns

- **API (mobile app)**: Pre-generated API key per user, hashed, stored in env/db.
  Constant-time comparison. No JWT needed at this scale.
- **Admin panel**: Session cookie, server-side session in SQLite. HttpOnly, Secure,
  SameSite=Strict. 7-day expiry.
- JWT is overkill. OAuth2/OIDC is overkill. API key + session cookie covers everything.

### Admin Panel

- Jinja2 templates rendered by FastAPI. HTMX 2.x (14kB, no build step) for dynamic
  behavior (form submission, inline editing, partial updates).
- No React, Vue, or Angular. No node_modules. No bundler.
- CSS: classless framework (Pico CSS, Simple.css) or inline Tailwind CDN.

### APNS (Server-Side)

- `aioapns`: async, HTTP/2, token-based JWT. 1.3k notifications/sec on single core.
- Load `.p8` key file path, key ID, team ID from environment variables.
- Maintain persistent HTTP/2 connections. Do not open/close per request.
- Reuse JWT tokens for their 1-hour validity window.

### Deployment

- Systemd unit file: auto-restart, start on boot.
- Caddy reverse proxy: automatic HTTPS via Let's Encrypt. Minimal config.
- Single Uvicorn worker (two-user load does not justify multi-process).
- Docker adds complexity disproportionate to the app's scale. Skip it.

### Observability

- structlog: JSON output in prod, pretty-print in dev. Request correlation IDs.
- `/health` endpoint returning 200 with basic status.
- Structured error logging for unhandled exceptions.
- Full stacks (Prometheus/Grafana/Jaeger) are unjustified overhead.

### Security Scanning

- GitHub Dependabot: free, baseline vulnerability alerting.
- Snyk free tier: deeper SCA analysis.
- Pin versions. Review dependency updates before merging.
