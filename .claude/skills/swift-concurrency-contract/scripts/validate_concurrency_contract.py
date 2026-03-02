#!/usr/bin/env python3
"""Validate Exhibit A's Swift concurrency contract."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, NoReturn, TypedDict

CONTRACT_NAME = "swift-concurrency-contract"
JUSTIFICATION_MARKER = "CONCURRENCY-JUSTIFICATION:"
DETACHED_REASON_MARKER = "DETACHED-REASON:"

RULE_TITLES = {
    "SCC001": "Default main-actor isolation must be configured",
    "SCC002": "nonisolated(nonsending) caller-actor behavior must be configured",
    "SCC003": "Actor-isolated conformance inference must be configured",
    "SCC004": "Legacy GCD/OperationQueue constructs are forbidden",
    "SCC005": "Combine import is forbidden for async workflows",
    "SCC006": "Task.detached requires explicit documented reason",
    "SCC007": "Concurrency introduction requires measured justification",
    "SCC008": "@concurrent must only be used for approved intentional contexts",
    "SCC009": "Background work must be explicitly annotated with @concurrent",
    "SCC010": "async throws call sites must handle errors explicitly",
    "SCC011": "Lifecycle-bound view work must use .task instead of async onAppear",
    "SCC012": "Parallel fan-out must use structured concurrency (TaskGroup)",
    "SCC013": "Network requests require withTaskCancellationHandler",
    "SCC014": "Main-actor code must not perform blocking I/O or sleeps",
    "SCC015": "Actor protocol conformances in extensions must declare isolation",
}

IGNORED_DIRS = {
    ".git",
    ".build",
    "build",
    "DerivedData",
    ".swiftpm",
    "Pods",
    "Carthage",
    ".idea",
    ".vscode",
}


@dataclass(frozen=True)
class Violation:
    """Single contract violation."""

    rule_id: str
    title: str
    rejection: str
    file: str
    line: int
    snippet: str

    def as_dict(self) -> ViolationOutput:
        """Convert to JSON-safe dict."""
        return {
            "rule_id": self.rule_id,
            "title": self.title,
            "rejection": self.rejection,
            "file": self.file,
            "line": self.line,
            "snippet": self.snippet,
        }


class SummaryOutput(TypedDict):
    """Structured summary payload."""

    files_scanned: int
    rules_checked: int
    violations: int


class ViolationOutput(TypedDict):
    """Structured violation payload."""

    rule_id: str
    title: str
    rejection: str
    file: str
    line: int
    snippet: str


class ResultOutput(TypedDict):
    """Structured contract result payload."""

    contract: str
    verdict: Literal["PASS", "REJECT"]
    summary: SummaryOutput
    violations: list[ViolationOutput]


def _relative_path(root: Path, file_path: Path) -> str:
    """Return root-relative path with POSIX separators."""
    try:
        rel = file_path.resolve().relative_to(root.resolve())
    except ValueError:
        rel = file_path
    return rel.as_posix()


def _is_ignored(path: Path) -> bool:
    """Return True if any path segment is in the ignore list."""
    return any(part in IGNORED_DIRS for part in path.parts)


def _has_marker(lines: list[str], line_no: int, marker: str, window: int = 3) -> bool:
    """Check current line and preceding window for a required marker."""
    start = max(1, line_no - window)
    for idx in range(start, line_no + 1):
        if marker in lines[idx - 1]:
            return True
    return False


def _line_snippet(line: str) -> str:
    """Normalize snippet for output."""
    return line.strip()[:220]


def _extract_function_blocks(lines: list[str]) -> list[tuple[int, int, str]]:
    """Extract function blocks as (start_line, end_line, function_name)."""
    blocks: list[tuple[int, int, str]] = []
    func_re = re.compile(r"^\s*(?:@\w+(?:\([^)]*\))?\s*)*func\s+([A-Za-z_]\w*)")
    i = 0
    n = len(lines)

    while i < n:
        match = func_re.search(lines[i])
        if not match:
            i += 1
            continue

        name = match.group(1)
        start = i + 1
        brace_depth = 0
        seen_open = False
        j = i

        while j < n:
            line = lines[j]
            opens = line.count("{")
            closes = line.count("}")
            if opens > 0:
                seen_open = True
            brace_depth += opens
            brace_depth -= closes
            if seen_open and brace_depth <= 0:
                blocks.append((start, j + 1, name))
                break
            j += 1

        if j >= n:
            blocks.append((start, n, name))
            break
        i = j + 1

    return blocks


class ContractValidator:
    """Deterministic validator for Swift concurrency contract rules."""

    def __init__(self, root: Path):
        self.root = root.resolve()
        self.violations: list[Violation] = []
        self.swift_files = self._collect_swift_files()
        self.files_scanned = len(self.swift_files)

    def _collect_swift_files(self) -> list[Path]:
        files: list[Path] = []
        for path in self.root.rglob("*.swift"):
            if _is_ignored(path):
                continue
            files.append(path)
        files.sort()
        return files

    def _read_lines(self, file_path: Path) -> list[str]:
        return file_path.read_text(encoding="utf-8", errors="ignore").splitlines()

    def _add(
        self,
        rule_id: str,
        file_path: Path,
        line_no: int,
        message: str,
        snippet: str,
    ) -> None:
        self.violations.append(
            Violation(
                rule_id=rule_id,
                title=RULE_TITLES[rule_id],
                rejection=f"REJECT: {message}",
                file=_relative_path(self.root, file_path),
                line=line_no,
                snippet=snippet,
            )
        )

    def _validate_package_flags(self) -> None:
        package_swift = self.root / "Package.swift"
        if not package_swift.exists():
            for rule_id, token in (
                ("SCC001", ".defaultIsolation(MainActor.self)"),
                ("SCC002", "NonisolatedNonsendingByDefault"),
                ("SCC003", "InferIsolatedConformances"),
            ):
                self._add(
                    rule_id,
                    package_swift,
                    1,
                    f"{token} is required but Package.swift is missing.",
                    "Package.swift missing",
                )
            return

        content = package_swift.read_text(encoding="utf-8", errors="ignore")
        required = {
            "SCC001": ".defaultIsolation(MainActor.self)",
            "SCC002": "NonisolatedNonsendingByDefault",
            "SCC003": "InferIsolatedConformances",
        }
        for rule_id, token in required.items():
            if token not in content:
                self._add(
                    rule_id,
                    package_swift,
                    1,
                    f"{token} is required in Package.swift.",
                    token,
                )

    def _validate_legacy_constructs(self, file_path: Path, lines: list[str]) -> None:
        banned = re.compile(
            r"\b("
            r"DispatchQueue|DispatchGroup|DispatchSemaphore|DispatchWorkItem|"
            r"DispatchSource|OperationQueue|NSOperationQueue"
            r")\b"
        )
        for idx, line in enumerate(lines, start=1):
            if banned.search(line):
                self._add(
                    "SCC004",
                    file_path,
                    idx,
                    "Legacy GCD/OperationQueue APIs are forbidden.",
                    _line_snippet(line),
                )

            if re.search(r"^\s*import\s+Combine\b", line):
                self._add(
                    "SCC005",
                    file_path,
                    idx,
                    "Combine is forbidden for async workflow transport.",
                    _line_snippet(line),
                )

    def _validate_justification_markers(
        self, file_path: Path, lines: list[str]
    ) -> None:
        detached_re = re.compile(r"\bTask\.detached\s*\{")
        concurrency_re = re.compile(
            r"(\bTask\s*\{|\basync\s+let\b|\bwithTaskGroup\s*\(|"
            r"\bwithThrowingTaskGroup\s*\(|(?:^|\s)@concurrent\b)"
        )

        for idx, line in enumerate(lines, start=1):
            if detached_re.search(line):
                has_justification = _has_marker(lines, idx, JUSTIFICATION_MARKER)
                has_detached_reason = _has_marker(lines, idx, DETACHED_REASON_MARKER)
                if not (has_justification and has_detached_reason):
                    self._add(
                        "SCC006",
                        file_path,
                        idx,
                        (
                            "Task.detached requires both "
                            "CONCURRENCY-JUSTIFICATION and DETACHED-REASON markers."
                        ),
                        _line_snippet(line),
                    )

            if concurrency_re.search(line):
                if re.search(r"\.task\s*\{", line):
                    continue
                if not _has_marker(lines, idx, JUSTIFICATION_MARKER):
                    self._add(
                        "SCC007",
                        file_path,
                        idx,
                        "Concurrency introduced without CONCURRENCY-JUSTIFICATION marker.",
                        _line_snippet(line),
                    )

    def _validate_concurrent_usage(self, file_path: Path, lines: list[str]) -> None:
        allowed_keywords = (
            "network",
            "fetch",
            "download",
            "upload",
            "image",
            "thumbnail",
            "cache",
            "export",
            "sync",
            "background",
            "io",
        )
        concurrent_re = re.compile(r"(?:^|\s)@concurrent\b")

        for idx, line in enumerate(lines, start=1):
            if not concurrent_re.search(line):
                continue
            start = max(1, idx - 2)
            end = min(len(lines), idx + 8)
            context = "\n".join(lines[start - 1 : end]).lower()
            if not any(keyword in context for keyword in allowed_keywords):
                self._add(
                    "SCC008",
                    file_path,
                    idx,
                    (
                        "@concurrent used outside approved context "
                        "(network/image/cache/export/sync/background)."
                    ),
                    _line_snippet(line),
                )

        func_re = re.compile(
            r"^\s*(?:@\w+(?:\([^)]*\))?\s*)*func\s+([A-Za-z_]\w*)[^{]*\basync\b"
        )
        background_words = (
            "background",
            "export",
            "sync",
            "cache",
            "image",
            "thumbnail",
            "process",
        )
        for idx, line in enumerate(lines, start=1):
            match = func_re.search(line)
            if not match:
                continue
            function_name = match.group(1).lower()
            if not any(word in function_name for word in background_words):
                continue

            start = max(1, idx - 4)
            attribute_window = "\n".join(lines[start - 1 : idx])
            if "@concurrent" not in attribute_window:
                self._add(
                    "SCC009",
                    file_path,
                    idx,
                    "Background/export/sync/cache/image async functions must be @concurrent.",
                    _line_snippet(line),
                )

    def _validate_async_error_handling(self, file_path: Path, lines: list[str]) -> None:
        async_throws_re = re.compile(r"\bfunc\b[^{]*\basync\s+throws\b")
        try_await_re = re.compile(r"\btry\s+await\b")

        for start, end, name in _extract_function_blocks(lines):
            block = lines[start - 1 : end]
            declaration = lines[start - 1]
            if not async_throws_re.search(declaration):
                continue
            contains_try_await = any(try_await_re.search(line) for line in block)
            has_catch = any(re.search(r"\bcatch\b", line) for line in block)
            if contains_try_await and not has_catch:
                self._add(
                    "SCC010",
                    file_path,
                    start,
                    f"Function '{name}' contains try/await without explicit catch handling.",
                    _line_snippet(declaration),
                )

    def _validate_swiftui_patterns(self, file_path: Path, lines: list[str]) -> None:
        content = "\n".join(lines)
        is_swiftui = (
            "import SwiftUI" in content
            or re.search(r"struct\s+\w+\s*:\s*View\b", content) is not None
        )
        if not is_swiftui:
            return

        for idx, line in enumerate(lines, start=1):
            if ".onAppear" not in line:
                continue
            lookahead = "\n".join(lines[idx - 1 : min(len(lines), idx + 8)])
            if "Task {" in lookahead or re.search(r"\bawait\b", lookahead):
                self._add(
                    "SCC011",
                    file_path,
                    idx,
                    "Async lifecycle work in onAppear is forbidden; use .task instead.",
                    _line_snippet(line),
                )

    def _validate_parallelism_structure(
        self, file_path: Path, lines: list[str]
    ) -> None:
        for start, end, name in _extract_function_blocks(lines):
            block = lines[start - 1 : end]
            task_count = sum(
                1
                for line in block
                if re.search(r"(?<!\.)\bTask\s*\{", line)
                and "Task.detached" not in line
            )
            has_task_group = any(
                "withTaskGroup(" in line or "withThrowingTaskGroup(" in line
                for line in block
            )
            if task_count >= 2 and not has_task_group:
                self._add(
                    "SCC012",
                    file_path,
                    start,
                    f"Function '{name}' launches multiple tasks without TaskGroup.",
                    _line_snippet(lines[start - 1]),
                )

    def _validate_network_cancellation(self, file_path: Path, lines: list[str]) -> None:
        network_patterns = (
            "URLSession.shared.data(",
            "URLSession.shared.download(",
            "URLSession.shared.upload(",
            ".data(for:",
            ".download(for:",
            ".upload(for:",
        )
        for start, end, name in _extract_function_blocks(lines):
            block = lines[start - 1 : end]
            block_text = "\n".join(block)
            has_network = any(token in block_text for token in network_patterns)
            if not has_network:
                continue
            if "withTaskCancellationHandler" not in block_text:
                self._add(
                    "SCC013",
                    file_path,
                    start,
                    f"Network function '{name}' must use withTaskCancellationHandler.",
                    _line_snippet(lines[start - 1]),
                )

    def _validate_main_actor_blocking(self, file_path: Path, lines: list[str]) -> None:
        if "@MainActor" not in "\n".join(lines):
            return
        blocking_re = re.compile(
            r"(Data\s*\(\s*contentsOf:|String\s*\(\s*contentsOf:|Thread\.sleep|"
            r"sleep\s*\(|usleep\s*\(|FileHandle\s*\(\s*forReadingAtPath:)"
        )
        for idx, line in enumerate(lines, start=1):
            if blocking_re.search(line):
                self._add(
                    "SCC014",
                    file_path,
                    idx,
                    "Blocking I/O or sleep API used in main-actor-isolated file.",
                    _line_snippet(line),
                )

    def _validate_actor_conformances(self, file_path: Path, lines: list[str]) -> None:
        actor_re = re.compile(r"^\s*actor\s+([A-Za-z_]\w*)\b")
        extension_re = re.compile(r"^\s*extension\s+([A-Za-z_]\w*)\s*:\s*[^/{]+")
        actor_names = {
            match.group(1) for line in lines if (match := actor_re.search(line))
        }
        if not actor_names:
            return

        for idx, line in enumerate(lines, start=1):
            match = extension_re.search(line)
            if not match:
                continue
            type_name = match.group(1)
            if type_name not in actor_names:
                continue

            prev = "\n".join(lines[max(0, idx - 3) : idx])
            has_isolation = bool(
                re.search(r"@MainActor|@globalActor|nonisolated|@concurrent", prev)
            )
            if not has_isolation:
                self._add(
                    "SCC015",
                    file_path,
                    idx,
                    (
                        f"Actor extension conformance for '{type_name}' "
                        "must declare explicit isolation."
                    ),
                    _line_snippet(line),
                )

    def run(self) -> None:
        """Run all contract checks."""
        self._validate_package_flags()
        for swift_file in self.swift_files:
            lines = self._read_lines(swift_file)
            self._validate_legacy_constructs(swift_file, lines)
            self._validate_justification_markers(swift_file, lines)
            self._validate_concurrent_usage(swift_file, lines)
            self._validate_async_error_handling(swift_file, lines)
            self._validate_swiftui_patterns(swift_file, lines)
            self._validate_parallelism_structure(swift_file, lines)
            self._validate_network_cancellation(swift_file, lines)
            self._validate_main_actor_blocking(swift_file, lines)
            self._validate_actor_conformances(swift_file, lines)

        self.violations.sort(key=lambda v: (v.file, v.line, v.rule_id))

    def result(self) -> ResultOutput:
        """Return structured result payload."""
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


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Validate Exhibit A's strict Swift concurrency contract."
    )
    parser.add_argument("--root", default=".", help="Repository root to scan")
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Output format",
    )
    return parser.parse_args(argv)


def _print_text(result: ResultOutput) -> None:
    """Emit deterministic text output."""
    summary = result["summary"]
    files = summary["files_scanned"]
    rules = summary["rules_checked"]
    violations = summary["violations"]
    print(
        f"{result['contract']}: {result['verdict']} "
        f"(files={files}, rules={rules}, violations={violations})"
    )
    for item in result["violations"]:
        print(
            f"{item['rule_id']} {item['file']}:{item['line']} "
            f"{item['rejection']} :: {item['snippet']}"
        )


def main(argv: list[str] | None = None) -> NoReturn:
    """Entrypoint."""
    args = parse_args(argv or sys.argv[1:])
    validator = ContractValidator(Path(args.root))
    validator.run()
    result = validator.result()

    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        _print_text(result)

    sys.exit(0 if result["verdict"] == "PASS" else 1)


if __name__ == "__main__":
    main()
