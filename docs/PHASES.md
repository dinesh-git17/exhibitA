# Implementation Roadmap -- Exhibit A

**Source Document:** `docs/exhibit-a-design-doc.md` **Generated:** 2026-03-02 **Total Phases:** 9 **Total Epics:** 23

---

## Phase Summary

| Phase | Class          | Name                              | Epics | Depends On   | Entry Gate                                                        | Exit Gate                                                                            |
| ----- | -------------- | --------------------------------- | ----- | ------------ | ----------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| 0     | Infrastructure | Backend Foundation                | 3     | None         | VPS accessible; Python 3.13+ available; APNS P8 key generated    | Health endpoint returns 200; all API endpoints respond; auth enforced; Litestream on  |
| 1     | Infrastructure | Admin Panel                       | 2     | Phase 0      | Phase 0 exit criteria met                                        | Admin login works; dashboard renders; CRUD functional; APNS push fires               |
| 2     | Infrastructure | iOS Foundation                    | 5     | Phase 1      | Phase 1 exit criteria met; Xcode 26+ installed                   | Project compiles; tokens defined; state/router work; API client fetches; components render |
| 3     | Feature        | Home Screen                       | 1     | Phase 2      | Phase 2 exit criteria met                                        | Home screen renders per S2.1; cards navigate; unread badges display                  |
| 4     | Feature        | Filed Letters                     | 2     | Phase 3      | Phase 3 exit criteria met                                        | Letter list and detail render; markdown body displays; navigation works              |
| 5     | Feature        | Sealed Thoughts                   | 2     | Phase 3      | Phase 3 exit criteria met                                        | Thought list and detail render; plain text centered; navigation works                |
| 6     | Feature        | Contract Book and Signatures      | 4     | Phase 4, 5   | Phase 4 and 5 exit criteria met                                  | Page-curl works; articles paginate; signatures sign and upload; final page renders   |
| 7     | Integration    | Sync, Push, and Offline           | 2     | Phase 6      | Phase 6 exit criteria met                                        | Sync-on-launch works; BGAppRefreshTask runs; push deep-links; offline upload retries |
| 8     | Integration    | Sound, Haptics, and Animation     | 2     | Phase 7      | Phase 7 exit criteria met                                        | Sounds play and toggle; haptics fire; animations render at 60fps                     |

## Dependency Graph

```
Phase 0 --> Phase 1 --> Phase 2 --> Phase 3 --> Phase 4 --> Phase 6 --> Phase 7 --> Phase 8
                                          \--> Phase 5 --/
```

---

## Phase 0: Backend Foundation

**Class:** Infrastructure **Depends on:** None **Design doc sections:** S7.1, S7.2, S7.3, S7.3.1, S7.3.2, S7.3.3, S10.7,
S10.10, S10.11, S15.1

### Entry Criteria

- VPS (`157.180.94.145`) accessible via SSH
- Python 3.13+ and `uv` available on VPS
- APNS P8 key generated from Apple Developer portal and stored on VPS
- Repository cloned to VPS at `/opt/exhibit-a/`

### Exit Criteria

- `GET /health` returns 200
- All SQLite tables created with correct schema and constraints
- All app-facing API endpoints respond with correct schemas per S7.3.1
- Bearer token auth rejects unauthenticated requests with 401
- Caddy proxies HTTPS at `exhibita.dineshd.dev` to `localhost:8001`
- Systemd service restarts FastAPI on failure
- Litestream replicates SQLite WAL to Backblaze B2
- `ruff format --check && ruff check && mypy --strict` pass
- `pytest` smoke tests pass for all endpoints
- `scripts/protocol-zero.sh` exits 0
- `scripts/check-em-dashes.sh` exits 0

### Epics

#### E0.1: Scaffold FastAPI backend with SQLite schema and repository scripts

**Scope:** Project directory structure at `/opt/exhibit-a/`, Python environment with `uv`, FastAPI app factory, SQLite
WAL database with full schema per S7.2, Pydantic settings, structlog configuration, health endpoint, and repository lint
scripts. **Deliverable:** FastAPI app starts on port 8001, SQLite WAL initialized with all tables and indexes, health
endpoint responds, lint scripts executable. **Files touched:**

- `requirements.txt` (create)
- `app/__init__.py` (create)
- `app/__main__.py` (create)
- `app/config.py` (create)
- `app/db.py` (create)
- `app/models.py` (create)
- `start.sh` (create)
- `.env.example` (create)
- `scripts/protocol-zero.sh` (create)
- `scripts/check-em-dashes.sh` (create)

**Acceptance criteria:**

- `python -m app` starts Uvicorn on port 8001
- `GET /health` returns `{"status": "ok"}` with 200
- SQLite database created in WAL mode with all 6 tables and 4 indexes per S7.2
- `ruff format --check && ruff check && mypy --strict` pass
- Both scripts exit 0 on a clean repository

#### E0.2: Implement content, signature, sync, and device-token API endpoints

**Scope:** All app-facing REST endpoints per S7.3: content retrieval with type and since filtering, single content
fetch, per-contract signature retrieval, raw signature PNG serving, signature upload via multipart, sync log query, and
device token registration. Response schemas per S7.3.1, error format per S7.3.2, HTTP status codes per S7.3.3.
**Deliverable:** All app-facing API endpoints respond with correct data and error envelopes. **Files touched:**

- `app/routes/__init__.py` (create)
- `app/routes/content.py` (create)
- `app/routes/signatures.py` (create)
- `app/routes/devices.py` (create)

**Acceptance criteria:**

- `GET /content` returns `{"items": [...]}` ordered by type and section_order
- `GET /content?type=contract` filters correctly
- `GET /content?since=<timestamp>` returns only items updated after timestamp
- `POST /signatures` accepts multipart PNG (max 1MB) and returns 201
- `GET /signatures/{id}/image` returns raw PNG with `Content-Type: image/png`
- `GET /sync?since=<timestamp>` returns `{"changes": [...]}`
- `POST /device-tokens` stores token and returns 201
- Duplicate signature returns 409 with `ALREADY_SIGNED` error code
- All error responses use the envelope format from S7.3.2

#### E0.3: Add auth middleware and deployment configuration

**Scope:** Bearer token authentication middleware with bcrypt/argon2 hash comparison and constant-time validation per
S10.7. API key generation and seeding for both signers. Caddy reverse proxy configuration for `exhibita.dineshd.dev`.
Systemd service unit for single Uvicorn worker on port 8001. Litestream configuration for continuous SQLite WAL
replication to Backblaze B2. **Deliverable:** All app-facing endpoints require valid Bearer token; production deployment
operational with HTTPS, process management, and backup. **Files touched:**

- `app/auth.py` (create)
- `litestream.yml` (create)

**Acceptance criteria:**

- Requests without `Authorization` header return 401 `UNAUTHORIZED`
- Requests with invalid Bearer token return 401
- Valid Bearer token grants access; server identifies signer from key
- `POST /signatures` rejects mismatched signer identity with 400 `INVALID_SIGNER`
- Caddy serves HTTPS at `exhibita.dineshd.dev` with auto-renewed TLS
- Systemd restarts FastAPI within 5 seconds of process exit
- Litestream replicates WAL frames to Backblaze B2 within 60 seconds

---

## Phase 1: Admin Panel

**Class:** Infrastructure **Depends on:** Phase 0 **Design doc sections:** S9.1, S9.2, S9.3, S9.4, S9.5, S9.6, S9.7,
S9.8

### Entry Criteria

- Phase 0 exit criteria met
- Backend running on VPS with all API endpoints operational
- API keys generated and stored for both signers

### Exit Criteria

- Admin login authenticates with API key and creates session cookie
- Session cookie is `HttpOnly`, `Secure`, `SameSite=Strict` with 7-day expiry
- Dashboard displays content counts and recent filings
- Content CRUD works for contracts, letters, and thoughts
- Delete requires confirmation
- APNS push notification fires on content creation with correct copy per type
- `ruff format --check && ruff check && mypy --strict` pass
- `pytest` tests pass

### Epics

#### E1.1: Implement admin route handlers, session auth, APNS client, and core templates

**Scope:** All admin route handlers per S9.8: login, session management, dashboard, content list, create/edit/delete for
all three content types, and reorder support. Session-based auth with API key login per S9.2 (bcrypt hash comparison,
SQLite session store, cookie attributes). APNS client per S9.6 with JWT auth over HTTP/2 for push on content creation.
Base layout template, login form, dashboard summary, and navigation/flash components. **Deliverable:** Admin login flow
works, dashboard displays content summary, all content CRUD route handlers respond, and APNS push fires on content
creation. **Files touched:**

- `app/routes/admin.py` (create)
- `app/apns.py` (create)
- `app/templates/base.html` (create)
- `app/templates/login.html` (create)
- `app/templates/dashboard.html` (create)
- `app/templates/components/nav.html` (create)
- `app/templates/components/flash.html` (create)

**Acceptance criteria:**

- `GET /admin` redirects to `/admin/login` when unauthenticated
- Valid API key at `POST /admin/login` creates session and redirects to dashboard
- Dashboard shows counts for contracts, letters, thoughts, and signatures
- All CRUD endpoints create, read, update, and delete content records
- APNS push sends with correct notification copy per content type (S9.6)
- Failed APNS pushes are logged but do not block content creation

#### E1.2: Build content management templates and admin styling

**Scope:** Content list template grouped by type with edit/delete actions per S9.5. Unified content form template
adapting to content type per S9.4 (contract fields: article_number, title, body, requires_signature, position; letter
fields: title, subtitle, classification dropdown, markdown body, position; thought fields: body, position). Content row
component. Admin CSS styling with legal-warmth aesthetic per S9.9. HTMX for dynamic form behavior (markdown preview,
delete confirmation). **Deliverable:** All admin templates render correctly with HTMX dynamic forms and legal-themed
styling. **Files touched:**

- `app/templates/content_list.html` (create)
- `app/templates/content_form.html` (create)
- `app/templates/components/content_row.html` (create)
- `app/static/admin.css` (create)
- `app/static/htmx.min.js` (create)

**Acceptance criteria:**

- Content list displays items grouped by type with title, date, and position
- Contract form includes article_number, title, body, requires_signature, position fields
- Letter form includes classification dropdown with all 9 options from S9.4
- Thought form is minimal: body text area with character count and position
- Edit forms pre-populate with existing values
- Delete shows confirmation modal before proceeding
- HTMX swaps render markdown preview on letter body keyup

---

## Phase 2: iOS Foundation

**Class:** Infrastructure **Depends on:** Phase 1 **Design doc sections:** S6.1, S6.2, S6.3, S6.4, S6.5, S6.7, S8.1,
S8.2, S10.1, S10.3, S10.5, S10.7, S10.9

### Entry Criteria

- Phase 1 exit criteria met
- Xcode with iOS 26+ SDK installed
- Apple Developer account active for code signing and TestFlight

### Exit Criteria

- Xcode project compiles and launches on iOS 26 simulator
- Liquid Glass suppressed with opaque backgrounds
- All S6.2 color tokens defined for light and dark mode
- Typography styles match S6.3 table
- Paper noise generates at runtime (no bitmap textures)
- AppState and Router are `@Observable` and functional
- API client fetches content from backend with Bearer auth from Keychain
- JSON file cache and signature PNG cache persist to disk
- All shared UI components render correctly in Xcode previews
- SwiftLint reports clean

### Epics

#### E2.1: Scaffold Xcode project with build configuration

**Scope:** Project structure per S8.1. Xcode project with iOS 26+ deployment target. xcconfig files for signer identity
(`dinesh`/`carolina`) and API key injection at build time per S10.7. SwiftLint 0.58+ configuration at `.swiftlint.yml`.
SwiftFormat configuration at `.swiftformat`. SPM configured with `Package.resolved` committed. Liquid Glass suppression
via opaque backgrounds and UIKit appearance overrides per S10.1. App entry point with `@main`. **Deliverable:** Xcode
project compiles and launches on iOS 26 simulator with empty app shell. **Files touched:**

- `ExhibitA/ExhibitA.xcodeproj/` (create)
- `ExhibitA/ExhibitA/App/ExhibitAApp.swift` (create)
- `ExhibitA/ExhibitA/Core/Config.swift` (create)
- `ExhibitA/.swiftlint.yml` (create)
- `ExhibitA/.swiftformat` (create)

**Acceptance criteria:**

- Project builds without errors or warnings for iOS 26 simulator
- xcconfig injects `SIGNER_IDENTITY` and `API_KEY` at build time
- SwiftLint runs and reports clean
- Liquid Glass suppressed: no translucent backgrounds or glass effects

#### E2.2: Define design system color and typography tokens

**Scope:** All color tokens from S6.2 for light and dark mode (13 light tokens, 10 dark tokens). Typography styles from
S6.3 (10 roles with typeface, weight, size, line height, color). Spacing constants on the 8pt grid. Shadow constants per
S6.4 (warm-tinted layered shadows). Programmatic SVG paper noise generator per S6.4 (feTurbulence fractalNoise,
baseFrequency 0.65, 3 octaves, 3-5% light / 2-3% dark). Color assets in asset catalog for Xcode preview support.
**Deliverable:** Complete design token set consumable by any SwiftUI view. **Files touched:**

- `ExhibitA/ExhibitA/Design/Theme.swift` (create)
- `ExhibitA/ExhibitA/Design/PaperNoise.swift` (create)
- `ExhibitA/ExhibitA/Resources/Assets.xcassets` (create)

**Acceptance criteria:**

- All 13 light-mode color tokens from S6.2 defined and accessible
- All 10 dark-mode color tokens from S6.2 defined and switch automatically
- Typography styles match S6.3 table (typeface, weight, size, line height, color)
- Paper noise renders programmatically at runtime with no bundled bitmap textures
- Shadow constants produce warm-tinted layered shadows matching `rgba(44,33,24,...)`

#### E2.3: Implement AppState, Router, and navigation shell

**Scope:** `@Observable` AppState per S10.5 with sync state tracking (`last_sync_at`), unread content tracking (seen
UUIDs in UserDefaults), and content storage references. `@Observable` Router per S8.2 with `NavigationPath`, route enum
(`contractBook`, `letterDetail(id:)`, `thoughtDetail(id:)`), and `navigate(to:)` method. Environment injection at app
root. `NavigationStack` shell with `navigationDestination` handlers for all routes. **Deliverable:** Navigation shell
with working route transitions between all destinations. **Files touched:**

- `ExhibitA/ExhibitA/App/AppState.swift` (create)
- `ExhibitA/ExhibitA/App/Router.swift` (create)

**Acceptance criteria:**

- `AppState` is `@Observable` with sync timestamps and unread tracking
- `Router` is `@Observable` with `NavigationPath` and route enum
- Both are injected via `@Environment` at app root
- `router.navigate(to: .contractBook)` pushes correct destination
- Unread state persists across app launches via UserDefaults

#### E2.4: Build API client, KeychainService, and content cache

**Scope:** URLSession API client per S8.1/Core with Bearer token auth from Keychain. All API request methods matching
S7.3 endpoints (content fetch with filters, single content, signatures, signature image, signature upload, sync, device
token registration). KeychainService per S10.7 wrapping Security framework with `kSecAttrAccessibleAfterFirstUnlock` for
background sync access. JSON file cache for content (`Codable` models to `.json` files in caches directory) per S10.3.
PNG file cache for signature images on disk. **Deliverable:** Working API client that fetches content from backend and
caches locally. **Files touched:**

- `ExhibitA/ExhibitA/Core/API/ExhibitAClient.swift` (create)
- `ExhibitA/ExhibitA/Core/API/APIModels.swift` (create)
- `ExhibitA/ExhibitA/Core/Cache/ContentCache.swift` (create)
- `ExhibitA/ExhibitA/Core/Cache/SignatureCache.swift` (create)
- `ExhibitA/ExhibitA/Core/Security/KeychainService.swift` (create)

**Acceptance criteria:**

- API client sends `Authorization: Bearer <key>` header from Keychain on every request
- Content responses decode to `Codable` models matching S7.3.1 schemas
- JSON cache persists content to disk and reads back correctly
- Signature PNG cache writes and reads image files by ID
- KeychainService stores and retrieves API key with `kSecAttrAccessibleAfterFirstUnlock`
- All operations use `async/await`

#### E2.5: Create shared UI components

**Scope:** Reusable components per S8.1 Design/Components. MonogramView: "EA" in New York Bold, `accent.primary`
burgundy, centered. ClassificationLabel: uppercase text in SF Pro Text Medium, 11pt, `accent.soft`, 2pt tracking.
ExhibitBadge: "EXHIBIT L-001" format in SF Pro Text Medium, 13pt, `accent.soft`, uppercase. UnreadBadge: `accent.soft`
dot with 2s breathing pulse animation per S2.1. **Deliverable:** All shared components render correctly with design
tokens from E2.2. **Files touched:**

- `ExhibitA/ExhibitA/Design/Components/MonogramView.swift` (create)
- `ExhibitA/ExhibitA/Design/Components/ClassificationLabel.swift` (create)
- `ExhibitA/ExhibitA/Design/Components/ExhibitBadge.swift` (create)
- `ExhibitA/ExhibitA/Design/Components/UnreadBadge.swift` (create)

**Acceptance criteria:**

- MonogramView displays "EA" in New York Bold with `accent.primary` color
- ClassificationLabel renders uppercase labels with 2pt tracking in `accent.soft`
- ExhibitBadge formats exhibit numbers (e.g., "EXHIBIT L-001") correctly
- UnreadBadge renders `accent.soft` dot with gentle 2s breathing pulse animation
- All components render in Xcode previews with correct tokens

---

## Phase 3: Home Screen

**Class:** Feature **Depends on:** Phase 2 **Design doc sections:** S2.1

### Entry Criteria

- Phase 2 exit criteria met
- All design tokens, shared components, AppState, Router, and API client operational

### Exit Criteria

- Home screen renders header area (title, subtitle, monogram) per S2.1
- Three entry cards render with correct labels, subtitles, SF Symbols, and warm shadows
- Cards navigate to contractBook, letters, and thoughts routes
- Unread badges display on cards when new content exists
- Legal footer text renders at bottom
- Layout matches S2.1 specification on iPhone SE through iPhone 16 Pro Max

### Epics

#### E3.1: Build home screen with filing cabinet layout and navigation

**Scope:** Filing cabinet landing screen per S2.1. Header: "EXHIBIT A" in New York Bold 34pt centered, subtitle "Case
No. DC-2025-0214 | Dinesh & Carolina" in SF Pro Text Regular 14pt, "EA" MonogramView. Three entry cards on
`background.secondary` with layered warm shadow and 12pt corner radius: The Contract ("The Binding Agreement"), Filed
Letters ("Correspondence on Record" with dynamic count), Sealed Thoughts ("Classified Memoranda" with dynamic count). SF
Symbol per card. UnreadBadge on cards with new content. Legal footer in New York Regular Italic 13pt `text.muted`. Card
tap navigates via Router.
**Deliverable:** Home screen renders with complete layout, live data counts, unread indicators, and navigation. **Files
touched:**

- `ExhibitA/ExhibitA/Features/Home/HomeView.swift` (create)

**Acceptance criteria:**

- Header renders title, subtitle, and monogram per S2.1
- Three cards render with correct labels, subtitles, and SF Symbols
- Cards vary in height based on content (not uniform grid)
- Unread `accent.soft` dot appears on cards with new content
- Tapping each card navigates to the correct route
- Legal footer text displays at bottom of screen
- Layout adapts from iPhone SE to iPhone 16 Pro Max

---

## Phase 4: Filed Letters

**Class:** Feature **Depends on:** Phase 3 **Design doc sections:** S4.1, S4.2, S10.6

### Entry Criteria

- Phase 3 exit criteria met
- Home screen navigation to letters route functional

### Exit Criteria

- Letter list renders cards with exhibit numbers, titles, filed dates, classifications, and unread indicators
- Letter detail renders markdown body with New York Regular 18pt on `background.reading`
- Navigation from list to detail works via Router
- Dividers are hairline (0.5pt) in `border.separator`

### Epics

#### E4.1: Build letter list view

**Scope:** Correspondence log per S4.1. Header: "CORRESPONDENCE ON RECORD" with "Dinesh & Carolina" subtitle. Letter
cards with ExhibitBadge (e.g., "EXHIBIT L-001"), title in quotes, filed date, ClassificationLabel (e.g., "Sincere",
"Grievance"), and UnreadBadge for unread items. Hairline separators (0.5pt `border.separator`) between letters. Data
loaded from ContentCache filtered by type `letter`, ordered by section_order descending. **Deliverable:** Letter list
renders with correct layout, data binding, and unread indicators. **Files touched:**

- `ExhibitA/ExhibitA/Features/Letters/LetterListView.swift` (create)

**Acceptance criteria:**

- Header renders "CORRESPONDENCE ON RECORD" with subtitle
- Each letter card shows exhibit number, title, date, and classification
- Unread indicator displays for letters not yet viewed
- Letters ordered by section_order (most recent first)
- Tapping a letter card navigates to detail view via Router

#### E4.2: Build letter detail reader with markdown rendering

**Scope:** Full-screen reader per S4.2 on `background.reading` (#F8F1E3) with programmatic paper noise at 3% opacity.
Header: exhibit number in SF Pro Text Medium 13pt `accent.soft` uppercase, title in New York Semibold 22pt
`text.primary`, filed date in SF Pro Text 14pt `text.muted`, ClassificationLabel in plain text (no border, no stamp).
Body: letter text rendered from markdown via `AttributedString` with New York Regular 18pt `text.reading`, 20-24pt
margins, 18pt paragraph spacing, 1.48x line height. Footer: "Filed with love, [date]" in SF Pro Text Regular Italic 13pt
`text.muted`. Vertical scroll. **Deliverable:** Letter detail renders markdown body with correct typography on warm
reading surface. **Files touched:**

- `ExhibitA/ExhibitA/Features/Letters/LetterDetailView.swift` (create)

**Acceptance criteria:**

- Background is `background.reading` with paper noise overlay
- Header shows exhibit number, title, date, and classification
- Body renders markdown (bold, italic, paragraphs) via `AttributedString`
- Typography matches S4.2: New York Regular 18pt, `text.reading`, 1.48x line height
- Horizontal margins are 20-24pt
- Footer displays "Filed with love, [date]"
- Content scrolls vertically for long letters

---

## Phase 5: Sealed Thoughts

**Class:** Feature **Depends on:** Phase 3 **Design doc sections:** S5.1, S5.2

### Entry Criteria

- Phase 3 exit criteria met
- Home screen navigation to thoughts route functional

### Exit Criteria

- Thought list renders memoranda with IDs, timestamps, and preview text
- Thought detail displays plain text centered on `background.reading` with generous padding
- Navigation from list to detail works via Router

### Epics

#### E5.1: Build thought list view

**Scope:** Classified memoranda list per S5.1. Header: "CLASSIFIED MEMORANDA" with "For Authorized Eyes Only" subtitle.
Thought entries with memo ID (e.g., "MEMO-047"), date and time, preview text (first 2-3 lines of body), and UnreadBadge
for unread items. Hairline separators (0.5pt `border.separator`). Data loaded from ContentCache filtered by type
`thought`, ordered by section_order descending. **Deliverable:** Thought list renders with correct layout, data binding,
and unread indicators. **Files touched:**

- `ExhibitA/ExhibitA/Features/Thoughts/ThoughtListView.swift` (create)

**Acceptance criteria:**

- Header renders "CLASSIFIED MEMORANDA" with subtitle
- Each thought shows memo ID, date/time, and body preview
- Unread indicator displays for thoughts not yet viewed
- Thoughts ordered by section_order (most recent first)
- Tapping a thought navigates to detail view via Router

#### E5.2: Build thought detail view

**Scope:** Minimal intimate reader per S5.2. `background.reading` surface with paper noise. Thought text centered with
generous padding (32pt horizontal, 48pt vertical) in New York Regular 18pt `text.reading`. Date and time above text in
SF Pro Text 14pt `text.muted`. No markdown rendering (plain text). No scroll needed (thoughts are short).
**Deliverable:** Thought detail displays plain text centered on warm reading surface with generous whitespace. **Files
touched:**

- `ExhibitA/ExhibitA/Features/Thoughts/ThoughtDetailView.swift` (create)

**Acceptance criteria:**

- Background is `background.reading` with paper noise overlay
- Date and time render above thought text in `text.muted`
- Thought body renders as plain text in New York Regular 18pt `text.reading`
- Horizontal padding is 32pt, vertical padding is 48pt
- Text is centered on the reading surface

---

## Phase 6: Contract Book and Signatures

**Class:** Feature **Depends on:** Phase 4, 5 **Design doc sections:** S3.1, S3.2, S3.3, S3.4, S3.5, S3.6, S3.7, S3.8,
S6.5, S8.3, S8.4

### Entry Criteria

- Phase 4 and Phase 5 exit criteria met
- List-detail pattern validated by letters and thoughts
- API client and cache verified with real content

### Exit Criteria

- UIPageViewController wraps in SwiftUI with `.pageCurl` transition
- Cover page renders per S3.2
- Table of contents lists all articles with tappable navigation
- Articles paginate dynamically based on screen height per S3.4
- Page numbers display per-article format ("Article III -- 2 of 4")
- Signature blocks show signed/unsigned states per S3.7
- PencilKit signing flow completes: tap line, draw, sign
- Signed signatures render with slight random rotation (1-3 degrees)
- Signatures upload to backend via API client
- Final "In Witness Whereof" page renders per S3.8

### Epics

#### E6.1: Build UIPageViewController wrapper with cover and table of contents

**Scope:** `UIPageViewController` with `.pageCurl` transition style wrapped in `UIViewControllerRepresentable` per S8.3.
Coordinator manages page order and tracks current position. Each page is a SwiftUI view wrapped in
`UIHostingController`. Cover page per S3.2 with title, party names, case number, filed date, jurisdiction, quote, and
monogram. Table of contents per S3.3 with all articles listed using dotted leaders and page numbers; tapping jumps to
the article's page index. **Deliverable:** Page-curl navigation works between cover, TOC, and placeholder content pages.
**Files touched:**

- `ExhibitA/ExhibitA/Features/Contract/ContractBookView.swift` (create)
- `ExhibitA/ExhibitA/Features/Contract/CoverPageView.swift` (create)
- `ExhibitA/ExhibitA/Features/Contract/TOCPageView.swift` (create)

**Acceptance criteria:**

- `UIPageViewController` renders with `.pageCurl` transition on swipe
- Cover page displays all elements per S3.2 with correct typography
- TOC lists all articles with dotted leaders and page numbers
- Tapping a TOC entry jumps to that article's first page
- Current page tracks correctly across swipe navigation

#### E6.2: Implement contract article pagination

**Scope:** Dynamic text measurement and pagination per S3.4. Article body rendered in New York serif with section
markers (S) in `accent.primary` Semibold 18pt, legal preambles (WHEREAS) in Regular Italic 18pt `text.secondary`, and
body clauses in Regular 18pt `text.reading`. Content splits across pages at natural break points (between clauses,
between preamble and agreement, between paragraphs). Page number display at bottom-center: "Article III -- 2 of 4" in SF
Pro Text 12pt `text.muted`. Signature block always rendered as the final page of each article. **Deliverable:** Articles
paginate dynamically based on available screen height with correct typography. **Files touched:**

- `ExhibitA/ExhibitA/Features/Contract/ContractPageView.swift` (create)

**Acceptance criteria:**

- Article body splits across pages at natural break points
- Section markers render in `accent.primary` Semibold
- WHEREAS preambles render in Regular Italic `text.secondary`
- Page numbers display per-article format ("Article III -- 2 of 4")
- Pagination adapts to screen size (iPhone SE through iPhone 16 Pro Max)
- Signature block is always the last page of each article

#### E6.3: Build signature block and PencilKit signing flow

**Scope:** Signature block component per S3.7 and S6.5. Unsigned state: dotted line with "Tap to sign" label, subtle
pulse animation in `accent.warm`. Signed state: signature PNG rendered from cache/API with slight random rotation (1-3
degrees), date displayed below, no re-signing allowed. Signing flow per S8.4: tap triggers `.sheet` with
`SignaturePadView` containing PencilKit `PKCanvasView` (`drawingPolicy = .anyInput`, tool picker disabled,
`PKInkingTool(.pen, color: text.reading, width: 2)`) on `background.reading`. "Clear" resets canvas, "Sign" exports
`PKDrawing` as PNG, saves to SignatureCache, updates UI optimistically, uploads via API client. Only the signer matching
`Config.signerIdentity` can tap their line. **Deliverable:** PencilKit signing flow completes end-to-end with local
persistence and server upload. **Files touched:**

- `ExhibitA/ExhibitA/Features/Contract/SignatureBlockView.swift` (create)
- `ExhibitA/ExhibitA/Features/Contract/SignaturePadView.swift` (create)

**Acceptance criteria:**

- Unsigned lines show dotted line with "Tap to sign" and pulse animation
- Only the current signer's line is tappable
- PencilKit canvas uses `drawingPolicy = .anyInput` with tool picker disabled
- Ink tool is `.pen` with `text.reading` color and width 2
- "Clear" resets the canvas; "Sign" exports PNG and dismisses sheet
- Signature saved to local cache immediately (optimistic)
- Signature uploads to `POST /signatures` with correct content_id and signer
- Signed state renders PNG with 1-3 degree random rotation
- Re-signing is blocked (signatures are permanent)

#### E6.4: Create final page and wire contract state integration

**Scope:** Final "In Witness Whereof" page per S3.8 closing text: parties, established date, and closing message. Wire
contract book to AppState for signature state persistence and content loading from cache. Ensure existing signatures
load from SignatureCache on book open. Handle signature upload success/failure states. **Deliverable:** Final page
renders, and contract book displays real content with persisted signatures. **Files touched:**

- `ExhibitA/ExhibitA/Features/Contract/FinalPageView.swift` (create)

**Acceptance criteria:**

- Final page renders "IN WITNESS WHEREOF" closing text per S3.8
- Contract book loads articles from ContentCache
- Existing signatures load from SignatureCache on book open
- Newly signed signatures persist across app launches
- Page sequence: cover, TOC, articles (with signature pages), final page

---

## Phase 7: Sync, Push, and Offline

**Class:** Integration **Depends on:** Phase 6 **Design doc sections:** S7.4, S9.6, S9.7, S10.2, S10.3, S15.3

### Entry Criteria

- Phase 6 exit criteria met
- All feature screens operational with cached data
- Backend sync and device-token endpoints operational (Phase 0)

### Exit Criteria

- App syncs content delta on launch using `GET /sync?since=` per S7.4
- `BGAppRefreshTask` registered and executes background sync per S7.4
- Unread badges update after sync discovers new content
- App registers for push notifications and stores device token via `POST /device-tokens`
- Push notification deep-links to correct content via Router per S8.2
- Signature uploads retry in background when offline per S10.3
- Queued uploads complete automatically when connectivity returns

### Epics

#### E7.1: Implement sync engine, background refresh, and push notification handling

**Scope:** Sync-on-launch flow per S7.4: read `last_sync_at` from UserDefaults, call `GET /sync?since=`, fetch changed
content items, update ContentCache, update `last_sync_at`. `BGAppRefreshTask` registration in `ExhibitAApp` per S7.4:
register task identifier at launch, schedule opportunistic background refresh, run same sync logic. Push notification
registration: request authorization, register for remote notifications, send device token to `POST /device-tokens` with
signer identity. Push notification handling: parse route from notification payload, navigate via Router. Unread
tracking: compare synced content IDs against seen set in UserDefaults, update unread state in AppState. **Deliverable:**
App syncs on launch and in background, registers for push, and deep-links from notifications. **Files touched:**

- `ExhibitA/ExhibitA/Core/Sync/SyncService.swift` (create)
- `ExhibitA/ExhibitA/App/ExhibitAApp.swift` (modify)

**Acceptance criteria:**

- App calls `GET /sync?since=` on launch and processes changes
- `last_sync_at` updates after successful sync
- `BGAppRefreshTask` registered and scheduled for background sync
- App requests push notification authorization on first launch
- Device token sent to `POST /device-tokens` after registration
- Push notification with route payload navigates to correct content
- Unread badges update after sync discovers new content IDs

#### E7.2: Implement offline signature upload queue

**Scope:** Background `URLSession` configuration for signature upload retry per S10.3. Upload queue that persists
pending uploads across app launches. When a signature is signed offline, the PNG is saved locally (already handled by
E6.3) and the upload is queued. Background `URLSession` handles reconnection and retry automatically. On server
rejection (409 duplicate), queue removes the item and app displays existing signature. On success, `signed_at` timestamp
persisted locally. **Deliverable:** Signatures upload reliably in background with automatic retry on connectivity
restoration. **Files touched:**

- `ExhibitA/ExhibitA/Core/Sync/UploadQueue.swift` (create)

**Acceptance criteria:**

- Upload queue persists pending signature uploads across app launches
- Background `URLSession` retries uploads when connectivity returns
- Server 409 (duplicate) response clears the queued item without error
- Successful upload persists `signed_at` timestamp locally
- Queue processes without blocking the UI

---

## Phase 8: Sound, Haptics, and Animation Polish

**Class:** Integration **Depends on:** Phase 7 **Design doc sections:** S6.6, S6.8

### Entry Criteria

- Phase 7 exit criteria met
- All feature screens and integration wiring operational

### Exit Criteria

- Page turn sound plays during contract book navigation per S6.8
- Signature placed sound plays after signing per S6.8
- New content notification chime plays on push-triggered sync per S6.8
- Settings gear on home screen toggles all sounds; preference persists via UserDefaults
- Haptic feedback fires on signature placement (UIImpactFeedbackGenerator, .medium) per S3.7
- Unread badge pulses with 2s breathing cycle per S2.1
- Home screen cards show subtle parallax on scroll per S6.6
- Signature fades in with 0.5s ease and scale from 0.95 to 1.0 per S6.6
- Screen transitions use slow fades (0.3-0.4s) per S6.6

### Epics

#### E8.1: Add sound effects service and settings toggle

**Scope:** Sound service managing three audio cues per S6.8: page turn (soft, muffled paper sound), signature placed
(quiet pen-on-paper), and new content chime (gentle, warm). All sounds triggered by name through the service. Settings
view accessible via gear icon on home screen: toggle for sound on/off, preference persisted in UserDefaults. Default:
sounds enabled on first launch. Sounds respect the toggle state globally. **Deliverable:** Sound service plays all three
audio cues, controllable via a persistent settings toggle. **Files touched:**

- `ExhibitA/ExhibitA/Core/SoundService.swift` (create)
- `ExhibitA/ExhibitA/Features/Home/SettingsView.swift` (create)

**Acceptance criteria:**

- Page turn sound is soft and slightly muffled (not crisp)
- Signature placed sound is brief pen-on-paper
- New content chime is gentle and warm (not digital)
- Settings gear on home screen opens sound toggle
- Sound preference persists in UserDefaults across launches
- Default is sounds enabled on first launch
- All sounds respect the toggle (no sound plays when disabled)

#### E8.2: Wire haptic feedback, sound triggers, and animation polish into views

**Scope:** Haptic feedback per S3.7: `UIImpactFeedbackGenerator(.medium)` on signature placement. Sound triggers: page
turn sound in ContractBookView page transitions, signature placed sound in SignaturePadView on sign confirmation.
Animation polish per S6.6: slow fades (0.3-0.4s) between screen transitions, signature fade-in (0.5s ease with scale
0.95 to 1.0) in SignatureBlockView, subtle parallax on home screen cards on scroll, unread badge breathing pulse (2s
cycle, already defined in E2.5 but wired to animation timing here). **Deliverable:** All haptics, sound triggers, and
animations wired into feature views at 60fps. **Files touched:**

- `ExhibitA/ExhibitA/Features/Home/HomeView.swift` (modify)
- `ExhibitA/ExhibitA/Features/Contract/ContractBookView.swift` (modify)
- `ExhibitA/ExhibitA/Features/Contract/SignatureBlockView.swift` (modify)
- `ExhibitA/ExhibitA/Features/Contract/SignaturePadView.swift` (modify)

**Acceptance criteria:**

- Haptic fires on signature placement (medium impact)
- Page turn sound plays on contract book page transitions
- Signature placed sound plays on sign confirmation
- Screen transitions use 0.3-0.4s fade (not hard cuts)
- Signature animates into place with 0.5s ease and 0.95-to-1.0 scale
- Home screen cards exhibit subtle parallax on scroll
- All animations render at 60fps on iPhone SE through iPhone 16 Pro Max

---

## Execution Notes

- Phases execute sequentially. Do not begin Phase N+1 until Phase N exit criteria are met.
- Epics within a phase may execute in parallel if their file sets are disjoint.
- If an epic's acceptance criteria cannot be met, stop and reassess before continuing.
- This roadmap is deterministic. Follow it top-to-bottom.
- Backend phases (0-1) deploy to VPS at `157.180.94.145`. iOS phases (2-8) build locally in Xcode.
- All Python code must pass `ruff format --check && ruff check && mypy --strict` before phase exit.
- All Swift code must pass SwiftLint before phase exit.
- `scripts/protocol-zero.sh` and `scripts/check-em-dashes.sh` must exit 0 at every phase boundary.
