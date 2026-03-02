#!/usr/bin/env python3
"""Validate Exhibit A testing contract."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, TypedDict

CONTRACT_NAME = "testing-contract"

RULE_TITLES = {
    "TTC000": "Swift test files must exist",
    "TTC001": "Point-Free SnapshotTesting dependency must be pinned to 1.17+",
    "TTC002": "Snapshot suite must use @Suite(.snapshots(record: .failed))",
    "TTC003": "Snapshot config must use scoped withSnapshotTesting(record:diffTool:)",
    "TTC004": "Global isRecording flags are forbidden",
    "TTC005": "Snapshot tests are forbidden in UI test targets",
    "TTC006": "Snapshot coverage must include required targets in light/dark and body/accessibility3",
    "TTC007": "Snapshot data must be deterministic",
    "TTC008": "Every ViewModel must have unit tests",
    "TTC009": "Unit tests must use @Test (XCTestCase-only tests forbidden)",
    "TTC010": "@MainActor ViewModels require @MainActor tests",
    "TTC011": "Networking tests must use URLProtocol stubbing",
    "TTC012": "Networking tests must use recorded response fixtures",
    "TTC013": "Tests must never hit real servers",
    "TTC014": "Signature export tests must assert non-empty PNG output",
    "TTC015": "Signature export tests must assert PNG under 50KB",
    "TTC016": "Signature export tests must assert crop to drawing bounds",
    "TTC017": "Integration test must cover seed/sync/content/upload/confirm",
    "TTC018": "No test may exceed 2 seconds runtime",
    "TTC019": "Coverage must be at least 85%",
    "TTC020": "Feature changes in PR diff must include tests",
    "TTC021": "Dependencies must be mocked via protocols, not concrete types",
}

IGNORED_DIRS = {
    ".git",
    ".build",
    "build",
    "DerivedData",
    ".swiftpm",
    "Pods",
    "Carthage",
    "node_modules",
    ".idea",
    ".vscode",
}

SNAPSHOT_TARGETS = {
    "cover-page": ("cover page", "cover_page", "cover-page", "coverpage"),
    "table-of-contents": (
        "table of contents",
        "table_of_contents",
        "table-of-contents",
        "toc",
    ),
    "article-page": ("article page", "article_page", "article-page", "article"),
    "signature-block-unsigned": (
        "signature block unsigned",
        "signature_block_unsigned",
        "signature-block-unsigned",
        "unsigned signature",
    ),
    "signature-block-signed": (
        "signature block signed",
        "signature_block_signed",
        "signature-block-signed",
        "signed signature",
    ),
    "letter-detail": ("letter detail", "letter_detail", "letter-detail"),
    "thought-detail": ("thought detail", "thought_detail", "thought-detail"),
}

MODE_TOKENS = {
    "light": ("::light::", " light ", ".light", "userinterfacestyle: .light"),
    "dark": ("::dark::", " dark ", ".dark", "userinterfacestyle: .dark"),
}

TYPE_TOKENS = {
    "body": ("::body", " .body", "body)"),
    "accessibility3": ("::accessibility3", ".accessibility3", "accessibility3"),
}

INTEGRATION_MARKERS = (
    "INTEGRATION-CONTRACT: seed-server-data",
    "INTEGRATION-CONTRACT: app-syncs",
    "INTEGRATION-CONTRACT: content-appears",
    "INTEGRATION-CONTRACT: signature-uploads",
    "INTEGRATION-CONTRACT: server-confirms",
)

SNAPSHOT_NONDETERMINISTIC_PATTERNS = (
    re.compile(r"\bDate\s*\("),
    re.compile(r"\bDate\.now\b"),
    re.compile(r"\bUUID\s*\("),
    re.compile(r"\b(?:Int|Double|Float|Bool)\.random\s*\("),
    re.compile(r"\barc4random\b"),
    re.compile(r"\bProcessInfo\.processInfo\.environment\b"),
    re.compile(r"\bLocale\.current\b"),
    re.compile(r"\bTimeZone\.current\b"),
    re.compile(r"\bCalendar\.current\b"),
)


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
        return {
            "rule_id": self.rule_id,
            "title": self.title,
            "rejection": self.rejection,
            "file": self.file,
            "line": self.line,
            "snippet": self.snippet,
        }


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


def _is_ignored(path: Path) -> bool:
    return any(part in IGNORED_DIRS for part in path.parts)


def _relative_path(root: Path, path: Path) -> str:
    try:
        rel = path.resolve().relative_to(root.resolve())
    except ValueError:
        rel = path
    return rel.as_posix()


def _version_tuple(version: str) -> tuple[int, ...] | None:
    match = re.match(r"^\s*(\d+)\.(\d+)(?:\.(\d+))?", version.strip())
    if not match:
        return None
    major = int(match.group(1))
    minor = int(match.group(2))
    patch = int(match.group(3) or 0)
    return (major, minor, patch)


class ContractValidator:
    """Deterministic validator for the Exhibit A testing contract."""

    def __init__(self, root: Path, base_ref: str):
        self.root = root.resolve()
        self.base_ref = base_ref
        self.violations: list[Violation] = []
        self.swift_files = self._collect_swift_files()
        self.files_scanned = len(self.swift_files)
        self._cache: dict[Path, list[str]] = {}
        self._text_cache: dict[Path, str] = {}
        self.test_files = [p for p in self.swift_files if self._is_test_file(p)]
        self.unit_test_files = [
            p for p in self.test_files if "uitest" not in p.as_posix().lower()
        ]
        self.ui_test_files = [
            p for p in self.test_files if "uitest" in p.as_posix().lower()
        ]
        self.source_files = [p for p in self.swift_files if p not in self.test_files]
        self.snapshot_test_files = self._find_snapshot_test_files()

    def _collect_swift_files(self) -> list[Path]:
        files: list[Path] = []
        for path in self.root.rglob("*.swift"):
            if _is_ignored(path):
                continue
            files.append(path)
        return sorted(files)

    def _read_lines(self, path: Path) -> list[str]:
        cached = self._cache.get(path)
        if cached is not None:
            return cached
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        self._cache[path] = lines
        return lines

    def _read_text(self, path: Path) -> str:
        cached = self._text_cache.get(path)
        if cached is not None:
            return cached
        text = path.read_text(encoding="utf-8", errors="ignore")
        self._text_cache[path] = text
        return text

    def _all_rows(self, files: list[Path]) -> list[tuple[Path, int, str]]:
        rows: list[tuple[Path, int, str]] = []
        for file_path in files:
            for idx, line in enumerate(self._read_lines(file_path), start=1):
                rows.append((file_path, idx, line))
        return rows

    def _is_test_file(self, path: Path) -> bool:
        lowered = path.as_posix().lower()
        return (
            "tests/" in lowered
            or lowered.endswith("tests.swift")
            or "/test/" in lowered
            or "testcase" in lowered
        )

    def _add(
        self, rule_id: str, file_path: Path, line: int, message: str, snippet: str
    ) -> None:
        self.violations.append(
            Violation(
                rule_id=rule_id,
                title=RULE_TITLES[rule_id],
                rejection=f"REJECT: {message}",
                file=_relative_path(self.root, file_path),
                line=max(1, line),
                snippet=snippet,
            )
        )

    def _add_project(self, rule_id: str, message: str, snippet: str) -> None:
        self._add(rule_id, self.root / "PROJECT_ROOT", 1, message, snippet)

    def _find_snapshot_test_files(self) -> list[Path]:
        files: list[Path] = []
        for file_path in self.unit_test_files:
            text = self._read_text(file_path)
            if (
                "SnapshotTesting" in text
                or "assertSnapshot" in text
                or "withSnapshotTesting(" in text
                or ".snapshots(" in text
            ):
                files.append(file_path)
        return files

    def _check_test_files_exist(self) -> None:
        if not self.test_files:
            self._add_project(
                "TTC000",
                "Project must include Swift test files before feature work can be accepted.",
                "no Swift test files detected",
            )

    def _snapshot_versions_from_package_resolved(self) -> list[tuple[str, Path, int]]:
        versions: list[tuple[str, Path, int]] = []
        for path in self.root.rglob("Package.resolved"):
            if _is_ignored(path):
                continue
            try:
                payload = json.loads(self._read_text(path))
            except json.JSONDecodeError:
                continue
            pins: list[dict[str, Any]] = []
            if isinstance(payload.get("pins"), list):
                pins = payload["pins"]
            elif isinstance(payload.get("object"), dict):
                inner = payload["object"]
                if isinstance(inner.get("pins"), list):
                    pins = inner["pins"]
            for pin in pins:
                identity = str(pin.get("identity") or pin.get("package") or "").lower()
                location = str(
                    pin.get("location") or pin.get("repositoryURL") or ""
                ).lower()
                if (
                    "snapshot-testing" not in identity
                    and "snapshot-testing" not in location
                ):
                    continue
                state = pin.get("state", {})
                if isinstance(state, dict):
                    version = state.get("version")
                    if isinstance(version, str):
                        versions.append((version, path, 1))
        return versions

    def _snapshot_versions_from_manifest(self) -> list[tuple[str, Path, int]]:
        versions: list[tuple[str, Path, int]] = []
        package_swift = self.root / "Package.swift"
        if package_swift.exists():
            lines = self._read_lines(package_swift)
            for idx, line in enumerate(lines, start=1):
                if "swift-snapshot-testing" not in line.lower():
                    continue
                search_window = " ".join(
                    lines[max(0, idx - 1) : min(len(lines), idx + 4)]
                )
                match = re.search(
                    r"(?:from|exact|upToNextMajor)\s*:\s*\"(\d+\.\d+(?:\.\d+)?)\"",
                    search_window,
                )
                if match:
                    versions.append((match.group(1), package_swift, idx))

        podfile_lock = self.root / "Podfile.lock"
        if podfile_lock.exists():
            for idx, line in enumerate(self._read_lines(podfile_lock), start=1):
                match = re.search(r"SnapshotTesting\s+\((\d+\.\d+(?:\.\d+)?)\)", line)
                if match:
                    versions.append((match.group(1), podfile_lock, idx))

        cartfile_resolved = self.root / "Cartfile.resolved"
        if cartfile_resolved.exists():
            for idx, line in enumerate(self._read_lines(cartfile_resolved), start=1):
                if "swift-snapshot-testing" not in line.lower():
                    continue
                match = re.search(r"\"(\d+\.\d+(?:\.\d+)?)\"", line)
                if match:
                    versions.append((match.group(1), cartfile_resolved, idx))

        return versions

    def _check_snapshot_dependency_version(self) -> None:
        versions = self._snapshot_versions_from_package_resolved()
        versions.extend(self._snapshot_versions_from_manifest())
        if not versions:
            self._add_project(
                "TTC001",
                "Point-Free SnapshotTesting dependency must be present and pinned to version 1.17 or newer.",
                "missing SnapshotTesting dependency evidence",
            )
            return

        floor = (1, 17, 0)
        for version, file_path, line in versions:
            tupled = _version_tuple(version)
            if tupled is None or tupled < floor:
                self._add(
                    "TTC001",
                    file_path,
                    line,
                    f"SnapshotTesting version {version} is below required 1.17.0.",
                    _line_snippet(version),
                )

    def _check_snapshot_swift_testing_integration(self) -> None:
        suite_pattern = re.compile(
            r"@Suite\s*\(\s*\.snapshots\s*\(\s*record\s*:\s*\.failed\s*\)\s*\)",
            re.MULTILINE,
        )
        found = False
        for file_path in self.snapshot_test_files:
            if suite_pattern.search(self._read_text(file_path)):
                found = True
                break
        if not found:
            self._add_project(
                "TTC002",
                "Snapshot suites must use `@Suite(.snapshots(record: .failed))`.",
                "missing required @Suite(.snapshots(record: .failed))",
            )

    def _check_snapshot_config_scoped(self) -> None:
        if not self.snapshot_test_files:
            self._add_project(
                "TTC003",
                "Snapshot test files are missing; cannot verify scoped withSnapshotTesting(record:diffTool:).",
                "no snapshot test files found",
            )
            return

        scoped_call = re.compile(r"withSnapshotTesting\s*\(", re.MULTILINE)
        for file_path in self.snapshot_test_files:
            text = self._read_text(file_path)
            if "assertSnapshot" in text and not scoped_call.search(text):
                self._add(
                    "TTC003",
                    file_path,
                    1,
                    "Snapshot assertions must be scoped with withSnapshotTesting(record:diffTool:).",
                    "missing withSnapshotTesting(...) in snapshot test file",
                )
                continue

            good_call = False
            for match in scoped_call.finditer(text):
                snippet = text[match.start() : match.start() + 320]
                if "record:" in snippet and "diffTool:" in snippet:
                    good_call = True
                    break
            if "withSnapshotTesting(" in text and not good_call:
                self._add(
                    "TTC003",
                    file_path,
                    1,
                    "withSnapshotTesting must declare both record: and diffTool: arguments.",
                    "withSnapshotTesting(...) missing record: or diffTool:",
                )

    def _check_no_global_recording(self) -> None:
        forbidden = re.compile(r"\bSnapshotTesting\.isRecording\b|\bisRecording\s*=")
        for file_path in self.test_files:
            for idx, line in enumerate(self._read_lines(file_path), start=1):
                if forbidden.search(line):
                    self._add(
                        "TTC004",
                        file_path,
                        idx,
                        "Global recording flags are forbidden; use scoped withSnapshotTesting(record:diffTool:) only.",
                        _line_snippet(line),
                    )

    def _check_snapshot_in_unit_target_only(self) -> None:
        snapshot_tokens = re.compile(
            r"SnapshotTesting|assertSnapshot|withSnapshotTesting|\.snapshots\("
        )
        for file_path in self.ui_test_files:
            for idx, line in enumerate(self._read_lines(file_path), start=1):
                if snapshot_tokens.search(line):
                    self._add(
                        "TTC005",
                        file_path,
                        idx,
                        "Snapshot tests must live in unit test targets, never UI test targets.",
                        _line_snippet(line),
                    )

    def _snapshot_context_rows(self) -> list[tuple[Path, int, str]]:
        contexts: list[tuple[Path, int, str]] = []
        trigger = re.compile(
            r"assertSnapshot|assertSnapshots|verifySnapshot|@Test|withSnapshotTesting"
        )
        for file_path in self.snapshot_test_files:
            lines = self._read_lines(file_path)
            lowered_lines = [f" {line.lower()} " for line in lines]
            for idx, line in enumerate(lines):
                if not trigger.search(line):
                    continue
                start = max(0, idx - 8)
                end = min(len(lines), idx + 9)
                context = " ".join(lowered_lines[start:end])
                contexts.append((file_path, idx + 1, context))
        return contexts

    def _check_snapshot_target_coverage(self) -> None:
        if not self.snapshot_test_files:
            self._add_project(
                "TTC006",
                "Snapshot target coverage is missing because no snapshot tests were found.",
                "missing snapshot test coverage",
            )
            return

        contexts = self._snapshot_context_rows()
        covered: set[tuple[str, str, str]] = set()
        for _file_path, _line, context in contexts:
            for target, aliases in SNAPSHOT_TARGETS.items():
                if not any(alias in context for alias in aliases):
                    continue
                for mode, mode_tokens in MODE_TOKENS.items():
                    if not any(token in context for token in mode_tokens):
                        continue
                    for size, size_tokens in TYPE_TOKENS.items():
                        if any(token in context for token in size_tokens):
                            covered.add((target, mode, size))

        missing: list[str] = []
        for target in SNAPSHOT_TARGETS:
            for mode in MODE_TOKENS:
                for size in TYPE_TOKENS:
                    combo = (target, mode, size)
                    if combo not in covered:
                        missing.append(f"{target}:{mode}:{size}")

        if missing:
            preview = ", ".join(missing[:8])
            self._add_project(
                "TTC006",
                "Snapshot coverage must include every required target in light/dark and body/accessibility3 variants.",
                f"missing {len(missing)} variants (sample: {preview})",
            )

    def _check_snapshot_determinism(self) -> None:
        for file_path in self.snapshot_test_files:
            for idx, line in enumerate(self._read_lines(file_path), start=1):
                for pattern in SNAPSHOT_NONDETERMINISTIC_PATTERNS:
                    if pattern.search(line):
                        self._add(
                            "TTC007",
                            file_path,
                            idx,
                            "Snapshot data must be deterministic; remove dates/randomness/environment-dependent values.",
                            _line_snippet(line),
                        )

    def _find_view_models(self) -> list[tuple[str, bool, Path, int, str]]:
        view_models: list[tuple[str, bool, Path, int, str]] = []
        vm_re = re.compile(
            r"^\s*(?:@\w+(?:\([^)]*\))?\s*)*(?:final\s+)?(?:class|struct|actor)\s+([A-Za-z_]\w*ViewModel)\b"
        )
        for file_path in self.source_files:
            lines = self._read_lines(file_path)
            for idx, line in enumerate(lines, start=1):
                match = vm_re.search(line)
                if not match:
                    continue
                window = " ".join(lines[max(0, idx - 3) : min(len(lines), idx + 1)])
                is_main_actor = "@MainActor" in window
                view_models.append(
                    (match.group(1), is_main_actor, file_path, idx, line)
                )
        return view_models

    def _check_view_model_tests(self) -> None:
        view_models = self._find_view_models()
        if not view_models:
            return

        unit_text = "\n".join(self._read_text(path) for path in self.unit_test_files)
        for name, _is_main_actor, file_path, idx, line in view_models:
            if name not in unit_text:
                self._add(
                    "TTC008",
                    file_path,
                    idx,
                    f"{name} is missing unit test coverage.",
                    _line_snippet(line),
                )

    def _check_swift_testing_macro_usage(self) -> None:
        if not self.unit_test_files:
            return

        at_test_seen = False
        xctestcase_re = re.compile(r"\bclass\s+\w+\s*:\s*XCTestCase\b")
        for file_path in self.unit_test_files:
            lines = self._read_lines(file_path)
            if any("@Test" in line for line in lines):
                at_test_seen = True
            for idx, line in enumerate(lines, start=1):
                if xctestcase_re.search(line):
                    self._add(
                        "TTC009",
                        file_path,
                        idx,
                        "XCTestCase-only tests are forbidden. Use Swift Testing with @Test macros.",
                        _line_snippet(line),
                    )

        if not at_test_seen:
            self._add_project(
                "TTC009",
                "Unit tests must use Swift Testing @Test macros.",
                "missing @Test annotations in unit tests",
            )

    def _check_main_actor_view_model_tests(self) -> None:
        view_models = self._find_view_models()
        for name, is_main_actor, source_file, idx, line in view_models:
            if not is_main_actor:
                continue
            candidate_files = [
                path for path in self.unit_test_files if name in self._read_text(path)
            ]
            if not candidate_files:
                self._add(
                    "TTC010",
                    source_file,
                    idx,
                    f"{name} is @MainActor but has no matching @MainActor test file.",
                    _line_snippet(line),
                )
                continue
            has_main_actor = any(
                "@MainActor" in self._read_text(path) for path in candidate_files
            )
            if not has_main_actor:
                self._add(
                    "TTC010",
                    candidate_files[0],
                    1,
                    f"Tests for {name} must be annotated with @MainActor.",
                    "missing @MainActor in ViewModel test",
                )

    def _network_source_detected(self) -> bool:
        hint = re.compile(
            r"(network|api|client|endpoint|transport|urlsession|http)", re.IGNORECASE
        )
        for file_path in self.source_files:
            if hint.search(file_path.as_posix()):
                return True
            if "URLSession" in self._read_text(file_path):
                return True
        return False

    def _check_networking_tests(self) -> None:
        if not self._network_source_detected():
            return

        joined = "\n".join(self._read_text(path) for path in self.unit_test_files)
        if "URLProtocol" not in joined or "protocolClasses" not in joined:
            self._add_project(
                "TTC011",
                "Networking tests must stub transport using URLProtocol and protocolClasses.",
                "missing URLProtocol stub usage",
            )

        fixture_tokens = (
            "fixture",
            "recordedresponse",
            "recorded_response",
            "bundle.module.url",
            "data(contentsof:",
            ".json",
        )
        normalized = joined.replace(" ", "").lower()
        if not any(token in normalized for token in fixture_tokens):
            self._add_project(
                "TTC012",
                "Networking tests must use recorded response fixtures, not ad hoc live data.",
                "missing recorded fixture usage in networking tests",
            )

    def _check_no_real_server_calls(self) -> None:
        url_re = re.compile(r"https?://[^\s\"')]+")
        allow = ("localhost", "127.0.0.1", "0.0.0.0")
        for file_path in self.test_files:
            for idx, line in enumerate(self._read_lines(file_path), start=1):
                for match in url_re.findall(line):
                    if any(host in match for host in allow):
                        continue
                    self._add(
                        "TTC013",
                        file_path,
                        idx,
                        "Tests must never call real servers; use URLProtocol stubs and recorded fixtures.",
                        _line_snippet(line),
                    )

    def _signature_test_text(self) -> str:
        chunks: list[str] = []
        for file_path in self.unit_test_files:
            lowered = file_path.as_posix().lower()
            if "signature" in lowered or "pencilkit" in lowered:
                chunks.append(self._read_text(file_path))
                continue
            text = self._read_text(file_path)
            if "signature" in text.lower() or "pencilkit" in text.lower():
                chunks.append(text)
        return "\n".join(chunks)

    def _check_signature_export_tests(self) -> None:
        text = self._signature_test_text()
        if not text:
            self._add_project(
                "TTC014",
                "Signature export tests are required and must validate PNG output.",
                "missing signature export tests",
            )
            self._add_project(
                "TTC015",
                "Signature export tests must assert PNG is under 50KB.",
                "missing signature payload size tests",
            )
            self._add_project(
                "TTC016",
                "Signature export tests must assert crop to drawing bounds before PNG encoding.",
                "missing signature crop tests",
            )
            return

        lowered = text.lower()
        if "pngdata()" not in lowered or (
            "isempty" not in lowered
            and "> 0" not in lowered
            and "count > 0" not in lowered
        ):
            self._add_project(
                "TTC014",
                "Signature export tests must assert PNG output is non-empty.",
                "expected pngData() and non-empty assertion",
            )

        size_ok = re.search(r"(?:<|<=)\s*50_?000", text) or re.search(
            r"50\s*\*\s*1024", text
        )
        if not size_ok:
            self._add_project(
                "TTC015",
                "Signature export tests must enforce payload under 50KB.",
                "expected assertion against 50_000 bytes",
            )

        crop_ok = "drawing.bounds" in lowered or (
            "crop" in lowered and "bounds" in lowered
        )
        if not crop_ok:
            self._add_project(
                "TTC016",
                "Signature export tests must verify crop to drawing bounds before encoding.",
                "expected drawing.bounds crop assertion",
            )

    def _check_required_integration_flow(self) -> None:
        integration_files: list[Path] = []
        for file_path in self.test_files:
            lowered = file_path.as_posix().lower()
            if "integration" in lowered:
                integration_files.append(file_path)
                continue
            if "INTEGRATION-CONTRACT:" in self._read_text(file_path):
                integration_files.append(file_path)
        if not integration_files:
            self._add_project(
                "TTC017",
                "Required integration test is missing.",
                "missing integration test file",
            )
            return

        joined = "\n".join(self._read_text(path) for path in integration_files)
        missing = [marker for marker in INTEGRATION_MARKERS if marker not in joined]
        if missing:
            self._add_project(
                "TTC017",
                "Integration tests must include all required flow markers (seed/sync/content/upload/confirm).",
                f"missing markers: {', '.join(missing)}",
            )

    def _check_time_limits(self) -> None:
        if not self.unit_test_files:
            return

        for file_path in self.unit_test_files:
            lines = self._read_lines(file_path)
            for idx, line in enumerate(lines):
                if "@Test" not in line:
                    continue
                end = idx
                annotation_parts = [lines[idx].strip()]
                while end + 1 < len(lines):
                    next_line = lines[end + 1].strip()
                    if "func " in next_line or next_line.startswith("@"):
                        break
                    annotation_parts.append(next_line)
                    end += 1
                annotation = " ".join(annotation_parts)

                if ".timeLimit(" not in annotation:
                    self._add(
                        "TTC018",
                        file_path,
                        idx + 1,
                        "Each @Test must declare a .timeLimit of 2 seconds or less.",
                        _line_snippet(lines[idx]),
                    )
                    continue

                seconds_match = re.search(
                    r"\.seconds\s*\(\s*([0-9]+(?:\.[0-9]+)?)\s*\)", annotation
                )
                millis_match = re.search(
                    r"\.milliseconds\s*\(\s*([0-9]+(?:\.[0-9]+)?)\s*\)", annotation
                )
                minutes_match = re.search(r"\.minutes\s*\(", annotation)
                if minutes_match:
                    self._add(
                        "TTC018",
                        file_path,
                        idx + 1,
                        "Test time limit exceeds 2 seconds.",
                        _line_snippet(lines[idx]),
                    )
                    continue

                if seconds_match:
                    seconds = float(seconds_match.group(1))
                    if seconds > 2.0:
                        self._add(
                            "TTC018",
                            file_path,
                            idx + 1,
                            "Test time limit exceeds 2 seconds.",
                            _line_snippet(lines[idx]),
                        )
                    continue

                if millis_match:
                    millis = float(millis_match.group(1))
                    if millis > 2000.0:
                        self._add(
                            "TTC018",
                            file_path,
                            idx + 1,
                            "Test time limit exceeds 2 seconds.",
                            _line_snippet(lines[idx]),
                        )
                    continue

                self._add(
                    "TTC018",
                    file_path,
                    idx + 1,
                    "Unable to parse @Test time limit; use .timeLimit(.seconds(2)) or lower.",
                    _line_snippet(lines[idx]),
                )

    def _coverage_files(self) -> list[Path]:
        patterns = (
            "*coverage*.json",
            "*coverage*.txt",
            "*.xcovreport",
            "*.xccovreport",
            "*.lcov",
        )
        files: set[Path] = set()
        for pattern in patterns:
            for path in self.root.rglob(pattern):
                if _is_ignored(path):
                    continue
                if path.is_file():
                    files.add(path)
        return sorted(files)

    def _extract_coverage_value(self, path: Path) -> float | None:
        text = self._read_text(path)
        suffix = path.suffix.lower()
        if suffix == ".json":
            try:
                payload: Any = json.loads(text)
            except json.JSONDecodeError:
                payload = None
            if payload is not None:
                values: list[float] = []

                def walk(node: Any, key_hint: str = "") -> None:
                    if isinstance(node, dict):
                        for key, value in node.items():
                            walk(value, key.lower())
                    elif isinstance(node, list):
                        for item in node:
                            walk(item, key_hint)
                    elif isinstance(node, (int, float)):
                        if "coverage" in key_hint:
                            values.append(float(node))

                walk(payload)
                if values:
                    normalized: list[float] = []
                    for value in values:
                        normalized.append(value * 100.0 if value <= 1.0 else value)
                    return max(normalized)

        match = re.search(
            r"(?:line|total|overall)?\s*coverage[^0-9]{0,20}([0-9]+(?:\.[0-9]+)?)\s*%",
            text,
            re.IGNORECASE,
        )
        if match:
            return float(match.group(1))

        generic = re.findall(r"([0-9]+(?:\.[0-9]+)?)\s*%", text)
        if generic:
            values = [float(item) for item in generic]
            return max(values)
        return None

    def _check_coverage_threshold(self) -> None:
        files = self._coverage_files()
        if not files:
            self._add_project(
                "TTC019",
                "Coverage artifact is required and must report at least 85%.",
                "missing coverage artifact (coverage*.json/txt, .xcovreport, .xccovreport, .lcov)",
            )
            return

        percentages: list[tuple[float, Path]] = []
        for path in files:
            value = self._extract_coverage_value(path)
            if value is not None:
                percentages.append((value, path))
        if not percentages:
            self._add_project(
                "TTC019",
                "Coverage artifact exists but percentage could not be parsed.",
                "unparseable coverage report",
            )
            return

        best = max(percentages, key=lambda item: item[0])
        if best[0] < 85.0:
            self._add(
                "TTC019",
                best[1],
                1,
                f"Coverage must be >= 85%, found {best[0]:.2f}%.",
                f"coverage={best[0]:.2f}%",
            )

    def _check_feature_diff_includes_tests(self) -> None:
        git_root = self.root / ".git"
        if not git_root.exists():
            self._add_project(
                "TTC020",
                "Git metadata is required to enforce PR diff test inclusion.",
                "missing .git directory",
            )
            return

        cmd = [
            "git",
            "-C",
            str(self.root),
            "diff",
            "--name-only",
            f"{self.base_ref}...HEAD",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            self._add_project(
                "TTC020",
                f"Unable to inspect git diff against base ref `{self.base_ref}`.",
                result.stderr.strip() or "git diff failed",
            )
            return

        changed = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if not changed:
            return

        changed_swift_non_test = [
            path
            for path in changed
            if path.endswith(".swift") and not self._is_test_file(Path(path))
        ]
        changed_tests = [path for path in changed if self._is_test_file(Path(path))]
        if changed_swift_non_test and not changed_tests:
            self._add_project(
                "TTC020",
                "PR introduces Swift functionality but includes no test file changes.",
                f"changed source files without test changes: {', '.join(changed_swift_non_test[:5])}",
            )

    def _check_protocol_mocks(self) -> None:
        concrete_init = re.compile(
            r"\blet\s+\w+(?:\s*:\s*[A-Za-z_]\w+)?\s*=\s*([A-Z]\w*(?:Service|Client|Repository|Manager|API|Store))\s*\("
        )
        for file_path in self.unit_test_files:
            lines = self._read_lines(file_path)
            for idx, line in enumerate(lines, start=1):
                match = concrete_init.search(line)
                if not match:
                    continue
                type_name = match.group(1)
                lowered = type_name.lower()
                if any(
                    token in lowered
                    for token in ("mock", "stub", "fake", "spy", "protocol")
                ):
                    continue
                self._add(
                    "TTC021",
                    file_path,
                    idx,
                    "Tests must mock dependencies via protocols, never concrete production types.",
                    _line_snippet(line),
                )

    def validate(self) -> None:
        self._check_test_files_exist()
        self._check_snapshot_dependency_version()
        self._check_snapshot_swift_testing_integration()
        self._check_snapshot_config_scoped()
        self._check_no_global_recording()
        self._check_snapshot_in_unit_target_only()
        self._check_snapshot_target_coverage()
        self._check_snapshot_determinism()
        self._check_view_model_tests()
        self._check_swift_testing_macro_usage()
        self._check_main_actor_view_model_tests()
        self._check_networking_tests()
        self._check_no_real_server_calls()
        self._check_signature_export_tests()
        self._check_required_integration_flow()
        self._check_time_limits()
        self._check_coverage_threshold()
        self._check_feature_diff_includes_tests()
        self._check_protocol_mocks()

    def build_result(self) -> ResultOutput:
        ordered = sorted(
            self.violations,
            key=lambda item: (item.rule_id, item.file, item.line, item.snippet),
        )
        verdict: Literal["PASS", "REJECT"] = "PASS" if not ordered else "REJECT"
        return {
            "contract": CONTRACT_NAME,
            "verdict": verdict,
            "summary": {
                "files_scanned": self.files_scanned,
                "rules_checked": len(RULE_TITLES),
                "violations": len(ordered),
            },
            "violations": [violation.as_dict() for violation in ordered],
        }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Exhibit A testing contract.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(),
        help="Project root to validate (default: current directory)",
    )
    parser.add_argument(
        "--base-ref",
        default="HEAD~1",
        help="Base ref for PR diff test inclusion checks (default: HEAD~1)",
    )
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Output format (default: json)",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    validator = ContractValidator(args.root, args.base_ref)
    validator.validate()
    result = validator.build_result()

    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print(f"contract: {result['contract']}")
        print(f"verdict: {result['verdict']}")
        print(
            "summary: "
            f"files={result['summary']['files_scanned']} "
            f"rules={result['summary']['rules_checked']} "
            f"violations={result['summary']['violations']}"
        )
        for violation in result["violations"]:
            print(
                f"{violation['rule_id']} {violation['file']}:{violation['line']} "
                f"{violation['rejection']} | {violation['snippet']}"
            )

    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
