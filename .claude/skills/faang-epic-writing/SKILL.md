---
name: faang-epic-writing
description: Expand PHASES.md epic entries into fully executable, implementation-grade epic documents with binary completion criteria, explicit scope boundaries, dependency declarations, and file-level implementation surface mapping. Use when expanding an epic from PHASES.md into a standalone document, writing a new epic, reviewing an epic for completeness, or when a user requests epic generation, epic expansion, or epic review. Triggers on epic document creation, epic expansion from PHASES.md, epic review, definition of done construction, or any task producing an epic-level planning artifact.
---

# FAANG Epic Writing

Transform PHASES.md epic entries into standalone, implementation-grade engineering documents that a senior engineer executes start-to-finish without clarification requests.

---

## 1. Core Doctrine

An epic is a **buildable feature slice** scoped to a single focused coding session (1-3 days). It is not a task list, not a project plan, not a requirements document. It is an executable contract between planning and implementation.

**Governing axioms:**

- Every statement in an epic must be **binary verifiable**. If completion cannot be determined by running code or inspecting output, the statement is invalid.
- Every epic operates on a **bounded, explicit file set**. If files are not named, the scope is undefined.
- Every epic declares its **dependencies explicitly**. If a prerequisite is not listed, the epic claims it has none.
- Every epic contains an **Out of Scope** section. If adjacent work is not excluded, it is implicitly included, which is a scope failure.

---

## 2. Workflow

### Step 1: Read PHASES.md

Read the implementation roadmap:

```
docs/PHASES.md
```

Identify the target epic by its phase number and epic number (e.g., E2.3). Extract:

- Epic title and scope description
- Phase class and phase dependencies
- Files touched list
- Acceptance criteria from the roadmap

If PHASES.md does not exist, **HALT**. Epic expansion requires a roadmap.

### Step 2: Read the Design Document

Read the design document:

```
docs/exhibit-a-design-doc.md
```

Cross-reference the epic's scope against the design doc sections listed in the phase header. Extract:

- Specific UI layouts, interactions, and behaviors within scope
- Named constants, tokens, or values the epic must use
- Integration points with services or state
- Constraints and rules applicable to the epic's domain

Do not infer requirements beyond what the design doc states.

### Step 3: Validate Dependencies

Before generating the epic document:

1. Read the dependency list from PHASES.md for the epic's parent phase
2. Verify each dependency phase exists in PHASES.md
3. Verify the dependency phase's exit criteria are defined
4. If any dependency is unresolvable, **HALT** and report the missing dependency

An epic MUST NOT be generated if its dependency chain is incomplete.

### Step 4: Map the Implementation Surface

For every file listed in the epic's "Files touched" section in PHASES.md:

1. Determine whether the file is **created** (new) or **modified** (existing)
2. For new files: define the file's single responsibility and its public interface
3. For modified files: read the current file content, identify the exact insertion or modification points
4. List integration points: which other files import, reference, or depend on this file

### Step 5: Construct the Epic Document

Write the epic document using the strict format defined in [references/epic-format.md](references/epic-format.md).

Apply all scope and DoD rules defined in this skill.

### Step 6: Write to the Output Path

Write the generated epic to:

```
docs/PH-{phase_number}/{epic_number}-{epic_id}-{epic_name}.md
```

Where:

- `{phase_number}` is the phase number (e.g., `PH-0`, `PH-3`)
- `{epic_number}` is the full epic identifier (e.g., `0-1`, `3-2`)
- `{epic_id}` is derived from the epic's primary system or component
- `{epic_name}` is a lowercase, dash-separated slug of the deliverable

Create the `docs/PH-{N}/` directory if it does not exist.

**Naming examples:**

```
docs/PH-0/0-1-backend-scaffold-schema.md
docs/PH-0/0-2-api-endpoints-auth.md
docs/PH-2/2-1-design-system-tokens.md
docs/PH-3/3-1-home-screen-layout.md
docs/PH-4/4-2-contract-pagination-logic.md
```

---

## 3. Epic Scope Discipline (BLOCKING)

### 3.1 Single Deliverable Rule

Every epic produces exactly one buildable deliverable. If an epic describes two independent deliverables, it is two epics incorrectly merged.

Valid deliverables:

| Type                   | Verification Method                     |
| ---------------------- | --------------------------------------- |
| Runnable screen/view   | Launch the app, navigate to the screen  |
| Working service        | Call the public API, observe the result |
| Passing test suite     | Run tests, all green                    |
| Complete data layer    | Import the module, types resolve        |
| Integrated interaction | Execute the end-to-end flow, observe it |

### 3.2 File Boundary Rule

An epic's scope is defined by its file set. Two epics in the same phase MUST NOT modify the same file.

### 3.3 System Boundary Rule

An epic touches one system. If it spans UI and a backend service, or spans two unrelated services, it must be split. The exception is a feature epic that consumes (but does not define) an existing service interface.

### 3.4 Mandatory Out-of-Scope Section

Every epic MUST contain an **Out of Scope** section that explicitly names:

- Adjacent features that a reasonable engineer might assume are included
- Later-phase work that builds on this epic's output
- Shared infrastructure modifications not covered by this epic
- Polish, optimization, or edge case handling deferred to a later epic

An empty Out of Scope section is a scope failure. There is always adjacent work to exclude.

---

## 4. Definition of Done Construction (BLOCKING)

### 4.1 Binary Verifiability Rule

Every DoD item must be answerable with YES or NO by running the application, executing a test, or inspecting a file. Subjective assessment is prohibited.

**Prohibited phrases in DoD items:**

| Phrase                | Violation           | Replacement Pattern                              |
| --------------------- | ------------------- | ------------------------------------------------ |
| "works well"          | Subjective          | "\[specific behavior\] occurs when \[trigger\]"  |
| "looks good"          | Subjective          | "\[element\] renders at \[size\] with \[token\]" |
| "handles errors"      | Vague               | "\[error type\] produces \[specific response\]"  |
| "is responsive"       | Undefined metric    | "\[view\] renders within \[N\]ms of appearance"  |
| "properly configured" | Ambiguous           | "\[setting\] equals \[value\] in \[location\]"   |
| "as expected"         | Circular            | State the expectation explicitly                 |
| "should be"           | Conditional         | Use "is" or "does"                               |
| "clean code"          | Non-verifiable      | Remove. Code standards are enforced globally     |
| "no bugs"             | Unfalsifiable       | Remove. Test specific behaviors instead          |
| "performant"          | Undefined threshold | "\[operation\] completes in under \[N\]ms"       |

### 4.2 Lifecycle Coverage Rule

DoD items must cover the full lifecycle of the deliverable, not just its initial state:

1. **Creation/Initialization**: The component exists and renders/loads/initializes
2. **Interaction**: User actions produce correct state transitions
3. **State Persistence**: If applicable, state survives app restart
4. **Teardown/Cleanup**: Resources are released, observers are removed
5. **Edge Cases**: Empty state, error state, interruption recovery

Not every epic requires all five categories, but the absence of any applicable category must be a conscious decision, not an oversight.

### 4.3 DoD Item Format

Every item follows this structure:

```
- [ ] [Subject] [verb in present tense] [observable outcome] [when/after condition]
```

Examples:

```
- [ ] HomeView renders three entry cards with correct typography and warm shadows on launch
- [ ] Tapping "The Binding Agreement" card navigates to ContractBookView
- [ ] Unread badge displays on sections with new content after sync
- [ ] Badge clears when user opens the corresponding content item
- [ ] AppState.lastSyncAt updates after successful sync completes
```

### 4.4 Minimum DoD Item Count

| Epic Complexity     | Minimum Items |
| ------------------- | ------------- |
| Data layer only     | 3             |
| Single screen       | 5             |
| Multi-interaction   | 7             |
| Service integration | 5             |
| Game mechanic       | 8             |

Below the minimum indicates incomplete coverage.

---

## 5. Dependency Enforcement (BLOCKING)

### 5.1 Dependency Declaration

Every epic header MUST contain a `Dependencies` field listing:

- Phase dependencies (which prior phases must be complete)
- Epic dependencies (which specific epics within those phases are required)
- Asset dependencies (which images, audio files, or data files must exist)
- Service dependencies (which service interfaces must be available)

### 5.2 Dependency Validation

Before generating an epic, verify:

1. Every listed dependency exists in PHASES.md
2. Every listed dependency has defined exit criteria
3. No circular dependency exists (this epic does not appear in its own dependency chain)

If validation fails, **HALT** and report the specific failure.

### 5.3 Implicit Dependency Detection

When reading the design doc, detect dependencies the PHASES.md entry may have omitted:

- If the epic uses a design token, it depends on the design system epic
- If the epic reads AppState, it depends on the state management epic
- If the epic uses a shared UI component, it depends on the shared UI epic
- If the epic plays audio, it depends on the AudioService epic
- If the epic triggers haptics, it depends on the HapticService epic

Report any detected implicit dependencies as additions to the header.

---

## 6. Implementation Surface Mapping

### 6.1 File Inventory

Every epic MUST contain a file inventory table:

```markdown
| File                                          | Action | Responsibility                                 |
| --------------------------------------------- | ------ | ---------------------------------------------- |
| `ExhibitA/Features/Home/HomeView.swift`   | Create | Filing cabinet landing screen with entry cards |
| `ExhibitA/App/AppState.swift`             | Modify | Add unread tracking and sync state properties  |
```

**Action** is exactly one of: `Create`, `Modify`.

**Responsibility** is a single sentence describing what this epic does to the file.

### 6.2 Integration Point Mapping

For each file, identify:

- **Imports from**: Which other project files this file imports
- **Imported by**: Which other project files import this file
- **State reads**: Which AppState properties this file reads
- **State writes**: Which AppState properties this file mutates

This mapping prevents hidden coupling and makes cross-epic conflicts visible.

### 6.3 Prohibited Surface Descriptions

- "Various files" or "related files" -- name every file explicitly
- "Update as needed" -- specify the exact modification
- "Standard boilerplate" -- describe the content

---

## 7. Epic vs Task Distinction (BLOCKING)

### 7.1 What Is an Epic

An epic is a **buildable feature slice** that:

- Produces a single named deliverable
- Operates on a bounded file set (1-12 files)
- Requires 0.5-3 days of focused engineering work
- Has binary, verifiable completion criteria
- Can be demonstrated or tested in isolation

### 7.2 What Is NOT an Epic

| Item                            | Classification | Correct Treatment                      |
| ------------------------------- | -------------- | -------------------------------------- |
| "Set up Xcode"                  | Task           | Part of a project scaffold epic        |
| "Write unit tests"              | Task           | Part of the epic that builds the code  |
| "Code review"                   | Process step   | Not a planning artifact                |
| "Research API options"          | Spike          | Resolved before epic generation begins |
| "Fix that bug from last sprint" | Defect         | Separate fix branch, not an epic       |
| "Refactor AudioService"         | Epic           | Valid if it has a deliverable          |

### 7.3 Task-Level Contamination

If an epic's DoD contains items like "create the file", "add the import", "write the struct", these are implementation steps, not completion criteria. DoD items describe **observable outcomes**, not **development steps**.

**Prohibited DoD items:**

```
- [ ] Create HomeView.swift                 <- implementation step
- [ ] Import SwiftUI                        <- implementation step
- [ ] Add NavigationStack wrapper           <- implementation step
```

**Correct DoD items:**

```
- [ ] HomeView renders three entry cards on launch with correct typography
- [ ] Tapping a card navigates to the corresponding feature screen
- [ ] Unread badges display and clear based on sync state
```

---

## 8. Anti-Patterns (MUST REJECT)

### 8.1 Scope Anti-Patterns

| Anti-Pattern              | Description                                                   | Resolution                                 |
| ------------------------- | ------------------------------------------------------------- | ------------------------------------------ |
| **Scope Creep Epic**      | Epic includes "and also" work beyond its stated deliverable   | Remove the "and also" into a separate epic |
| **God Epic**              | Epic touches 15+ files across multiple systems                | Split by system boundary                   |
| **Ghost Dependency**      | Epic assumes prior work exists but does not declare it        | Add explicit dependency or halt            |
| **Wishful Thinking Epic** | DoD includes items the epic's file set cannot produce         | Align DoD to file set or expand file set   |
| **Copy-Paste Epic**       | Epic duplicates structure from another epic without tailoring | Rewrite from the design doc for this scope |
| **Infinite Scope Epic**   | No Out of Scope section, implying everything is in scope      | Add explicit exclusions                    |

### 8.2 DoD Anti-Patterns

| Anti-Pattern           | Description                                        | Resolution                            |
| ---------------------- | -------------------------------------------------- | ------------------------------------- |
| **Vibes-Based DoD**    | "App feels smooth", "UI looks polished"            | Replace with measurable criteria      |
| **Tautological DoD**   | "Feature works as designed"                        | State what "works" means concretely   |
| **Developer-Step DoD** | "Code compiles", "Tests written"                   | These are prerequisites, not outcomes |
| **Unbounded DoD**      | "All edge cases handled"                           | Name each edge case explicitly        |
| **Future-Tense DoD**   | "Will support dark mode", "Should handle rotation" | Present tense, binary: "does X"       |

---

## 9. Output Format

See [references/epic-format.md](references/epic-format.md) for the strict template every generated epic must follow.

See [references/scope-boundaries.md](references/scope-boundaries.md) for guidance on writing effective scope and out-of-scope sections.
