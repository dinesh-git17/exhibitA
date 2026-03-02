#!/usr/bin/env python3
"""Validate Exhibit A networking layer contract."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, NoReturn, TypedDict

CONTRACT_NAME = "networking-layer-contract"

RULE_TITLES = {
    "NLC000": "Swift source files must exist",
    "NLC001": "APIClient must be implemented as an actor",
    "NLC002": "APIClient must be mockable via protocol abstraction",
    "NLC003": "Networking classes cannot own shared mutable state",
    "NLC004": "Request protocol must define typed Decodable response",
    "NLC005": "Completion-handler URLSession APIs are forbidden",
    "NLC006": "URLSession calls must use async/await",
    "NLC007": "Retry policy must be exponential with strict bounds",
    "NLC008": "Networking logs must use OSLog in debug builds only",
    "NLC009": "print-based debugging is forbidden",
    "NLC010": "URL construction must be enum-driven without raw URL strings",
    "NLC011": "Offline upload queue must persist JSON to disk",
    "NLC012": "Connectivity retry must use NWPathMonitor",
    "NLC013": "Certificate pinning is required for exhibita.dineshd.dev",
    "NLC014": "Every request must enforce a 15-second timeout",
    "NLC015": "APIError must provide exhaustive contract cases",
    "NLC016": "Codable models must stay strict and static",
    "NLC017": "Silent error swallowing is forbidden",
    "NLC018": "Network calls must return Result or throw typed APIError",
    "NLC019": "Tests must never hit real servers",
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

NETWORK_FILE_HINT = re.compile(
    r"(api|network|client|endpoint|request|transport|upload|session|service|http)",
    re.IGNORECASE,
)

RAW_URL_RE = re.compile(r'"(?:https?|wss?)://[^"]+"')

NETWORK_CALL_TOKENS = (
    ".data(for:",
    ".data(from:",
    ".upload(for:",
    ".download(for:",
    ".download(from:",
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


def _extract_function_blocks(lines: list[str]) -> list[tuple[int, int, str, str]]:
    """Return tuples of (start_line, end_line, name, declaration_line)."""
    blocks: list[tuple[int, int, str, str]] = []
    func_re = re.compile(r"^\s*(?:@\w+(?:\([^)]*\))?\s*)*func\s+([A-Za-z_]\w*)[^{]*$")
    i = 0
    while i < len(lines):
        match = func_re.search(lines[i])
        if not match:
            i += 1
            continue
        name = match.group(1)
        decl = lines[i]
        start = i + 1
        j = i
        balance = 0
        opened = False
        while j < len(lines):
            line = lines[j]
            opens = line.count("{")
            closes = line.count("}")
            if opens:
                opened = True
            balance += opens - closes
            if opened and balance <= 0:
                blocks.append((start, j + 1, name, decl))
                break
            j += 1
        if j >= len(lines):
            blocks.append((start, len(lines), name, decl))
            break
        i = j + 1
    return blocks


class ContractValidator:
    """Deterministic validator for Exhibit A networking contract."""

    def __init__(self, root: Path):
        self.root = root.resolve()
        self.violations: list[Violation] = []
        self.swift_files = self._collect_swift_files()
        self.files_scanned = len(self.swift_files)
        self.rule_count = len(RULE_TITLES) - 1

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
                line=max(line_no, 1),
                snippet=snippet,
            )
        )

    def _all_lines(self) -> list[tuple[Path, int, str]]:
        rows: list[tuple[Path, int, str]] = []
        for file_path in self.swift_files:
            lines = self._read_lines(file_path)
            for idx, line in enumerate(lines, start=1):
                rows.append((file_path, idx, line))
        return rows

    def _find_network_files(self) -> list[Path]:
        network_files: list[Path] = []
        for file_path in self.swift_files:
            rel = _relative_path(self.root, file_path)
            content = "\n".join(self._read_lines(file_path))
            if NETWORK_FILE_HINT.search(rel) or "URLSession" in content:
                network_files.append(file_path)
        return network_files

    def _check_api_client_actor_and_mockability(self) -> None:
        decl_re = re.compile(
            r"^\s*(?:@\w+(?:\([^)]*\))?\s*)*(actor|class|struct)\s+APIClient\b(?:\s*:\s*([^{]+))?"
        )
        protocol_re = re.compile(r"^\s*protocol\s+([A-Za-z_]\w*)\b")

        api_client_decls: list[tuple[str, Path, int, str]] = []
        protocols: set[str] = set()

        for file_path in self.swift_files:
            for idx, line in enumerate(self._read_lines(file_path), start=1):
                m = decl_re.search(line)
                if m:
                    api_client_decls.append((m.group(1), file_path, idx, line))
                p = protocol_re.search(line)
                if p and "APIClient" in p.group(1):
                    protocols.add(p.group(1))

        if not api_client_decls:
            self._add(
                "NLC001",
                self.root / "PROJECT_ROOT",
                1,
                "Type `APIClient` is missing. Declare `actor APIClient`.",
                "missing actor APIClient",
            )
            return

        actor_decl: tuple[str, Path, int, str] | None = None
        for kind, file_path, idx, line in api_client_decls:
            if kind != "actor":
                self._add(
                    "NLC001",
                    file_path,
                    idx,
                    "`APIClient` must be declared as an `actor`.",
                    _line_snippet(line),
                )
            else:
                actor_decl = (kind, file_path, idx, line)

        if not actor_decl:
            return

        _, actor_file, actor_line, actor_decl_line = actor_decl
        has_protocol_conformance = ":" in actor_decl_line and bool(
            re.search(r":[^{]*\w+", actor_decl_line)
        )
        if not protocols:
            self._add(
                "NLC002",
                actor_file,
                actor_line,
                "Define a protocol abstraction for APIClient mockability.",
                _line_snippet(actor_decl_line),
            )
            return

        conformance_tokens = {
            token.strip()
            for token in (
                actor_decl_line.split(":", 1)[1].split("{", 1)[0].split(",")
                if ":" in actor_decl_line
                else []
            )
        }
        if not has_protocol_conformance or not (conformance_tokens & protocols):
            self._add(
                "NLC002",
                actor_file,
                actor_line,
                "APIClient actor must conform to a protocol for mocking.",
                _line_snippet(actor_decl_line),
            )

    def _check_networking_classes_mutable_state(self) -> None:
        class_re = re.compile(
            r"^\s*(?:final\s+)?class\s+([A-Za-z_]\w*(API|Network|Client|Service|Transport|Uploader)\w*)\b"
        )
        mutable_re = re.compile(
            r"^\s*(?:public|internal|private|fileprivate)?\s*var\s+[A-Za-z_]\w*\b"
        )
        for file_path in self._find_network_files():
            lines = self._read_lines(file_path)
            for idx, line in enumerate(lines, start=1):
                class_match = class_re.search(line)
                if not class_match:
                    continue
                balance = line.count("{") - line.count("}")
                j = idx
                while j < len(lines):
                    if j > idx:
                        balance += lines[j - 1].count("{") - lines[j - 1].count("}")
                    if balance <= 0 and j > idx:
                        break
                    candidate = lines[j - 1]
                    if mutable_re.search(candidate) and "{ get" not in candidate:
                        self._add(
                            "NLC003",
                            file_path,
                            j,
                            "Networking classes cannot hold mutable shared state; use actors.",
                            _line_snippet(candidate),
                        )
                    j += 1

    def _check_request_protocol(self) -> None:
        request_decl = re.compile(r"\bprotocol\s+Request\b[^{]*\{", re.MULTILINE)
        associated = re.compile(
            r"associatedtype\s+Response\s*:\s*Decodable", re.MULTILINE
        )
        found_request = False
        for file_path in self.swift_files:
            content = "\n".join(self._read_lines(file_path))
            if not request_decl.search(content):
                continue
            found_request = True
            if not associated.search(content):
                self._add(
                    "NLC004",
                    file_path,
                    1,
                    "`Request` protocol must include `associatedtype Response: Decodable`.",
                    "protocol Request missing typed Response associatedtype",
                )
        if not found_request:
            self._add(
                "NLC004",
                self.root / "PROJECT_ROOT",
                1,
                "Define `protocol Request` with `associatedtype Response: Decodable`.",
                "protocol Request missing",
            )

    def _check_urlsession_async_only(self) -> None:
        completion_api = re.compile(r"\b(dataTask|uploadTask|downloadTask)\s*\(")
        completion_handler = re.compile(r"completionHandler\s*:")
        callback_sig = re.compile(
            r"\(\s*(Data|Data\?)\s*,?\s*(URLResponse\??)\s*,?\s*(Error\??)\s*\)\s*->\s*Void"
        )

        for file_path, idx, line in self._all_lines():
            if completion_api.search(line):
                self._add(
                    "NLC005",
                    file_path,
                    idx,
                    "Completion-handler URLSession task APIs are forbidden.",
                    _line_snippet(line),
                )
            if "URLSession" in line and completion_handler.search(line):
                if "AuthChallengeDisposition" in line:
                    continue
                self._add(
                    "NLC005",
                    file_path,
                    idx,
                    "URLSession completion handlers are forbidden; use async/await.",
                    _line_snippet(line),
                )
            if callback_sig.search(line):
                self._add(
                    "NLC005",
                    file_path,
                    idx,
                    "Networking callback signatures are forbidden.",
                    _line_snippet(line),
                )

        for file_path in self._find_network_files():
            lines = self._read_lines(file_path)
            for idx, line in enumerate(lines, start=1):
                if not any(token in line for token in NETWORK_CALL_TOKENS):
                    continue
                prev = lines[idx - 2] if idx >= 2 else ""
                if (
                    "await " not in line
                    and " await" not in prev
                    and "await\n" not in prev
                ):
                    self._add(
                        "NLC006",
                        file_path,
                        idx,
                        "URLSession async APIs must be called with `await`.",
                        _line_snippet(line),
                    )

    def _check_retry_policy(self) -> None:
        corpus = "\n".join(
            "\n".join(self._read_lines(p)) for p in self._find_network_files()
        )
        if not corpus.strip():
            return

        checks = {
            "max_retries": re.search(
                r"(maxRetries|retryLimit)\s*=\s*3|for\s+\w+\s+in\s+0\.\.<\s*3",
                corpus,
            ),
            "exponential": re.search(
                r"(exponential|backoff|pow\s*\(\s*2|1\s*<<)",
                corpus,
                re.IGNORECASE,
            ),
            "network_error_gate": re.search(
                r"(URLError|networkError)",
                corpus,
            ),
            "server_5xx_gate": re.search(
                r"(500\s*\.\.<\s*600|statusCode\s*/\s*100\s*==\s*5|>=\s*500.*<\s*600)",
                corpus,
            ),
        }
        missing = [name for name, ok in checks.items() if not ok]
        if missing:
            self._add(
                "NLC007",
                self.root / "PROJECT_ROOT",
                1,
                "Retry policy must include exponential backoff, maxRetries=3, and retry gating for network/5xx errors.",
                f"missing retry elements: {', '.join(missing)}",
            )

    def _check_logging(self) -> None:
        logger_decl = re.compile(
            r"Logger\s*\(\s*subsystem:\s*[^,]+,\s*category:\s*[^)]+\)"
        )
        log_call = re.compile(r"\.\s*(debug|info|notice|error|fault)\s*\(")
        oslog_in_network = False
        logger_with_metadata = False

        for file_path in self._find_network_files():
            lines = self._read_lines(file_path)
            content = "\n".join(lines)
            if "import OSLog" in content:
                oslog_in_network = True
            if logger_decl.search(content):
                logger_with_metadata = True
            for idx, line in enumerate(lines, start=1):
                if "print(" in line or "debugPrint(" in line:
                    self._add(
                        "NLC009",
                        file_path,
                        idx,
                        "print/debugPrint logging is forbidden in networking code.",
                        _line_snippet(line),
                    )
                if log_call.search(line) and "#if DEBUG" not in content:
                    self._add(
                        "NLC008",
                        file_path,
                        idx,
                        "Networking logs must be gated with `#if DEBUG`.",
                        _line_snippet(line),
                    )

        for file_path, idx, line in self._all_lines():
            if "print(" in line or "debugPrint(" in line:
                self._add(
                    "NLC009",
                    file_path,
                    idx,
                    "print/debugPrint usage is forbidden project-wide.",
                    _line_snippet(line),
                )

        if not oslog_in_network or not logger_with_metadata:
            self._add(
                "NLC008",
                self.root / "PROJECT_ROOT",
                1,
                "Networking layer must use OSLog `Logger(subsystem:category:)` with DEBUG-only logging.",
                "missing OSLog import or subsystem/category logger declaration",
            )

    def _check_url_construction(self) -> None:
        enum_path_re = re.compile(r"^\s*enum\s+\w*(Path|Endpoint)\w*\b")
        has_path_enum = False

        for file_path in self.swift_files:
            lines = self._read_lines(file_path)
            for idx, line in enumerate(lines, start=1):
                if enum_path_re.search(line):
                    has_path_enum = True
                if RAW_URL_RE.search(line):
                    self._add(
                        "NLC010",
                        file_path,
                        idx,
                        "Raw URL strings are forbidden. Build URLs from enum paths.",
                        _line_snippet(line),
                    )
                if re.search(r'URL\s*\(\s*string:\s*"[^"]+"', line):
                    self._add(
                        "NLC010",
                        file_path,
                        idx,
                        "Direct URL(string:) literals are forbidden.",
                        _line_snippet(line),
                    )

        if not has_path_enum:
            self._add(
                "NLC010",
                self.root / "PROJECT_ROOT",
                1,
                "Define enum-driven API path construction (e.g. `enum APIPath`).",
                "path enum not found",
            )

    def _check_offline_upload_queue(self) -> None:
        corpus = "\n".join(
            "\n".join(self._read_lines(path)) for path in self.swift_files
        )
        has_queue_type = re.search(
            r"(actor|class|struct)\s+\w*(UploadQueue|OfflineUploadQueue)\b", corpus
        )
        has_json = "JSONEncoder" in corpus and "JSONDecoder" in corpus
        has_disk = "write(to:" in corpus or "Data(contentsOf:" in corpus
        if not (has_queue_type and has_json and has_disk):
            self._add(
                "NLC011",
                self.root / "PROJECT_ROOT",
                1,
                "Offline upload queue must persist queued jobs as JSON on disk.",
                "missing upload queue type and/or JSON disk persistence",
            )

    def _check_nwpathmonitor_retry(self) -> None:
        corpus = "\n".join(
            "\n".join(self._read_lines(path)) for path in self.swift_files
        )
        has_monitor = "NWPathMonitor" in corpus
        has_handler = "pathUpdateHandler" in corpus
        has_retry_trigger = re.search(r"pathUpdateHandler[\s\S]{0,300}retry", corpus)
        if not (has_monitor and has_handler and has_retry_trigger):
            self._add(
                "NLC012",
                self.root / "PROJECT_ROOT",
                1,
                "Use NWPathMonitor pathUpdateHandler to trigger upload retry on connectivity changes.",
                "missing NWPathMonitor connectivity-triggered retry wiring",
            )

    def _check_certificate_pinning(self) -> None:
        corpus = "\n".join(
            "\n".join(self._read_lines(path)) for path in self.swift_files
        )
        has_domain = "exhibita.dineshd.dev" in corpus
        has_delegate_type = re.search(r":\s*[^\n{]*URLSessionDelegate\b", corpus)
        has_challenge = re.search(
            r"urlSession\s*\([\s\S]{0,400}didReceive\s+challenge", corpus
        )
        has_trust_eval = (
            "SecTrust" in corpus
            or "SecCertificate" in corpus
            or "SecTrustEvaluateWithError" in corpus
        )
        if not (has_domain and has_delegate_type and has_challenge and has_trust_eval):
            self._add(
                "NLC013",
                self.root / "PROJECT_ROOT",
                1,
                "Implement URLSessionDelegate certificate pinning for exhibita.dineshd.dev.",
                "missing delegate pinning flow (domain/delegate/challenge/trust)",
            )

    def _check_timeout_rules(self) -> None:
        timeout_re = re.compile(
            r"(timeoutIntervalForRequest|timeoutInterval)\s*=\s*15(?:\.0)?\b"
        )
        has_timeout_policy = False
        for file_path, idx, line in self._all_lines():
            if timeout_re.search(line):
                has_timeout_policy = True

        for file_path in self._find_network_files():
            lines = self._read_lines(file_path)
            for idx, line in enumerate(lines, start=1):
                if "URLRequest(" not in line:
                    continue
                local_window = "\n".join(lines[idx - 1 : min(len(lines), idx + 8)])
                if timeout_re.search(local_window):
                    continue
                if not has_timeout_policy:
                    self._add(
                        "NLC014",
                        file_path,
                        idx,
                        "Every request must apply a 15-second timeout.",
                        _line_snippet(line),
                    )

        if not has_timeout_policy:
            self._add(
                "NLC014",
                self.root / "PROJECT_ROOT",
                1,
                "Set request timeout to 15 seconds on URLRequest or URLSessionConfiguration.",
                "15-second timeout policy missing",
            )

    def _check_api_error_model(self) -> None:
        required = {
            "networkError(URLError)": re.compile(
                r"case\s+networkError\s*\(\s*URLError\s*\)"
            ),
            "serverError(statusCode: Int, body: Data)": re.compile(
                r"case\s+serverError\s*\(\s*statusCode:\s*Int\s*,\s*body:\s*Data\s*\)"
            ),
            "decodingError(DecodingError)": re.compile(
                r"case\s+decodingError\s*\(\s*DecodingError\s*\)"
            ),
            "unauthorized": re.compile(r"case\s+unauthorized\b"),
            "notFound": re.compile(r"case\s+notFound\b"),
        }
        found = False
        for file_path in self.swift_files:
            content = "\n".join(self._read_lines(file_path))
            if "enum APIError" not in content:
                continue
            found = True
            missing = [
                name for name, pat in required.items() if not pat.search(content)
            ]
            if missing:
                self._add(
                    "NLC015",
                    file_path,
                    1,
                    "APIError must include all required exhaustive cases.",
                    f"missing APIError cases: {', '.join(missing)}",
                )
        if not found:
            self._add(
                "NLC015",
                self.root / "PROJECT_ROOT",
                1,
                "Define `enum APIError` with all required typed cases.",
                "APIError enum missing",
            )

    def _check_codable_strictness(self) -> None:
        for file_path, idx, line in self._all_lines():
            if "AnyCodable" in line:
                self._add(
                    "NLC016",
                    file_path,
                    idx,
                    "AnyCodable is forbidden; use strict typed Codable models.",
                    _line_snippet(line),
                )
            if re.search(r"\bDynamic\w*CodingKey\b", line):
                self._add(
                    "NLC016",
                    file_path,
                    idx,
                    "Dynamic coding keys are forbidden.",
                    _line_snippet(line),
                )
            if re.search(r"\[\s*String\s*:\s*Any\s*\]", line):
                self._add(
                    "NLC016",
                    file_path,
                    idx,
                    "Unstructured `[String: Any]` payloads are forbidden in networking models.",
                    _line_snippet(line),
                )
            if "JSONSerialization.jsonObject" in line:
                self._add(
                    "NLC016",
                    file_path,
                    idx,
                    "Dynamic JSONSerialization usage is forbidden for API models.",
                    _line_snippet(line),
                )

    def _check_silent_error_swallowing(self) -> None:
        for file_path in self.swift_files:
            lines = self._read_lines(file_path)
            for idx, line in enumerate(lines, start=1):
                if "try?" in line:
                    self._add(
                        "NLC017",
                        file_path,
                        idx,
                        "Silent `try?` error swallowing is forbidden.",
                        _line_snippet(line),
                    )
                if re.search(r"\bcatch\s*\{\s*\}", line):
                    self._add(
                        "NLC017",
                        file_path,
                        idx,
                        "Empty catch blocks are forbidden.",
                        _line_snippet(line),
                    )

                if re.search(r"\bcatch\s*\{", line):
                    start_idx = idx - 1
                    catch_part = line.split("catch", 1)[1]
                    balance = catch_part.count("{") - catch_part.count("}")
                    end_idx = start_idx
                    while end_idx + 1 < len(lines) and balance > 0:
                        end_idx += 1
                        balance += lines[end_idx].count("{") - lines[end_idx].count("}")
                    block_lines = lines[start_idx : end_idx + 1]
                    body = "\n".join(block_lines[1:-1]).strip()
                    if not body:
                        self._add(
                            "NLC017",
                            file_path,
                            idx,
                            "Catch blocks must not silently swallow errors.",
                            _line_snippet(line),
                        )
                    elif not re.search(
                        r"\b(throw|return|logger\.|os_log|assertionFailure|preconditionFailure|fatalError)\b",
                        body,
                    ):
                        self._add(
                            "NLC017",
                            file_path,
                            idx,
                            "Catch blocks must rethrow, return typed failure, or log explicitly.",
                            _line_snippet(line),
                        )

    def _check_network_return_contract(self) -> None:
        for file_path in self._find_network_files():
            lines = self._read_lines(file_path)
            for start, end, _name, decl in _extract_function_blocks(lines):
                block = "\n".join(lines[start - 1 : end])
                if not any(token in block for token in NETWORK_CALL_TOKENS):
                    continue
                if re.search(r"->\s*Result\s*<[^>]+,\s*APIError\s*>", decl):
                    continue
                if "throws(APIError)" in decl:
                    continue
                self._add(
                    "NLC018",
                    file_path,
                    start,
                    "Network functions must return `Result<T, APIError>` or `throws(APIError)`.",
                    _line_snippet(decl),
                )

    def _check_test_isolation(self) -> None:
        for file_path in self.swift_files:
            rel = _relative_path(self.root, file_path)
            lines = self._read_lines(file_path)
            content = "\n".join(lines)
            is_test_file = (
                "Tests/" in rel
                or rel.endswith("Tests.swift")
                or "import XCTest" in content
            )
            if not is_test_file:
                continue
            uses_urlsession = "URLSession.shared" in content or "URLSession(" in content
            has_mocking = "Mock" in content or "URLProtocol" in content
            if uses_urlsession and not has_mocking:
                self._add(
                    "NLC019",
                    file_path,
                    1,
                    "Tests using URLSession must use mocks/stubs and never real servers.",
                    "missing Mock/URLProtocol-based transport isolation",
                )
            for idx, line in enumerate(lines, start=1):
                if RAW_URL_RE.search(line) or "exhibita.dineshd.dev" in line:
                    self._add(
                        "NLC019",
                        file_path,
                        idx,
                        "Tests must not contain real-server URLs.",
                        _line_snippet(line),
                    )

    def run(self) -> None:
        if not self.swift_files:
            self._add(
                "NLC000",
                self.root / "PROJECT_ROOT",
                1,
                "No Swift source files were found under the target root.",
                "no *.swift files discovered",
            )
            return

        self._check_api_client_actor_and_mockability()
        self._check_networking_classes_mutable_state()
        self._check_request_protocol()
        self._check_urlsession_async_only()
        self._check_retry_policy()
        self._check_logging()
        self._check_url_construction()
        self._check_offline_upload_queue()
        self._check_nwpathmonitor_retry()
        self._check_certificate_pinning()
        self._check_timeout_rules()
        self._check_api_error_model()
        self._check_codable_strictness()
        self._check_silent_error_swallowing()
        self._check_network_return_contract()
        self._check_test_isolation()

        self.violations.sort(key=lambda v: (v.file, v.line, v.rule_id))

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
            "violations": [violation.as_dict() for violation in self.violations],
        }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Swift code against Exhibit A networking contract."
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
        f"(files={summary['files_scanned']}, rules={summary['rules_checked']}, "
        f"violations={summary['violations']})"
    )
    for item in result["violations"]:
        print(
            f"{item['rule_id']} {item['file']}:{item['line']} "
            f"{item['rejection']} :: {item['snippet']}"
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
