#!/usr/bin/env python3
"""Validate Exhibit A error-handling and failure UX contract."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, NoReturn, TypedDict

CONTRACT_NAME = "error-handling-contract"

RULE_TITLES = {
    "EHC000": "Swift source files must exist",
    "EHC001": "Required ERROR-CONTRACT doctrine markers must exist",
    "EHC002": "Network-down UI must present the exact recess copy and retry action",
    "EHC003": "Network-down UI must render paper texture background",
    "EHC004": "Signature upload failure must retain local signature and show dustyRose sync indicator",
    "EHC005": "Signature upload failure must auto-retry on connectivity restoration",
    "EHC006": "Sync failures must retry silently and surface UI only after 3 consecutive failures",
    "EHC007": "Empty states must be contextual and illustrated; blank states are forbidden",
    "EHC008": "Primary loading states must use skeleton layouts matching real content",
    "EHC009": "Spinners are forbidden on primary screens",
    "EHC010": "Throwing functions must use typed error enums",
    "EHC011": "Error handling switches must be exhaustive and default-free",
    "EHC012": "User-facing copy must never expose technical/raw system errors",
    "EHC013": "Recoverable error states must expose retry, dismiss, or cache fallback",
    "EHC014": "Force unwraps, force casts, and force tries are forbidden",
    "EHC015": "fatalError/preconditionFailure forbidden in production paths",
    "EHC016": "Generic or swallowed catch blocks are forbidden",
    "EHC017": "Failure copy must stay in character (filing-oriented tone)",
    "EHC018": "Carolina-first reliability doctrine must be explicit",
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

REQUIRED_MARKERS = (
    "ERROR-CONTRACT: network-down-copy-the-court-is-in-recess",
    "ERROR-CONTRACT: network-down-retry-action",
    "ERROR-CONTRACT: network-down-paper-texture",
    "ERROR-CONTRACT: signature-failure-retain-local-signature",
    "ERROR-CONTRACT: signature-failure-sync-indicator-dustyRose-circular-arrow",
    "ERROR-CONTRACT: signature-failure-auto-retry-on-connectivity-restore",
    "ERROR-CONTRACT: sync-transient-silent-retry",
    "ERROR-CONTRACT: sync-ui-after-3-consecutive-failures",
    "ERROR-CONTRACT: empty-state-context-message-illustration",
    "ERROR-CONTRACT: primary-loading-skeleton-match-layout",
    "ERROR-CONTRACT: no-primary-spinner",
    "ERROR-CONTRACT: typed-error-enums-and-exhaustive-switches",
    "ERROR-CONTRACT: recovery-actions-retry-dismiss-cache",
    "ERROR-CONTRACT: user-copy-no-technical-leaks",
    "ERROR-CONTRACT: carolina-experience-priority",
)

PRIMARY_SCREEN_HINT = re.compile(
    r"(home|dashboard|feed|main|root|content|court|landing|index)", re.IGNORECASE
)

FORCE_UNWRAP_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*!\s*(?:[).,?:\]\n]|$)")
IUO_DECL_RE = re.compile(r":\s*[A-Za-z_][A-Za-z0-9_<>,\[\]\s\.?]*!\s*(?:=|\{|$)")
UNTYPED_THROWS_RE = re.compile(r"\bfunc\b[^\n{]*\bthrows\b(?!\s*\()")
ERROR_ENUM_RE = re.compile(
    r"\benum\s+([A-Za-z_][A-Za-z0-9_]*Error)\s*:\s*[^\n{]*\bError\b"
)
STRING_LITERAL_RE = re.compile(r'"(?:\\.|[^"\\])*"')
TECH_COPY_RE = re.compile(
    r"(HTTP\s*\d{3}|status\s*code|NSError|URLError|NSURLError|localizedDescription|DecodingError|stack\s*trace|exception|debug\s*info|fatal\s*error)",
    re.IGNORECASE,
)
RECOVERY_TOKEN_RE = re.compile(
    r"\b(retry|dismiss|try again|use cached|cache fallback|offline copy|continue offline)\b",
    re.IGNORECASE,
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


def _relative_path(root: Path, path: Path) -> str:
    try:
        rel = path.resolve().relative_to(root.resolve())
    except ValueError:
        rel = path
    return rel.as_posix()


def _is_ignored(path: Path) -> bool:
    return any(part in IGNORED_DIRS for part in path.parts)


def _line_snippet(line: str) -> str:
    return line.strip()[:220]


def _is_comment(line: str) -> bool:
    stripped = line.strip()
    return (
        stripped.startswith("//")
        or stripped.startswith("/*")
        or stripped.startswith("*")
    )


def _is_test_or_preview(path: Path) -> bool:
    lower = path.as_posix().lower()
    return "tests" in lower or "preview" in lower


class ContractValidator:
    """Deterministic validator for Exhibit A error-handling contract."""

    def __init__(self, root: Path):
        self.root = root.resolve()
        self.swift_files = self._collect_files(("*.swift",))
        self.copy_files = self._collect_files(("*.swift", "*.strings", "*.xcstrings"))
        self.files_scanned = len(self.swift_files)
        self.rule_count = len(RULE_TITLES) - 1
        self.violations: list[Violation] = []
        self.violation_index: set[tuple[str, str, int]] = set()
        self.cache: dict[Path, list[str]] = {}

    def _collect_files(self, patterns: tuple[str, ...]) -> list[Path]:
        files: list[Path] = []
        seen: set[Path] = set()
        for pattern in patterns:
            for path in self.root.rglob(pattern):
                if _is_ignored(path):
                    continue
                if path in seen:
                    continue
                seen.add(path)
                files.append(path)
        return sorted(files)

    def _read_lines(self, path: Path) -> list[str]:
        cached = self.cache.get(path)
        if cached is not None:
            return cached
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        self.cache[path] = lines
        return lines

    def _all_text(self, files: list[Path] | None = None) -> str:
        targets = files if files is not None else self.swift_files
        return "\n".join("\n".join(self._read_lines(path)) for path in targets)

    def _all_rows(self, files: list[Path] | None = None) -> list[tuple[Path, int, str]]:
        targets = files if files is not None else self.swift_files
        rows: list[tuple[Path, int, str]] = []
        for path in targets:
            for idx, line in enumerate(self._read_lines(path), start=1):
                rows.append((path, idx, line))
        return rows

    def _window(
        self, path: Path, line_no: int, before: int = 2, after: int = 12
    ) -> str:
        lines = self._read_lines(path)
        start = max(0, line_no - 1 - before)
        end = min(len(lines), line_no - 1 + after)
        return "\n".join(lines[start:end])

    def _line_with(self, needle: str) -> tuple[Path, int, str] | None:
        low = needle.lower()
        for path in self.swift_files:
            for idx, line in enumerate(self._read_lines(path), start=1):
                if low in line.lower():
                    return (path, idx, line)
        return None

    def _add(
        self, rule_id: str, file_path: Path, line_no: int, message: str, snippet: str
    ) -> None:
        rel = _relative_path(self.root, file_path)
        line = max(1, line_no)
        key = (rule_id, rel, line)
        if key in self.violation_index:
            return
        self.violation_index.add(key)
        self.violations.append(
            Violation(
                rule_id=rule_id,
                title=RULE_TITLES[rule_id],
                rejection=f"REJECT: {message}",
                file=rel,
                line=line,
                snippet=snippet,
            )
        )

    def _check_required_markers(self) -> None:
        missing = [
            marker for marker in REQUIRED_MARKERS if self._line_with(marker) is None
        ]
        if missing:
            self._add(
                "EHC001",
                self.root / "PROJECT_ROOT",
                1,
                "Required ERROR-CONTRACT doctrine markers are missing.",
                f"missing markers: {', '.join(missing)}",
            )

    def _check_network_down_state(self) -> None:
        full = self._all_text().lower()
        if "the court is in recess" not in full:
            self._add(
                "EHC002",
                self.root / "PROJECT_ROOT",
                1,
                'Network-down state must include exact copy "The court is in recess".',
                'missing phrase: "The court is in recess"',
            )

        if not re.search(r"\b(retry|try again)\b", full):
            self._add(
                "EHC002",
                self.root / "PROJECT_ROOT",
                1,
                "Network-down state must expose an explicit retry action.",
                "missing retry action token",
            )

        paper_tokens = (
            "papertexture",
            "paper texture",
            "paper_background",
            "paperbackground",
            "papertexturebackground",
        )
        if not any(token in full for token in paper_tokens):
            self._add(
                "EHC003",
                self.root / "PROJECT_ROOT",
                1,
                "Network-down state must render a paper texture background.",
                "missing paper texture token",
            )

    def _check_signature_failures(self) -> None:
        full = self._all_text().lower()

        retention_tokens = (
            "retainlocalsignature",
            "retain local signature",
            "localsignaturecache",
            "cachesignature",
            "persistsignaturelocally",
            "signaturecache",
        )
        has_retention = any(token in full for token in retention_tokens)

        has_dusty_rose = "dustyrose" in full or "dusty_rose" in full
        arrow_tokens = (
            "arrow.clockwise",
            "arrow.triangle.2.circlepath",
            "circulararrow",
            "syncindicator",
        )
        has_indicator = any(token in full for token in arrow_tokens)

        if not has_retention or not (has_dusty_rose and has_indicator):
            self._add(
                "EHC004",
                self.root / "PROJECT_ROOT",
                1,
                "Signature failure path must retain local signature and show dustyRose circular-arrow sync indicator.",
                "expected retention token + dustyRose + circular-arrow indicator",
            )

        connectivity_tokens = (
            "nwpathmonitor",
            "pathupdatehandler",
            "waitsforconnectivity",
            "reachability",
            "networkpath",
        )
        retry_tokens = (
            "retrypendinguploads",
            "resumependinguploads",
            "retrysignatureupload",
            "retryfaileduploads",
            "enqueuependingupload",
        )
        has_connectivity = any(token in full for token in connectivity_tokens)
        has_retry_on_restore = any(token in full for token in retry_tokens)
        if not (has_connectivity and has_retry_on_restore):
            self._add(
                "EHC005",
                self.root / "PROJECT_ROOT",
                1,
                "Signature uploads must auto-retry when connectivity is restored.",
                "expected connectivity monitor + retry-on-restore flow",
            )

        for path in self.swift_files:
            rows = self._read_lines(path)
            for idx, line in enumerate(rows, start=1):
                low = line.lower()
                if "catch" not in low:
                    continue
                window = self._window(path, idx, before=0, after=14).lower()
                if "signature" in window and ("remove" in window or "delete" in window):
                    self._add(
                        "EHC004",
                        path,
                        idx,
                        "Signature failure handling must not delete local signature state.",
                        _line_snippet(line),
                    )

    def _check_sync_failures(self) -> None:
        full = self._all_text().lower()

        silent_retry_tokens = (
            "transient",
            "backoff",
            "tasksleep",
            "retrysync",
            "scheduleretry",
            "silentretry",
            "silently",
        )
        if not any(token in full for token in silent_retry_tokens):
            self._add(
                "EHC006",
                self.root / "PROJECT_ROOT",
                1,
                "Sync failures must retry silently for transient errors.",
                "missing transient silent retry evidence",
            )

        threshold_re = re.compile(
            r"(consecutive|sync)?\s*failure\s*count\s*(>=|==)\s*3|if\s+\w*failure\w*\s*>=\s*3",
            re.IGNORECASE,
        )
        has_threshold = any(
            threshold_re.search(line) for _, _, line in self._all_rows(self.swift_files)
        )

        ui_surface_tokens = (
            "showsyncerror",
            "issyncerrorpresented",
            "syncfailurebanner",
            "presentsyncerror",
            "syncalert",
        )
        has_ui_surface = any(token in full for token in ui_surface_tokens)

        if not has_threshold or not has_ui_surface:
            self._add(
                "EHC006",
                self.root / "PROJECT_ROOT",
                1,
                "Sync error UI must appear only after 3 consecutive failures.",
                "missing failure-count threshold or gated UI surfacing token",
            )

    def _check_empty_and_loading_states(self) -> None:
        full = self._all_text().lower()

        for path, idx, line in self._all_rows(self.swift_files):
            if _is_comment(line):
                continue
            if "EmptyView()" in line and "allow-empty-contract" not in line:
                self._add(
                    "EHC007",
                    path,
                    idx,
                    "Blank EmptyView states are forbidden. Provide contextual message and subtle illustration.",
                    _line_snippet(line),
                )

        has_contextual_empty = "contentunavailableview(" in full or (
            "emptystate" in full and "image(" in full and "text(" in full
        )
        if not has_contextual_empty:
            self._add(
                "EHC007",
                self.root / "PROJECT_ROOT",
                1,
                "Empty states must include contextual copy and subtle illustration.",
                "missing ContentUnavailableView or equivalent empty-state composition",
            )

        skeleton_tokens = (
            "redacted(reason: .placeholder)",
            "skeleton",
            "shimmer",
            "placeholdercard",
        )
        if not any(token in full for token in skeleton_tokens):
            self._add(
                "EHC008",
                self.root / "PROJECT_ROOT",
                1,
                "Primary loading states must use skeleton layouts matching real content.",
                "missing skeleton placeholder pattern",
            )

        for path in self.swift_files:
            rel = _relative_path(self.root, path)
            is_primary_file = bool(PRIMARY_SCREEN_HINT.search(rel))
            lines = self._read_lines(path)
            file_text = "\n".join(lines)
            for idx, line in enumerate(lines, start=1):
                if "ProgressView(" not in line:
                    continue
                if "secondary-spinner-exception" in line:
                    continue
                if is_primary_file or "ERROR-CONTRACT: primary-screen" in file_text:
                    self._add(
                        "EHC009",
                        path,
                        idx,
                        "Primary screens must use skeleton loading and never ProgressView spinners.",
                        _line_snippet(line),
                    )

    def _check_typed_errors(self) -> None:
        error_enums: set[str] = set()
        for path, idx, line in self._all_rows(self.swift_files):
            if _is_comment(line):
                continue
            enum_match = ERROR_ENUM_RE.search(line)
            if enum_match:
                error_enums.add(enum_match.group(1))

            if UNTYPED_THROWS_RE.search(line):
                self._add(
                    "EHC010",
                    path,
                    idx,
                    "Use typed throws with explicit error enum (throws(MyError)).",
                    _line_snippet(line),
                )

        if not error_enums:
            self._add(
                "EHC010",
                self.root / "PROJECT_ROOT",
                1,
                "Define typed error enums conforming to Error for all throwing paths.",
                "missing enum <Name>Error: Error",
            )

        for path in self.swift_files:
            lines = self._read_lines(path)
            for idx, line in enumerate(lines, start=1):
                stripped = line.strip()
                if stripped.startswith("catch {"):
                    self._add(
                        "EHC016",
                        path,
                        idx,
                        "Generic catch blocks are forbidden. Bind typed error and switch exhaustively.",
                        _line_snippet(line),
                    )
                    continue

                if stripped.startswith("catch"):
                    window = self._window(path, idx, before=0, after=14)
                    if "switch" not in window:
                        self._add(
                            "EHC011",
                            path,
                            idx,
                            "Catch blocks must switch exhaustively over typed errors.",
                            _line_snippet(line),
                        )

                if "switch" in line and "error" in line.lower():
                    block = self._window(path, idx, before=0, after=20)
                    if re.search(r"\bdefault\s*:", block):
                        self._add(
                            "EHC011",
                            path,
                            idx,
                            "Error switches must be exhaustive without default cases.",
                            _line_snippet(line),
                        )

                if "try?" in line:
                    self._add(
                        "EHC016",
                        path,
                        idx,
                        "Silent error swallowing via try? is forbidden on contract paths.",
                        _line_snippet(line),
                    )

    def _check_copy_and_recovery(self) -> None:
        text_full = self._all_text(self.copy_files)
        has_filing_tone = "filing error. please try again." in text_full.lower()
        if not has_filing_tone:
            self._add(
                "EHC017",
                self.root / "PROJECT_ROOT",
                1,
                "Failure messaging must remain in-character (for example: Filing error. Please try again.).",
                "missing filing-oriented error copy",
            )

        global_recovery = {
            "retry": False,
            "dismiss": False,
            "cache": False,
        }

        for path in self.copy_files:
            lines = self._read_lines(path)
            content = "\n".join(lines)

            file_has_error_ui = bool(
                re.search(r"error", content, re.IGNORECASE)
                and re.search(
                    r"(Text\(|Alert\(|\.alert\(|ContentUnavailableView|confirmationDialog)",
                    content,
                )
            )

            file_has_recovery = bool(RECOVERY_TOKEN_RE.search(content))
            if file_has_error_ui and not file_has_recovery:
                self._add(
                    "EHC013",
                    path,
                    1,
                    "Error UI must provide a recovery path (retry, dismiss, or cache fallback).",
                    "missing recovery action tokens",
                )

            low = content.lower()
            if "retry" in low or "try again" in low:
                global_recovery["retry"] = True
            if "dismiss" in low or "cancel" in low or "close" in low:
                global_recovery["dismiss"] = True
            if "cache" in low or "offline copy" in low or "continue offline" in low:
                global_recovery["cache"] = True

            for idx, line in enumerate(lines, start=1):
                for literal in STRING_LITERAL_RE.findall(line):
                    unquoted = literal.strip('"')
                    if TECH_COPY_RE.search(unquoted):
                        self._add(
                            "EHC012",
                            path,
                            idx,
                            "User-facing copy cannot expose HTTP/system/raw technical diagnostics.",
                            _line_snippet(line),
                        )

                if "Text(" in line or "Alert(" in line or ".alert(" in line:
                    if TECH_COPY_RE.search(line):
                        self._add(
                            "EHC012",
                            path,
                            idx,
                            "Developer-facing diagnostics cannot appear in UI components.",
                            _line_snippet(line),
                        )

        for key, present in global_recovery.items():
            if present:
                continue
            self._add(
                "EHC013",
                self.root / "PROJECT_ROOT",
                1,
                "Recoverable error handling must expose retry, dismiss, and cache-fallback affordances across the app.",
                f"missing recovery affordance token category: {key}",
            )

        if "carolina" not in text_full.lower():
            self._add(
                "EHC018",
                self.root / "PROJECT_ROOT",
                1,
                "Carolina-first experience doctrine must be explicit in contracted error handling paths.",
                "missing Carolina prioritization token",
            )

    def _check_crash_prevention(self) -> None:
        for path, idx, line in self._all_rows(self.swift_files):
            if _is_comment(line):
                continue

            if "try!" in line or "as!" in line:
                self._add(
                    "EHC014",
                    path,
                    idx,
                    "Crash-prone force operations (try!/as!) are forbidden.",
                    _line_snippet(line),
                )

            if FORCE_UNWRAP_RE.search(line) and "!=" not in line and "!==" not in line:
                self._add(
                    "EHC014",
                    path,
                    idx,
                    "Force unwrap is forbidden. Handle optionals safely.",
                    _line_snippet(line),
                )

            if IUO_DECL_RE.search(line):
                self._add(
                    "EHC014",
                    path,
                    idx,
                    "Implicitly unwrapped optionals are forbidden in production paths.",
                    _line_snippet(line),
                )

            if "fatalError(" in line or "preconditionFailure(" in line:
                if _is_test_or_preview(path):
                    continue
                self._add(
                    "EHC015",
                    path,
                    idx,
                    "fatalError/preconditionFailure are forbidden in production error paths.",
                    _line_snippet(line),
                )

    def run(self) -> None:
        if not self.swift_files:
            self._add(
                "EHC000",
                self.root / "PROJECT_ROOT",
                1,
                "No Swift source files were found under the target root.",
                "no *.swift files discovered",
            )
            return

        self._check_required_markers()
        self._check_network_down_state()
        self._check_signature_failures()
        self._check_sync_failures()
        self._check_empty_and_loading_states()
        self._check_typed_errors()
        self._check_copy_and_recovery()
        self._check_crash_prevention()

        self.violations.sort(key=lambda v: (v.file, v.line, v.rule_id, v.snippet))

    def result(self) -> ResultOutput:
        verdict: Literal["PASS", "REJECT"] = "PASS" if not self.violations else "REJECT"
        return {
            "contract": CONTRACT_NAME,
            "verdict": verdict,
            "summary": {
                "files_scanned": self.files_scanned,
                "rules_checked": self.rule_count,
                "violations": len(self.violations),
            },
            "violations": [item.as_dict() for item in self.violations],
        }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Swift code against Exhibit A error-handling contract."
    )
    parser.add_argument("--root", default=".", help="Project root to scan")
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Output format",
    )
    return parser.parse_args(argv)


def _print_text(result: ResultOutput) -> None:
    summary = result["summary"]
    print(
        f"{result['contract']}: {result['verdict']} "
        f"(files={summary['files_scanned']}, rules={summary['rules_checked']}, violations={summary['violations']})"
    )
    for violation in result["violations"]:
        print(
            f"{violation['rule_id']} {violation['file']}:{violation['line']} "
            f"{violation['rejection']} :: {violation['snippet']}"
        )


def main(argv: list[str] | None = None) -> NoReturn:
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
