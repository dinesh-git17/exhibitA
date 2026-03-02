# Python Engineering Baseline (2026)

Baseline for contract rule alignment with modern primary-source guidance.

## Skill and Enforcement

- Skills require YAML frontmatter with `name` and `description`; description is the trigger surface.
- Deterministic enforcement via executable validators returning explicit PASS/REJECT signals.
- JSON output with structured diagnostics for integration with tool and hook ecosystems.

## Python Runtime

- Require Python `>=3.13` as project baseline.
- Use modern typing syntax. Avoid legacy compatibility scaffolding unless forced by a dependency.

## Typing Discipline

- Full annotations on all public APIs.
- No `Any` leakage in public contracts.
- Typed collections (`list[str]`, `dict[str, int]`) instead of bare containers.
- mypy strict mode with zero failures.

## Ruff and Style

- Ruff as canonical lint and format toolchain.
- No overlapping stacks (`black`, `flake8`, `isort`) when Ruff replaces them.
- Both `ruff check` and `ruff format --check` gates required.

## Documentation and Comments

- Public modules, classes, and functions require docstrings.
- One docstring style consistently (Google or NumPy).
- Docstrings state intent and behavior, not signature repetition.
- Comments explain rationale and invariants. No narrative filler or stale TODO/FIXME clutter.

## Design and Reliability

- Functions small and single-purpose.
- Nesting depth limited for readability.
- Hidden side effects forbidden (module-level execution, mutable defaults, implicit global mutation).
- Bare except and silent failures forbidden.
- Structured logging for error paths.
- Deterministic import hygiene and testability with minimal mocking.

## Primary Sources (2026-03-02)

- Claude Code Skills: <https://docs.anthropic.com/en/docs/claude-code/skills>
- Claude Code Hooks: <https://docs.anthropic.com/en/docs/claude-code/hooks-guide>
- Agent Skills format: <https://agentskills.io/skills>
- Python 3.13+ documentation: <https://docs.python.org/3/>
- Python `type` statement: <https://docs.python.org/3/reference/simple_stmts.html#the-type-statement>
- Typing specification: <https://typing.python.org/en/latest/spec/>
- PEP 8: <https://peps.python.org/pep-0008/>
- PEP 257: <https://peps.python.org/pep-0257/>
- Ruff formatter: <https://docs.astral.sh/ruff/formatter/>
- Ruff configuration: <https://docs.astral.sh/ruff/settings/>
- mypy config and strict mode: <https://mypy.readthedocs.io/en/stable/config_file.html>
- mypy CLI strict mode: <https://mypy.readthedocs.io/en/stable/command_line.html>
- Google Python style guide: <https://google.github.io/styleguide/pyguide.html>
- NumPy docstring standard: <https://numpydoc.readthedocs.io/en/latest/format.html>
