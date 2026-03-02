#!/usr/bin/env python3
"""Validate Exhibit A iOS accessibility contract."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypedDict

CONTRACT_NAME = "accessibility-contract"

RULE_TITLES = {
    "ACC000": "Swift source files must exist",
    "ACC001": "Project must explicitly declare WCAG 2.2 AA baseline",
    "ACC002": "Interactive elements must provide 44x44pt minimum targets",
    "ACC003": "Interactive elements must provide VoiceOver labels",
    "ACC004": "Interactive elements must provide VoiceOver hints",
    "ACC005": "Every image must provide accessibilityLabel or accessibilityHidden",
    "ACC006": "Custom components must expose accessibility metadata",
    "ACC007": "Signature state announcements must use full contextual phrases",
    "ACC008": "Page curl must provide VoiceOver alternative navigation",
    "ACC009": "Rotor or gesture-based accessibility navigation must exist",
    "ACC010": "Text must use semantic font styles; fixed-size fonts are forbidden",
    "ACC011": "Pagination must reflow at large Dynamic Type sizes",
    "ACC012": "Contrast architecture must enforce 4.5:1 and 3:1 with custom palette validation",
    "ACC013": "Decorative UI elements must be accessibilityHidden(true)",
    "ACC014": "Focus must move to confirmation after signature placement",
    "ACC015": "Signature blocks must combine child accessibility elements",
    "ACC016": "UI tests must execute performA11yAudit()",
    "ACC017": "Dynamic content must announce updates through UIAccessibility.post(.announcement)",
    "ACC018": "Completion states require VoiceOver verification evidence",
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

INTERACTIVE_PATTERN = re.compile(
    r"\b(Button|NavigationLink|Toggle|Stepper|Slider|TextField|SecureField|Link|Menu|Picker|DatePicker)\s*\(|\.onTapGesture\s*\(|\bUIButton\s*\(|\bUIControl\b"
)
IMAGE_PATTERN = re.compile(r"\bImage\s*\(|\bUIImageView\s*\(")
DECORATIVE_PATTERN = re.compile(
    r"^\s*(Circle|Rectangle|RoundedRectangle|Capsule|Ellipse|Divider|LinearGradient|RadialGradient|AngularGradient)\s*\("
)
CUSTOM_COMPONENT_PATTERN = re.compile(
    r"\b(UIViewRepresentable|UIViewControllerRepresentable)\b|\bclass\s+\w+\s*:\s*(UIView|UIControl|UIViewController)\b"
)

LABEL_PATTERN = re.compile(r"\.accessibilityLabel\s*\(|\baccessibilityLabel\s*=")
HINT_PATTERN = re.compile(r"\.accessibilityHint\s*\(|\baccessibilityHint\s*=")
HIDDEN_PATTERN = re.compile(
    r"\.accessibilityHidden\s*\(\s*true\s*\)|\bisAccessibilityElement\s*=\s*false\b"
)
METADATA_PATTERN = re.compile(
    r"\.accessibility(Label|Hint|Value|Traits|Identifier|Element)\s*\(|\baccessibility(Label|Hint|Value|Traits|Identifier)\s*=|\bisAccessibilityElement\b"
)

TOUCH_TARGET_WIDTH_PATTERN = re.compile(
    r"frame\s*\([^)]*(minWidth|width)\s*:\s*(44(?:\.0+)?|[4-9][5-9](?:\.0+)?|[5-9]\d(?:\.\d+)?)"
)
TOUCH_TARGET_HEIGHT_PATTERN = re.compile(
    r"frame\s*\([^)]*(minHeight|height)\s*:\s*(44(?:\.0+)?|[4-9][5-9](?:\.0+)?|[5-9]\d(?:\.\d+)?)"
)
TOUCH_TARGET_UKIT_PATTERN = re.compile(
    r"(heightAnchor|widthAnchor)\.constraint\s*\(\s*(greaterThanOrEqualToConstant|equalToConstant)\s*:\s*(44(?:\.0+)?)"
)

FIXED_FONT_PATTERN = re.compile(
    r"\.font\s*\(\s*\.system\s*\(\s*size\s*:|UIFont\.systemFont\s*\(\s*ofSize\s*:|UIFont\s*\(\s*name\s*:\s*[^,]+,\s*size\s*:"
)
SEMANTIC_FONT_PATTERN = re.compile(
    r"\.font\s*\(\s*\.(largeTitle|title|title2|title3|headline|subheadline|body|callout|footnote|caption|caption2)\b|UIFont\.preferredFont\s*\(\s*forTextStyle\s*:"
)

PAGINATION_HINT_PATTERN = re.compile(
    r"\b(pagination|paginate|pageIndex|currentPage|pageNumber|loadNextPage|loadPreviousPage|pageCurl)\b",
    re.IGNORECASE,
)
DYNAMIC_TYPE_PATTERN = re.compile(r"dynamicTypeSize|sizeCategory|isAccessibilitySize")
REFLOW_PATTERN = re.compile(
    r"isAccessibilitySize|>=\s*\.accessibility|if\s+.*dynamicTypeSize|switch\s+.*dynamicTypeSize"
)

PAGE_CURL_PATTERN = re.compile(
    r"pageCurl|UIPageViewController\s*\([^)]*transitionStyle\s*:\s*\.pageCurl"
)
ALTERNATIVE_NAV_PATTERN = re.compile(
    r"accessibilityAction\s*\(|UIAccessibilityCustomAction|accessibilityCustomActions|\"Next Page\"|\"Previous Page\"|nextPage|previousPage"
)
ROTOR_PATTERN = re.compile(
    r"accessibilityRotor\s*\(|UIAccessibilityCustomRotor|accessibilityAdjustableAction\s*\("
)

SIGNATURE_HINT_PATTERN = re.compile(r"signature", re.IGNORECASE)
ANNOUNCEMENT_CALL_PATTERN = re.compile(
    r"UIAccessibility\.post\s*\(\s*notification\s*:\s*\.announcement\s*,\s*argument\s*:\s*(.+?)\)",
    re.DOTALL,
)
LAYOUT_FOCUS_PATTERN = re.compile(
    r"UIAccessibility\.post\s*\(\s*notification\s*:\s*\.(layoutChanged|screenChanged)\s*,\s*argument\s*:\s*[^\n]*confirm",
    re.IGNORECASE,
)
FOCUS_STATE_PATTERN = re.compile(
    r"@AccessibilityFocusState|\.accessibilityFocused\s*\("
)
COMBINE_PATTERN = re.compile(
    r"\.accessibilityElement\s*\(\s*children\s*:\s*\.combine\s*\)"
)

CONTRAST_WORD_PATTERN = re.compile(r"contrast", re.IGNORECASE)
CUSTOM_PALETTE_PATTERN = re.compile(r"Color\s*\(\s*\"|UIColor\s*\(\s*named\s*:")
CONTRAST_VALIDATION_PATTERN = re.compile(
    r"contrastRatio|validateContrast|validatePaletteContrast|performContrastAudit|wcagContrast",
    re.IGNORECASE,
)

DYNAMIC_CONTENT_PATTERN = re.compile(
    r"\b(append|insert|remove|delete|loadMore|reload|refresh|update|signaturePlaced|signatureCleared)\b",
    re.IGNORECASE,
)

COMPLETION_PATTERN = re.compile(
    r"\b(isComplete\s*=\s*true|completed\s*=\s*true|status\s*=\s*\.complete|mark(?:As)?Complete\s*\()"
)
VOICEOVER_VERIFICATION_PATTERN = re.compile(
    r"VoiceOver|voiceOverVerified|verifyVoiceOver|voiceover verification", re.IGNORECASE
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


def _line_snippet(line: str) -> str:
    return line.strip()[:220]


def _is_ignored(path: Path) -> bool:
    return any(part in IGNORED_DIRS for part in path.parts)


def _is_comment(line: str) -> bool:
    stripped = line.strip()
    return (
        stripped.startswith("//")
        or stripped.startswith("/*")
        or stripped.startswith("*")
    )


class ContractValidator:
    """Deterministic validator for Exhibit A accessibility requirements."""

    def __init__(self, root: Path):
        self.root = root.resolve()
        self.swift_files = self._collect_swift_files()
        self.cache: dict[Path, list[str]] = {}
        self.violations: list[Violation] = []
        self.violation_index: set[tuple[str, str, int]] = set()
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

    def _window_text(
        self, path: Path, line_no: int, before: int = 2, after: int = 18
    ) -> str:
        lines = self._read_lines(path)
        start = max(0, line_no - 1 - before)
        end = min(len(lines), line_no - 1 + after)
        return "\n".join(lines[start:end])

    def _first_line(
        self, path: Path, pattern: re.Pattern[str]
    ) -> tuple[int, str] | None:
        for idx, line in enumerate(self._read_lines(path), start=1):
            if pattern.search(line):
                return (idx, line)
        return None

    def _add(
        self,
        rule_id: str,
        file_path: Path,
        line_no: int,
        message: str,
        snippet: str,
    ) -> None:
        rel = _relative_path(self.root, file_path)
        key = (rule_id, rel, max(1, line_no))
        if key in self.violation_index:
            return
        self.violation_index.add(key)
        self.violations.append(
            Violation(
                rule_id=rule_id,
                title=RULE_TITLES[rule_id],
                rejection=f"REJECT: {message}",
                file=rel,
                line=max(1, line_no),
                snippet=snippet,
            )
        )

    def _add_missing(self, rule_id: str, message: str, snippet: str) -> None:
        self._add(rule_id, self.root / "PROJECT_ROOT", 1, message, snippet)

    def _interactive_rows(self) -> list[tuple[Path, int, str]]:
        rows: list[tuple[Path, int, str]] = []
        for path, line_no, line in self._all_rows():
            if _is_comment(line):
                continue
            if INTERACTIVE_PATTERN.search(line):
                rows.append((path, line_no, line))
        return rows

    def _check_wcag_baseline(self, all_text: str) -> None:
        if "WCAG" not in all_text or "2.2" not in all_text or "AA" not in all_text:
            self._add_missing(
                "ACC001",
                "Project must explicitly encode WCAG 2.2 AA as the minimum accessibility baseline.",
                "missing WCAG 2.2 AA declaration",
            )

    def _check_touch_targets_and_interactive_semantics(self) -> None:
        interactive_rows = self._interactive_rows()
        if not interactive_rows:
            return

        for path, line_no, line in interactive_rows:
            window = self._window_text(path, line_no)

            has_label = bool(LABEL_PATTERN.search(window))
            has_hint = bool(HINT_PATTERN.search(window))
            has_touch_target = bool(
                (
                    TOUCH_TARGET_WIDTH_PATTERN.search(window)
                    and TOUCH_TARGET_HEIGHT_PATTERN.search(window)
                )
                or TOUCH_TARGET_UKIT_PATTERN.search(window)
            )

            if not has_touch_target:
                self._add(
                    "ACC002",
                    path,
                    line_no,
                    "Interactive element must enforce at least a 44x44pt target size.",
                    _line_snippet(line),
                )

            if not has_label:
                self._add(
                    "ACC003",
                    path,
                    line_no,
                    "Interactive element is missing a VoiceOver label.",
                    _line_snippet(line),
                )

            if not has_hint:
                self._add(
                    "ACC004",
                    path,
                    line_no,
                    "Interactive element is missing a VoiceOver hint.",
                    _line_snippet(line),
                )

    def _check_images(self) -> None:
        for path, line_no, line in self._all_rows():
            if _is_comment(line):
                continue
            if not IMAGE_PATTERN.search(line):
                continue

            window = self._window_text(path, line_no, before=1, after=12)
            if "Image(decorative:" in line:
                # Decorative images are still required to be explicitly hidden later.
                continue

            if not (LABEL_PATTERN.search(window) or HIDDEN_PATTERN.search(window)):
                self._add(
                    "ACC005",
                    path,
                    line_no,
                    "Image must include .accessibilityLabel(...) or .accessibilityHidden(true).",
                    _line_snippet(line),
                )

    def _check_custom_components(self) -> None:
        for path in self.swift_files:
            text = "\n".join(self._read_lines(path))
            if not CUSTOM_COMPONENT_PATTERN.search(text):
                continue

            if not METADATA_PATTERN.search(text):
                self._add(
                    "ACC006",
                    path,
                    1,
                    "Custom UIKit/bridged components must expose accessibility metadata (label, hint, traits, or isAccessibilityElement).",
                    "missing accessibility metadata in custom component",
                )

    def _signature_files(self) -> list[Path]:
        files: list[Path] = []
        for path in self.swift_files:
            rel = _relative_path(self.root, path)
            text = "\n".join(self._read_lines(path))
            if SIGNATURE_HINT_PATTERN.search(rel) or SIGNATURE_HINT_PATTERN.search(
                text
            ):
                files.append(path)
        return files

    def _check_signature_contract(self, signature_files: list[Path]) -> None:
        if not signature_files:
            return

        signature_text = self._joined_text(signature_files)

        contextual_phrase_found = False
        for match in ANNOUNCEMENT_CALL_PATTERN.finditer(signature_text):
            argument = match.group(1)
            literal_match = re.search(r'"([^"]+)"', argument)
            if literal_match:
                phrase = literal_match.group(1).strip()
                words = [word for word in re.split(r"\s+", phrase) if word]
                has_state = bool(
                    re.search(
                        r"placed|cleared|removed|updated|saved|completed",
                        phrase,
                        re.IGNORECASE,
                    )
                )
                if len(words) >= 4 and "signature" in phrase.lower() and has_state:
                    contextual_phrase_found = True
                    break

        if not contextual_phrase_found:
            self._add_missing(
                "ACC007",
                "Signature flows must announce state changes with full contextual phrases (for example: 'Signature placed on page 3. Confirm to continue.').",
                "missing contextual signature announcement",
            )

        if not COMBINE_PATTERN.search(signature_text):
            self._add_missing(
                "ACC015",
                "Signature blocks must use .accessibilityElement(children: .combine).",
                "missing accessibilityElement(children: .combine)",
            )

        has_focus_handoff = bool(LAYOUT_FOCUS_PATTERN.search(signature_text))
        if not has_focus_handoff:
            has_focus_handoff = bool(
                FOCUS_STATE_PATTERN.search(signature_text)
                and re.search(r"confirm", signature_text, re.IGNORECASE)
            )

        if not has_focus_handoff:
            self._add_missing(
                "ACC014",
                "After signature placement, move accessibility focus to the confirmation control.",
                "missing post-signature focus handoff",
            )

    def _check_page_curl_navigation(self, all_text: str) -> None:
        if not PAGE_CURL_PATTERN.search(all_text):
            return

        if not ALTERNATIVE_NAV_PATTERN.search(all_text):
            self._add_missing(
                "ACC008",
                "Page curl interactions must provide VoiceOver-accessible alternative navigation actions.",
                "missing accessible next/previous page actions",
            )

        if not ROTOR_PATTERN.search(all_text):
            self._add_missing(
                "ACC009",
                "Page navigation must expose rotor or adjustable accessibility gestures.",
                "missing accessibilityRotor/accessibilityAdjustableAction support",
            )

    def _check_dynamic_type_and_reflow(self) -> None:
        semantic_font_found = False
        for path, line_no, line in self._all_rows():
            if _is_comment(line):
                continue
            if SEMANTIC_FONT_PATTERN.search(line):
                semantic_font_found = True
            if FIXED_FONT_PATTERN.search(line):
                self._add(
                    "ACC010",
                    path,
                    line_no,
                    "Fixed-size typography is forbidden. Use semantic text styles and Dynamic Type.",
                    _line_snippet(line),
                )

        if not semantic_font_found:
            self._add_missing(
                "ACC010",
                "No semantic font styles detected. Use .font(.body/.headline/...) or UIFont.preferredFont(forTextStyle:).",
                "missing semantic typography",
            )

        pagination_files: list[Path] = []
        for path in self.swift_files:
            text = "\n".join(self._read_lines(path))
            if PAGINATION_HINT_PATTERN.search(text):
                pagination_files.append(path)

        if not pagination_files:
            return

        for path in pagination_files:
            text = "\n".join(self._read_lines(path))
            if not DYNAMIC_TYPE_PATTERN.search(text) or not REFLOW_PATTERN.search(text):
                self._add(
                    "ACC011",
                    path,
                    1,
                    "Pagination views must reflow for large Dynamic Type sizes using explicit dynamicTypeSize-aware layout branching.",
                    "missing pagination reflow path for large text",
                )

    def _check_contrast_requirements(self, all_text: str) -> None:
        has_contrast_word = bool(CONTRAST_WORD_PATTERN.search(all_text))
        has_body_ratio = bool(re.search(r"4\.5\s*:?\s*1|4\.5", all_text))
        has_large_ratio = bool(re.search(r"3(?:\.0+)?\s*:?\s*1|3\.0", all_text))
        has_validation_hook = bool(CONTRAST_VALIDATION_PATTERN.search(all_text))

        if not (has_contrast_word and has_body_ratio and has_large_ratio):
            self._add_missing(
                "ACC012",
                "Accessibility architecture must encode 4.5:1 body-text and 3:1 large-text contrast thresholds.",
                "missing explicit contrast thresholds",
            )

        if CUSTOM_PALETTE_PATTERN.search(all_text) and not has_validation_hook:
            self._add_missing(
                "ACC012",
                "Custom color palettes must run explicit contrast validation before release.",
                "missing custom palette contrast validator",
            )

    def _check_decorative_elements(self) -> None:
        for path, line_no, line in self._all_rows():
            if _is_comment(line):
                continue

            is_decorative = bool(
                DECORATIVE_PATTERN.search(line) or "Image(decorative:" in line
            )
            if not is_decorative:
                continue

            window = self._window_text(path, line_no, before=0, after=6)
            if not re.search(r"\.accessibilityHidden\s*\(\s*true\s*\)", window):
                self._add(
                    "ACC013",
                    path,
                    line_no,
                    "Decorative elements must be hidden from assistive technologies with .accessibilityHidden(true).",
                    _line_snippet(line),
                )

    def _check_ui_test_audit(self) -> None:
        ui_test_files: list[Path] = []
        for path in self.swift_files:
            rel = _relative_path(self.root, path)
            if re.search(r"UITests|UI[_-]?Tests", rel):
                ui_test_files.append(path)

        if not ui_test_files:
            self._add_missing(
                "ACC016",
                "Project must include UI tests that execute performA11yAudit().",
                "missing UITest performA11yAudit() coverage",
            )
            return

        for path in ui_test_files:
            text = "\n".join(self._read_lines(path))
            if "performA11yAudit(" in text:
                return

        self._add_missing(
            "ACC016",
            "UI test suite must call performA11yAudit() prior to marking screens complete.",
            "missing performA11yAudit() call in UITests",
        )

    def _check_dynamic_announcements(self) -> None:
        for path in self.swift_files:
            text = "\n".join(self._read_lines(path))
            if not DYNAMIC_CONTENT_PATTERN.search(text):
                continue
            if ANNOUNCEMENT_CALL_PATTERN.search(text):
                continue

            first_match = self._first_line(path, DYNAMIC_CONTENT_PATTERN)
            if first_match is None:
                continue
            line_no, line = first_match
            self._add(
                "ACC017",
                path,
                line_no,
                "Dynamic content changes must be announced with UIAccessibility.post(notification: .announcement, argument: ...).",
                _line_snippet(line),
            )

    def _check_completion_voiceover_verification(self) -> None:
        for path in self.swift_files:
            lines = self._read_lines(path)
            for idx, line in enumerate(lines, start=1):
                if _is_comment(line):
                    continue
                if not COMPLETION_PATTERN.search(line):
                    continue

                window = self._window_text(path, idx, before=2, after=10)
                if not VOICEOVER_VERIFICATION_PATTERN.search(window):
                    self._add(
                        "ACC018",
                        path,
                        idx,
                        "Completion markers require explicit VoiceOver verification evidence.",
                        _line_snippet(line),
                    )

    def validate(self) -> ResultOutput:
        if not self.swift_files:
            self._add_missing(
                "ACC000",
                "No Swift files found under root.",
                "missing *.swift files",
            )
            return self._report()

        all_text = self._joined_text(self.swift_files)

        self._check_wcag_baseline(all_text)
        self._check_touch_targets_and_interactive_semantics()
        self._check_images()
        self._check_custom_components()
        self._check_page_curl_navigation(all_text)
        self._check_dynamic_type_and_reflow()
        self._check_contrast_requirements(all_text)
        self._check_decorative_elements()

        signature_files = self._signature_files()
        self._check_signature_contract(signature_files)

        self._check_ui_test_audit()
        self._check_dynamic_announcements()
        self._check_completion_voiceover_verification()

        return self._report()

    def _report(self) -> ResultOutput:
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


def _print_text_report(result: ResultOutput) -> None:
    print(f"contract: {result['contract']}")
    print(f"verdict: {result['verdict']}")
    print(
        "summary: "
        f"files_scanned={result['summary']['files_scanned']} "
        f"rules_checked={result['summary']['rules_checked']} "
        f"violations={result['summary']['violations']}"
    )
    if not result["violations"]:
        return
    print("violations:")
    for violation in result["violations"]:
        print(
            f"- {violation['rule_id']} {violation['file']}:{violation['line']} "
            f"{violation['rejection']}"
        )
        print(f"  snippet: {violation['snippet']}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the Exhibit A accessibility contract."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(),
        help="Project root to scan (default: current directory)",
    )
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Output format (default: json)",
    )
    args = parser.parse_args()

    validator = ContractValidator(args.root)
    result = validator.validate()

    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        _print_text_report(result)

    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
