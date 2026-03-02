---
name: phase-epic-decomposition
description: Decompose a product design document into a deterministic, dependency-ordered implementation roadmap with sequential phases, scoped epics, and explicit entry/exit criteria. Use when translating a design doc into an actionable engineering plan, creating a PHASES.md delivery roadmap, or when a user requests implementation phasing, epic breakdowns, or execution sequencing. Triggers on design-to-implementation planning, phase decomposition, epic structuring, roadmap generation, or delivery sequencing requests.
---

# Phase and Epic Decomposition

Transform a product design document into a deterministic implementation roadmap that engineers execute top-to-bottom without ambiguity.

## Workflow

### Step 1: Ingest the Design Document

Read the source design document:

```
docs/exhibit-a-design-doc.md
```

Extract and catalog:

- All system boundaries (frameworks, services, persistence, networking)
- All feature surfaces (chapters, screens, interactions)
- All cross-cutting concerns (state management, audio, haptics, navigation)
- All external dependencies (APIs, hardware capabilities, permissions)
- Explicit goals and non-goals

Do not infer requirements beyond what the document states.

### Step 2: Classify Work Units

Categorize every identified work unit into exactly one class:

| Class              | Definition                                                     | Examples                                                                           |
| ------------------ | -------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| **Infrastructure** | Foundational systems that feature code depends on              | Project scaffold, state management, design tokens, navigation, shared UI, services |
| **Feature**        | User-facing functionality tied to a specific chapter or screen | Chapter 0 fingerprint, Chapter 1 game, Chapter 2 poems                             |
| **Integration**    | Wiring between systems, cross-cutting behavior, polish         | Audio session management, haptic service, API client, interruption handling        |

A work unit belongs to exactly one class. If it spans two classes, decompose it further.

### Step 3: Build the Dependency Graph

For each work unit, declare its prerequisites explicitly:

- Infrastructure units have no feature dependencies (they are DAG roots)
- Feature units depend on the infrastructure they consume
- Integration units depend on the feature and infrastructure units they connect

**Validation rule:** The dependency graph MUST be a Directed Acyclic Graph. If a cycle is detected, the decomposition is invalid. Resolve by extracting the shared concern into a separate unit.

### Step 4: Assign Phases by Topological Order

Group work units into phases using topological sort on the dependency graph:

1. **Phase 0** always exists. It contains all infrastructure work with zero dependencies.
2. Subsequent phases contain work units whose dependencies are satisfied by prior phases.
3. Work units within a single phase MUST NOT depend on each other.
4. A phase MUST contain only one work class (infrastructure, feature, or integration). Mixed-class phases are prohibited.

**Exception:** If a feature phase has exactly one tightly-coupled integration concern (e.g., Chapter 2 requires the API client), that integration work MAY be included in the same phase only if it touches zero files outside the feature's directory.

### Step 5: Determine Epic Count per Phase

Each phase decomposes into epics. Apply these sizing rules:

- An epic represents a focused coding session (1-3 days of work for a single engineer)
- An epic touches a bounded set of files. Two epics in the same phase MUST NOT modify the same file
- An epic has a single clear deliverable (a runnable component, a passing test suite, a working screen)

**Counting heuristic:**

| Phase Complexity | Guideline                                                 |
| ---------------- | --------------------------------------------------------- |
| Single system    | 1-2 epics                                                 |
| Multi-screen     | 1 epic per screen                                         |
| Multi-system     | 1 epic per system                                         |
| Game chapter     | 3-5 epics (engine, sprites, HUD, game logic, integration) |

See [references/epic-granularity.md](references/epic-granularity.md) for detailed sizing rules.

### Step 6: Define Entry and Exit Criteria

Every phase requires:

**Entry criteria** — preconditions that must be true before work begins:

- All predecessor phases complete
- All required assets/APIs/permissions available
- Specific files or interfaces from prior phases verified working

**Exit criteria** — conditions that must be true before the phase is considered done:

- All epics in the phase are complete
- Code compiles without errors
- Relevant tests pass (if testing applies)
- No blocking defects remain

Exit criteria MUST be observable and binary (met or not met). No subjective assessments.

### Step 7: Generate PHASES.md

Write the output to:

```
docs/PHASES.md
```

Use the strict output format defined in [references/output-format.md](references/output-format.md).

## Decomposition Rules

### Dependency Ordering (BLOCKING)

1. Infrastructure before features. No feature work begins until its infrastructure dependencies exist.
2. Shared services before consumers. `ExhibitAClient`, `ContentCache`, `KeychainService` must exist before any chapter that uses them.
3. State management before any screen. `AppState` and persistence must be complete and tested before feature views consume it.
4. Design system before any UI. Color tokens, typography constants, spacing constants, and shared UI components must exist before chapter-specific views.
5. Navigation shell before feature content. The routing system must work before feature screens are built.
6. Simpler features before complex features. Screens with fewer subsystems are built first to validate patterns before tackling complex features.

### Scope Isolation (BLOCKING)

1. Each phase operates on a disjoint file set. If Phase N and Phase M both need to modify `AudioService.swift`, extract the shared work into an earlier phase.
2. Each epic within a phase operates on a disjoint file set. No two epics modify the same file.
3. If a shared file must be extended in a later phase, the extension is its own dedicated epic, not buried inside a feature epic.
4. Cross-cutting concerns (haptics, audio, analytics) get their own integration phase. They are not embedded in feature phases.

### Anti-Patterns (MUST REJECT)

- **God phase**: A phase containing more than 5 epics. Decompose further.
- **Mega-epic**: An epic requiring more than 3 days of work. Split it.
- **Multi-system epic**: An epic that touches both UI and a backend service. Separate them.
- **Implicit dependency**: A phase that "probably" needs something from another phase but does not declare it. Make every dependency explicit.
- **Horizontal slicing**: Phases organized by technical layer ("all models", "all views", "all services") instead of by deliverable capability. Use vertical slicing within feature phases.
- **Premature feature work**: Building a chapter screen before the shared UI components it needs exist.

## Phase Classification Reference

See [references/phase-classification.md](references/phase-classification.md) for canonical phase types, ordering rules, and examples mapped to the Exhibit A architecture.

## Epic Granularity Reference

See [references/epic-granularity.md](references/epic-granularity.md) for epic sizing rules, file-disjointness enforcement, and deliverable definitions.

## Output Format Reference

See [references/output-format.md](references/output-format.md) for the exact PHASES.md structure, table format, and per-phase epic breakdown template.
