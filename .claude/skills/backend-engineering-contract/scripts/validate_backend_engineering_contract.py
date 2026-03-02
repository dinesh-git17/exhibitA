#!/usr/bin/env python3
"""Validate Exhibit A backend engineering contract deterministically."""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypedDict

CONTRACT_NAME = "backend-engineering-contract"

RULE_TITLES = {
    "BEC000": "Python backend service files must exist",
    "BEC001": "FastAPI dependency must be >= 0.126.0",
    "BEC002": "Pydantic dependency must be >= 2.7.0",
    "BEC003": "pydantic.v1 compatibility imports are forbidden",
    "BEC004": "Configuration must use pydantic-settings typed models and forbid direct env reads",
    "BEC005": "Python runtime must be >= 3.12",
    "BEC006": "mypy strict mode must be configured",
    "BEC007": "Ruff must be configured",
    "BEC008": "flake8, black, and isort usage is forbidden",
    "BEC009": "structlog must be configured",
    "BEC010": "structlog logging must be JSON and contextvars-aware",
    "BEC011": "Correlation IDs must propagate through contextvars",
    "BEC012": "Every FastAPI route must declare response_model",
    "BEC013": "Mutating routes must use typed request models",
    "BEC014": "Raw dict payloads are forbidden for route inputs and outputs",
    "BEC015": "RFC 9457 problem-details format must be implemented",
    "BEC016": "Database access must use async aiosqlite",
    "BEC017": "SQLite WAL mode must be enabled",
    "BEC018": "Schema migrations must use versioned SQL files",
    "BEC019": "Ad-hoc schema mutation is forbidden outside migrations",
    "BEC020": "HTTP middleware must inject correlation IDs",
    "BEC021": "HTTP middleware must measure request timing",
    "BEC022": "HTTP middleware must emit structured request logs",
    "BEC023": "Signature uploads must be rate-limited to 10 requests/minute per signer",
    "BEC024": "CORS must be restricted to the app bundle origin",
    "BEC025": "GET /health must return status, db, and uptime_seconds",
    "BEC026": "FastAPI default_response_class must be ORJSONResponse",
    "BEC027": "Application lifecycle must use lifespan context manager",
    "BEC028": "Deprecated FastAPI on_event hooks are forbidden",
    "BEC029": "Session cookies must set HttpOnly, Secure, and SameSite=Strict",
    "BEC030": "APNS transport must use httpx with HTTP/2",
    "BEC031": "APNS authentication must use Apple P8 JWT token auth",
    "BEC032": "Every function must include full type annotations",
    "BEC033": "print() statements are forbidden",
    "BEC034": "SQL execution must be parameterized and non-interpolated",
    "BEC035": "Endpoints must return structured 4xx problem-details errors",
    "BEC036": "Raw 500 errors must be sanitized via structured handlers",
    "BEC037": "pytest-asyncio and >=90% coverage gate are required",
}

IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    ".mypy_cache",
    ".pytest_cache",
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

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}
MUTATING_METHODS = {"POST", "PUT", "PATCH"}
INFRASTRUCTURE_TYPES = {
    "Request",
    "Response",
    "BackgroundTasks",
    "HTTPConnection",
    "WebSocket",
    "UploadFile",
    "File",
    "Form",
    "Query",
    "Path",
    "Header",
    "Cookie",
    "Body",
    "Depends",
}
PRIMITIVE_TYPES = {
    "str",
    "int",
    "float",
    "bool",
    "bytes",
    "None",
    "Any",
    "object",
}
SQL_MUTATION_RE = re.compile(
    r"\b(create\s+table|alter\s+table|drop\s+table|create\s+index|drop\s+index)\b",
    re.IGNORECASE,
)
SQL_DML_RE = re.compile(r"\b(select|insert|update|delete|replace)\b", re.IGNORECASE)
RAW_SQL_INTERP_RE = re.compile(r"(%s|\{\w+\}|\{\})")
PVER_RE = re.compile(r"(\d+)\.(\d+)(?:\.(\d+))?")


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
        return {
            "rule_id": self.rule_id,
            "title": self.title,
            "rejection": self.rejection,
            "file": self.file,
            "line": self.line,
            "snippet": self.snippet,
        }


@dataclass
class RouteInfo:
    """Parsed route metadata for deterministic checks."""

    file_path: Path
    line: int
    path: str
    methods: set[str]
    has_response_model: bool
    function_node: ast.FunctionDef | ast.AsyncFunctionDef


class SummaryOutput(TypedDict):
    files_scanned: int
    rules_checked: int
    violations: int


class ViolationOutput(TypedDict):
    rule_id: str
    title: str
    rejection: str
    file: str
    line: int
    snippet: str


class ResultOutput(TypedDict):
    contract: str
    verdict: Literal["PASS", "REJECT"]
    summary: SummaryOutput
    violations: list[ViolationOutput]


def _line_snippet(line: str) -> str:
    return line.strip()[:220]


def _parse_version(version: str) -> tuple[int, int, int] | None:
    match = PVER_RE.search(version)
    if not match:
        return None
    return (int(match.group(1)), int(match.group(2)), int(match.group(3) or 0))


def _version_ge(actual: tuple[int, int, int], minimum: tuple[int, int, int]) -> bool:
    return actual >= minimum


def _extract_annotation_text(annotation: ast.expr | None) -> str:
    if annotation is None:
        return ""
    try:
        return ast.unparse(annotation)
    except Exception:
        return ""


def _annotation_root(annotation_text: str) -> str:
    text = annotation_text.strip()
    if not text:
        return ""
    if text.startswith("Annotated["):
        inner = text[len("Annotated[") :]
        first = inner.split(",", 1)[0].strip()
        text = first
    text = text.split("|", 1)[0].strip()
    text = text.split("[", 1)[0].strip()
    return text.split(".")[-1]


def _is_raw_dict_annotation(annotation_text: str) -> bool:
    text = annotation_text.replace("typing.", "").strip()
    return bool(re.match(r"^(dict|Dict)(\[.*\])?$", text))


class ContractValidator:
    """Deterministic validator for Exhibit A backend engineering rules."""

    def __init__(self, root: Path):
        self.root = root.resolve()
        self.violations: list[Violation] = []
        self._seen: set[tuple[str, str, int, str]] = set()
        self.cache_lines: dict[Path, list[str]] = {}
        self.cache_text: dict[Path, str] = {}

        self.python_files = self._collect_files("*.py")
        self.service_python_files = [
            p for p in self.python_files if not self._is_test_path(p)
        ]
        self.config_files = self._collect_config_files()
        self.sql_files = self._collect_files("*.sql")
        self.files_scanned = (
            len(self.python_files) + len(self.config_files) + len(self.sql_files)
        )

        self.model_names: set[str] = set()
        self.route_infos: list[RouteInfo] = []
        self.function_nodes: list[
            tuple[Path, ast.FunctionDef | ast.AsyncFunctionDef]
        ] = []
        self.exception_handlers: set[str] = set()
        self.fastapi_calls: list[tuple[Path, ast.Call]] = []
        self.set_cookie_calls: list[tuple[Path, ast.Call]] = []
        self.middleware_nodes: list[
            tuple[Path, ast.FunctionDef | ast.AsyncFunctionDef]
        ] = []
        self.sql_calls: list[tuple[Path, ast.Call]] = []

        self._parse_python_asts()

    def _is_ignored(self, path: Path) -> bool:
        return any(part in IGNORED_DIRS for part in path.parts)

    def _is_test_path(self, path: Path) -> bool:
        lowered = path.as_posix().lower()
        return (
            "/tests/" in lowered
            or lowered.endswith("_test.py")
            or lowered.endswith("test_.py")
            or lowered.endswith("tests.py")
            or "/test/" in lowered
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
        explicit = {
            "pyproject.toml",
            "requirements.txt",
            "requirements-dev.txt",
            "requirements-prod.txt",
            "mypy.ini",
            ".mypy.ini",
            "setup.cfg",
            "tox.ini",
            ".python-version",
            ".pre-commit-config.yaml",
            "Pipfile",
            "Pipfile.lock",
            "poetry.lock",
            "Makefile",
        }
        files: list[Path] = []
        for path in self.root.rglob("*"):
            if not path.is_file():
                continue
            if self._is_ignored(path):
                continue
            name = path.name
            if name in explicit:
                files.append(path)
                continue
            if name.endswith(".toml") or name.endswith(".ini") or name.endswith(".cfg"):
                if (
                    "pyproject" in name
                    or "mypy" in name
                    or "ruff" in name
                    or "pytest" in name
                ):
                    files.append(path)
            if name.startswith("requirements") and name.endswith(".txt"):
                files.append(path)
        return sorted(set(files))

    def _read_lines(self, path: Path) -> list[str]:
        if path not in self.cache_lines:
            self.cache_lines[path] = path.read_text(
                encoding="utf-8", errors="ignore"
            ).splitlines()
        return self.cache_lines[path]

    def _read_text(self, path: Path) -> str:
        if path not in self.cache_text:
            self.cache_text[path] = path.read_text(encoding="utf-8", errors="ignore")
        return self.cache_text[path]

    def _relative(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.root).as_posix()
        except ValueError:
            return path.as_posix()

    def _add(
        self, rule_id: str, path: Path, line: int, message: str, snippet: str
    ) -> None:
        key = (rule_id, self._relative(path), max(1, line), snippet)
        if key in self._seen:
            return
        self._seen.add(key)
        self.violations.append(
            Violation(
                rule_id=rule_id,
                title=RULE_TITLES[rule_id],
                rejection=f"REJECT: {message}",
                file=self._relative(path),
                line=max(1, line),
                snippet=snippet,
            )
        )

    def _add_project(self, rule_id: str, message: str, snippet: str) -> None:
        self._add(rule_id, self.root / "PROJECT_ROOT", 1, message, snippet)

    def _find_line(
        self, path: Path, pattern: re.Pattern[str]
    ) -> tuple[int, str] | None:
        for idx, line in enumerate(self._read_lines(path), start=1):
            if pattern.search(line):
                return idx, _line_snippet(line)
        return None

    def _parse_python_asts(self) -> None:
        for file_path in self.service_python_files:
            try:
                tree = ast.parse(self._read_text(file_path))
            except SyntaxError as exc:
                self._add(
                    "BEC000",
                    file_path,
                    exc.lineno or 1,
                    "Python backend files must be valid syntax for deterministic validation.",
                    "syntax error blocks contract validation",
                )
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for base in node.bases:
                        base_name = _annotation_root(_extract_annotation_text(base))
                        if base_name == "BaseModel":
                            self.model_names.add(node.name)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    self.function_nodes.append((file_path, node))
                    self._collect_route_data(file_path, node)
                    self._collect_exception_handler_data(node)
                    if self._is_http_middleware_function(node):
                        self.middleware_nodes.append((file_path, node))
                if isinstance(node, ast.Call):
                    self._collect_fastapi_data(file_path, node)
                    self._collect_set_cookie_data(file_path, node)
                    self._collect_sql_call_data(file_path, node)

    def _collect_route_data(
        self, file_path: Path, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> None:
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            func = decorator.func
            if not isinstance(func, ast.Attribute):
                continue
            attr = func.attr.lower()
            if attr not in HTTP_METHODS and attr != "api_route":
                continue

            route_path = ""
            if (
                decorator.args
                and isinstance(decorator.args[0], ast.Constant)
                and isinstance(decorator.args[0].value, str)
            ):
                route_path = decorator.args[0].value

            methods: set[str]
            if attr == "api_route":
                methods = set()
                for keyword in decorator.keywords:
                    if keyword.arg != "methods":
                        continue
                    if isinstance(keyword.value, (ast.List, ast.Tuple)):
                        for elt in keyword.value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(
                                elt.value, str
                            ):
                                methods.add(elt.value.upper())
                if not methods:
                    methods = {"GET"}
            else:
                methods = {attr.upper()}

            has_response_model = False
            for keyword in decorator.keywords:
                if keyword.arg == "response_model" and not (
                    isinstance(keyword.value, ast.Constant)
                    and keyword.value.value is None
                ):
                    has_response_model = True

            self.route_infos.append(
                RouteInfo(
                    file_path=file_path,
                    line=node.lineno,
                    path=route_path,
                    methods=methods,
                    has_response_model=has_response_model,
                    function_node=node,
                )
            )

    def _collect_exception_handler_data(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> None:
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            func = decorator.func
            if not isinstance(func, ast.Attribute) or func.attr != "exception_handler":
                continue
            if not decorator.args:
                continue
            name = _annotation_root(_extract_annotation_text(decorator.args[0]))
            if name:
                self.exception_handlers.add(name)

    def _is_http_middleware_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> bool:
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            if not isinstance(decorator.func, ast.Attribute):
                continue
            if decorator.func.attr != "middleware":
                continue
            if not decorator.args:
                continue
            first = decorator.args[0]
            if isinstance(first, ast.Constant) and first.value == "http":
                return True
        return False

    def _collect_fastapi_data(self, file_path: Path, node: ast.Call) -> None:
        name = ""
        if isinstance(node.func, ast.Name):
            name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            name = node.func.attr
        if name == "FastAPI":
            self.fastapi_calls.append((file_path, node))

    def _collect_set_cookie_data(self, file_path: Path, node: ast.Call) -> None:
        if isinstance(node.func, ast.Attribute) and node.func.attr == "set_cookie":
            self.set_cookie_calls.append((file_path, node))

    def _collect_sql_call_data(self, file_path: Path, node: ast.Call) -> None:
        if isinstance(node.func, ast.Attribute) and node.func.attr in {
            "execute",
            "executemany",
            "executescript",
        }:
            self.sql_calls.append((file_path, node))

    def _config_blob(self) -> str:
        return "\n".join(self._read_text(path) for path in self.config_files)

    def _package_specs(self, package: str) -> list[tuple[Path, int, str]]:
        specs: list[tuple[Path, int, str]] = []
        pkg = re.escape(package)
        req_line = re.compile(rf"^\s*{pkg}(?:\[[^\]]+\])?\s*([^#\n;]*)", re.IGNORECASE)
        quoted_dep = re.compile(
            rf"['\"]{pkg}(?:\[[^\]]+\])?([^'\"]*)['\"]", re.IGNORECASE
        )
        table_dep = re.compile(rf"^\s*{pkg}\s*=\s*['\"]([^'\"]+)['\"]", re.IGNORECASE)

        for file_path in self.config_files:
            lines = self._read_lines(file_path)
            for idx, raw_line in enumerate(lines, start=1):
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                m = req_line.search(raw_line)
                if m:
                    specs.append((file_path, idx, m.group(1).strip()))
                for m2 in quoted_dep.finditer(raw_line):
                    specs.append((file_path, idx, m2.group(1).strip()))
                m3 = table_dep.search(raw_line)
                if m3:
                    specs.append((file_path, idx, m3.group(1).strip()))
        return specs

    def _spec_meets_minimum(self, spec: str, minimum: tuple[int, int, int]) -> bool:
        if not spec:
            return False

        cleaned = spec.replace(" ", "")
        if cleaned.startswith("=="):
            parsed = _parse_version(cleaned[2:])
            return parsed is not None and _version_ge(parsed, minimum)
        if cleaned.startswith(">="):
            parsed = _parse_version(cleaned[2:])
            return parsed is not None and _version_ge(parsed, minimum)
        if cleaned.startswith(">"):
            parsed = _parse_version(cleaned[1:])
            return parsed is not None and parsed > minimum
        if cleaned.startswith("~="):
            parsed = _parse_version(cleaned[2:])
            return parsed is not None and _version_ge(parsed, minimum)
        if cleaned.startswith("^"):
            parsed = _parse_version(cleaned[1:])
            return parsed is not None and _version_ge(parsed, minimum)

        parsed_direct = _parse_version(cleaned)
        if parsed_direct is not None:
            return _version_ge(parsed_direct, minimum)

        # Compound specifiers: accept only when an explicit lower bound satisfies minimum.
        comparator = re.compile(r"(>=|>|==|~=|\^)\s*(\d+\.\d+(?:\.\d+)?)")
        for op, version_text in comparator.findall(spec):
            parsed = _parse_version(version_text)
            if parsed is None:
                continue
            if op == ">=" and _version_ge(parsed, minimum):
                return True
            if op == ">" and parsed > minimum:
                return True
            if op in {"==", "~=", "^"} and _version_ge(parsed, minimum):
                return True
        return False

    def _check_dependencies(self) -> None:
        fastapi_specs = self._package_specs("fastapi")
        if not fastapi_specs:
            self._add_project(
                "BEC001",
                "Declare FastAPI dependency with explicit minimum version >=0.126.0.",
                "missing fastapi dependency",
            )
        elif not any(
            self._spec_meets_minimum(spec, (0, 126, 0)) for _, _, spec in fastapi_specs
        ):
            file_path, line, spec = fastapi_specs[0]
            self._add(
                "BEC001",
                file_path,
                line,
                "FastAPI version must be pinned at >=0.126.0.",
                spec or "fastapi without version floor",
            )

        pydantic_specs = self._package_specs("pydantic")
        if not pydantic_specs:
            self._add_project(
                "BEC002",
                "Declare pydantic dependency with explicit minimum version >=2.7.0.",
                "missing pydantic dependency",
            )
        elif not any(
            self._spec_meets_minimum(spec, (2, 7, 0)) for _, _, spec in pydantic_specs
        ):
            file_path, line, spec = pydantic_specs[0]
            self._add(
                "BEC002",
                file_path,
                line,
                "Pydantic version must be pinned at >=2.7.0.",
                spec or "pydantic without version floor",
            )

        settings_specs = self._package_specs("pydantic-settings")
        if not settings_specs:
            self._add_project(
                "BEC004",
                "Configuration must use pydantic-settings BaseSettings models.",
                "missing pydantic-settings dependency",
            )

        ruff_specs = self._package_specs("ruff")
        blob = self._config_blob()
        if not ruff_specs and "[tool.ruff" not in blob:
            self._add_project(
                "BEC007",
                "Ruff must be configured as the canonical lint/format tool.",
                "missing ruff dependency or [tool.ruff] config",
            )

        structlog_specs = self._package_specs("structlog")
        if not structlog_specs:
            self._add_project(
                "BEC009",
                "Structured logging must use structlog dependency.",
                "missing structlog dependency",
            )

        pytest_async_specs = self._package_specs("pytest-asyncio")
        if not pytest_async_specs:
            self._add_project(
                "BEC037",
                "Async backend tests must include pytest-asyncio.",
                "missing pytest-asyncio dependency",
            )

    def _check_forbidden_tooling(self) -> None:
        forbidden = re.compile(r"\b(flake8|black|isort)\b")
        for file_path in self.config_files:
            found = self._find_line(file_path, forbidden)
            if found:
                line, snippet = found
                self._add(
                    "BEC008",
                    file_path,
                    line,
                    "flake8/black/isort are forbidden; use Ruff for linting and formatting.",
                    snippet,
                )

    def _check_python_runtime(self) -> None:
        pyproject = self.root / "pyproject.toml"
        python_version_file = self.root / ".python-version"

        if pyproject.exists():
            text = self._read_text(pyproject)
            match = re.search(r"requires-python\s*=\s*['\"]([^'\"]+)['\"]", text)
            if match:
                spec = match.group(1)
                if not self._spec_meets_minimum(spec, (3, 12, 0)):
                    line_info = self._find_line(
                        pyproject, re.compile(r"requires-python")
                    )
                    line = line_info[0] if line_info else 1
                    snippet = line_info[1] if line_info else spec
                    self._add(
                        "BEC005",
                        pyproject,
                        line,
                        "Python runtime must be >=3.12.",
                        snippet,
                    )
                return

            poetry_match = re.search(
                r"^\s*python\s*=\s*['\"]([^'\"]+)['\"]", text, flags=re.MULTILINE
            )
            if poetry_match:
                spec = poetry_match.group(1)
                if not self._spec_meets_minimum(spec, (3, 12, 0)):
                    line_info = self._find_line(
                        pyproject, re.compile(r"^\s*python\s*=", re.MULTILINE)
                    )
                    line = line_info[0] if line_info else 1
                    snippet = line_info[1] if line_info else spec
                    self._add(
                        "BEC005",
                        pyproject,
                        line,
                        "Python runtime must be >=3.12.",
                        snippet,
                    )
                return

        if python_version_file.exists():
            value = self._read_text(python_version_file).strip()
            parsed = _parse_version(value)
            if parsed is None or not _version_ge(parsed, (3, 12, 0)):
                self._add(
                    "BEC005",
                    python_version_file,
                    1,
                    "Python runtime must be >=3.12.",
                    value or "empty .python-version",
                )
                return
            return

        self._add_project(
            "BEC005",
            "Declare Python 3.12+ in pyproject.toml or .python-version.",
            "missing runtime declaration",
        )

    def _check_mypy_strict(self) -> None:
        strict_re = re.compile(r"strict\s*=\s*true", re.IGNORECASE)
        cli_re = re.compile(r"\bmypy\b[^\n]*--strict")

        for file_path in self.config_files:
            text = self._read_text(file_path)
            if strict_re.search(text) or cli_re.search(text):
                return

        self._add_project(
            "BEC006",
            "mypy must run in strict mode (strict=true or --strict).",
            "missing mypy strict configuration",
        )

    def _check_pydantic_v1_forbidden(self) -> None:
        pat = re.compile(r"\bpydantic\.v1\b|from\s+pydantic\s+import\s+v1")
        for file_path in self.service_python_files:
            found = self._find_line(file_path, pat)
            if found:
                line, snippet = found
                self._add(
                    "BEC003",
                    file_path,
                    line,
                    "Do not import pydantic.v1 compatibility modules.",
                    snippet,
                )

    def _check_settings_modeling(self) -> None:
        has_basesettings_import = False
        has_typed_settings_class = False

        for file_path in self.service_python_files:
            text = self._read_text(file_path)
            if re.search(r"from\s+pydantic_settings\s+import\s+BaseSettings", text):
                has_basesettings_import = True
            try:
                tree = ast.parse(text)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    base_names = {
                        _annotation_root(_extract_annotation_text(base))
                        for base in node.bases
                    }
                    if "BaseSettings" in base_names:
                        typed_fields = [
                            child
                            for child in node.body
                            if isinstance(child, ast.AnnAssign)
                            and isinstance(child.target, ast.Name)
                        ]
                        if typed_fields:
                            has_typed_settings_class = True

        if not has_basesettings_import or not has_typed_settings_class:
            self._add_project(
                "BEC004",
                "Define typed settings classes inheriting BaseSettings from pydantic-settings.",
                "missing typed BaseSettings configuration model",
            )

        direct_env = re.compile(r"\bos\.getenv\(|\bos\.environ(?:\[|\.get\()")
        for file_path in self.service_python_files:
            found = self._find_line(file_path, direct_env)
            if found:
                line, snippet = found
                self._add(
                    "BEC004",
                    file_path,
                    line,
                    "Direct environment variable reads are forbidden; load config via BaseSettings models.",
                    snippet,
                )

    def _check_structlog_practices(self) -> None:
        service_blob = "\n".join(
            self._read_text(path) for path in self.service_python_files
        )

        if "structlog" not in service_blob:
            self._add_project(
                "BEC009",
                "Configure service logging with structlog.",
                "missing structlog usage in service code",
            )

        has_json = bool(
            re.search(
                r"JSONRenderer\s*\(|structlog\.processors\.JSONRenderer", service_blob
            )
        )
        has_context_merge = bool(
            re.search(
                r"merge_contextvars|bind_contextvars|structlog\.contextvars",
                service_blob,
            )
        )
        if not has_json or not has_context_merge:
            self._add_project(
                "BEC010",
                "structlog must emit JSON and merge contextvars for correlation propagation.",
                "missing JSONRenderer or contextvars integration",
            )

        has_correlation = bool(
            re.search(
                r"ContextVar\(\s*['\"]correlation_id['\"]|bind_contextvars\([^\)]*correlation_id|correlation_id",
                service_blob,
            )
        )
        if not has_correlation:
            self._add_project(
                "BEC011",
                "Propagate correlation_id via contextvars in request path.",
                "missing correlation_id contextvars propagation",
            )

    def _check_routes(self) -> None:
        if not self.route_infos:
            self._add_project(
                "BEC012",
                "Backend must expose typed FastAPI routes with explicit response models.",
                "no FastAPI routes discovered",
            )
            return

        for route in self.route_infos:
            node = route.function_node
            if not route.has_response_model:
                self._add(
                    "BEC012",
                    route.file_path,
                    route.line,
                    "Every route decorator must set response_model to a typed model.",
                    f"route {route.path or '<dynamic-path>'} missing response_model",
                )

            if _is_raw_dict_annotation(_extract_annotation_text(node.returns)):
                self._add(
                    "BEC014",
                    route.file_path,
                    route.line,
                    "Route return annotations cannot be raw dict types.",
                    _extract_annotation_text(node.returns),
                )

            for child in ast.walk(node):
                if isinstance(child, ast.Return) and isinstance(child.value, ast.Dict):
                    self._add(
                        "BEC014",
                        route.file_path,
                        child.lineno,
                        "Routes must return typed response models, not raw dict literals.",
                        "return {...}",
                    )

            if route.methods & MUTATING_METHODS:
                if not self._route_has_typed_request_model(node):
                    self._add(
                        "BEC013",
                        route.file_path,
                        route.line,
                        "POST/PUT/PATCH routes must accept at least one typed request model.",
                        f"route {route.path or '<dynamic-path>'} lacks typed request model",
                    )

            for annotation in self._route_parameter_annotations(node):
                if _is_raw_dict_annotation(annotation):
                    self._add(
                        "BEC014",
                        route.file_path,
                        route.line,
                        "Route parameters cannot be annotated as dict/Dict payloads.",
                        annotation,
                    )

    def _route_parameter_annotations(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> list[str]:
        params: list[ast.arg] = []
        params.extend(node.args.posonlyargs)
        params.extend(node.args.args)
        params.extend(node.args.kwonlyargs)
        if node.args.vararg:
            params.append(node.args.vararg)
        if node.args.kwarg:
            params.append(node.args.kwarg)
        return [
            _extract_annotation_text(arg.annotation)
            for arg in params
            if arg.arg not in {"self", "cls"}
        ]

    def _route_has_typed_request_model(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> bool:
        params: list[ast.arg] = []
        params.extend(node.args.posonlyargs)
        params.extend(node.args.args)
        params.extend(node.args.kwonlyargs)

        for arg in params:
            if arg.arg in {"self", "cls"}:
                continue
            annotation = _extract_annotation_text(arg.annotation)
            if not annotation:
                continue
            if _is_raw_dict_annotation(annotation):
                continue
            root = _annotation_root(annotation)
            if root in INFRASTRUCTURE_TYPES or root in PRIMITIVE_TYPES:
                continue
            if (
                root in self.model_names
                or root.endswith("Model")
                or root.endswith("Request")
            ):
                return True
        return False

    def _check_problem_details(self) -> None:
        blob = "\n".join(self._read_text(path) for path in self.service_python_files)
        has_media_type = "application/problem+json" in blob
        has_fields = all(
            token in blob for token in ['"type"', '"title"', '"status"', '"detail"']
        )

        if not has_media_type or not has_fields:
            self._add_project(
                "BEC015",
                "RFC 9457 problem-details responses must include media type and required fields.",
                "missing application/problem+json or type/title/status/detail fields",
            )

        required_4xx_handlers = {"RequestValidationError", "HTTPException"}
        missing_4xx = required_4xx_handlers.difference(self.exception_handlers)
        if missing_4xx:
            self._add_project(
                "BEC035",
                "Register exception handlers that map validation/client errors to problem-details 4xx responses.",
                f"missing handlers: {', '.join(sorted(missing_4xx))}",
            )

        if "Exception" not in self.exception_handlers:
            self._add_project(
                "BEC036",
                "Register a top-level Exception handler returning sanitized problem-details 500 responses.",
                "missing Exception handler",
            )

    def _check_database_rules(self) -> None:
        blob = "\n".join(self._read_text(path) for path in self.service_python_files)
        if "aiosqlite" not in blob:
            self._add_project(
                "BEC016",
                "Async database access must use aiosqlite.",
                "missing aiosqlite usage",
            )

        wal_re = re.compile(r"pragma\s+journal_mode\s*=\s*wal", re.IGNORECASE)
        wal_found = False
        for file_path in self.service_python_files + self.sql_files:
            line_info = self._find_line(file_path, wal_re)
            if line_info:
                wal_found = True
                break
        if not wal_found:
            self._add_project(
                "BEC017",
                "Enable WAL mode explicitly for SQLite concurrency.",
                "missing PRAGMA journal_mode=WAL",
            )

        migration_sql = [
            path
            for path in self.sql_files
            if "migrations" in {part.lower() for part in path.parts}
        ]
        if not migration_sql:
            self._add_project(
                "BEC018",
                "Schema migrations must live in versioned SQL files under a migrations directory.",
                "no migration SQL files found",
            )
        else:
            name_re = re.compile(r"^[Vv]\d{3,}__[A-Za-z0-9_.-]+\.sql$")
            for path in migration_sql:
                if not name_re.match(path.name):
                    self._add(
                        "BEC018",
                        path,
                        1,
                        "Migration SQL filenames must be versioned as V###__description.sql.",
                        path.name,
                    )

        for path in self.sql_files:
            if "migrations" not in {part.lower() for part in path.parts}:
                for idx, line in enumerate(self._read_lines(path), start=1):
                    if SQL_MUTATION_RE.search(line):
                        self._add(
                            "BEC019",
                            path,
                            idx,
                            "Schema mutation SQL is forbidden outside versioned migrations.",
                            _line_snippet(line),
                        )

    def _check_middleware(self) -> None:
        if not self.middleware_nodes:
            self._add_project(
                "BEC020",
                "Declare HTTP middleware that injects correlation IDs.",
                "missing @app.middleware('http') handler",
            )
            self._add_project(
                "BEC021",
                "Declare HTTP middleware that measures request duration.",
                "missing request timing middleware",
            )
            self._add_project(
                "BEC022",
                "Declare HTTP middleware that emits structured request logs.",
                "missing structured request logging middleware",
            )
            return

        combined = []
        first_path, first_node = self.middleware_nodes[0]
        for file_path, node in self.middleware_nodes:
            lines = self._read_lines(file_path)
            start = max(1, node.lineno)
            end = getattr(node, "end_lineno", node.lineno)
            segment = "\n".join(lines[start - 1 : end])
            combined.append(segment)
        joined = "\n".join(combined)

        if not re.search(
            r"correlation[_-]?id|x-correlation-id", joined, re.IGNORECASE
        ) or not re.search(r"ContextVar|bind_contextvars|contextvars", joined):
            self._add(
                "BEC020",
                first_path,
                first_node.lineno,
                "Middleware must create/propagate correlation IDs via contextvars.",
                "missing correlation_id contextvar binding in middleware",
            )

        if not re.search(
            r"time\.(monotonic|perf_counter)|perf_counter\(", joined
        ) or not re.search(r"duration|elapsed", joined, re.IGNORECASE):
            self._add(
                "BEC021",
                first_path,
                first_node.lineno,
                "Middleware must measure request timing using monotonic/perf_counter clocks.",
                "missing request duration measurement",
            )

        if not re.search(r"structlog|get_logger", joined) or not re.search(
            r"method|path|status_code|duration|elapsed", joined, re.IGNORECASE
        ):
            self._add(
                "BEC022",
                first_path,
                first_node.lineno,
                "Middleware must log request metadata with structured logger fields.",
                "missing structured request logging fields",
            )

    def _check_rate_limiting_signature_uploads(self) -> None:
        signature_routes = [
            route
            for route in self.route_infos
            if "POST" in route.methods and "signature" in (route.path or "").lower()
        ]
        if not signature_routes:
            self._add_project(
                "BEC023",
                "Expose a signature upload endpoint with deterministic rate limiting controls.",
                "missing POST signature route",
            )
            return

        for route in signature_routes:
            lines = self._read_lines(route.file_path)
            start = max(1, route.function_node.lineno - 5)
            end = getattr(route.function_node, "end_lineno", route.function_node.lineno)
            block = "\n".join(lines[start - 1 : end])
            has_rate = bool(
                re.search(
                    r"10\s*/\s*minute|10\s*per\s*minute|10/minute|10/min|limit\(['\"]10/minute['\"]",
                    block,
                    re.IGNORECASE,
                )
            )
            has_signer_key = bool(
                re.search(r"signer|signer_id|signer_key", block, re.IGNORECASE)
            )
            if not has_rate or not has_signer_key:
                self._add(
                    "BEC023",
                    route.file_path,
                    route.line,
                    "Signature uploads must enforce 10 req/min per signer identity.",
                    "missing explicit 10/minute per-signer limiter",
                )

    def _check_cors(self) -> None:
        cors_calls: list[tuple[Path, ast.Call]] = []
        for file_path, node in self.fastapi_calls:
            del file_path  # keep loop parity
            del node
        for file_path in self.service_python_files:
            text = self._read_text(file_path)
            try:
                tree = ast.parse(text)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                if (
                    not isinstance(node.func, ast.Attribute)
                    or node.func.attr != "add_middleware"
                ):
                    continue
                if not node.args:
                    continue
                arg0 = _annotation_root(_extract_annotation_text(node.args[0]))
                if arg0 == "CORSMiddleware":
                    cors_calls.append((file_path, node))

        if not cors_calls:
            self._add_project(
                "BEC024",
                "Configure CORSMiddleware with restricted app bundle origin.",
                "missing CORSMiddleware configuration",
            )
            return

        for file_path, call in cors_calls:
            allow_origins = None
            allow_origin_regex = None
            for kw in call.keywords:
                if kw.arg == "allow_origins":
                    allow_origins = kw.value
                if kw.arg == "allow_origin_regex":
                    allow_origin_regex = kw.value

            if allow_origins is None and allow_origin_regex is None:
                self._add(
                    "BEC024",
                    file_path,
                    call.lineno,
                    "CORSMiddleware must explicitly restrict origins.",
                    "missing allow_origins/allow_origin_regex",
                )
                continue

            if isinstance(allow_origins, ast.List):
                values = [
                    elt.value
                    for elt in allow_origins.elts
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                ]
                if "*" in values or len(values) != 1:
                    self._add(
                        "BEC024",
                        file_path,
                        call.lineno,
                        "allow_origins must contain exactly one explicit app bundle origin.",
                        str(values),
                    )

            if isinstance(allow_origin_regex, ast.Constant) and isinstance(
                allow_origin_regex.value, str
            ):
                if ".*" in allow_origin_regex.value:
                    self._add(
                        "BEC024",
                        file_path,
                        call.lineno,
                        "allow_origin_regex cannot be wildcard; it must map to the bundle origin.",
                        allow_origin_regex.value,
                    )

    def _check_health_endpoint(self) -> None:
        health_routes = [
            route
            for route in self.route_infos
            if "GET" in route.methods and route.path.strip() == "/health"
        ]

        if not health_routes:
            self._add_project(
                "BEC025",
                "Implement GET /health endpoint with writable DB and uptime telemetry.",
                "missing GET /health route",
            )
            return

        for route in health_routes:
            returns_valid = False
            for node in ast.walk(route.function_node):
                if not isinstance(node, ast.Return) or not isinstance(
                    node.value, ast.Dict
                ):
                    continue
                keys = []
                values: dict[str, ast.expr] = {}
                for key_node, value_node in zip(
                    node.value.keys, node.value.values, strict=False
                ):
                    if isinstance(key_node, ast.Constant) and isinstance(
                        key_node.value, str
                    ):
                        keys.append(key_node.value)
                        values[key_node.value] = value_node
                if {"status", "db", "uptime_seconds"}.issubset(set(keys)):
                    status_ok = (
                        isinstance(values["status"], ast.Constant)
                        and values["status"].value == "ok"
                    )
                    db_ok = (
                        isinstance(values["db"], ast.Constant)
                        and values["db"].value == "writable"
                    )
                    if status_ok and db_ok:
                        returns_valid = True
                        break
            if not returns_valid:
                self._add(
                    "BEC025",
                    route.file_path,
                    route.line,
                    "GET /health must return {'status':'ok','db':'writable','uptime_seconds':N}.",
                    "health response payload does not satisfy required contract",
                )

    def _check_fastapi_app_shape(self) -> None:
        if not self.fastapi_calls:
            self._add_project(
                "BEC026",
                "Instantiate FastAPI with explicit default_response_class and lifespan.",
                "missing FastAPI() application declaration",
            )
            self._add_project(
                "BEC027",
                "Use lifespan context manager for app lifecycle.",
                "missing FastAPI lifespan configuration",
            )
            return

        has_default_orjson = False
        has_lifespan = False
        for file_path, call in self.fastapi_calls:
            kw_lookup = {kw.arg: kw.value for kw in call.keywords if kw.arg}

            if "default_response_class" in kw_lookup:
                candidate = _annotation_root(
                    _extract_annotation_text(kw_lookup["default_response_class"])
                )
                if candidate == "ORJSONResponse":
                    has_default_orjson = True
                else:
                    self._add(
                        "BEC026",
                        file_path,
                        call.lineno,
                        "default_response_class must be ORJSONResponse.",
                        _extract_annotation_text(kw_lookup["default_response_class"]),
                    )
            if "lifespan" in kw_lookup:
                if (
                    not isinstance(kw_lookup["lifespan"], ast.Constant)
                    or kw_lookup["lifespan"].value is not None
                ):
                    has_lifespan = True

        if not has_default_orjson:
            self._add_project(
                "BEC026",
                "Set FastAPI(default_response_class=ORJSONResponse).",
                "missing default_response_class=ORJSONResponse",
            )

        if not has_lifespan:
            self._add_project(
                "BEC027",
                "Set FastAPI(lifespan=...) using context manager lifecycle.",
                "missing lifespan=... on FastAPI",
            )

        on_event_re = re.compile(r"@\w+\.on_event\(")
        for file_path in self.service_python_files:
            match = self._find_line(file_path, on_event_re)
            if match:
                line, snippet = match
                self._add(
                    "BEC028",
                    file_path,
                    line,
                    "Deprecated on_event hooks are forbidden. Use lifespan context manager.",
                    snippet,
                )

    def _check_session_cookies(self) -> None:
        if not self.set_cookie_calls:
            self._add_project(
                "BEC029",
                "Session management must set HttpOnly/Secure/SameSite=Strict cookies.",
                "missing set_cookie session handling",
            )
            return

        for file_path, call in self.set_cookie_calls:
            kw = {item.arg: item.value for item in call.keywords if item.arg}
            httponly_ok = (
                isinstance(kw.get("httponly"), ast.Constant)
                and kw["httponly"].value is True
            )
            secure_ok = (
                isinstance(kw.get("secure"), ast.Constant)
                and kw["secure"].value is True
            )
            samesite_val = kw.get("samesite")
            samesite_ok = (
                isinstance(samesite_val, ast.Constant)
                and isinstance(samesite_val.value, str)
                and samesite_val.value.lower() == "strict"
            )
            if not (httponly_ok and secure_ok and samesite_ok):
                self._add(
                    "BEC029",
                    file_path,
                    call.lineno,
                    "Session cookies must set httponly=True, secure=True, samesite='strict'.",
                    "set_cookie missing required security flags",
                )

    def _check_apns(self) -> None:
        blob = "\n".join(self._read_text(path) for path in self.service_python_files)
        has_http2 = bool(
            re.search(
                r"httpx\.(AsyncClient|Client)\([^\)]*http2\s*=\s*True",
                blob,
                re.IGNORECASE,
            )
        )
        has_apns_identity = (
            "apns" in blob.lower() or "api.push.apple.com" in blob.lower()
        )
        if not has_http2 or not has_apns_identity:
            self._add_project(
                "BEC030",
                "APNS client must use httpx transport with http2=True.",
                "missing APNS httpx HTTP/2 client setup",
            )

        has_p8 = bool(re.search(r"\.p8|AuthKey_[A-Z0-9]+\.p8", blob))
        has_jwt = bool(
            re.search(
                r"jwt\.encode|ES256|authorization\s*=\s*f?['\"]bearer",
                blob,
                re.IGNORECASE,
            )
        )
        if not has_p8 or not has_jwt:
            self._add_project(
                "BEC031",
                "APNS authentication must use Apple P8 token-based JWT auth.",
                "missing P8 key + JWT bearer token flow",
            )

    def _check_function_annotations_and_print(self) -> None:
        for file_path, node in self.function_nodes:
            missing = []
            params: list[ast.arg] = []
            params.extend(node.args.posonlyargs)
            params.extend(node.args.args)
            params.extend(node.args.kwonlyargs)
            if node.args.vararg:
                params.append(node.args.vararg)
            if node.args.kwarg:
                params.append(node.args.kwarg)

            for arg in params:
                if arg.arg in {"self", "cls"}:
                    continue
                if arg.annotation is None:
                    missing.append(arg.arg)

            if node.returns is None:
                missing.append("return")

            if missing:
                self._add(
                    "BEC032",
                    file_path,
                    node.lineno,
                    "All function parameters and return types must be annotated.",
                    f"missing annotations: {', '.join(sorted(missing))}",
                )

            for child in ast.walk(node):
                if (
                    isinstance(child, ast.Call)
                    and isinstance(child.func, ast.Name)
                    and child.func.id == "print"
                ):
                    self._add(
                        "BEC033",
                        file_path,
                        child.lineno,
                        "print() is forbidden; emit logs through structlog.",
                        "print(...)",
                    )

    def _check_sql_parameterization(self) -> None:
        for file_path, call in self.sql_calls:
            if not call.args:
                continue
            sql_expr = call.args[0]
            sql_text = _extract_annotation_text(sql_expr)
            lowered = sql_text.lower()

            if isinstance(sql_expr, (ast.JoinedStr, ast.BinOp, ast.Call)):
                self._add(
                    "BEC034",
                    file_path,
                    call.lineno,
                    "SQL must not be interpolated with f-strings/formatting operators.",
                    sql_text,
                )

            if isinstance(sql_expr, ast.Constant) and isinstance(sql_expr.value, str):
                literal = sql_expr.value
                literal_lower = literal.lower()
                if SQL_MUTATION_RE.search(literal):
                    self._add(
                        "BEC019",
                        file_path,
                        call.lineno,
                        "Schema mutation SQL is forbidden in runtime code; use migrations.",
                        _line_snippet(literal),
                    )

                if RAW_SQL_INTERP_RE.search(literal):
                    self._add(
                        "BEC034",
                        file_path,
                        call.lineno,
                        "SQL strings must use parameter placeholders, not interpolation markers.",
                        _line_snippet(literal),
                    )

                if SQL_DML_RE.search(literal_lower):
                    has_placeholder = (
                        "?" in literal
                        or re.search(r":[A-Za-z_]\w*", literal) is not None
                    )
                    has_param_arg = len(call.args) > 1 or any(
                        kw.arg in {"parameters", "params"} for kw in call.keywords
                    )
                    if not has_placeholder or not has_param_arg:
                        self._add(
                            "BEC034",
                            file_path,
                            call.lineno,
                            "SQL execute calls must provide placeholders and bound parameters.",
                            _line_snippet(literal),
                        )

            if isinstance(sql_expr, ast.Name):
                # Variable SQL is allowed only if parameters are still passed.
                has_param_arg = len(call.args) > 1 or any(
                    kw.arg in {"parameters", "params"} for kw in call.keywords
                )
                if not has_param_arg:
                    self._add(
                        "BEC034",
                        file_path,
                        call.lineno,
                        "SQL statements passed by variable still require bound parameters.",
                        lowered or sql_text,
                    )

    def _check_pytest_coverage(self) -> None:
        blob = self._config_blob()
        match = re.search(r"--cov-fail-under(?:=|\s+)(\d+)", blob)
        if not match:
            self._add_project(
                "BEC037",
                "Test configuration must enforce --cov-fail-under=90 or higher.",
                "missing pytest coverage floor",
            )
            return

        value = int(match.group(1))
        if value < 90:
            self._add_project(
                "BEC037",
                "Coverage gate must be at least 90%.",
                f"--cov-fail-under={value}",
            )

    def validate(self) -> ResultOutput:
        if not self.service_python_files:
            self._add_project(
                "BEC000",
                "Backend contract requires Python service files under source directories.",
                "no Python service files found",
            )

        self._check_dependencies()
        self._check_forbidden_tooling()
        self._check_python_runtime()
        self._check_mypy_strict()
        self._check_pydantic_v1_forbidden()
        self._check_settings_modeling()
        self._check_structlog_practices()
        self._check_routes()
        self._check_problem_details()
        self._check_database_rules()
        self._check_middleware()
        self._check_rate_limiting_signature_uploads()
        self._check_cors()
        self._check_health_endpoint()
        self._check_fastapi_app_shape()
        self._check_session_cookies()
        self._check_apns()
        self._check_function_annotations_and_print()
        self._check_sql_parameterization()
        self._check_pytest_coverage()

        self.violations.sort(key=lambda v: (v.rule_id, v.file, v.line, v.snippet))

        verdict: Literal["PASS", "REJECT"] = "PASS" if not self.violations else "REJECT"
        return {
            "contract": CONTRACT_NAME,
            "verdict": verdict,
            "summary": {
                "files_scanned": self.files_scanned,
                "rules_checked": len(RULE_TITLES),
                "violations": len(self.violations),
            },
            "violations": [violation.as_dict() for violation in self.violations],
        }


def _print_text(result: ResultOutput) -> None:
    print(f"contract: {result['contract']}")
    print(f"verdict: {result['verdict']}")
    print(
        "summary: "
        f"files_scanned={result['summary']['files_scanned']} "
        f"rules_checked={result['summary']['rules_checked']} "
        f"violations={result['summary']['violations']}"
    )
    if result["violations"]:
        print("violations:")
        for item in result["violations"]:
            print(
                f"- {item['rule_id']} {item['file']}:{item['line']} {item['rejection']}"
            )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Exhibit A backend engineering contract."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(),
        help="Repository root path to scan.",
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="Output format.",
    )
    args = parser.parse_args()

    validator = ContractValidator(args.root)
    result = validator.validate()

    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        _print_text(result)

    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
