#!/usr/bin/env python3
"""Validate Exhibit A SwiftUI architecture contract."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypedDict

IGNORE_DIRS = {
    ".git",
    ".build",
    "build",
    "DerivedData",
    "Pods",
    "Carthage",
    "node_modules",
    ".swiftpm",
}

DISPLAY_COMPONENT_SUFFIXES = (
    "Row",
    "Cell",
    "Badge",
    "Chip",
    "Button",
    "Label",
    "Icon",
    "Card",
    "Tile",
)


@dataclass
class Violation:
    """A single contract failure with source location."""

    rule_id: str
    title: str
    rejection: str
    file: str
    line: int
    snippet: str


@dataclass
class TypeDecl:
    """A parsed Swift type declaration."""

    name: str
    kind: str
    line: int
    attrs: set[str]
    conforms_to_view: bool


class SummaryDict(TypedDict):
    """Summary section for contract reports."""

    files_scanned: int
    rules_checked: int
    violations: int


class ViolationDict(TypedDict):
    """Serialized violation entry for report output."""

    rule_id: str
    title: str
    rejection: str
    file: str
    line: int
    snippet: str


class ReportDict(TypedDict):
    """Top-level contract validator report."""

    status: Literal["pass", "reject"]
    summary: SummaryDict
    violations: list[ViolationDict]


def _serialize_violation(violation: Violation) -> ViolationDict:
    """Convert a violation dataclass to the report payload shape."""
    return {
        "rule_id": violation.rule_id,
        "title": violation.title,
        "rejection": violation.rejection,
        "file": violation.file,
        "line": violation.line,
        "snippet": violation.snippet,
    }


class ContractValidator:
    """Rule-based validator for strict SwiftUI architecture requirements."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.swift_files = self._collect_swift_files()
        self.cache: dict[Path, str] = {}
        self.violations: list[Violation] = []
        self.rules_checked = 26

        self.type_decls: dict[Path, list[TypeDecl]] = {}
        self.class_or_actor_types: set[str] = set()
        self.viewmodel_types: set[str] = set()
        self.mainactor_types: set[str] = set()
        self.screen_views: list[tuple[Path, TypeDecl]] = []

    def _collect_swift_files(self) -> list[Path]:
        files: list[Path] = []
        for path in self.root.rglob("*.swift"):
            if any(part in IGNORE_DIRS for part in path.parts):
                continue
            files.append(path)
        return sorted(files)

    def _read(self, path: Path) -> str:
        if path not in self.cache:
            self.cache[path] = path.read_text(encoding="utf-8", errors="ignore")
        return self.cache[path]

    def _relative(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.root))
        except ValueError:
            return str(path)

    def _add_violation(
        self,
        rule_id: str,
        title: str,
        rejection: str,
        path: Path,
        line: int,
        snippet: str,
    ) -> None:
        self.violations.append(
            Violation(
                rule_id=rule_id,
                title=title,
                rejection=rejection,
                file=self._relative(path),
                line=max(line, 1),
                snippet=snippet.strip()[:200],
            )
        )

    def _index_types(self) -> None:
        type_pattern = re.compile(
            r"^\s*(?P<attrs>(?:@\w+(?:\([^)]*\))?\s+)*)"
            r"(?:(?:public|internal|private|fileprivate|open|final)\s+)*"
            r"(?P<kind>class|struct|actor)\s+(?P<name>\w+)"
            r"(?:\s*:\s*(?P<conformance>[^\{]+))?"
        )
        attr_only_pattern = re.compile(r"^\s*@(?P<attr>\w+)")

        for swift_file in self.swift_files:
            content = self._read(swift_file)
            lines = content.splitlines()
            pending_attrs: set[str] = set()
            decls: list[TypeDecl] = []

            for idx, line in enumerate(lines, start=1):
                type_match = type_pattern.match(line)
                if type_match:
                    inline_attrs = set(
                        re.findall(r"@(\w+)", type_match.group("attrs") or "")
                    )
                    attrs = set(pending_attrs) | inline_attrs
                    name = type_match.group("name")
                    kind = type_match.group("kind")
                    conformance = type_match.group("conformance") or ""
                    conforms_to_view = bool(re.search(r"\bView\b", conformance))
                    decls.append(
                        TypeDecl(
                            name=name,
                            kind=kind,
                            line=idx,
                            attrs=attrs,
                            conforms_to_view=conforms_to_view,
                        )
                    )
                    if kind in {"class", "actor"}:
                        self.class_or_actor_types.add(name)
                    if name.endswith("ViewModel"):
                        self.viewmodel_types.add(name)
                    if "MainActor" in attrs:
                        self.mainactor_types.add(name)
                    pending_attrs.clear()
                    continue

                attr_only = attr_only_pattern.match(line)
                if attr_only and not line.strip().startswith("//"):
                    pending_attrs.add(attr_only.group("attr"))
                    continue

                stripped = line.strip()
                if stripped and not stripped.startswith("//"):
                    pending_attrs.clear()

            self.type_decls[swift_file] = decls

            for decl in decls:
                if decl.conforms_to_view:
                    self.screen_views.append((swift_file, decl))

    def _iter_lines(self) -> Iterable[tuple[Path, int, str]]:
        for swift_file in self.swift_files:
            for idx, line in enumerate(self._read(swift_file).splitlines(), start=1):
                yield swift_file, idx, line

    def _check_forbidden_api_usage(self) -> None:
        checks = [
            (
                "ARC001",
                "ObservableObject Is Forbidden",
                re.compile(r"\bObservableObject\b"),
                "REJECT: `ObservableObject` is banned. Use `@Observable` view models.",
            ),
            (
                "ARC002",
                "StateObject Is Forbidden",
                re.compile(r"@StateObject\b"),
                "REJECT: `@StateObject` is banned. Own view models with `@State`.",
            ),
            (
                "ARC003",
                "ObservedObject Is Forbidden",
                re.compile(r"@ObservedObject\b"),
                "REJECT: `@ObservedObject` is banned. Use `@Observable` + access tracking.",
            ),
            (
                "ARC004",
                "Combine Imports Are Forbidden",
                re.compile(r"^\s*import\s+Combine\b"),
                "REJECT: `import Combine` is forbidden anywhere in the project.",
            ),
        ]

        for path, line_no, line in self._iter_lines():
            for rule_id, title, pattern, rejection in checks:
                if pattern.search(line):
                    self._add_violation(rule_id, title, rejection, path, line_no, line)

    def _check_force_unwrap_and_iuo(self) -> None:
        iuo_pattern = re.compile(r"(?:\:|->)\s*[^=\{\n]+!\s*(?=[=,\{\)\n]|$)")
        force_unwrap_pattern = re.compile(
            r"(?:[A-Za-z_][A-Za-z0-9_\.]*|\)|\])!\s*(?![=])"
        )

        for path, line_no, line in self._iter_lines():
            stripped = line.strip()
            if stripped.startswith("//"):
                continue

            if iuo_pattern.search(line):
                self._add_violation(
                    "ARC005",
                    "Implicitly Unwrapped Optionals Are Forbidden",
                    "REJECT: IUOs are not allowed. Replace `Type!` with safe optional handling.",
                    path,
                    line_no,
                    line,
                )

            for match in force_unwrap_pattern.finditer(line):
                token = match.group(0)
                if token.startswith("as"):
                    continue
                if "!=" in token:
                    continue
                left = line[: match.start()]
                if re.search(r"(:|->)\s*[^\n]*$", left):
                    continue
                if re.search(r"\btry!$", left.strip()):
                    continue
                self._add_violation(
                    "ARC006",
                    "Force Unwrap Is Forbidden",
                    "REJECT: Force unwrap (`!`) is forbidden anywhere in the project.",
                    path,
                    line_no,
                    line,
                )

    def _check_viewmodel_rules(self) -> None:
        vm_decl_pattern = re.compile(r"\b(?:class|struct|actor)\s+(\w+ViewModel)\b")
        async_func_pattern = re.compile(r"\bfunc\b[^\n{]*\basync\b")

        for path in self.swift_files:
            content = self._read(path)
            decls = self.type_decls.get(path, [])
            vm_decls = [decl for decl in decls if decl.name.endswith("ViewModel")]

            if not vm_decls and not vm_decl_pattern.search(content):
                continue

            imports = re.findall(
                r"^\s*import\s+([A-Za-z0-9_]+)\b", content, re.MULTILINE
            )
            non_foundation_imports = [imp for imp in imports if imp != "Foundation"]

            if "Foundation" not in imports:
                self._add_violation(
                    "ARC007",
                    "ViewModel Must Import Foundation",
                    "REJECT: ViewModel files must import `Foundation`.",
                    path,
                    1,
                    "missing `import Foundation`",
                )

            for imp in non_foundation_imports:
                self._add_violation(
                    "ARC008",
                    "ViewModel Import Is Too Broad",
                    "REJECT: ViewModel files may only import `Foundation`.",
                    path,
                    1,
                    f"import {imp}",
                )

            for vm_decl in vm_decls:
                if "Observable" not in vm_decl.attrs:
                    self._add_violation(
                        "ARC009",
                        "ViewModel Must Be @Observable",
                        "REJECT: Every `*ViewModel` must be annotated with `@Observable`.",
                        path,
                        vm_decl.line,
                        f"{vm_decl.kind} {vm_decl.name}",
                    )

                has_async_work = bool(async_func_pattern.search(content))
                if has_async_work and "MainActor" not in vm_decl.attrs:
                    self._add_violation(
                        "ARC010",
                        "Async ViewModel Must Be MainActor Isolated",
                        "REJECT: ViewModels with async work must be `@MainActor`.",
                        path,
                        vm_decl.line,
                        f"{vm_decl.kind} {vm_decl.name}",
                    )

    def _is_display_component(self, path: Path, view_name: str) -> bool:
        content = self._read(path)
        path_parts = set(path.parts)
        if "Components" in path_parts or "Component" in path_parts:
            return True
        if "ARCHITECTURE: display-only" in content:
            return True
        return view_name.endswith(DISPLAY_COMPONENT_SUFFIXES)

    def _check_screen_structure_and_previews(self) -> None:
        for path, decl in self.screen_views:
            if decl.name.endswith("Preview"):
                continue
            if self._is_display_component(path, decl.name):
                continue

            expected_vm = (
                f"{decl.name[:-4]}ViewModel"
                if decl.name.endswith("View")
                else f"{decl.name}ViewModel"
            )
            if expected_vm not in self.viewmodel_types:
                self._add_violation(
                    "ARC011",
                    "Screen Must Have ViewModel",
                    "REJECT: Every screen view must have a matching `*ViewModel`.",
                    path,
                    decl.line,
                    f"struct {decl.name}: View (missing {expected_vm})",
                )

            content = self._read(path)
            if "#Preview" not in content:
                self._add_violation(
                    "ARC012",
                    "Screen Must Have Preview",
                    "REJECT: Every screen must define a `#Preview` block.",
                    path,
                    decl.line,
                    f"struct {decl.name}: View (no #Preview)",
                )
                continue

            preview_blocks = self._extract_preview_blocks(content)
            if preview_blocks and not any(
                re.search(
                    r"\b(Mock|mock|Fixture|fixture|PreviewData|previewData)\b", block
                )
                for block in preview_blocks
            ):
                self._add_violation(
                    "ARC013",
                    "Preview Must Use Mock Data",
                    "REJECT: `#Preview` must use mock/fixture data, never live dependencies.",
                    path,
                    decl.line,
                    "#Preview lacks Mock/Fixture usage",
                )

    def _extract_preview_blocks(self, content: str) -> list[str]:
        blocks: list[str] = []
        lines = content.splitlines()
        for idx, line in enumerate(lines):
            if "#Preview" not in line:
                continue
            block_lines = [line]
            balance = line.count("{") - line.count("}")
            cursor = idx + 1
            while cursor < len(lines):
                block_line = lines[cursor]
                block_lines.append(block_line)
                balance += block_line.count("{") - block_line.count("}")
                cursor += 1
                if balance <= 0 and len(block_lines) > 1:
                    break
            blocks.append("\n".join(block_lines))
        return blocks

    def _check_state_reference_types(self) -> None:
        explicit_type_pattern = re.compile(
            r"@State\s+(?:private\s+)?var\s+\w+\s*:\s*([A-Za-z_][A-Za-z0-9_]*)"
        )
        inferred_type_pattern = re.compile(
            r"@State\s+(?:private\s+)?var\s+\w+\s*=\s*([A-Za-z_][A-Za-z0-9_]*)\s*\("
        )

        for path, line_no, line in self._iter_lines():
            explicit = explicit_type_pattern.search(line)
            inferred = inferred_type_pattern.search(line)
            ref_type = None

            if explicit:
                ref_type = explicit.group(1)
            elif inferred:
                ref_type = inferred.group(1)

            if not ref_type:
                continue

            if ref_type in self.class_or_actor_types and not ref_type.endswith(
                "ViewModel"
            ):
                self._add_violation(
                    "ARC014",
                    "@State Reference Type Violation",
                    "REJECT: `@State` cannot own reference types unless "
                    "the type is a `*ViewModel`.",
                    path,
                    line_no,
                    line,
                )

    def _check_navigation_contract(self) -> None:
        has_navigation_stack = False
        has_navigation_path = False
        has_route_enum = False
        has_type_safe_destination = False

        imperative_patterns = [
            re.compile(r"\bpushViewController\b"),
            re.compile(r"\bpopViewController\b"),
            re.compile(r"\bpopToRootViewController\b"),
            re.compile(r"\bnavigationController\?\.[A-Za-z_][A-Za-z0-9_]*"),
        ]

        for path, line_no, line in self._iter_lines():
            if "NavigationStack" in line:
                has_navigation_stack = True
            if "NavigationPath" in line:
                has_navigation_path = True
            if re.search(r"\benum\s+\w*Route\b", line):
                has_route_enum = True
            if re.search(r"navigationDestination\s*\(\s*for:\s*\w+\.self", line):
                has_type_safe_destination = True

            for pattern in imperative_patterns:
                if pattern.search(line):
                    self._add_violation(
                        "ARC015",
                        "Imperative Navigation Is Forbidden",
                        "REJECT: Navigation must be declarative; imperative "
                        "push/pop APIs are forbidden.",
                        path,
                        line_no,
                        line,
                    )

        if has_navigation_stack and not (
            has_navigation_path and has_route_enum and has_type_safe_destination
        ):
            self._add_violation(
                "ARC016",
                "Navigation Contract Incomplete",
                "REJECT: Navigation must use `NavigationPath` + `Route` enum "
                "+ type-safe `navigationDestination`.",
                self.root,
                1,
                "Missing NavigationPath/Route enum/navigationDestination(for:)",
            )

    def _check_dependency_injection_contract(self) -> None:
        has_environment_key = False
        has_environment_values_extension = False
        has_environment_property_wrapper = False

        for _, _, line in self._iter_lines():
            if re.search(r"\b:\s*EnvironmentKey\b", line):
                has_environment_key = True
            if re.search(r"\bextension\s+EnvironmentValues\b", line):
                has_environment_values_extension = True
            if re.search(r"@Environment\(\s*\\\.", line):
                has_environment_property_wrapper = True

        if not (has_environment_key and has_environment_values_extension):
            self._add_violation(
                "ARC017",
                "Environment DI Keys Missing",
                "REJECT: Dependencies must be injected with custom "
                "`EnvironmentKey` + `EnvironmentValues` extension.",
                self.root,
                1,
                "Custom Environment key definitions were not found.",
            )

        if self.screen_views and not has_environment_property_wrapper:
            self._add_violation(
                "ARC018",
                "Environment-Based Dependency Injection Missing",
                "REJECT: Screens must consume dependencies via `@Environment(\\.key)`.",
                self.root,
                1,
                "No @Environment(\\.key) usage found.",
            )

    def _check_project_structure(self) -> None:
        rel_paths = [self._relative(path) for path in self.swift_files]
        has_views_dir = any("/Views/" in f or f.startswith("Views/") for f in rel_paths)
        has_viewmodels_dir = any(
            "/ViewModels/" in f or f.startswith("ViewModels/") for f in rel_paths
        )
        has_navigation_dir = any(
            "/Navigation/" in f or f.startswith("Navigation/") for f in rel_paths
        )

        if not has_views_dir:
            self._add_violation(
                "ARC024",
                "Project Structure Missing Views Directory",
                "REJECT: Screen views must live under a `Views/` directory.",
                self.root,
                1,
                "No Swift files found in any `Views/` path.",
            )

        if not has_viewmodels_dir:
            self._add_violation(
                "ARC025",
                "Project Structure Missing ViewModels Directory",
                "REJECT: View models must live under a `ViewModels/` directory.",
                self.root,
                1,
                "No Swift files found in any `ViewModels/` path.",
            )

        if not has_navigation_dir:
            self._add_violation(
                "ARC026",
                "Project Structure Missing Navigation Directory",
                "REJECT: Route enums and navigation state must live under `Navigation/`.",
                self.root,
                1,
                "No Swift files found in any `Navigation/` path.",
            )

    def _check_concurrency_settings(self) -> None:
        config_files = []
        package_swift = self.root / "Package.swift"
        if package_swift.exists():
            config_files.append(package_swift)

        for pattern in ("*.xcconfig", "*.pbxproj"):
            config_files.extend(self.root.rglob(pattern))

        default_isolation_ok = False
        nonsending_ok = False

        for cfg in config_files:
            if any(part in IGNORE_DIRS for part in cfg.parts):
                continue
            text = self._read(cfg)
            if re.search(r"defaultIsolation\s*\(\s*MainActor\.self\s*\)", text):
                default_isolation_ok = True
            if re.search(r"SWIFT_DEFAULT_ACTOR_ISOLATION\s*=\s*MainActor", text):
                default_isolation_ok = True

            if re.search(r"SWIFT_NONISOLATED_NONSENDING_BY_DEFAULT\s*=\s*YES", text):
                nonsending_ok = True
            if re.search(r"NonisolatedNonsendingByDefault", text):
                nonsending_ok = True
            if re.search(r"nonisolatedNonsendingByDefault", text):
                nonsending_ok = True

        if not default_isolation_ok:
            self._add_violation(
                "ARC019",
                "Default MainActor Isolation Not Configured",
                "REJECT: Swift 6.2 approachable concurrency requires "
                "default isolation = MainActor.",
                self.root,
                1,
                "Missing `defaultIsolation(MainActor.self)` / "
                "`SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor`",
            )

        if not nonsending_ok:
            self._add_violation(
                "ARC020",
                "nonisolated(nonsending) Inheritance Not Configured",
                "REJECT: Configure nonisolated(nonsending) async inheritance behavior explicitly.",
                self.root,
                1,
                "Missing `SWIFT_NONISOLATED_NONSENDING_BY_DEFAULT = YES` or equivalent setting.",
            )

    def _check_actor_conformance_and_concurrency_escape(self) -> None:
        extension_pattern = re.compile(
            r"^\s*(?:@\w+(?:\([^)]*\))?\s+)*extension\s+(\w+)\s*:\s*([^\{]+)"
        )

        for path in self.swift_files:
            lines = self._read(path).splitlines()
            for idx, line in enumerate(lines, start=1):
                ext_match = extension_pattern.match(line)
                if ext_match:
                    type_name = ext_match.group(1)
                    if type_name in self.mainactor_types:
                        prior = "\n".join(lines[max(0, idx - 3) : idx])
                        if "@MainActor" not in prior:
                            self._add_violation(
                                "ARC021",
                                "Actor-Isolated Protocol Conformance Must Be Explicit",
                                "REJECT: Protocol conformance for actor-isolated "
                                "types must declare isolation explicitly.",
                                path,
                                idx,
                                line,
                            )

                if "Task.detached" in line or "DispatchQueue.global" in line:
                    if "@concurrent" not in self._read(path):
                        self._add_violation(
                            "ARC022",
                            "Concurrent Escape Requires @concurrent",
                            "REJECT: Explicit concurrent execution must be "
                            "audited and marked with `@concurrent`.",
                            path,
                            idx,
                            line,
                        )

    def _check_view_body_logic(self) -> None:
        forbidden_tokens = re.compile(
            r"\b(await|try|URLSession|JSONDecoder|DispatchQueue|Task\s*\{|FileManager)\b"
        )

        for path, decl in self.screen_views:
            if self._is_display_component(path, decl.name):
                continue
            content = self._read(path)
            lines = content.splitlines()

            for idx, line in enumerate(lines, start=1):
                if re.search(r"\bvar\s+body\s*:\s*some\s+View\b", line):
                    body_lines = self._extract_braced_block(lines, idx - 1)
                    for offset, body_line in body_lines:
                        if forbidden_tokens.search(body_line):
                            self._add_violation(
                                "ARC023",
                                "Business Logic in View Body Is Forbidden",
                                "REJECT: View bodies must remain dumb; move "
                                "async/workflow logic into ViewModel methods.",
                                path,
                                offset,
                                body_line,
                            )

    def _extract_braced_block(
        self, lines: list[str], start_index: int
    ) -> list[tuple[int, str]]:
        block: list[tuple[int, str]] = []
        balance = 0
        started = False

        for idx in range(start_index, len(lines)):
            line = lines[idx]
            if not started and "{" in line:
                started = True
            if started:
                balance += line.count("{")
                balance -= line.count("}")
                block.append((idx + 1, line))
                if balance <= 0:
                    break
        return block

    def validate(self) -> ReportDict:
        """Run all contract checks and return a typed report."""
        if not self.swift_files:
            self._add_violation(
                "ARC000",
                "No Swift Source Files Found",
                "REJECT: Contract cannot be evaluated because no `.swift` files were discovered.",
                self.root,
                1,
                "No Swift files found under project root.",
            )
            return self._report()

        self._index_types()
        self._check_forbidden_api_usage()
        self._check_force_unwrap_and_iuo()
        self._check_viewmodel_rules()
        self._check_screen_structure_and_previews()
        self._check_state_reference_types()
        self._check_navigation_contract()
        self._check_dependency_injection_contract()
        self._check_project_structure()
        self._check_concurrency_settings()
        self._check_actor_conformance_and_concurrency_escape()
        self._check_view_body_logic()

        return self._report()

    def _report(self) -> ReportDict:
        """Build a deterministic report payload."""
        status: Literal["pass", "reject"] = "pass" if not self.violations else "reject"
        return {
            "status": status,
            "summary": {
                "files_scanned": len(self.swift_files),
                "rules_checked": self.rules_checked,
                "violations": len(self.violations),
            },
            "violations": [_serialize_violation(v) for v in self.violations],
        }


def render_markdown(report: ReportDict) -> str:
    """Render a human-readable markdown view of the report."""
    summary = report["summary"]
    lines = [
        "# SwiftUI Architecture Contract Report",
        "",
        f"Verdict: {'PASS' if report['status'] == 'pass' else 'REJECT'}",
        f"Files scanned: {summary['files_scanned']}",
        f"Rules checked: {summary['rules_checked']}",
        f"Violations: {summary['violations']}",
        "",
    ]

    violations = report["violations"]
    if not violations:
        lines.append("No violations detected.")
        return "\n".join(lines)

    lines.append("## Violations")
    for violation in violations:
        lines.extend(
            [
                f"- [{violation['rule_id']}] {violation['title']}",
                f"  - Rejection: {violation['rejection']}",
                f"  - Location: {violation['file']}:{violation['line']}",
                f"  - Snippet: `{violation['snippet']}`",
            ]
        )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the validator CLI."""
    parser = argparse.ArgumentParser(
        description="Validate a Swift project against the SwiftUI architecture contract."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(),
        help="Project root to scan (default: current directory)",
    )
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
        help="Output format",
    )
    return parser.parse_args()


def main() -> int:
    """Run the validator command and return process status."""
    args = parse_args()
    validator = ContractValidator(args.root)
    report = validator.validate()

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(render_markdown(report))

    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
