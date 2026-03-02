---
name: git-ci-contract
description: Enforce Exhibit A's Git and CI governance contract with deterministic PASS/REJECT validation and structured rejection diagnostics. Use when creating, modifying, reviewing, or validating Git workflow policy, branch protections, commit conventions, PR gating, iOS CI workflows, backend CI workflows, SwiftLint policy, snapshot pipeline behavior, artifact size checks, or repository hygiene controls.
---

# Git & CI Contract

Strict contract enforcement. No advisory mode. Reject every violating change.

## Doctrine

All code must pass deterministic quality gates before merge. Version control is part of architecture, not developer convenience.

## Required Repo Governance Structure

Require all of the following:

- `.github/workflows/` with iOS and backend quality gates.
- Git governance config in `.github/rulesets/` and/or `.github/settings.yml` that encodes branch protections for `main`.
- Conventional commit enforcement via commitlint config (`commitlint.config.*` or `.commitlintrc*`) and CI execution.
- SwiftLint config file (`.swiftlint.yml` or `.swiftlint.yaml`) with required error severities.
- PR template checklist (`.github/pull_request_template.md` or `.github/PULL_REQUEST_TEMPLATE/*.md`).

## Validation

Run:

```bash
python3 .claude/skills/git-ci-contract/scripts/validate_git_ci_contract.py --root . --format json
```

- Exit code `0` and zero violations = `PASS`.
- Non-zero exit code = `REJECT`.
- Never waive or downgrade a rule.

## Contract Rules

### Git Workflow Governance

| Rule | Constraint |
|------|-----------|
| GCC001 | Conventional commits must be enforced with required types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore` |
| GCC002 | Branch naming policy must enforce `feature/<name>`, `fix/<name>`, `refactor/<name>` |
| GCC003 | Force pushes to `main` must be forbidden |
| GCC004 | Pull requests must be required for merges into `main` |
| GCC005 | Active branch must match naming policy (except `main`) |

### CI Structure and Gates

| Rule | Constraint |
|------|-----------|
| GCC000 | CI configuration must exist in repository (`.github/workflows`) |
| GCC047 | Quality gates must be defined for both iOS and backend pipelines |
| GCC046 | CI quality steps must not use `continue-on-error: true` |

### iOS Pipeline

| Rule | Constraint |
|------|-----------|
| GCC010 | iOS CI must run SwiftLint |
| GCC011 | iOS CI must build the project |
| GCC012 | iOS CI must run unit tests |
| GCC013 | iOS CI must run snapshot tests |

### Backend Pipeline

| Rule | Constraint |
|------|-----------|
| GCC020 | Backend CI must run `mypy` in strict mode |
| GCC021 | Backend CI must run `ruff check` |
| GCC022 | Backend CI must run `ruff format --check` |
| GCC023 | Backend CI must run `pytest` with coverage gate `>=90%` |

### Quality and Hygiene Controls

| Rule | Constraint |
|------|-----------|
| GCC030 | SwiftLint `force_unwrapping` must be `error` |
| GCC031 | SwiftLint `implicitly_unwrapped_optional` must be `error` |
| GCC032 | SwiftLint `force_cast` must be `error` |

### Artifact and Snapshot Discipline

| Rule | Constraint |
|------|-----------|
| GCC040 | CI must compare binary artifacts and alert/fail on `>10%` size growth |
| GCC041 | Snapshot reference images must be committed to repository |
| GCC042 | CI must upload snapshot diff artifacts on snapshot failures |

### Attribution and PR Governance

| Rule | Constraint |
|------|-----------|
| GCC043 | CI must scan for AI attribution markers and fail on matches |
| GCC044 | Repository content must not include AI attribution markers |
| GCC045 | PR template checklist must include tests pass, snapshot update, and no SwiftLint violations |

Reference baseline: `references/git-ci-2026-baseline.md`

## Output

Emit this exact structure:

```json
{
  "contract": "git-ci-contract",
  "verdict": "PASS | REJECT",
  "summary": {
    "files_scanned": 0,
    "rules_checked": 25,
    "violations": 0
  },
  "violations": [
    {
      "rule_id": "GCC000",
      "title": "...",
      "rejection": "REJECT: ...",
      "file": "path/to/file",
      "line": 1,
      "snippet": "offending line"
    }
  ]
}
```

If `verdict` is `REJECT`, block approval until every violation is resolved.
