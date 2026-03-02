# Scope Boundary Writing Guide

Techniques for writing precise scope and out-of-scope sections that prevent drift, eliminate ambiguity, and enforce buildable boundaries.

## Scope Section Rules

### What Belongs in Scope

The Scope section answers one question: **what files does this epic touch, and what does it do to each one?**

Scope is defined by the file inventory. If a file is not in the inventory, it is not in scope. If a behavior requires a file not in the inventory, either add the file or move the behavior to a different epic.

### Scope Precision Spectrum

| Level     | Example                                                                                                                                                                     | Verdict    |
| --------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| Too vague | "Build the home screen"                                                                                                                                                     | Rejected   |
| Vague     | "Implement the filing cabinet UI and navigation"                                                                                                                            | Rejected   |
| Adequate  | "Create HomeView with three entry cards and unread badges"                                                                                                                  | Acceptable |
| Precise   | "Create HomeView.swift: three entry cards on `background.secondary` with warm layered shadow, SF Symbol icons in accent colors, unread dot badge with 2s breathing pulse animation, navigation via Router" | Target     |

### Scope Sentence Structure

Use this pattern for scope descriptions:

```
{Action verb} {component name} with {primary behavior}: {specific parameters from design doc}
```

Examples:

```
Create ContractBookView wrapping UIPageViewController with .pageCurl transition style and SwiftUI hosting
Define design system color tokens: 13 named colors per the design doc §6.2 light mode palette table
Modify AppState to add lastSyncAt Date with UserDefaults persistence keyed to "last_sync_at"
```

## Out-of-Scope Section Rules

### Purpose

Out of Scope protects the implementing engineer from scope creep by preemptively excluding work that adjacent stakeholders, future phases, or reasonable assumption might attach to this epic.

### Mandatory Exclusion Categories

Every Out of Scope section MUST contain at least one item from each of these categories:

| Category                | Question It Answers                                                 |
| ----------------------- | ------------------------------------------------------------------- |
| Adjacent features       | What nearby feature could someone assume is included?               |
| Later-phase work        | What follow-on work depends on this epic but is not part of it?     |
| Infrastructure changes  | What shared service or system change could this epic trigger?       |
| Polish and optimization | What refinement, animation tuning, or performance work is deferred? |

### Writing Effective Exclusions

**Good exclusions** are specific enough that an engineer would recognize the item as a potential scope addition:

```
- Sound effects on page-curl animation (deferred to sound design integration epic)
- Haptic feedback on signature placement (deferred to haptics integration epic)
- Push notification deep linking to specific content (covered by push notification epic)
- Dark mode color token variants (covered by design system epic, which defines both palettes)
```

**Bad exclusions** are generic statements that exclude nothing meaningful:

```
- Other features                    <- too vague, every engineer knows this
- Future enhancements               <- excludes nothing specific
- Performance optimization          <- what optimization? be specific
- Testing                           <- testing is part of every epic, not out of scope
```

### Exclusion Format

Each exclusion follows this pattern:

```
- {Specific work item} ({reason for exclusion or where it lives instead})
```

The parenthetical is mandatory. It tells the reader where the excluded work goes, preventing it from falling through the cracks.

## Boundary Conflict Resolution

When scope boundaries are ambiguous:

### Shared File Conflict

Two epics claim the same file. Resolution:

1. Determine which epic has the primary responsibility for the file
2. Assign the file to that epic
3. Extract the other epic's changes into a preparatory epic in an earlier phase
4. Document the extraction in both epics' Out of Scope sections

### Behavior Ownership Conflict

Two epics claim the same user-visible behavior. Resolution:

1. Identify which epic's deliverable directly produces the behavior
2. Assign the behavior to that epic
3. The other epic receives the behavior's prerequisite work only
4. Both epics' DoD must reflect the split cleanly

### Service Extension Conflict

Two feature epics need the same service to have a new method. Resolution:

1. Create a service-extension epic in the prior integration or infrastructure phase
2. That epic adds both methods to the service
3. Both feature epics list the service-extension epic as a dependency
4. Neither feature epic modifies the service file

## Scope Validation Checklist

Before finalizing an epic's scope:

- [ ] Every file in the file inventory has a single responsible epic
- [ ] No file appears in two epics within the same phase
- [ ] Every behavior in DoD traces to at least one file in the inventory
- [ ] Out of Scope contains minimum 3 items with parenthetical rationale
- [ ] All four exclusion categories are represented
- [ ] No generic exclusions ("other features", "future work")
- [ ] Adjacent epics' scopes do not overlap with this epic's scope
