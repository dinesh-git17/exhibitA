---
name: memory-manager
description: Manages persistent memory across Claude Code sessions. Triggers automatically at session start (load context), after completing major implementations, after architectural or technical decisions, after git pushes, and at session end or when the user invokes /save-memory. Reads and writes to the auto memory directory at ~/.claude/projects/.../memory/.
---

# Memory Manager

## Memory Location

Persistent memory lives at the Claude Code auto memory path:

```
~/.claude/projects/-Users-Dinesh-Desktop-exhibitA/memory/
```

`MEMORY.md` is the primary file (auto-loaded into context every session).
Additional topic files (e.g., `decisions.md`, `progress.md`) can be created
for detailed notes and linked from MEMORY.md.

## Trigger Points

Update memory at each of these events:

### 1. Session Start

- Read MEMORY.md and any linked topic files.
- If a `Next Session` section exists in any topic file, read it, act on it,
  then clear it.
- Confirm context loaded with a one-line summary. Do not echo file contents.

### 2. After Major Implementations

When a feature, module, or significant code change is completed:

- Record what was built and key patterns chosen in the appropriate section.
- Update stack/conventions in MEMORY.md if something material changed.
- Add new file paths or module names to project context if relevant.

### 3. After Architectural or Technical Decisions

When a design choice, technology selection, or trade-off is made:

- Append a dated entry to a `## Decisions` section (or `decisions.md` topic file).
- Format: `- YYYY-MM-DD: <decision summary> -- <rationale>`
- Never delete or rewrite existing decision entries. Append only.

### 4. After Git Pushes

When code is pushed to a remote branch:

- Record the branch name, PR number (if created), and a one-line summary.
- Move completed work items out of any "In Flight" tracking.
- Update progress state so the next session has accurate context.

### 5. Session End / /save-memory

Full memory sync. Review the entire session and:

- Update MEMORY.md with any material changes to project identity, stack,
  conventions, or constraints.
- Append decisions made this session (dated, append-only).
- Update progress: completed items, in-flight state, blockers.
- Write a `## Next Session` note summarizing where to pick up.
- Confirm each file written with its path.

## Write Rules

| Target               | Strategy                                                     |
| -------------------- | ------------------------------------------------------------ |
| MEMORY.md            | Update in place. Keep under 200 lines (truncation boundary). |
| Topic files          | Create as needed. Link from MEMORY.md.                       |
| Decisions            | Append only. Never delete or rewrite past entries.           |
| Progress / In Flight | Rewrite to reflect current state.                            |
| Completed items      | Append with date. Never delete.                              |
| Next Session         | Write at session end. Clear at session start.                |

## Rules

- Prefer updating existing sections over creating new topic files.
- MEMORY.md must stay under 200 lines. Move detail to topic files.
- Use the Edit tool to update in place. Do not recreate files.
- Entries must be concise and scannable, not exhaustive.
- Do not duplicate information already in CLAUDE.md or the design doc.
- If memory files do not exist, create them with minimal headers.
- Never store secrets, credentials, or environment-specific paths.
