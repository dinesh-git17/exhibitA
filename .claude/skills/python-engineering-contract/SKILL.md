---
name: python-engineering-contract
description: Enforce a strict Python engineering contract with deterministic PASS/REJECT validation and structured rejection diagnostics. Use when creating, modifying, reviewing, refactoring, or validating Python codebases, modules, services, scripts, tests, and project configuration where Python 3.13+, Ruff, mypy strict typing, docstring quality, import hygiene, error handling, logging discipline, and maintainable design must be contractually enforced.
---

# Python Engineering Contract

Strict contract enforcement. No advisory mode. Reject every violating change.

## Preconditions

Before running validation, confirm all three hold:

1. Target directory contains at least one `.py` file.
2. `ruff` and `mypy` are installed and on `$PATH`.
3. `pyproject.toml` or equivalent config exists at the repository root.

If any precondition fails, report the specific missing requirement and halt. Do not proceed to validation.

## Execution

Run the validator against the target root:

```bash
python3 .claude/skills/python-engineering-contract/scripts/validate_python_engineering_contract.py --root <target> --format json
```

Parse the result:

- Exit code `0` with zero violations: verdict is `PASS`. No action required.
- Non-zero exit code: verdict is `REJECT`. Enumerate every violation from the JSON output, fix each one, then re-run until `PASS`.

Never waive, downgrade, or reinterpret a rule. Never mark work complete while violations remain.

## Expected Project Shape

```text
<repo>/
  pyproject.toml
  src/<package>/...
  tests/...
```

Equivalent layouts accepted when source and test directories are clearly separated.

## Contract Rules

### Baseline

| Rule   | Constraint                                               |
| ------ | -------------------------------------------------------- |
| PEC000 | Python source files exist and parse successfully         |
| PEC001 | Python runtime pinned to `>=3.13`                        |
| PEC026 | Project structure includes clear source and tests layout |

### Formatting and Linting

| Rule   | Constraint                                                       |
| ------ | ---------------------------------------------------------------- |
| PEC002 | Ruff configured for linting and formatting                       |
| PEC003 | `black`, `flake8`, `isort` forbidden when Ruff is canonical      |
| PEC004 | `ruff check` and `ruff format --check` pass with zero violations |
| PEC013 | PEP 8 naming and baseline style                                  |

### Typing Discipline

| Rule   | Constraint                                                          |
| ------ | ------------------------------------------------------------------- |
| PEC005 | mypy strict mode configuration exists                               |
| PEC006 | mypy strict run passes                                              |
| PEC009 | All public functions fully type-annotated                           |
| PEC010 | `Any` and implicit `Any` in public APIs forbidden                   |
| PEC011 | Typed collections required (`list[str]`, `dict[str, int]`)          |
| PEC012 | Runtime typing hacks forbidden (`# type: ignore`, `cast(Any, ...)`) |

### Docstrings and Comments

| Rule   | Constraint                                                         |
| ------ | ------------------------------------------------------------------ |
| PEC007 | Every public module, class, and function has a docstring           |
| PEC008 | Docstrings explain intent; one consistent style (Google or NumPy)  |
| PEC024 | Comments explain reasoning; stale and redundant comments forbidden |

### Structure and Determinism

| Rule   | Constraint                         |
| ------ | ---------------------------------- |
| PEC014 | Functions small and single-purpose |
| PEC015 | Deeply nested logic forbidden      |
| PEC016 | Hidden side effects forbidden      |

### Error Handling and Logging

| Rule   | Constraint                                 |
| ------ | ------------------------------------------ |
| PEC017 | Bare `except` blocks forbidden             |
| PEC018 | Silent failures forbidden                  |
| PEC022 | `print()` forbidden in production code     |
| PEC023 | Structured logging required in error paths |

### Imports and Testing

| Rule   | Constraint                                         |
| ------ | -------------------------------------------------- |
| PEC019 | Import order: stdlib, then third-party, then local |
| PEC020 | Unused imports forbidden                           |
| PEC021 | Wildcard imports forbidden                         |
| PEC025 | Heavy mocking patterns forbidden                   |

Reference baseline: `references/python-engineering-baseline-2026.md`

## Output Schema

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
