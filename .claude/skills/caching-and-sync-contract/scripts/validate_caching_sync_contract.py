#!/usr/bin/env python3
"""Validate Exhibit A caching and sync architecture contract."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypedDict

CONTRACT_NAME = "caching-and-sync-contract"

RULE_TITLES = {
    "CSC000": "Swift source files must exist",
    "CSC001": "Offline-first doctrine markers must be explicit",
    "CSC002": "Content cache must be documents-backed JSON and hydrate on launch",
    "CSC003": "Cache reads and writes must be actor-isolated",
    "CSC004": "Cache writes must use temp file then rename/replace",
    "CSC005": "Signature PNG storage must be content-addressable and disk-backed",
    "CSC006": "Sync state machine must expose required states",
    "CSC007": "last_sync_at must be persisted in UserDefaults",
    "CSC008": "Sync requests must use incremental since parameter",
    "CSC009": "Optimistic signature flow must cache before upload",
    "CSC010": "Signature uploads must run in background contexts",
    "CSC011": "Failed uploads must set retry indicator",
    "CSC012": "Failed uploads must never remove cached content",
    "CSC013": "Launch cache rendering target must be <= 300ms",
    "CSC014": "Network sync/upload must be background-only",
    "CSC015": "Unread tracking must persist Set<UUID> via UserDefaults",
    "CSC016": "Unread badge logic must derive from unread set membership",
    "CSC017": "Cache invalidation must be tied to sync response handling",
    "CSC018": "Time-based cache invalidation is forbidden",
    "CSC019": "Launch spinner must not gate cached startup state",
    "CSC020": "Blocking or UI-coupled network calls are forbidden",
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
    ".next",
}

REQUIRED_MARKERS = (
    "CACHE-CONTRACT: local-cache-authoritative",
    "CACHE-CONTRACT: network-sync-only",
    "CACHE-CONTRACT: launch-cache-hydration",
    "CACHE-CONTRACT: cache-write-atomic-temp-rename",
    "CACHE-CONTRACT: signatures-optimistic-background-upload",
    "CACHE-CONTRACT: rollback-retain-cache-show-retry",
    "CACHE-CONTRACT: invalidate-on-sync-response-only",
    "CACHE-CONTRACT: launch-latency-under-300ms",
    "CACHE-CONTRACT: network-background-only",
    "CACHE-CONTRACT: no-launch-spinner-if-cache",
)

TIME_INVALIDATION_TOKENS = (
    "ttl",
    "timeToLive",
    "expiresAt",
    "expiration",
    "expiry",
    "staleAfter",
    "DispatchSourceTimer",
    "Timer.scheduledTimer",
)

NETWORK_TOKENS = (
    ".data(for:",
    ".data(from:",
    ".upload(for:",
    ".download(for:",
    "URLSession.shared.data(",
    "URLSession.shared.upload(",
    "URLSession.shared.download(",
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


def _relative_path(root: Path, file_path: Path) -> str:
    try:
        rel = file_path.resolve().relative_to(root.resolve())
    except ValueError:
        rel = file_path
    return rel.as_posix()


def _is_ignored(path: Path) -> bool:
    return any(part in IGNORED_DIRS for part in path.parts)


def _line_snippet(line: str) -> str:
    return line.strip()[:220]


class ContractValidator:
    """Deterministic validator for the caching and sync architecture contract."""

    def __init__(self, root: Path):
        self.root = root.resolve()
        self.violations: list[Violation] = []
        self.swift_files = self._collect_swift_files()
        self.files_scanned = len(self.swift_files)
        self.rule_count = len(RULE_TITLES) - 1
        self._cache_lower: dict[Path, list[str]] = {}

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

    def _lower_lines(self, file_path: Path) -> list[str]:
        cached = self._cache_lower.get(file_path)
        if cached is not None:
            return cached
        lowered = [line.lower() for line in self._read_lines(file_path)]
        self._cache_lower[file_path] = lowered
        return lowered

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
                line=max(line_no, 1),
                snippet=snippet,
            )
        )

    def _full_text(self) -> str:
        chunks: list[str] = []
        for file_path in self.swift_files:
            chunks.append("\n".join(self._read_lines(file_path)))
        return "\n".join(chunks)

    def _line_with(self, needle: str) -> tuple[Path, int, str] | None:
        low = needle.lower()
        for file_path in self.swift_files:
            lines = self._read_lines(file_path)
            for idx, line in enumerate(lines, start=1):
                if low in line.lower():
                    return (file_path, idx, line)
        return None

    def _check_doctrine_markers(self) -> None:
        missing = []
        for marker in REQUIRED_MARKERS:
            hit = self._line_with(marker)
            if hit is None:
                missing.append(marker)
        if missing:
            self._add(
                "CSC001",
                self.root / "PROJECT_ROOT",
                1,
                "Required CACHE-CONTRACT doctrine markers are missing.",
                f"missing markers: {', '.join(missing)}",
            )

    def _check_documents_json_launch_hydration(self) -> None:
        full = self._full_text()
        has_docs_dir = ".documentDirectory" in full or "documentsDirectory" in full
        has_json = ".json" in full
        hydration_tokens = (
            "loadCache(",
            "hydrateCache(",
            "bootstrapFromCache(",
            "loadCachedContent(",
            "CACHE-CONTRACT: launch-cache-hydration",
        )
        has_hydration = any(token in full for token in hydration_tokens)
        if has_docs_dir and has_json and has_hydration:
            return
        self._add(
            "CSC002",
            self.root / "PROJECT_ROOT",
            1,
            "Cache must be JSON in app documents directory and loaded at launch.",
            "expected .documentDirectory + .json + launch hydration path",
        )

    def _check_cache_actor(self) -> None:
        actor_re = re.compile(r"^\s*actor\s+\w*(Cache|Store|Repository)\w*\b")
        for file_path in self.swift_files:
            for idx, line in enumerate(self._read_lines(file_path), start=1):
                if actor_re.search(line):
                    return
        self._add(
            "CSC003",
            self.root / "PROJECT_ROOT",
            1,
            "Declare an actor-based cache store to isolate cache reads/writes.",
            "expected actor <NameContainingCache/Store/Repository>",
        )

    def _check_atomic_write(self) -> None:
        has_temp = False
        has_rename = False
        temp_hit: tuple[Path, int, str] | None = None
        rename_hit: tuple[Path, int, str] | None = None
        temp_re = re.compile(r"\b(tmp|temp|temporaryDirectory)\b", re.IGNORECASE)
        rename_re = re.compile(r"\b(replaceItemAt|moveItem\(at:)\b")
        for file_path in self.swift_files:
            for idx, line in enumerate(self._read_lines(file_path), start=1):
                if not has_temp and temp_re.search(line):
                    has_temp = True
                    temp_hit = (file_path, idx, line)
                if not has_rename and rename_re.search(line):
                    has_rename = True
                    rename_hit = (file_path, idx, line)
        if has_temp and has_rename:
            return
        anchor = temp_hit or rename_hit
        if anchor is None:
            self._add(
                "CSC004",
                self.root / "PROJECT_ROOT",
                1,
                "Cache writes must use temp-file write followed by rename/replace.",
                "missing temp-file and rename/replace write path",
            )
            return
        self._add(
            "CSC004",
            anchor[0],
            anchor[1],
            "Cache writes must use both temp-file staging and rename/replace commit.",
            _line_snippet(anchor[2]),
        )

    def _check_signature_png_contract(self) -> None:
        filename_re = re.compile(
            r'"\\\([^)]*content[^)]*\)_\\\([^)]*signer[^)]*\)\.png"',
            re.IGNORECASE,
        )
        has_filename_pattern = False
        has_disk_persistence = False
        signature_hint: tuple[Path, int, str] | None = None
        for file_path in self.swift_files:
            lines = self._read_lines(file_path)
            for idx, line in enumerate(lines, start=1):
                low = line.lower()
                if not has_filename_pattern and filename_re.search(line):
                    has_filename_pattern = True
                    signature_hint = (file_path, idx, line)
                if (
                    not has_filename_pattern
                    and "_\\(" in line
                    and "signer" in low
                    and ".png" in low
                    and "content" in low
                ):
                    has_filename_pattern = True
                    signature_hint = (file_path, idx, line)
                if not has_disk_persistence and (
                    ("pngdata()" in low and "write(to:" in low)
                    or ("createfile" in low and ".png" in low)
                ):
                    has_disk_persistence = True
                    if signature_hint is None:
                        signature_hint = (file_path, idx, line)
        if has_filename_pattern and has_disk_persistence:
            return
        anchor = signature_hint or (
            self.root / "PROJECT_ROOT",
            1,
            "missing signature storage contract",
        )
        self._add(
            "CSC005",
            anchor[0],
            anchor[1],
            "Persist signatures to disk with filename format {content_id}_{signer}.png.",
            _line_snippet(anchor[2]),
        )

    def _check_sync_state_machine(self) -> None:
        full = self._full_text()
        enum_match = re.search(
            r"enum\s+SyncState\b[^{]*\{(?P<body>[\s\S]*?)\n\}",
            full,
        )
        if not enum_match:
            self._add(
                "CSC006",
                self.root / "PROJECT_ROOT",
                1,
                "Define enum SyncState with required states.",
                "missing enum SyncState",
            )
            return
        body = enum_match.group("body")
        requirements = (
            (r"\bcase\s+idle\b", ".idle"),
            (r"\bcase\s+syncing\b", ".syncing"),
            (r"\bcase\s+completed\s*\(\s*Date\s*\)", ".completed(Date)"),
            (r"\bcase\s+failed\s*\(\s*Error\s*\)", ".failed(Error)"),
        )
        missing = [
            label for pattern, label in requirements if re.search(pattern, body) is None
        ]
        if not missing:
            return
        self._add(
            "CSC006",
            self.root / "PROJECT_ROOT",
            1,
            "SyncState is missing required states.",
            f"missing states: {', '.join(missing)}",
        )

    def _check_last_sync_user_defaults(self) -> None:
        full = self._full_text()
        if "UserDefaults" in full and "last_sync_at" in full:
            return
        self._add(
            "CSC007",
            self.root / "PROJECT_ROOT",
            1,
            "Persist last_sync_at in UserDefaults.",
            'missing UserDefaults usage with key "last_sync_at"',
        )

    def _check_since_parameter(self) -> None:
        full = self._full_text()
        has_since = (
            "?since=" in full
            or re.search(r'URLQueryItem\s*\(\s*name:\s*"since"', full) is not None
            or re.search(r"queryItems?.*since", full, re.IGNORECASE) is not None
        )
        if has_since:
            return
        self._add(
            "CSC008",
            self.root / "PROJECT_ROOT",
            1,
            "Sync requests must include incremental since parameter.",
            'missing ?since= or URLQueryItem(name: "since", ...)',
        )

    def _check_optimistic_signature_cache_before_upload(self) -> None:
        passed = False
        for file_path in self.swift_files:
            lower = self._lower_lines(file_path)
            cache_idx: int | None = None
            upload_idx: int | None = None
            for idx, line in enumerate(lower, start=1):
                if (
                    cache_idx is None
                    and "signature" in line
                    and any(
                        token in line for token in ("cache", "insert", "append", "save")
                    )
                ):
                    cache_idx = idx
                if (
                    upload_idx is None
                    and "signature" in line
                    and any(token in line for token in ("upload", "sync", "send"))
                ):
                    upload_idx = idx
            if (
                cache_idx is not None
                and upload_idx is not None
                and cache_idx <= upload_idx
            ):
                passed = True
                break
        if passed:
            return
        self._add(
            "CSC009",
            self.root / "PROJECT_ROOT",
            1,
            "Optimistic flow must cache signature before upload starts.",
            "expected signature cache insert/append/save before upload call",
        )

    def _check_background_upload(self) -> None:
        full = self._full_text()
        has_background_path = any(
            token in full
            for token in (
                "URLSessionConfiguration.background(",
                "BGProcessingTaskRequest",
                "BGAppRefreshTaskRequest",
                "backgroundURLSession",
            )
        )
        if has_background_path:
            return
        self._add(
            "CSC010",
            self.root / "PROJECT_ROOT",
            1,
            "Signature uploads must run in background execution paths.",
            "missing URLSessionConfiguration.background or BGTask request path",
        )

    def _check_retry_indicator(self) -> None:
        full = self._full_text()
        if re.search(
            r"catch[\s\S]{0,280}(retry|needsRetry|showRetry)", full, re.IGNORECASE
        ):
            return
        self._add(
            "CSC011",
            self.root / "PROJECT_ROOT",
            1,
            "Upload failure path must expose retry indicator state.",
            "missing retry marker in catch/failure path",
        )

    def _check_no_failure_removal(self) -> None:
        failure_removal = re.search(
            r"catch[\s\S]{0,280}(remove|delete)[\s\S]{0,160}(cache|signature)",
            self._full_text(),
            re.IGNORECASE,
        )
        if failure_removal is None:
            return
        self._add(
            "CSC012",
            self.root / "PROJECT_ROOT",
            1,
            "Failure handling must not remove cached content/signatures.",
            _line_snippet(failure_removal.group(0).splitlines()[0]),
        )

    def _check_launch_budget(self) -> None:
        full = self._full_text()
        budget_re = re.compile(
            r"\b(?:cacheLaunchBudgetMs|launchCacheBudgetMs|launchBudgetMs)\s*=\s*(\d+)"
        )
        match = budget_re.search(full)
        if match is not None:
            ms = int(match.group(1))
            if ms <= 300:
                return
            self._add(
                "CSC013",
                self.root / "PROJECT_ROOT",
                1,
                "Launch cache budget exceeds 300ms.",
                f"found budget {ms}ms",
            )
            return
        if "0.3" in full and "CACHE-CONTRACT: launch-latency-under-300ms" in full:
            return
        self._add(
            "CSC013",
            self.root / "PROJECT_ROOT",
            1,
            "Declare launch cache display budget at or below 300ms.",
            "missing cacheLaunchBudgetMs <= 300 or equivalent 0.3s declaration",
        )

    def _check_network_background_only(self) -> None:
        full = self._full_text()
        has_marker = "CACHE-CONTRACT: network-background-only" in full
        has_background_net = any(
            token in full
            for token in (
                "URLSessionConfiguration.background(",
                "BGProcessingTaskRequest",
                "BGAppRefreshTaskRequest",
            )
        )
        if has_marker and has_background_net:
            return
        self._add(
            "CSC014",
            self.root / "PROJECT_ROOT",
            1,
            "Network sync/upload must be explicitly background-only.",
            "missing network-background-only marker or background network configuration",
        )

    def _check_unread_set_user_defaults(self) -> None:
        full = self._full_text()
        if re.search(r"Set<\s*UUID\s*>", full) and "UserDefaults" in full:
            return
        self._add(
            "CSC015",
            self.root / "PROJECT_ROOT",
            1,
            "Persist unread IDs as Set<UUID> in UserDefaults.",
            "missing Set<UUID> + UserDefaults unread persistence",
        )

    def _check_unread_badge_logic(self) -> None:
        full = self._full_text()
        has_contains_check = re.search(
            r"(unread|seen).*(contains)|contains.*(unread|seen)", full, re.IGNORECASE
        )
        has_badge = re.search(r"\bbadge\b|\bunreadBadge\b", full, re.IGNORECASE)
        if has_contains_check and has_badge:
            return
        self._add(
            "CSC016",
            self.root / "PROJECT_ROOT",
            1,
            "New content outside unread set must produce unread badge state.",
            "missing unread-set membership check tied to badge output",
        )

    def _check_sync_response_invalidation(self) -> None:
        full = self._full_text()
        has_marker = "CACHE-CONTRACT: invalidate-on-sync-response-only" in full
        has_sync_response_invalidation = re.search(
            r"(syncResponse|handleSyncResponse|didReceiveSyncResponse)[\s\S]{0,220}(invalidate|evict|prune)",
            full,
            re.IGNORECASE,
        )
        if has_marker and has_sync_response_invalidation:
            return
        self._add(
            "CSC017",
            self.root / "PROJECT_ROOT",
            1,
            "Cache invalidation must occur only from sync response handling.",
            "missing sync-response-bound invalidation implementation",
        )

    def _check_no_time_based_invalidation(self) -> None:
        for file_path in self.swift_files:
            lines = self._read_lines(file_path)
            lowered = [line.lower() for line in lines]
            for idx, low in enumerate(lowered, start=1):
                if not any(token.lower() in low for token in TIME_INVALIDATION_TOKENS):
                    continue
                if any(
                    token in low for token in ("cache", "content", "sync", "invalidate")
                ):
                    self._add(
                        "CSC018",
                        file_path,
                        idx,
                        "Time-based cache invalidation is forbidden.",
                        _line_snippet(lines[idx - 1]),
                    )
                    return
        return

    def _check_launch_spinner_logic(self) -> None:
        for file_path in self.swift_files:
            lines = self._read_lines(file_path)
            for idx, line in enumerate(lines, start=1):
                if "ProgressView" not in line:
                    continue
                window = lines[max(0, idx - 4) : idx + 2]
                joined = "\n".join(window)
                if "isLoading" in joined and "cache.isEmpty" not in joined:
                    self._add(
                        "CSC019",
                        file_path,
                        idx,
                        "Launch spinner cannot gate initial state when cache exists.",
                        _line_snippet(line),
                    )
                    return
        return

    def _check_no_blocking_ui_network(self) -> None:
        for file_path in self.swift_files:
            lines = self._read_lines(file_path)
            content = "\n".join(lines)
            view_file = re.search(r"struct\s+\w+\s*:\s*View\b", content) is not None
            main_actor = "@MainActor" in content
            for idx, line in enumerate(lines, start=1):
                low = line.lower()
                if any(token.lower() in low for token in NETWORK_TOKENS) and (
                    view_file or main_actor
                ):
                    self._add(
                        "CSC020",
                        file_path,
                        idx,
                        "UI/main-actor code must not perform direct network calls.",
                        _line_snippet(line),
                    )
                    return
                if any(
                    token in low
                    for token in ("dispatchsemaphore", ".wait()", "sleep(", "usleep(")
                ):
                    self._add(
                        "CSC020",
                        file_path,
                        idx,
                        "Blocking synchronization/network patterns are forbidden.",
                        _line_snippet(line),
                    )
                    return
        return

    def validate(self) -> None:
        if not self.swift_files:
            self._add(
                "CSC000",
                self.root / "PROJECT_ROOT",
                1,
                "No Swift source files found under root.",
                "expected at least one *.swift file",
            )
            return

        self._check_doctrine_markers()
        self._check_documents_json_launch_hydration()
        self._check_cache_actor()
        self._check_atomic_write()
        self._check_signature_png_contract()
        self._check_sync_state_machine()
        self._check_last_sync_user_defaults()
        self._check_since_parameter()
        self._check_optimistic_signature_cache_before_upload()
        self._check_background_upload()
        self._check_retry_indicator()
        self._check_no_failure_removal()
        self._check_launch_budget()
        self._check_network_background_only()
        self._check_unread_set_user_defaults()
        self._check_unread_badge_logic()
        self._check_sync_response_invalidation()
        self._check_no_time_based_invalidation()
        self._check_launch_spinner_logic()
        self._check_no_blocking_ui_network()

    def result(self) -> ResultOutput:
        ordered = sorted(
            self.violations,
            key=lambda item: (item.rule_id, item.file, item.line, item.rejection),
        )
        verdict: Literal["PASS", "REJECT"] = "PASS" if not ordered else "REJECT"
        return {
            "contract": CONTRACT_NAME,
            "verdict": verdict,
            "summary": {
                "files_scanned": self.files_scanned,
                "rules_checked": self.rule_count,
                "violations": len(ordered),
            },
            "violations": [item.as_dict() for item in ordered],
        }


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate caching/sync architecture contract."
    )
    parser.add_argument("--root", default=".", help="Project root to scan.")
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Output format.",
    )
    return parser.parse_args(argv)


def _emit_text(result: ResultOutput) -> str:
    lines = [
        f"contract: {result['contract']}",
        f"verdict: {result['verdict']}",
        f"files_scanned: {result['summary']['files_scanned']}",
        f"rules_checked: {result['summary']['rules_checked']}",
        f"violations: {result['summary']['violations']}",
    ]
    for item in result["violations"]:
        lines.append(
            f"{item['rule_id']} {item['file']}:{item['line']} {item['rejection']} | {item['snippet']}"
        )
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    args = _parse_args(argv)
    validator = ContractValidator(Path(args.root))
    validator.validate()
    result = validator.result()

    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print(_emit_text(result))
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
