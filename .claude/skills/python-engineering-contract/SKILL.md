---
name: python-engineering-contract
description: Enforce a strict Python engineering contract with deterministic PASS/REJECT validation and structured rejection diagnostics. Use when creating, modifying, reviewing, refactoring, or validating Python codebases, modules, services, scripts, tests, and project configuration where Python 3.13+, Ruff, mypy strict typing, docstring quality, import hygiene, error handling, logging discipline, and maintainable design must be contractually enforced.
---

# Python Engineering Contract

Strict contract enforcement. No advisory mode. Reject every violating change.

## Doctrine

Python code must be readable, typed, testable, and maintainable by engineers who trust it blindly.

Treat sloppy formatting, weak typing, unclear logic, and hidden behavior as architectural violations.

## Expected Project Shape

Validate against this baseline structure:

```text
<repo>/
  pyproject.toml
  src/<package>/...
  tests/...
```

Equivalent package-first layouts are allowed when they preserve clear source vs test separation.

## Validation

Run:

```bash
python3 .claude/skills/python-engineering-contract/scripts/validate_python_engineering_contract.py --root . --format json
```

- Exit code `0` and zero violations = `PASS`.
- Non-zero exit code = `REJECT`.
- Never waive, downgrade, or reinterpret a rule.

## Contract Rules

### Baseline

| Rule | Constraint |
|------|-----------|
| PEC000 | Python source files must exist and parse successfully |
| PEC001 | Python runtime must be pinned to `>=3.13` |
| PEC026 | Project structure must include clear source and tests layout |

### Formatting and Linting

| Rule | Constraint |
|------|-----------|
| PEC002 | Ruff must be configured for linting and formatting |
| PEC003 | `black`, `flake8`, and `isort` are forbidden when Ruff is canonical |
| PEC004 | `ruff check` and `ruff format --check` must pass with zero violations |
| PEC013 | Naming and baseline style must follow PEP 8 |

### Typing Discipline

| Rule | Constraint |
|------|-----------|
| PEC005 | mypy strict mode configuration must exist |
| PEC006 | mypy strict run must pass |
| PEC009 | All public functions must have full type annotations |
| PEC010 | `Any` and implicit `Any` usage in public APIs are forbidden |
| PEC011 | Typed collections required (`list[str]`, `dict[str, int]`, etc.) |
| PEC012 | Runtime-only typing hacks are forbidden (`# type: ignore`, `cast(Any, ...)`) |

### Docstrings and Comments

| Rule | Constraint |
|------|-----------|
| PEC007 | Every public module, class, and function must include a docstring |
| PEC008 | Docstrings must explain intent and use one consistent style (Google or NumPy) |
| PEC024 | Comments must explain reasoning; stale/redundant comments are forbidden |

### Structure and Determinism

| Rule | Constraint |
|------|-----------|
| PEC014 | Functions must be small and single-purpose |
| PEC015 | Deeply nested logic is forbidden |
| PEC016 | Hidden side effects are forbidden |

### Error Handling and Logging

| Rule | Constraint |
|------|-----------|
| PEC017 | Bare `except` blocks are forbidden |
| PEC018 | Silent failures are forbidden |
| PEC022 | `print()` is forbidden in production code |
| PEC023 | Structured logging is required in error paths |

### Imports and Testing

| Rule | Constraint |
|------|-----------|
| PEC019 | Imports must be ordered: standard library, third-party, local |
| PEC020 | Unused imports are forbidden |
| PEC021 | Wildcard imports are forbidden |
| PEC025 | Testing must avoid heavy mocking patterns |

Reference baseline: `references/python-engineering-baseline-2026.md`

## Output

Emit this exact structure:

```json
{
  "contract": "python-engineering-contract",
  "verdict": "PASS | REJECT",
  "summary": {
    "files_scanned": 0,
    "rules_checked": 27,
    "violations": 0
  },
  "violations": [
    {
      "rule_id": "PEC000",
      "title": "...",
      "rejection": "REJECT: ...",
      "file": "path/to/file.py",
      "line": 1,
      "snippet": "offending code"
    }
  ]
}
```

If `verdict` is `REJECT`, block approval until every violation is resolved.
