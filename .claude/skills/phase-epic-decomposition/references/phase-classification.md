# Phase Classification

Canonical phase types, ordering constraints, and mapping to the Exhibit A design document.

## Phase Types

### Type I: Infrastructure Phase

Foundational systems with zero feature dependencies. These are DAG roots.

**Characteristics:**

- Produces interfaces, services, or base types consumed by all subsequent phases
- Contains no user-visible behavior
- Produces artifacts verifiable in isolation (compiles, tests pass, server responds, types resolve)

**Canonical infrastructure work units for Exhibit A:**

| Work Unit | Design Doc Section | Produces |
|---|---|---|
| Backend scaffold + DB | §7.1 Deployment, §7.2 Schema | FastAPI app, SQLite WAL schema, systemd service, Caddy config, Litestream backup |
| API endpoints | §7.3 API Endpoints | Content, signatures, sync, device-tokens, health endpoints with auth middleware |
| Admin panel | §9 Admin Panel | Jinja2 templates, HTMX forms, session auth, content CRUD, push integration |
| Xcode project scaffold | §8.1 Project Organization | Directory structure, build settings, xcconfig (signer, API key, base URL) |
| Design system tokens | §6 Visual Design | Color tokens (light + dark), typography styles, spacing constants, paper noise |
| AppState + Router | §8.2 Navigation, §10.5 State | @Observable state, NavigationStack, NavigationPath, route enum |
| API client + cache | §8.1 Core | URLSession client with Bearer auth, JSON file cache, PNG signature cache, KeychainService |
| Shared UI components | §2 Information Architecture | MonogramView, ClassificationLabel, ExhibitBadge, UnreadBadge |

**Ordering rule:** Backend infrastructure (scaffold, API, admin) forms a dependency chain. iOS infrastructure (Xcode scaffold, design tokens, state, API client, shared UI) forms a parallel chain. Design tokens must exist before shared UI components that reference them. API client must exist before any feature that fetches data.

### Type F: Feature Phase

User-facing functionality scoped to a single screen or feature area.

**Characteristics:**

- Depends on infrastructure outputs (tokens, state, navigation, API client, shared UI)
- Self-contained within a feature directory
- May depend on services but does not define them
- Deliverable is a working screen or interaction playable end-to-end

**Canonical feature work units for Exhibit A:**

| Work Unit | Design Doc Section | Dependencies |
|---|---|---|
| Home screen | §2.1 Home Screen | Design tokens, AppState, Router, shared UI |
| Contract book (page-curl) | §3 Contract | Design tokens, AppState, Router, UIPageViewController, API client |
| Signature flow | §3.7 Signatures | PencilKit, API client, signature cache, contract book |
| Letter list + detail | §4 Letters | Design tokens, AppState, Router, API client, AttributedString |
| Thought list + detail | §5 Thoughts | Design tokens, AppState, Router, API client |

**Ordering rule:** Feature phases ordered by dependency complexity (ascending):

1. Home screen ships first (consumes shared UI, no complex subsystems)
2. Letters and thoughts ship next (list + detail pattern, validates API client + cache)
3. Contract book ships after (UIPageViewController, pagination logic, signature blocks)
4. Signature flow ships last (depends on contract book + PencilKit + background upload)

### Type G: Integration Phase

Cross-cutting system wiring, service hardening, and polish.

**Characteristics:**

- Depends on both infrastructure and feature outputs
- Modifies or extends service interfaces defined in infrastructure
- Produces behavior observable across multiple features
- Addresses non-functional requirements (offline, push, dark mode, sound)

**Canonical integration work units for Exhibit A:**

| Work Unit | Design Doc Section | Scope |
|---|---|---|
| Push notification wiring | §9.6 Push, §9.7 Flow | APNS registration, device token endpoint, deep linking via Router |
| Sync engine + background refresh | §7.4 Sync Strategy | BGAppRefreshTask, sync-on-launch, unread badge tracking |
| Offline handling | §10.3 Offline-First | Queued signature uploads, background URLSession retry |
| Dark mode | §6.7 Dark Mode | Token switching, lifted accents, paper noise at 2-3% opacity |
| Sound design | §6.8 Sound Design | Page turn, signature placed, new content chime, toggle persistence |
| Haptic feedback | §6.6 Animations | Signature haptic, unread badge pulse |

## Dependency Ordering Algorithm

Given classified work units, determine phase assignment:

```
1. Place all Type I units with zero dependencies in Phase 0
2. Place remaining Type I units in Phase 1 (those depending on Phase 0 outputs)
3. For each Type F unit:
   a. Compute its dependency set (which infrastructure/service outputs it needs)
   b. Assign to the earliest phase where ALL dependencies are satisfied
   c. If two Type F units have no dependency relationship, they MAY share a phase
4. For each Type G unit:
   a. Compute its dependency set (which features and infrastructure it wires)
   b. Assign to the earliest phase AFTER all its dependencies are satisfied
5. Validate: no cycles exist. If Phase N depends on Phase M where M > N, restructure.
```

## Phase Numbering Convention

| Phase Range | Class | Description |
|---|---|---|
| 0 | Infrastructure | Backend foundation (zero-dependency) |
| 1 | Infrastructure | Admin panel (depends on backend) |
| 2 | Infrastructure | iOS foundation (scaffold, tokens, state, client) |
| 3-N | Feature | Screens and interactions, ordered by complexity |
| N+1 | Integration | Cross-cutting wiring (push, sync, offline) |
| N+2 | Integration | Polish (dark mode, sound, haptics, deploy) |

Phase numbers are sequential with no gaps. Each phase has exactly one class label.
