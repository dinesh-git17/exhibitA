# ~/.claude/commands/optimize-skill.md

## Usage: /optimize-skill <path-to-draft-skill-directory>

You are optimizing a skill package that was drafted by an external AI model (e.g. Codex, Gemini).
The research and content are complete. Do not re-research, verify, or web search anything.

Your job is a single-pass rewrite and packaging pass optimized specifically for Claude Code's reasoning engine.

---

INPUTS:

- Draft skill directory: $ARGUMENTS
- Reference: .claude/skills/skill-creator/SKILL.md

---

TASK:

1. Read .claude/skills/skill-creator/SKILL.md to internalize Claude-specific skill conventions and packaging requirements
2. List all files in the draft directory at $ARGUMENTS
3. Read every file found — SKILL.md, reference files, and scripts
4. For each file, apply the appropriate optimization pass:

   SKILL.md:
   - Reorder instructions to match Claude's step prioritization (preconditions before actions)
   - Explicit tool call sequencing — which tools, in what order, under what conditions
   - Decision branching written as Claude parses it, not generic pseudocode
   - Remove phrasing that implies another model's reasoning style (over-explained rationale, hedging language, chain-of-thought narration meant for the reader)
   - Tighten language — every sentence must constrain behavior, not describe it
   - Ensure reference files and scripts are referenced correctly by path

   Reference files:
   - Preserve all domain knowledge and research content untouched
   - Fix formatting inconsistencies that would cause Claude to misparse structure
   - Ensure headers, tables, and code blocks follow conventions from skill-creator

   Scripts:
   - Preserve logic and intent exactly
   - Fix any syntax or compatibility issues for the Claude Code execution environment
   - Ensure scripts are callable from SKILL.md instructions as written

5. Write each optimized file back to its original path
6. Package the skill per the skill-creator packaging conventions — verify directory structure, naming, and any required metadata are correct

---

CONSTRAINTS:

- No web search
- No file reads beyond $ARGUMENTS directory and .claude/skills/skill-creator/SKILL.md
- No clarifying questions
- Single pass — optimize and package in one run, no follow-up prompts
- No commentary, change summaries, or explanations in output
