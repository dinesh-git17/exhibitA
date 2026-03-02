#!/usr/bin/env python3
"""Validate a strict Python engineering contract deterministically."""
# pylint: disable=too-many-lines

from __future__ import annotations

import argparse
import ast
import io
import json
import re
import shutil
import subprocess
import sys
import tokenize
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypedDict

CONTRACT_NAME = "python-engineering-contract"
MIN_PYTHON = (3, 13, 0)

RULE_TITLES = {
    "PEC000": "Python source files must exist and parse successfully",
    "PEC001": "Python runtime must be pinned to >=3.13",
    "PEC002": "Ruff must be configured for linting and formatting",
    "PEC003": "black/flake8/isort are forbidden when Ruff is canonical",
    "PEC004": "Ruff check and format --check must pass with zero violations",
    "PEC005": "mypy strict mode configuration must exist",
    "PEC006": "mypy strict type-check run must pass",
    "PEC007": "Public modules, classes, and functions must have docstrings",
    "PEC008": "Docstrings must be intent-focused and consistently Google/NumPy style",
    "PEC009": "Public functions must have full type annotations",
    "PEC010": "Any and implicit Any usage in public APIs is forbidden",
    "PEC011": "Public API annotations must use typed collections",
    "PEC012": "Runtime-only typing hacks are forbidden",
    "PEC013": "Naming and baseline style must follow PEP 8",
    "PEC014": "Functions must remain small and single-purpose",
    "PEC015": "Deeply nested control flow is forbidden",
    "PEC016": "Hidden side effects are forbidden",
    "PEC017": "Bare except blocks are forbidden",
    "PEC018": "Silent error handling is forbidden",
    "PEC019": "Imports must be ordered stdlib -> third-party -> local",
    "PEC020": "Unused imports are forbidden",
    "PEC021": "Wildcard imports are forbidden",
    "PEC022": "print() is forbidden in production code",
    "PEC023": "Structured logging must be used in error paths",
    "PEC024": "Comments must explain reasoning, not narration or stale TODOs",
    "PEC025": "Testing must avoid heavy mocking patterns",
    "PEC026": "Project structure must include clear source and tests layout",
}

IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".build",
    ".idea",
    ".vscode",
    ".tox",
    ".nox",
    ".claude",
}

IMPORT_LEVELS = {"debug", "info", "warning", "error", "exception", "critical"}
UNTYPED_COLLECTIONS = {"list", "dict", "set", "tuple", "List", "Dict", "Set", "Tuple"}
CONTROL_NODES = (
    ast.If,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.With,
    ast.AsyncWith,
    ast.Try,
    ast.Match,
)

COMMENT_REDUNDANT_RE = [
    re.compile(
        r"^#\s*(set|sets|initialize|initializes|increment|increments|decrement|decrements)\b",
        re.IGNORECASE,
    ),
    re.compile(r"^#\s*this\s+(function|method|class)\b", re.IGNORECASE),
    re.compile(r"^#\s*call\b", re.IGNORECASE),
]

PACKAGE_RE = re.compile(r"^[a-z_][a-z0-9_]*$")
CLASS_RE = re.compile(r"^[A-Z][A-Za-z0-9]+$")
PYTHON_VERSION_RE = re.compile(r"(\d+)\.(\d+)(?:\.(\d+))?")

DocNode = ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef


@dataclass(frozen=True)
class Violation:
    """Single deterministic contract violation."""

    rule_id: str
    title: str
    rejection: str
    file: str
    line: int
    snippet: str

    def as_dict(self) -> ViolationOutput:
        """Convert the violation into the contract JSON shape."""
        return {
            "rule_id": self.rule_id,
            "title": self.title,
            "rejection": self.rejection,
            "file": self.file,
            "line": self.line,
            "snippet": self.snippet,
        }


SummaryOutput = TypedDict(  # noqa: UP013
    "SummaryOutput",
    {"files_scanned": int, "rules_checked": int, "violations": int},
)
ViolationOutput = TypedDict(  # noqa: UP013
    "ViolationOutput",
    {
        "rule_id": str,
        "title": str,
        "rejection": str,
        "file": str,
        "line": int,
        "snippet": str,
    },
)
ResultOutput = TypedDict(  # noqa: UP013
    "ResultOutput",
    {
        "contract": str,
        "verdict": Literal["PASS", "REJECT"],
        "summary": SummaryOutput,
        "violations": list[ViolationOutput],
    },
)


def _line_snippet(text: str) -> str:
    return text.strip()[:220]


def _parse_version(text: str) -> tuple[int, int, int] | None:
    match = PYTHON_VERSION_RE.search(text)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2)), int(match.group(3) or 0)


def _version_ge(left: tuple[int, int, int], right: tuple[int, int, int]) -> bool:
    return left >= right


def _spec_allows_minimum(spec: str, minimum: tuple[int, int, int]) -> bool:
    cleaned = spec.strip().strip("\"'")
    if not cleaned:
        return False

    direct = _parse_version(cleaned)
    if direct is not None and _version_ge(direct, minimum):
        return True

    # Handles common specifiers: >=3.13,<4.0 ; ^3.13 ; ~=3.13 ; ==3.13
    entries = re.findall(r"(>=|>|==|~=|\^|<=|<)?\s*(\d+\.\d+(?:\.\d+)?)", cleaned)
    if not entries:
        return False

    allow = False
    for op, version_txt in entries:
        parsed = _parse_version(version_txt)
        if parsed is None:
            continue
        if op in {"", "==", "~=", "^", ">="} and _version_ge(parsed, minimum):
            allow = True
        if op == ">" and parsed >= minimum:
            allow = True
    return allow


def _annotation_text(node: ast.expr | None) -> str:
    if node is None:
        return ""
    try:
        return ast.unparse(node)
    except (AttributeError, TypeError, ValueError):
        return ""


def _annotation_root(annotation: str) -> str:
    text = annotation.strip()
    if not text:
        return ""
    if text.startswith("Annotated["):
        text = text[len("Annotated[") :].split(",", 1)[0].strip()
    text = text.split("|", 1)[0].strip()
    text = text.split("[", 1)[0].strip()
    return text.split(".")[-1]


def _contains_any(annotation: str) -> bool:
    base = annotation.replace("typing.", "")
    return bool(re.search(r"\bAny\b", base))


def _has_untyped_collection(annotation: str) -> bool:
    root = _annotation_root(annotation)
    return root in UNTYPED_COLLECTIONS and "[" not in annotation


def _is_name_main_guard(node: ast.If) -> bool:
    test = node.test
    if not isinstance(test, ast.Compare):
        return False
    if len(test.ops) != 1 or len(test.comparators) != 1:
        return False
    if not isinstance(test.ops[0], ast.Eq):
        return False
    left = test.left
    right = test.comparators[0]
    if not (isinstance(left, ast.Name) and left.id == "__name__"):
        return False
    return isinstance(right, ast.Constant) and right.value == "__main__"


def _doc_style(doc: str) -> str:
    stripped = doc.strip()
    has_google = any(
        section in stripped for section in ("Args:", "Returns:", "Raises:")
    )
    has_numpy = "\nParameters\n" in stripped or stripped.startswith("Parameters\n")
    if has_google and not has_numpy:
        return "google"
    if has_numpy and not has_google:
        return "numpy"
    if has_google and has_numpy:
        return "mixed"
    return "none"


class ContractValidator:
    """Deterministic validator for Python engineering contract rules."""

    def __init__(self, root: Path):
        self.root = root.resolve()
        self.violations: list[Violation] = []
        self._seen: set[tuple[str, str, int, str]] = set()
        self.text_cache: dict[Path, str] = {}
        self.lines_cache: dict[Path, list[str]] = {}
        self.ast_cache: dict[Path, ast.Module] = {}
        self.comments_cache: dict[Path, set[int]] = {}

        self.python_files = self._collect_files("*.py")
        self.service_files = [p for p in self.python_files if not self._is_test_path(p)]
        self.test_files = [p for p in self.python_files if self._is_test_path(p)]
        self.config_files = self._collect_config_files()
        self.local_packages = self._discover_local_packages()
        self.files_scanned = len(self.python_files) + len(self.config_files)

        self._parse_asts()

    def _is_ignored(self, path: Path) -> bool:
        return any(part in IGNORED_DIRS for part in path.parts)

    def _is_test_path(self, path: Path) -> bool:
        normalized = path.as_posix().lower()
        return (
            "/tests/" in normalized
            or normalized.endswith("_test.py")
            or normalized.endswith("test_.py")
            or normalized.endswith("tests.py")
            or "/test/" in normalized
        )

    def _collect_files(self, pattern: str) -> list[Path]:
        files: list[Path] = []
        for path in self.root.rglob(pattern):
            if not path.is_file():
                continue
            if self._is_ignored(path):
                continue
            files.append(path)
        return sorted(files)

    def _collect_config_files(self) -> list[Path]:
        explicit_names = {
            "pyproject.toml",
            ".python-version",
            "mypy.ini",
            ".mypy.ini",
            "setup.cfg",
            "tox.ini",
            "ruff.toml",
            ".ruff.toml",
            "requirements.txt",
            "requirements-dev.txt",
            "requirements-prod.txt",
            ".pre-commit-config.yaml",
            "Pipfile",
            "Pipfile.lock",
            "poetry.lock",
            "Makefile",
        }
        files: list[Path] = []
        for path in self.root.rglob("*"):
            if not path.is_file() or self._is_ignored(path):
                continue
            if path.name in explicit_names:
                files.append(path)
                continue
            if path.name.endswith((".toml", ".ini", ".cfg")):
                if any(
                    token in path.name
                    for token in ("pyproject", "ruff", "mypy", "pytest")
                ):
                    files.append(path)
            if path.name.startswith("requirements") and path.name.endswith(".txt"):
                files.append(path)
        return sorted(set(files))

    def _discover_local_packages(self) -> set[str]:
        names: set[str] = set()
        src_root = self.root / "src"
        if src_root.is_dir():
            for pkg_init in src_root.glob("*/__init__.py"):
                names.add(pkg_init.parent.name)
        for pkg_init in self.root.glob("*/__init__.py"):
            if pkg_init.parent.name not in IGNORED_DIRS:
                names.add(pkg_init.parent.name)
        return names

    def _read_text(self, path: Path) -> str:
        if path not in self.text_cache:
            self.text_cache[path] = path.read_text(encoding="utf-8", errors="ignore")
        return self.text_cache[path]

    def _read_lines(self, path: Path) -> list[str]:
        if path not in self.lines_cache:
            self.lines_cache[path] = self._read_text(path).splitlines()
        return self.lines_cache[path]

    def _relative(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.root).as_posix()
        except ValueError:
            return path.as_posix()

    def _add(
        self, rule_id: str, path: Path, line: int, message: str, snippet: str
    ) -> None:
        rel = self._relative(path)
        key = (rule_id, rel, max(1, line), snippet)
        if key in self._seen:
            return
        self._seen.add(key)
        self.violations.append(
            Violation(
                rule_id=rule_id,
                title=RULE_TITLES[rule_id],
                rejection=f"REJECT: {message}",
                file=rel,
                line=max(1, line),
                snippet=snippet,
            )
        )

    def _add_project(self, rule_id: str, message: str, snippet: str) -> None:
        self._add(rule_id, self.root / "PROJECT_ROOT", 1, message, snippet)

    def _parse_asts(self) -> None:
        for path in self.service_files + self.test_files:
            text = self._read_text(path)
            try:
                self.ast_cache[path] = ast.parse(text)
            except SyntaxError as exc:
                self._add(
                    "PEC000",
                    path,
                    exc.lineno or 1,
                    "Python files must parse successfully for deterministic validation.",
                    "syntax error",
                )

    def _comment_lines(self, path: Path) -> set[int]:
        if path in self.comments_cache:
            return self.comments_cache[path]
        lines: set[int] = set()
        reader = io.StringIO(self._read_text(path)).readline
        try:
            for token in tokenize.generate_tokens(reader):
                if token.type == tokenize.COMMENT:
                    lines.add(token.start[0])
        except tokenize.TokenError:
            pass
        self.comments_cache[path] = lines
        return lines

    def _run_command(self, command: list[str]) -> tuple[int, str, str]:
        proc = subprocess.run(
            command,
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )
        return proc.returncode, proc.stdout, proc.stderr

    def _config_blob(self) -> str:
        return "\n".join(self._read_text(path) for path in self.config_files)

    def _extract_python_specs(self) -> list[tuple[Path, int, str]]:
        specs: list[tuple[Path, int, str]] = []
        pyproject_re = re.compile(r"requires-python\s*=\s*['\"]([^'\"]+)['\"]")
        poetry_re = re.compile(r"^\s*python\s*=\s*['\"]([^'\"]+)['\"]")

        for path in self.config_files:
            lines = self._read_lines(path)
            for idx, line in enumerate(lines, start=1):
                if path.name == ".python-version":
                    stripped = line.strip()
                    if stripped:
                        specs.append((path, idx, stripped))
                        break
                m1 = pyproject_re.search(line)
                if m1:
                    specs.append((path, idx, m1.group(1).strip()))
                m2 = poetry_re.search(line)
                if m2:
                    specs.append((path, idx, m2.group(1).strip()))
        return specs

    def _check_python_runtime(self) -> None:
        specs = self._extract_python_specs()
        if not specs:
            self._add_project(
                "PEC001",
                "Pin Python runtime to >=3.13 in pyproject.toml or .python-version.",
                "missing runtime pin",
            )
            return

        if not any(_spec_allows_minimum(spec, MIN_PYTHON) for _, _, spec in specs):
            path, line, spec = specs[0]
            self._add(
                "PEC001",
                path,
                line,
                "Python runtime must be >=3.13.",
                spec,
            )

    def _check_ruff_configuration(self) -> None:
        blob = self._config_blob()
        has_ruff_toml = any(
            path.name in {"ruff.toml", ".ruff.toml"} for path in self.config_files
        )
        has_ruff_section = "[tool.ruff" in blob or has_ruff_toml
        has_ruff_dep = bool(re.search(r"\bruff\b", blob))

        if not (has_ruff_section or has_ruff_dep):
            self._add_project(
                "PEC002",
                "Configure Ruff as the canonical lint+format tool.",
                "missing Ruff configuration",
            )

        for path in self.config_files:
            for idx, line in enumerate(self._read_lines(path), start=1):
                stripped = line.split("#", 1)[0].strip()
                if not stripped:
                    continue

                if re.match(r"^\[tool\.black\]$", stripped, re.IGNORECASE) or re.match(
                    r"^black(?:\s*[<>=!~].*)?$", stripped, re.IGNORECASE
                ):
                    self._add(
                        "PEC003",
                        path,
                        idx,
                        "black is forbidden when Ruff replaces lint/format/import sorting.",
                        _line_snippet(line),
                    )

                if re.match(r"^\[flake8\]$", stripped, re.IGNORECASE) or re.match(
                    r"^flake8(?:\s*[<>=!~].*)?$", stripped, re.IGNORECASE
                ):
                    self._add(
                        "PEC003",
                        path,
                        idx,
                        "flake8 is forbidden when Ruff replaces lint/format/import sorting.",
                        _line_snippet(line),
                    )

                if re.match(r"^\[tool\.isort\]$", stripped, re.IGNORECASE) or re.match(
                    r"^isort(?:\s*[<>=!~].*)?$", stripped, re.IGNORECASE
                ):
                    self._add(
                        "PEC003",
                        path,
                        idx,
                        "isort is forbidden when Ruff replaces lint/format/import sorting.",
                        _line_snippet(line),
                    )

                if (
                    re.search(r"\b(?:black|flake8|isort)\b", stripped)
                    and "repo:" in stripped
                ):
                    self._add(
                        "PEC003",
                        path,
                        idx,
                        "Legacy formatting/lint hooks are forbidden when Ruff is canonical.",
                        _line_snippet(line),
                    )

    def _check_ruff_execution(self) -> None:
        if not self.python_files:
            return

        binary = shutil.which("ruff")
        if binary is None:
            self._add_project(
                "PEC004",
                "Install Ruff so contract validation can run ruff check/format gates.",
                "ruff executable not found",
            )
            return

        check_code, check_stdout, check_stderr = self._run_command(
            [binary, "check", ".", "--output-format", "json"]
        )
        if check_code != 0:
            snippet = "ruff check failed"
            path = self.root / "PROJECT_ROOT"
            line = 1
            if check_stdout.strip().startswith("["):
                try:
                    payload = json.loads(check_stdout)
                    if payload:
                        first = payload[0]
                        filename = first.get("filename", "PROJECT_ROOT")
                        path = self.root / filename
                        location = first.get("location", {})
                        line = int(location.get("row", 1) or 1)
                        code = first.get("code", "")
                        message = first.get("message", "")
                        snippet = f"{code} {message}".strip()
                except json.JSONDecodeError:
                    snippet = _line_snippet(check_stdout)
            else:
                snippet = _line_snippet(check_stdout or check_stderr)
            self._add(
                "PEC004",
                path,
                line,
                "ruff check must pass with zero violations.",
                snippet,
            )

        fmt_code, fmt_stdout, fmt_stderr = self._run_command(
            [binary, "format", ".", "--check"]
        )
        if fmt_code != 0:
            self._add_project(
                "PEC004",
                "ruff format --check must pass with zero formatting changes.",
                _line_snippet(fmt_stdout or fmt_stderr or "ruff format --check failed"),
            )

    def _check_mypy_configuration(self) -> None:
        blob = self._config_blob()
        has_strict_flag = bool(re.search(r"\bstrict\s*=\s*true\b", blob, re.IGNORECASE))
        has_cli_strict = "--strict" in blob
        if not (has_strict_flag or has_cli_strict):
            self._add_project(
                "PEC005",
                "Configure mypy strict mode (strict=true or --strict in CI/pre-commit).",
                "missing mypy strict configuration",
            )

    def _check_mypy_execution(self) -> None:
        if not self.python_files:
            return

        binary = shutil.which("mypy")
        if binary is None:
            self._add_project(
                "PEC006",
                "Install mypy so strict typing gate can be executed.",
                "mypy executable not found",
            )
            return

        code, stdout, stderr = self._run_command(
            [
                binary,
                "--strict",
                "--hide-error-context",
                "--no-color-output",
                "--no-error-summary",
                ".",
            ]
        )
        if code != 0:
            first = next(
                (
                    line.strip()
                    for line in (stdout + "\n" + stderr).splitlines()
                    if line.strip()
                ),
                "mypy strict failed",
            )
            self._add_project(
                "PEC006",
                "mypy --strict must pass with zero type errors.",
                _line_snippet(first),
            )

    def _iter_public_nodes(self, path: Path) -> list[tuple[str, DocNode]]:
        tree = self.ast_cache.get(path)
        if tree is None:
            return []

        output: list[tuple[str, DocNode]] = [("module", tree)]
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                output.append(("class", node))
            if isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef)
            ) and not node.name.startswith("_"):
                output.append(("function", node))
        return output

    def _check_docstrings(self) -> None:
        styles_seen: set[str] = set()

        for path in self.service_files:
            tree = self.ast_cache.get(path)
            if tree is None:
                continue

            module_doc = ast.get_docstring(tree)
            if not module_doc:
                self._add(
                    "PEC007",
                    path,
                    1,
                    "Public modules must include a module docstring.",
                    self._read_lines(path)[0] if self._read_lines(path) else "",
                )
            else:
                first = module_doc.strip().splitlines()[0]
                if len(first.split()) < 4:
                    self._add(
                        "PEC008",
                        path,
                        1,
                        "Docstrings must explain intent, not minimal restatements.",
                        _line_snippet(first),
                    )

            for kind, node in self._iter_public_nodes(path):
                if kind == "module":
                    continue
                doc = ast.get_docstring(node)
                lineno = getattr(node, "lineno", 1)
                if not doc:
                    public_name = getattr(node, "name", "<module>")
                    self._add(
                        "PEC007",
                        path,
                        lineno,
                        f"Public {kind} '{public_name}' must include a docstring.",
                        getattr(node, "name", ""),
                    )
                    continue

                style = _doc_style(doc)
                if style in {"none", "mixed"}:
                    self._add(
                        "PEC008",
                        path,
                        lineno,
                        "Docstrings must follow a consistent Google or NumPy style.",
                        _line_snippet(doc.splitlines()[0]),
                    )
                else:
                    styles_seen.add(style)

                first_line = doc.strip().splitlines()[0]
                name = getattr(node, "name", "")
                if first_line.lower().startswith(f"{name.lower()}("):
                    self._add(
                        "PEC008",
                        path,
                        lineno,
                        "Docstrings must capture intent rather than restating signatures.",
                        _line_snippet(first_line),
                    )

        if len(styles_seen) > 1:
            self._add_project(
                "PEC008",
                "Use one docstring style consistently across public APIs (Google or NumPy).",
                f"mixed styles detected: {', '.join(sorted(styles_seen))}",
            )

    def _public_functions(
        self, path: Path
    ) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
        tree = self.ast_cache.get(path)
        if tree is None:
            return []
        funcs: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
        for node in ast.walk(tree):
            if isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef)
            ) and not node.name.startswith("_"):
                funcs.append(node)
        return funcs

    def _check_typing(self) -> None:
        hack_pattern = re.compile(r"#\s*type:\s*ignore|\bcast\s*\(\s*Any\b")

        for path in self.service_files:
            for idx, line in enumerate(self._read_lines(path), start=1):
                if hack_pattern.search(line):
                    self._add(
                        "PEC012",
                        path,
                        idx,
                        "Runtime-only typing escape hatches are forbidden in production code.",
                        _line_snippet(line),
                    )

            for node in self._public_functions(path):
                missing: list[str] = []
                any_usage: list[str] = []
                untyped_collection: list[str] = []

                args: list[ast.arg] = []
                args.extend(node.args.posonlyargs)
                args.extend(node.args.args)
                args.extend(node.args.kwonlyargs)
                if node.args.vararg:
                    args.append(node.args.vararg)
                if node.args.kwarg:
                    args.append(node.args.kwarg)

                for arg in args:
                    if arg.arg in {"self", "cls"}:
                        continue
                    ann_text = _annotation_text(arg.annotation)
                    if not ann_text:
                        missing.append(arg.arg)
                        continue
                    if _contains_any(ann_text):
                        any_usage.append(arg.arg)
                    if _has_untyped_collection(ann_text):
                        untyped_collection.append(arg.arg)

                ret_text = _annotation_text(node.returns)
                if not ret_text:
                    missing.append("return")
                else:
                    if _contains_any(ret_text):
                        any_usage.append("return")
                    if _has_untyped_collection(ret_text):
                        untyped_collection.append("return")

                if missing:
                    self._add(
                        "PEC009",
                        path,
                        node.lineno,
                        "Public functions must annotate all parameters and return types.",
                        f"missing: {', '.join(sorted(missing))}",
                    )
                if any_usage:
                    self._add(
                        "PEC010",
                        path,
                        node.lineno,
                        "Public APIs must not use Any or implicit Any.",
                        f"Any usage: {', '.join(sorted(any_usage))}",
                    )
                if untyped_collection:
                    self._add(
                        "PEC011",
                        path,
                        node.lineno,
                        "Public APIs must use typed collections (for example list[str]).",
                        f"untyped collections: {', '.join(sorted(untyped_collection))}",
                    )

    def _check_naming_and_style(self) -> None:
        for path in self.service_files:
            stem = path.stem
            if stem != "__init__" and not PACKAGE_RE.match(stem):
                self._add(
                    "PEC013",
                    path,
                    1,
                    "Module filenames must use snake_case per PEP 8.",
                    stem,
                )

            tree = self.ast_cache.get(path)
            if tree is None:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                    if not CLASS_RE.match(node.name):
                        self._add(
                            "PEC013",
                            path,
                            node.lineno,
                            "Class names must use CapWords.",
                            node.name,
                        )
                if isinstance(
                    node, (ast.FunctionDef, ast.AsyncFunctionDef)
                ) and not node.name.startswith("_"):
                    if not PACKAGE_RE.match(node.name):
                        self._add(
                            "PEC013",
                            path,
                            node.lineno,
                            "Function names must use snake_case.",
                            node.name,
                        )

    def _function_nesting_depth(self, node: ast.AST) -> int:
        max_depth = 0

        def walk(current: ast.AST, depth: int) -> None:
            nonlocal max_depth
            max_depth = max(max_depth, depth)
            for child in ast.iter_child_nodes(current):
                next_depth = depth + 1 if isinstance(child, CONTROL_NODES) else depth
                walk(child, next_depth)

        walk(node, 0)
        return max_depth

    def _function_complexity(self, node: ast.AST) -> int:
        count = 1
        for child in ast.walk(node):
            if isinstance(
                child,
                (
                    ast.If,
                    ast.For,
                    ast.AsyncFor,
                    ast.While,
                    ast.Try,
                    ast.BoolOp,
                    ast.Match,
                ),
            ):
                count += 1
        return count

    def _check_structure(self) -> None:
        for path in self.service_files:
            tree = self.ast_cache.get(path)
            if tree is None:
                continue

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    end = getattr(node, "end_lineno", node.lineno)
                    length = max(1, end - node.lineno + 1)
                    statement_count = len(node.body)
                    param_count = (
                        len(node.args.posonlyargs)
                        + len(node.args.args)
                        + len(node.args.kwonlyargs)
                        + (1 if node.args.vararg else 0)
                        + (1 if node.args.kwarg else 0)
                    )

                    if length > 60 or statement_count > 25 or param_count > 7:
                        self._add(
                            "PEC014",
                            path,
                            node.lineno,
                            "Functions must remain small and single-purpose.",
                            f"length={length}, statements={statement_count}, params={param_count}",
                        )

                    depth = self._function_nesting_depth(node)
                    if depth > 3:
                        self._add(
                            "PEC015",
                            path,
                            node.lineno,
                            "Control-flow nesting deeper than 3 levels is forbidden.",
                            f"nesting_depth={depth}",
                        )

                    defaults = list(node.args.defaults) + list(node.args.kw_defaults)
                    for default in defaults:
                        if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                            self._add(
                                "PEC016",
                                path,
                                node.lineno,
                                "Mutable default arguments are forbidden.",
                                _line_snippet(
                                    _annotation_text(default) or "mutable default"
                                ),
                            )
                    for child in ast.walk(node):
                        if isinstance(child, (ast.Global, ast.Nonlocal)):
                            self._add(
                                "PEC016",
                                path,
                                child.lineno,
                                (
                                    "Hidden side effects through global/nonlocal "
                                    "mutation are forbidden."
                                ),
                                _line_snippet(self._read_lines(path)[child.lineno - 1]),
                            )

            for top in tree.body:
                if isinstance(top, ast.If) and _is_name_main_guard(top):
                    continue
                if isinstance(top, ast.Expr) and isinstance(top.value, ast.Call):
                    self._add(
                        "PEC016",
                        path,
                        top.lineno,
                        (
                            "Module-level call side effects are forbidden outside "
                            "explicit entrypoints."
                        ),
                        _line_snippet(self._read_lines(path)[top.lineno - 1]),
                    )

    def _except_has_log_call(self, handler: ast.ExceptHandler) -> bool:
        for node in ast.walk(handler):
            if not isinstance(node, ast.Call) or not isinstance(
                node.func, ast.Attribute
            ):
                continue
            method = node.func.attr
            if method not in IMPORT_LEVELS:
                continue
            owner = node.func.value
            owner_name = ""
            if isinstance(owner, ast.Name):
                owner_name = owner.id.lower()
            if isinstance(owner, ast.Attribute):
                owner_name = owner.attr.lower()
            if "log" in owner_name or owner_name in {"logger", "structlog"}:
                return True
        return False

    def _check_error_handling(self) -> None:
        for path in self.service_files:
            tree = self.ast_cache.get(path)
            if tree is None:
                continue

            for node in ast.walk(tree):
                if not isinstance(node, ast.ExceptHandler):
                    continue

                if node.type is None:
                    self._add(
                        "PEC017",
                        path,
                        node.lineno,
                        "Bare except is forbidden; catch explicit exception types.",
                        _line_snippet(self._read_lines(path)[node.lineno - 1]),
                    )

                has_pass = any(isinstance(child, ast.Pass) for child in node.body)
                has_raise = any(
                    isinstance(child, ast.Raise) for child in ast.walk(node)
                )
                has_log = self._except_has_log_call(node)
                if has_pass or (not has_raise and not has_log):
                    self._add(
                        "PEC018",
                        path,
                        node.lineno,
                        (
                            "Error handling must not swallow failures; log context "
                            "or raise explicitly."
                        ),
                        _line_snippet(self._read_lines(path)[node.lineno - 1]),
                    )
                if not has_log:
                    self._add(
                        "PEC023",
                        path,
                        node.lineno,
                        "Error paths must emit structured logs with contextual fields.",
                        _line_snippet(self._read_lines(path)[node.lineno - 1]),
                    )

    def _import_class(self, module: str) -> int:
        if not module:
            return 2
        head = module.split(".", 1)[0]
        if head in sys.stdlib_module_names:
            return 0
        if head in self.local_packages:
            return 2
        return 1

    def _check_imports(self) -> None:
        for path in self.service_files:
            tree = self.ast_cache.get(path)
            if tree is None:
                continue

            imported_names: dict[str, tuple[int, str]] = {}
            used_names: set[str] = set()
            import_order: list[tuple[int, int, str]] = []

            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    used_names.add(node.id)

            for top in tree.body:
                if isinstance(top, ast.Import):
                    for alias in top.names:
                        name = alias.asname or alias.name.split(".")[0]
                        imported_names[name] = (top.lineno, alias.name)
                        import_order.append(
                            (top.lineno, self._import_class(alias.name), alias.name)
                        )
                elif isinstance(top, ast.ImportFrom):
                    module = top.module or ""
                    if top.level > 0:
                        module = "." + module
                    import_order.append(
                        (
                            top.lineno,
                            2 if top.level > 0 else self._import_class(module),
                            module,
                        )
                    )
                    for alias in top.names:
                        if alias.name == "*":
                            self._add(
                                "PEC021",
                                path,
                                top.lineno,
                                "Wildcard imports are forbidden.",
                                _line_snippet(self._read_lines(path)[top.lineno - 1]),
                            )
                            continue
                        name = alias.asname or alias.name
                        imported_names[name] = (top.lineno, module)

            for name, (line, source) in imported_names.items():
                if name.startswith("_"):
                    continue
                if name not in used_names:
                    self._add(
                        "PEC020",
                        path,
                        line,
                        "Unused imports are forbidden.",
                        f"{name} from {source}",
                    )

            prior = -1
            for line, group, module in sorted(import_order, key=lambda item: item[0]):
                if group < prior:
                    self._add(
                        "PEC019",
                        path,
                        line,
                        "Import blocks must be ordered stdlib -> third-party -> local.",
                        module,
                    )
                prior = max(prior, group)

    def _check_logging_and_print(self) -> None:
        logger_call_re = re.compile(
            r"\b(?:logger|log|structlog)\.(?:debug|info|warning|error|exception|critical)\("
        )

        for path in self.service_files:
            text = self._read_text(path)
            lines = self._read_lines(path)
            tree = self.ast_cache.get(path)
            if tree is None:
                continue

            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "print"
                ):
                    self._add(
                        "PEC022",
                        path,
                        node.lineno,
                        "print() is forbidden in production code. Use structured logging.",
                        _line_snippet(lines[node.lineno - 1]),
                    )
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    if node.func.attr in IMPORT_LEVELS:
                        if not node.keywords:
                            owner = ""
                            if isinstance(node.func.value, ast.Name):
                                owner = node.func.value.id
                            if isinstance(node.func.value, ast.Attribute):
                                owner = node.func.value.attr
                            if "log" in owner.lower() or owner.lower() == "logger":
                                self._add(
                                    "PEC023",
                                    path,
                                    node.lineno,
                                    (
                                        "Structured logging calls must include "
                                        "contextual keyword fields."
                                    ),
                                    _line_snippet(lines[node.lineno - 1]),
                                )

            if "except" in text and not logger_call_re.search(text):
                self._add(
                    "PEC023",
                    path,
                    1,
                    "Modules with error handling must emit structured logs.",
                    "missing logger.<level>(..., key=value)",
                )

    def _check_comments(self) -> None:
        for path in self.service_files:
            lines = self._read_lines(path)
            for idx, line in enumerate(lines, start=1):
                stripped = line.strip()
                if not stripped.startswith("#"):
                    continue
                if re.search(r"\b(TODO|FIXME|XXX)\b", stripped, re.IGNORECASE):
                    self._add(
                        "PEC024",
                        path,
                        idx,
                        "Outdated or unresolved TODO/FIXME comments are forbidden.",
                        _line_snippet(stripped),
                    )
                for pattern in COMMENT_REDUNDANT_RE:
                    if pattern.search(stripped):
                        self._add(
                            "PEC024",
                            path,
                            idx,
                            "Comments must explain reasoning, not narrate obvious code.",
                            _line_snippet(stripped),
                        )

            tree = self.ast_cache.get(path)
            if tree is None:
                continue
            comment_lines = self._comment_lines(path)
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                complexity = self._function_complexity(node)
                if complexity < 5:
                    continue
                start = node.lineno
                end = getattr(node, "end_lineno", node.lineno)
                has_comment = any(start <= line_no <= end for line_no in comment_lines)
                if not has_comment:
                    self._add(
                        "PEC024",
                        path,
                        node.lineno,
                        "Complex logic must include explanatory reasoning comments.",
                        f"complexity={complexity} without reasoning comments",
                    )

    def _check_tests(self) -> None:
        """Validate project layout and anti-overmocking test constraints."""
        has_tests_dir = (self.root / "tests").is_dir()
        has_source_dir = (self.root / "src").is_dir() or any(
            path.name == "__init__.py" for path in self.root.glob("*/__init__.py")
        )
        if not has_tests_dir or not has_source_dir:
            self._add_project(
                "PEC026",
                (
                    "Expected project structure must include clear source package(s) "
                    "and a tests/ directory."
                ),
                "expected: src/<package>/... and tests/",
            )

        for path in self.test_files:
            text = self._read_text(path)
            patch_count = len(re.findall(r"\b(?:mock\.patch|patch\()", text)) + len(
                re.findall(r"\bmonkeypatch\b", text)
            )
            if patch_count > 5:
                self._add(
                    "PEC025",
                    path,
                    1,
                    "Heavy mocking is forbidden; design code for direct, low-friction tests.",
                    f"patch-like usages={patch_count}",
                )

    def validate(self) -> ResultOutput:
        """Run all deterministic rule checks and build the final verdict."""
        if not self.python_files:
            self._add_project(
                "PEC000",
                "Contract requires Python source files.",
                "no Python files found",
            )

        self._check_python_runtime()
        self._check_ruff_configuration()
        self._check_ruff_execution()
        self._check_mypy_configuration()
        self._check_mypy_execution()
        self._check_docstrings()
        self._check_typing()
        self._check_naming_and_style()
        self._check_structure()
        self._check_error_handling()
        self._check_imports()
        self._check_logging_and_print()
        self._check_comments()
        self._check_tests()

        self.violations.sort(
            key=lambda item: (item.rule_id, item.file, item.line, item.snippet)
        )
        verdict: Literal["PASS", "REJECT"] = "PASS" if not self.violations else "REJECT"
        return {
            "contract": CONTRACT_NAME,
            "verdict": verdict,
            "summary": {
                "files_scanned": self.files_scanned,
                "rules_checked": len(RULE_TITLES),
                "violations": len(self.violations),
            },
            "violations": [item.as_dict() for item in self.violations],
        }


def _print_text(result: ResultOutput) -> None:
    """Render human-readable contract output."""
    print(f"contract: {result['contract']}")
    print(f"verdict: {result['verdict']}")
    print(
        "summary: "
        f"files_scanned={result['summary']['files_scanned']} "
        f"rules_checked={result['summary']['rules_checked']} "
        f"violations={result['summary']['violations']}"
    )
    for item in result["violations"]:
        print(f"- {item['rule_id']} {item['file']}:{item['line']} {item['rejection']}")


def main() -> int:
    """Parse CLI arguments, execute validation, and return process status."""
    parser = argparse.ArgumentParser(
        description="Validate Python engineering contract."
    )
    parser.add_argument(
        "--root", type=Path, default=Path(), help="Repository root to scan."
    )
    parser.add_argument(
        "--format",
        dest="output_format",
        choices=["json", "text"],
        default="json",
        help="Output format.",
    )
    parsed = parser.parse_args()
    args_map = vars(parsed)

    root_arg = args_map.get("root", Path())
    if not isinstance(root_arg, Path):
        root_arg = Path(root_arg)

    output_raw = args_map.get("output_format", "json")
    output_format: Literal["json", "text"] = "text" if output_raw == "text" else "json"

    validator = ContractValidator(root_arg)
    result = validator.validate()

    if output_format == "json":
        print(json.dumps(result, indent=2))
    else:
        _print_text(result)

    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
