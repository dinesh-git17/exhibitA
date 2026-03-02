# Epic Granularity

Sizing rules, file-disjointness enforcement, and deliverable definitions for epics within each phase.

## Epic Sizing Rules

### Duration Bounds

| Bound | Limit | Enforcement |
|---|---|---|
| Minimum | 0.5 days (4 hours) | Below this, merge into an adjacent epic |
| Target | 1-2 days (8-16 hours) | Preferred epic size |
| Maximum | 3 days (24 hours) | Above this, split into smaller epics |

An epic exceeding 3 days indicates mixed concerns. Decompose by:

1. Separating data layer work from view layer work
2. Separating static UI from interactive behavior
3. Separating backend endpoints from admin panel templates
4. Separating service integration from core logic

### File Scope Bounds

| Bound | Limit | Enforcement |
|---|---|---|
| Minimum | 1 file | Valid for single-component epics |
| Target | 3-8 files | Preferred file count per epic |
| Maximum | 12 files | Above this, split into sub-epics |

### Deliverable Requirement

Every epic MUST produce exactly one of:

| Deliverable Type | Definition | Example |
|---|---|---|
| Runnable component | A view or screen that renders and responds to input | Home screen with three entry cards |
| Working service | A service with public interface and verified behavior | API client with Bearer auth + JSON cache |
| Passing test suite | Tests that validate a unit of behavior | Sync logic round-trip tests |
| Complete data layer | Models, constants, or tokens ready for consumption | Design system color and typography tokens |
| Integrated interaction | End-to-end flow through multiple connected systems | Admin push → APNS → app sync → unread badge |
| Deployable backend | Server endpoints responding correctly | FastAPI with content + signature endpoints |

An epic without a named deliverable is not an epic. It is undefined work.

## File-Disjointness Enforcement

### Within-Phase Rule

Two epics in the same phase MUST NOT modify the same file.

**Verification procedure:**

1. List all files each epic will create or modify
2. Compute the intersection of file sets between all epic pairs in the phase
3. If any intersection is non-empty, restructure:
   - Extract the shared file's changes into a separate preparatory epic
   - OR reassign one of the conflicting epics to a different phase

### Cross-Phase Rule

A later phase MAY modify a file created in an earlier phase, but:

- The modification must be in its own dedicated epic (not embedded in a feature epic)
- The modification must be additive (extending an interface, adding a method) not destructive (rewriting existing logic)

### Common Violation Patterns

| Violation | Description | Resolution |
|---|---|---|
| Shared service extension | Two feature epics both need to add methods to API client | Create a client-extension epic in a prior phase that adds both methods |
| Shared view modification | Two epics both modify a shared UI component | Extract shared component changes into an infrastructure epic |
| Template conflict | Two epics both modify the same Jinja2 template | Dedicate one epic to template changes, run it first |

## Epic Decomposition by Feature Type

### Backend Phase (FastAPI + SQLite)

Server-side work: endpoints, database, auth, deployment.

**Standard decomposition:**

| Epic | Scope | Deliverable |
|---|---|---|
| 1 | Project scaffold + DB schema | FastAPI app starts, SQLite WAL initialized, health endpoint responds |
| 2 | Content + signature endpoints | All app-facing API endpoints respond with correct data |
| 3 | Auth middleware + deployment | Bearer token auth, Caddy config, systemd service, Litestream backup |

### Admin Panel Phase (Jinja2 + HTMX)

Web UI for content management.

**Standard decomposition:**

| Epic | Scope | Deliverable |
|---|---|---|
| 1 | Session auth + dashboard | Login flow, session management, dashboard summary view |
| 2 | Content CRUD forms | Create/edit/delete for contracts, letters, thoughts |
| 3 | Push integration | APNS wiring, notification on content creation |

### iOS Infrastructure Phase

Foundation before any feature screen.

**Standard decomposition:**

| Epic | Scope | Deliverable |
|---|---|---|
| 1 | Xcode scaffold + config | Project structure, xcconfig, SwiftLint, SwiftFormat, SPM |
| 2 | Design system tokens | Color tokens (light + dark), typography styles, spacing, paper noise |
| 3 | AppState + Router | @Observable state, NavigationStack, route enum, environment injection |
| 4 | API client + caching | URLSession client, KeychainService, JSON cache, signature PNG cache |
| 5 | Shared UI components | MonogramView, ClassificationLabel, ExhibitBadge, UnreadBadge |

### Simple Screen Feature (Home, Letters, Thoughts)

Pure SwiftUI, list + detail pattern, API consumption.

**Standard decomposition:**

| Epic | Scope | Deliverable |
|---|---|---|
| 1 | List view layout | Screen renders with correct layout, typography, cards, badges |
| 2 | Detail view + navigation | Detail reader works, navigation from list to detail functions |
| 3 | State integration | Unread tracking, sync state, API data binding |

### Complex Feature (Contract Book)

UIKit interop, pagination logic, signature mechanics.

**Standard decomposition:**

| Epic | Scope | Deliverable |
|---|---|---|
| 1 | UIPageViewController wrapper | Page-curl navigation with SwiftUI hosting, cover page, TOC |
| 2 | Contract article pagination | Dynamic text measurement, clause-aware page breaks, page numbering |
| 3 | Signature block + PencilKit | Signed/unsigned states, PencilKit half-sheet, PNG export, upload |
| 4 | Final page + state integration | "In Witness Whereof" page, signature persistence, API sync |

## Naming Convention

Epic names follow this format:

```
E{phase}.{sequence}: {imperative verb} {scope}
```

Examples:

- `E0.1: Scaffold FastAPI backend with SQLite schema`
- `E0.2: Implement content and signature API endpoints`
- `E2.1: Define design system color and typography tokens`
- `E4.1: Build contract book UIPageViewController wrapper`
- `E4.3: Implement PencilKit signature flow`
