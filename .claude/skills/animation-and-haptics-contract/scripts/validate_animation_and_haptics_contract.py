#!/usr/bin/env python3
"""Validate Exhibit A animation and haptics contract."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypedDict

CONTRACT_NAME = "animation-and-haptics-contract"

RULE_TITLES = {
    "AHC000": "Swift source files must exist",
    "AHC001": "Animation.default usage is forbidden",
    "AHC002": "Implicit .animation modifier usage is forbidden",
    "AHC003": "withAnimation must use approved curve families only",
    "AHC004": "Spring animations must specify duration and bounce",
    "AHC005": "Ease animations must specify duration",
    "AHC006": "Canonical motion constants must exist with exact values",
    "AHC007": "Page curl must use UIPageViewController with .pageCurl",
    "AHC008": "Page curl flow must target 60fps rendering",
    "AHC009": "Signature placement must use spring(duration:0.5,bounce:0.15)",
    "AHC010": "Signature placement must scale from 0.95 to 1.0",
    "AHC011": "Screen transitions must use easeOut(duration:0.35)",
    "AHC012": "Screen transitions must be fade-only",
    "AHC013": "Unread badge pulse must use repeating easeInOut(duration:1.0)",
    "AHC014": "Unread badge pulse must animate opacity 0.4 to 1.0",
    "AHC015": "Reduced motion must wire accessibilityReduceMotion environment value",
    "AHC016": "Animated files must branch on reduced motion",
    "AHC017": "Reduced motion branch must include instant fallback behavior",
    "AHC018": "Haptic event definitions must include required UX events",
    "AHC019": "Signature placed event must map to medium impact haptic",
    "AHC020": "Page curl complete event must map to light impact haptic",
    "AHC021": "First-time unlock event must map to success notification haptic",
    "AHC022": "Haptics must not be delayed relative to visual state changes",
    "AHC023": "Haptic generator usage must flow through event mapping",
    "AHC024": "UI sounds must be toggleable through UserDefaults",
    "AHC025": "UI sounds must use AVAudioPlayer with prepareToPlay",
    "AHC026": "SystemSoundID APIs are forbidden",
    "AHC027": "Motion and haptics must avoid blocking calls",
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

ANIMATION_FILE_HINT = re.compile(
    r"(withAnimation|\.transition\(|\.spring\(|\.easeOut\(|\.easeInOut\()", re.MULTILINE
)
HAPTIC_FILE_HINT = re.compile(
    r"(UIImpactFeedbackGenerator|UINotificationFeedbackGenerator|HapticEvent)"
)
AUDIO_FILE_HINT = re.compile(
    r"(AVAudioPlayer|UserDefaults|SystemSoundID|AudioServices)"
)

FORBIDDEN_TRANSITIONS = re.compile(
    r"\.transition\s*\(\s*\.(?:slide|move|offset|scale|push|asymmetric|modifier)\b"
)
FORBIDDEN_SYSTEM_SOUND = re.compile(
    r"\b(SystemSoundID|AudioServicesPlaySystemSound|AudioServicesCreateSystemSoundID)\b"
)
BLOCKING_CALLS = re.compile(
    r"\b(Thread\.sleep|sleep\s*\(|usleep\s*\(|Task\.sleep\s*\()"
)
DELAY_CALLS = re.compile(r"\b(asyncAfter|Task\.sleep\s*\(|sleep\s*\(|usleep\s*\()")


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


def _line_snippet(line: str) -> str:
    return line.strip()[:220]


def _is_ignored(path: Path) -> bool:
    return any(part in IGNORED_DIRS for part in path.parts)


class ContractValidator:
    """Deterministic validator for Exhibit A motion and haptics requirements."""

    def __init__(self, root: Path):
        self.root = root.resolve()
        self.swift_files = self._collect_swift_files()
        self.cache: dict[Path, list[str]] = {}
        self.violations: list[Violation] = []
        self.files_scanned = len(self.swift_files)
        self.rule_count = len(RULE_TITLES)

    def _collect_swift_files(self) -> list[Path]:
        files: list[Path] = []
        for path in self.root.rglob("*.swift"):
            if _is_ignored(path):
                continue
            files.append(path)
        return sorted(files)

    def _read_lines(self, path: Path) -> list[str]:
        if path not in self.cache:
            self.cache[path] = path.read_text(
                encoding="utf-8", errors="ignore"
            ).splitlines()
        return self.cache[path]

    def _joined_text(self, files: list[Path] | None = None) -> str:
        targets = files if files is not None else self.swift_files
        return "\n".join("\n".join(self._read_lines(path)) for path in targets)

    def _all_rows(self, files: list[Path] | None = None) -> list[tuple[Path, int, str]]:
        targets = files if files is not None else self.swift_files
        rows: list[tuple[Path, int, str]] = []
        for file_path in targets:
            for idx, line in enumerate(self._read_lines(file_path), start=1):
                rows.append((file_path, idx, line))
        return rows

    def _add(
        self, rule_id: str, file_path: Path, line_no: int, message: str, snippet: str
    ) -> None:
        self.violations.append(
            Violation(
                rule_id=rule_id,
                title=RULE_TITLES[rule_id],
                rejection=f"REJECT: {message}",
                file=_relative_path(self.root, file_path),
                line=max(1, line_no),
                snippet=snippet,
            )
        )

    def _add_missing(self, rule_id: str, message: str, snippet: str) -> None:
        self._add(rule_id, self.root / "PROJECT_ROOT", 1, message, snippet)

    def _first_line_match(
        self,
        pattern: re.Pattern[str],
        files: list[Path] | None = None,
    ) -> tuple[Path, int, str] | None:
        for path, line_no, line in self._all_rows(files):
            if pattern.search(line):
                return (path, line_no, line)
        return None

    def _animation_files(self) -> list[Path]:
        files: list[Path] = []
        for path in self.swift_files:
            text = "\n".join(self._read_lines(path))
            if ANIMATION_FILE_HINT.search(text):
                files.append(path)
        return files

    def _haptic_files(self) -> list[Path]:
        files: list[Path] = []
        for path in self.swift_files:
            text = "\n".join(self._read_lines(path))
            if HAPTIC_FILE_HINT.search(text):
                files.append(path)
        return files

    def _audio_files(self) -> list[Path]:
        files: list[Path] = []
        for path in self.swift_files:
            text = "\n".join(self._read_lines(path))
            if AUDIO_FILE_HINT.search(text):
                files.append(path)
        return files

    def _check_core_presence(self) -> None:
        if not self.swift_files:
            self._add_missing(
                "AHC000",
                "Project must include Swift source files for contract inspection.",
                "no .swift files found",
            )

    def _check_animation_api_discipline(self) -> None:
        default_pattern = re.compile(
            r"\bAnimation\.default\b|\.animation\s*\(\s*\.default\b|withAnimation\s*\(\s*\.default\b"
        )
        for path, line_no, line in self._all_rows():
            if default_pattern.search(line):
                self._add(
                    "AHC001",
                    path,
                    line_no,
                    "Animation.default is prohibited; use explicit spring/ease parameters from contract constants.",
                    _line_snippet(line),
                )

            if re.search(r"\.animation\s*\(", line):
                self._add(
                    "AHC002",
                    path,
                    line_no,
                    "Implicit .animation(...) modifier is forbidden; use explicit withAnimation(...) calls.",
                    _line_snippet(line),
                )

        allowed_curve = re.compile(
            r"withAnimation\s*\(\s*\.(spring|easeOut|easeInOut)\s*\("
        )
        spring_call = re.compile(r"(?:Animation\.)?spring\s*\(")
        ease_call = re.compile(r"(?:Animation\.)?(easeOut|easeInOut)\s*\(")
        with_animation = re.compile(r"withAnimation\s*\(")

        for path in self.swift_files:
            lines = self._read_lines(path)
            for idx, line in enumerate(lines, start=1):
                if "withAnimation" not in line:
                    continue
                window = " ".join(lines[max(0, idx - 1) : min(len(lines), idx + 3)])
                if with_animation.search(window) and not allowed_curve.search(window):
                    self._add(
                        "AHC003",
                        path,
                        idx,
                        "withAnimation(...) must use .spring(duration:bounce:), .easeOut(duration:), or .easeInOut(duration:).",
                        _line_snippet(line),
                    )

                if spring_call.search(window):
                    if "duration:" not in window or "bounce:" not in window:
                        self._add(
                            "AHC004",
                            path,
                            idx,
                            "Spring animation must explicitly set duration and bounce.",
                            _line_snippet(line),
                        )

                if ease_call.search(window) and "duration:" not in window:
                    self._add(
                        "AHC005",
                        path,
                        idx,
                        "Ease animation must explicitly set duration.",
                        _line_snippet(line),
                    )

        for path, line_no, line in self._all_rows():
            if re.search(r"(?:Animation\.)?spring\s*\(", line):
                window = " ".join(
                    self._read_lines(path)[
                        max(0, line_no - 1) : min(
                            len(self._read_lines(path)), line_no + 2
                        )
                    ]
                )
                if "duration:" not in window or "bounce:" not in window:
                    self._add(
                        "AHC004",
                        path,
                        line_no,
                        "Spring definitions must not rely on defaults; provide duration and bounce.",
                        _line_snippet(line),
                    )

            if re.search(r"(?:Animation\.)?ease(Out|InOut)\s*\(", line):
                window = " ".join(
                    self._read_lines(path)[
                        max(0, line_no - 1) : min(
                            len(self._read_lines(path)), line_no + 2
                        )
                    ]
                )
                if "duration:" not in window:
                    self._add(
                        "AHC005",
                        path,
                        line_no,
                        "Ease animation definitions must not rely on defaults; provide duration.",
                        _line_snippet(line),
                    )

        combined = self._joined_text()
        required_constants = {
            "signaturePlacementSpring": r"\b(?:static\s+)?let\s+signaturePlacementSpring\s*=\s*(?:Animation\.)?spring\(\s*duration:\s*0?\.5\s*,\s*bounce:\s*0?\.15",
            "screenTransitionEaseOut": r"\b(?:static\s+)?let\s+screenTransitionEaseOut\s*=\s*(?:Animation\.)?easeOut\(\s*duration:\s*0?\.35",
            "unreadBadgePulseEaseInOut": r"\b(?:static\s+)?let\s+unreadBadgePulseEaseInOut\s*=\s*(?:Animation\.)?easeInOut\(\s*duration:\s*1(?:\.0)?",
        }
        missing_names = [
            name
            for name, pattern in required_constants.items()
            if not re.search(pattern, combined)
        ]
        if missing_names:
            self._add_missing(
                "AHC006",
                "Canonical motion constants are missing or parameterized incorrectly.",
                f"missing constants: {', '.join(missing_names)}",
            )

    def _check_page_curl_and_signature_motion(self) -> None:
        combined = self._joined_text()
        page_curl_pattern = re.compile(
            r"UIPageViewController\s*\([\s\S]*?transitionStyle:\s*\.pageCurl",
            re.MULTILINE,
        )
        has_page_curl = bool(re.search(r"\.pageCurl\b", combined))

        if not has_page_curl or not page_curl_pattern.search(combined):
            self._add_missing(
                "AHC007",
                "Page curl transitions must use UIPageViewController with transitionStyle: .pageCurl.",
                "missing UIPageViewController(... transitionStyle: .pageCurl ...)",
            )

        has_60fps_target = bool(
            re.search(r"preferredFramesPerSecond\s*=\s*60\b", combined)
            or re.search(
                r"(preferredFrameRateRange|CAFrameRateRange)\s*=\s*CAFrameRateRange\s*\(\s*minimum:\s*60(?:\.0)?",
                combined,
            )
            or re.search(r"CAFrameRateRange\s*\(\s*minimum:\s*60(?:\.0)?", combined)
        )
        if not has_60fps_target:
            self._add_missing(
                "AHC008",
                "Page curl flow must explicitly target 60fps rendering.",
                "missing preferredFramesPerSecond = 60 or CAFrameRateRange(minimum: 60)",
            )

        signature_spring = re.search(
            r"(?:Animation\.)?spring\(\s*duration:\s*0?\.5\s*,\s*bounce:\s*0?\.15",
            combined,
        )
        if not signature_spring:
            self._add_missing(
                "AHC009",
                "Signature placement must use spring(duration: 0.5, bounce: 0.15).",
                "missing spring(duration: 0.5, bounce: 0.15)",
            )

        signature_scale = re.search(
            r"scaleEffect\s*\([^)]*(0\.95)[^)]*(1(?:\.0)?)[^)]*\)|scaleEffect\s*\([^)]*(1(?:\.0)?)[^)]*(0\.95)[^)]*\)",
            combined,
        )
        if not signature_scale:
            self._add_missing(
                "AHC010",
                "Signature placement animation must scale between 0.95 and 1.0.",
                "missing scaleEffect(... 0.95 ... 1.0 ...)",
            )

    def _check_transitions_and_badges(self) -> None:
        combined = self._joined_text()

        if not re.search(r"(?:Animation\.)?easeOut\(\s*duration:\s*0?\.35", combined):
            self._add_missing(
                "AHC011",
                "Screen transitions must use easeOut(duration: 0.35).",
                "missing easeOut(duration: 0.35)",
            )

        if not re.search(r"\.transition\s*\(\s*\.opacity\b", combined):
            self._add_missing(
                "AHC012",
                "Screen transitions must be fade-based using .transition(.opacity).",
                "missing .transition(.opacity)",
            )

        for path, line_no, line in self._all_rows():
            if FORBIDDEN_TRANSITIONS.search(line):
                self._add(
                    "AHC012",
                    path,
                    line_no,
                    "Non-fade transition detected; only opacity transitions are allowed for screens.",
                    _line_snippet(line),
                )

        if not re.search(
            r"(?:Animation\.)?easeInOut\(\s*duration:\s*1(?:\.0)?\s*\)[\s\S]{0,120}\.repeatForever",
            combined,
        ):
            self._add_missing(
                "AHC013",
                "Unread badge pulse must use repeating easeInOut(duration: 1.0).",
                "missing easeInOut(duration: 1.0).repeatForever(...)",
            )

        has_pulse_opacity = bool(
            re.search(
                r"opacity\s*\([^)]*(0\.4)[^)]*(1(?:\.0)?)[^)]*\)|opacity\s*\([^)]*(1(?:\.0)?)[^)]*(0\.4)[^)]*\)",
                combined,
            )
        )
        if not has_pulse_opacity:
            self._add_missing(
                "AHC014",
                "Unread badge pulse must animate opacity from 0.4 to 1.0.",
                "missing opacity(... 0.4 ... 1.0 ...)",
            )

    def _has_reduced_motion_fallback(self, lines: list[str]) -> bool:
        reduce_if = re.compile(r"if\s+.*reduceMotion")
        for idx, line in enumerate(lines):
            if not reduce_if.search(line):
                continue
            window = lines[idx : min(len(lines), idx + 20)]
            block = "\n".join(window)
            if "else" not in block:
                continue
            # Fallback branch must not animate and must include a direct state update.
            pre_else = block.split("else", 1)[0]
            if "withAnimation" in pre_else:
                continue
            if not re.search(r"\w+\s*=", pre_else):
                continue
            if "withAnimation" not in block:
                continue
            return True
        return False

    def _check_accessibility(self) -> None:
        combined = self._joined_text()
        if not re.search(
            r"@Environment\s*\(\s*\\\.accessibilityReduceMotion\s*\)", combined
        ):
            self._add_missing(
                "AHC015",
                "Global reduced-motion support must wire @Environment(\\.accessibilityReduceMotion).",
                "missing @Environment(\\.accessibilityReduceMotion)",
            )

        animated_files = self._animation_files()
        for path in animated_files:
            lines = self._read_lines(path)
            text = "\n".join(lines)
            if "reduceMotion" not in text:
                marker = self._first_line_match(
                    re.compile(r"(withAnimation|\.transition\()"), [path]
                )
                line_no = marker[1] if marker else 1
                snippet = marker[2] if marker else "missing reduced-motion branch"
                self._add(
                    "AHC016",
                    path,
                    line_no,
                    "Animated file must branch on reduced-motion state before running animations.",
                    _line_snippet(snippet),
                )
                continue

            if not self._has_reduced_motion_fallback(lines):
                marker = self._first_line_match(re.compile(r"reduceMotion"), [path])
                line_no = marker[1] if marker else 1
                snippet = (
                    marker[2] if marker else "invalid reduced-motion fallback structure"
                )
                self._add(
                    "AHC017",
                    path,
                    line_no,
                    "Reduced-motion branch must provide instant fallback and move animation to else branch.",
                    _line_snippet(snippet),
                )

    def _check_haptics(self) -> None:
        combined = self._joined_text()

        has_haptic_enum = bool(re.search(r"enum\s+\w*HapticEvent\b", combined))
        has_sig_event = bool(re.search(r"\bcase\b[^\n]*signaturePlaced", combined))
        has_page_event = bool(re.search(r"\bcase\b[^\n]*pageCurlComplete", combined))
        has_unlock_event = bool(
            re.search(r"\bcase\b[^\n]*contentUnlockedFirstTime", combined)
        )

        if not (
            has_haptic_enum and has_sig_event and has_page_event and has_unlock_event
        ):
            self._add_missing(
                "AHC018",
                "Haptic event mapping must define signaturePlaced, pageCurlComplete, and contentUnlockedFirstTime.",
                "missing enum HapticEvent cases",
            )

        if not re.search(
            r"case\s+\.signaturePlaced[\s\S]{0,260}UIImpactFeedbackGenerator\s*\(\s*style:\s*\.medium\s*\)",
            combined,
        ):
            self._add_missing(
                "AHC019",
                "signaturePlaced must map to UIImpactFeedbackGenerator(style: .medium).",
                "missing case .signaturePlaced -> UIImpactFeedbackGenerator(style: .medium)",
            )

        if not re.search(
            r"case\s+\.pageCurlComplete[\s\S]{0,260}UIImpactFeedbackGenerator\s*\(\s*style:\s*\.light\s*\)",
            combined,
        ):
            self._add_missing(
                "AHC020",
                "pageCurlComplete must map to UIImpactFeedbackGenerator(style: .light).",
                "missing case .pageCurlComplete -> UIImpactFeedbackGenerator(style: .light)",
            )

        if not re.search(
            r"case\s+\.contentUnlockedFirstTime[\s\S]{0,320}UINotificationFeedbackGenerator\s*\(\s*\)[\s\S]{0,120}notificationOccurred\s*\(\s*\.success\s*\)",
            combined,
        ):
            self._add_missing(
                "AHC021",
                "contentUnlockedFirstTime must map to success notification haptic.",
                "missing case .contentUnlockedFirstTime -> notificationOccurred(.success)",
            )

        haptic_files = self._haptic_files()
        for path, line_no, line in self._all_rows(haptic_files):
            if DELAY_CALLS.search(line):
                self._add(
                    "AHC022",
                    path,
                    line_no,
                    "Haptics must be emitted without delayed scheduling relative to visual state change.",
                    _line_snippet(line),
                )

        has_event_dispatch = bool(
            re.search(r"func\s+\w*haptic\w*\s*\(\s*for\s+\w*HapticEvent", combined)
            or re.search(
                r"switch\s+\w+\s*\{[\s\S]{0,500}case\s+\.signaturePlaced", combined
            )
        )
        if not has_event_dispatch and re.search(
            r"(UIImpactFeedbackGenerator|UINotificationFeedbackGenerator)", combined
        ):
            self._add_missing(
                "AHC023",
                "Direct haptic generator usage is forbidden; route through event mapping API.",
                "missing triggerHaptic(for: HapticEvent) style mapping",
            )

    def _check_audio(self) -> None:
        combined = self._joined_text()
        if not re.search(
            r"UserDefaults[\s\S]{0,120}(sound|audio)", combined, re.IGNORECASE
        ):
            self._add_missing(
                "AHC024",
                "UI sound playback must be toggleable via a UserDefaults-backed setting.",
                "missing UserDefaults sound toggle",
            )

        if "AVAudioPlayer" not in combined or "prepareToPlay()" not in combined:
            self._add_missing(
                "AHC025",
                "UI sounds must use AVAudioPlayer and preload buffers with prepareToPlay().",
                "missing AVAudioPlayer and/or prepareToPlay()",
            )

        for path, line_no, line in self._all_rows(
            self._audio_files() or self.swift_files
        ):
            if FORBIDDEN_SYSTEM_SOUND.search(line):
                self._add(
                    "AHC026",
                    path,
                    line_no,
                    "SystemSoundID APIs are forbidden for Exhibit A UI sound effects.",
                    _line_snippet(line),
                )

    def _check_responsiveness(self) -> None:
        relevant_files = set(self._animation_files() + self._haptic_files())
        targets = sorted(relevant_files) if relevant_files else self.swift_files
        for path, line_no, line in self._all_rows(targets):
            if BLOCKING_CALLS.search(line):
                self._add(
                    "AHC027",
                    path,
                    line_no,
                    "Motion and haptics must not block interaction responsiveness.",
                    _line_snippet(line),
                )

    def validate(self) -> ResultOutput:
        self._check_core_presence()
        if self.swift_files:
            self._check_animation_api_discipline()
            self._check_page_curl_and_signature_motion()
            self._check_transitions_and_badges()
            self._check_accessibility()
            self._check_haptics()
            self._check_audio()
            self._check_responsiveness()

        ordered = sorted(
            self.violations,
            key=lambda v: (v.rule_id, v.file, v.line, v.snippet),
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
            "violations": [violation.as_dict() for violation in ordered],
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
    for violation in result["violations"]:
        print(
            f"{violation['rule_id']} {violation['file']}:{violation['line']} "
            f"{violation['rejection']} | {violation['snippet']}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Exhibit A animation and haptics contract.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(),
        help="Project root to scan (default: current directory).",
    )
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Output format.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    validator = ContractValidator(args.root)
    result = validator.validate()

    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        _print_text(result)

    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
