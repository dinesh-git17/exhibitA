# Git & CI 2026 Baseline

Use this baseline when applying `git-ci-contract` to repositories.

## Research Snapshot (March 2, 2026)

- GitHub governance controls: protected branches/rulesets can require pull requests before merge and disable force pushes.
- Conventional Commits + commitlint: enforce typed commit prefixes through `type-enum` and CI execution.
- SwiftLint rule docs: `force_unwrapping`, `implicitly_unwrapped_optional`, and `force_cast` are configurable and should be elevated to `error`.
- Ruff and mypy docs: strict static checks should be enforced in CI (`ruff check`, `ruff format --check`, `mypy --strict` or strict config).
- pytest-cov docs: enforce coverage gates with `--cov-fail-under`.
- Snapshot testing docs: reference snapshots must be stored in repository (`__Snapshots__` / `ReferenceImages`) and failures should produce diff artifacts.
- GitHub artifact actions: CI can upload/download artifacts to compare current and baseline outputs (used for binary-size growth checks).
- Repository hygiene: policy-as-code scanning with denylist regex patterns is a deterministic way to block unwanted attribution markers.

## Contract Implications

- Treat commit discipline and CI gates as architectural controls.
- Reject any missing or weakly-configured gate.
- Require deterministic diagnostics with rule IDs and file/line anchoring.
