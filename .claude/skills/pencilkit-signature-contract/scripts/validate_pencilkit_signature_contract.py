#!/usr/bin/env python3
"""Validate Exhibit A PencilKit signature capture contract."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypedDict

CONTRACT_NAME = "pencilkit-signature-contract"

RULE_TITLES = {
    "PSC000": "Swift source files must exist",
    "PSC001": "Signature capture must use PKCanvasView via UIViewRepresentable",
    "PSC002": "Signature tool must use warmInk pen width 2.5",
    "PSC003": "Pencil and marker tools are forbidden",
    "PSC004": "Canvas background must use warm cream #FBF7F0",
    "PSC005": "Ruler must be disabled",
    "PSC006": "Tool picker must be disabled",
    "PSC007": "Input policy must be anyInput",
    "PSC008": "Export rendering must use UIScreen.main.scale",
    "PSC009": "Export must crop to PKDrawing bounds with ~8pt padding",
    "PSC010": "Full canvas export is forbidden",
    "PSC011": "Export must use UIImage.pngData()",
    "PSC012": "PNG export must enforce < 50KB and crop before encoding",
    "PSC013": "Clear action must confirm when non-empty and dismiss when empty",
    "PSC014": "Guide line must be centered, goldLeaf, and 0.5pt",
    "PSC015": "Undo/redo gestures must be disabled",
    "PSC016": "Canvas emptiness must bind back to SwiftUI",
    "PSC017": "Uploaded signatures must be immutable",
    "PSC018": "PencilKit must be defensively guarded with graceful fallback",
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

SIGNATURE_FILE_HINT = re.compile(
    r"(signature|pencilkit|pkcanvasview|pkdrawing|signing|autograph)",
    re.IGNORECASE,
)
SIGNATURE_CODE_HINT = re.compile(
    r"\b(PKCanvasView|PKDrawing|PencilKit|PKInkingTool|warmInk|goldLeaf)\b"
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


class ContractValidator:
    """Deterministic validator for PencilKit signature capture requirements."""

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
                line=max(1, line_no),
                snippet=snippet,
            )
        )

    def _all_rows(self, files: list[Path] | None = None) -> list[tuple[Path, int, str]]:
        targets = files if files is not None else self.swift_files
        rows: list[tuple[Path, int, str]] = []
        for file_path in targets:
            for idx, line in enumerate(self._read_lines(file_path), start=1):
                rows.append((file_path, idx, line))
        return rows

    def _signature_files(self) -> list[Path]:
        files: list[Path] = []
        for file_path in self.swift_files:
            rel = _relative_path(self.root, file_path)
            content = "\n".join(self._read_lines(file_path))
            if SIGNATURE_FILE_HINT.search(rel) or SIGNATURE_CODE_HINT.search(content):
                files.append(file_path)
        return files

    def _joined_text(self, files: list[Path]) -> str:
        return "\n".join("\n".join(self._read_lines(path)) for path in files)

    def _check_for_required_pattern(
        self,
        rule_id: str,
        files: list[Path],
        pattern: re.Pattern[str],
        message: str,
        missing_snippet: str,
    ) -> None:
        for path, line_no, line in self._all_rows(files):
            if pattern.search(line):
                return
        self._add(rule_id, self.root / "PROJECT_ROOT", 1, message, missing_snippet)

    def _check_forbidden_pattern(
        self,
        rule_id: str,
        files: list[Path],
        pattern: re.Pattern[str],
        message: str,
    ) -> None:
        for path, line_no, line in self._all_rows(files):
            if pattern.search(line):
                self._add(rule_id, path, line_no, message, _line_snippet(line))

    def _check_structure(self, files: list[Path], combined: str) -> None:
        has_bridge = bool(
            re.search(r"\bUIViewRepresentable\b", combined)
            and re.search(r"\bPKCanvasView\b", combined)
            and re.search(r"\bmakeUIView\s*\(", combined)
            and re.search(r"\bupdateUIView\s*\(", combined)
        )
        if not has_bridge:
            self._add(
                "PSC001",
                self.root / "PROJECT_ROOT",
                1,
                "Signature capture must bridge `PKCanvasView` via `UIViewRepresentable` with make/update hooks.",
                "missing UIViewRepresentable + PKCanvasView bridge",
            )

    def _check_export_pipeline(self, files: list[Path]) -> None:
        rows = self._all_rows(files)
        first_crop: tuple[Path, int, str] | None = None
        first_png: tuple[Path, int, str] | None = None

        for path, line_no, line in rows:
            if "image(from:" in line and first_crop is None:
                first_crop = (path, line_no, line)
            if "pngData()" in line and first_png is None:
                first_png = (path, line_no, line)

            if re.search(r"image\s*\(\s*from:\s*(?:\w+\.)?bounds\b", line):
                self._add(
                    "PSC010",
                    path,
                    line_no,
                    "Never export full canvas bounds; crop to drawing bounds only.",
                    _line_snippet(line),
                )

        if first_png is None:
            self._add(
                "PSC011",
                self.root / "PROJECT_ROOT",
                1,
                "Export pipeline must encode signature images using `UIImage.pngData()`.",
                "missing pngData()",
            )

        if first_crop is None:
            self._add(
                "PSC009",
                self.root / "PROJECT_ROOT",
                1,
                "Export pipeline must crop using `PKDrawing.bounds` before encoding.",
                "missing drawing.bounds crop",
            )

        if (
            first_crop
            and first_png
            and _relative_path(self.root, first_crop[0])
            == _relative_path(self.root, first_png[0])
        ):
            if first_png[1] <= first_crop[1]:
                self._add(
                    "PSC012",
                    first_png[0],
                    first_png[1],
                    "Crop must occur before PNG encoding.",
                    _line_snippet(first_png[2]),
                )

        if not any(
            re.search(r"(?:50\s*\*\s*1024|51200)", line)
            and re.search(r"(count|bytes|size)", line, re.IGNORECASE)
            for _, _, line in rows
        ):
            self._add(
                "PSC012",
                self.root / "PROJECT_ROOT",
                1,
                "PNG pipeline must enforce `< 50KB` signature payload size gate.",
                "missing 50KB size check",
            )

    def _check_clear_behavior(self, files: list[Path], combined: str) -> None:
        has_confirm = bool(re.search(r"\b(confirmationDialog|alert)\s*\(", combined))
        has_dismiss_if_empty = bool(
            re.search(
                r"if\s+isEmpty\s*\{[\s\S]{0,200}dismiss\s*\(",
                combined,
            )
            or re.search(
                r"if\s+isEmpty\s*\{[\s\S]{0,200}(close|cancel|onDismiss)\s*\(",
                combined,
            )
        )
        if not (has_confirm and has_dismiss_if_empty):
            self._add(
                "PSC013",
                self.root / "PROJECT_ROOT",
                1,
                "Clear button must confirm when strokes exist and dismiss immediately when empty.",
                "missing clear-confirmation or empty-dismiss path",
            )

    def _check_guideline(self, files: list[Path], combined: str) -> None:
        has_gold = bool(re.search(r"\bgoldLeaf\b", combined))
        has_half_pt = bool(
            re.search(r"(lineWidth|stroke\(lineWidth:)\s*:\s*0\.5\b", combined)
        )
        has_center = bool(
            re.search(r"(height\s*/\s*2|midY|centerY|verticalCenter)", combined)
        )
        if not (has_gold and has_half_pt and has_center):
            self._add(
                "PSC014",
                self.root / "PROJECT_ROOT",
                1,
                "Signature guide line must be centered and rendered in `goldLeaf` at 0.5pt.",
                "missing centered goldLeaf 0.5pt guide line",
            )

    def _check_undo_redo(self, files: list[Path], combined: str) -> None:
        allowed_markers = (
            r"\bdisableUndoRedo\b",
            r"\bsuppressUndoRedo\b",
            r"undoManager\?\.disableUndoRegistration\(",
            r"undoManager\?\.removeAllActions\(",
            r"canPerformAction\s*\(\s*_ action:\s*Selector",
        )
        if not any(re.search(marker, combined) for marker in allowed_markers):
            self._add(
                "PSC015",
                self.root / "PROJECT_ROOT",
                1,
                "Disable undo/redo gestures explicitly for signature capture.",
                "missing undo/redo suppression path",
            )

    def _check_binding_sync(self, combined: str) -> None:
        has_binding = bool(re.search(r"@Binding\s+var\s+isEmpty\b", combined))
        has_delegate_sync = bool(
            re.search(r"canvasViewDrawingDidChange\s*\(", combined)
            and re.search(r"isEmpty\s*=\s*.*drawing\.strokes\.isEmpty", combined)
        )
        if not (has_binding and has_delegate_sync):
            self._add(
                "PSC016",
                self.root / "PROJECT_ROOT",
                1,
                "Canvas emptiness must bind back to SwiftUI (`@Binding isEmpty`) from drawing updates.",
                "missing @Binding isEmpty sync",
            )

    def _check_immutability(self, combined: str) -> None:
        immutable_gate = re.search(
            r"(guard\s+!\w*(uploaded|locked)\w*\s+else\s*\{\s*return|if\s+\w*(uploaded|locked)\w*\s*\{\s*return)",
            combined,
            re.IGNORECASE,
        )
        if not immutable_gate:
            self._add(
                "PSC017",
                self.root / "PROJECT_ROOT",
                1,
                "Uploaded signature images must become immutable and reject post-upload edits.",
                "missing uploaded-signature immutability guard",
            )

    def _check_availability_guard(
        self, all_swift_text: str, signature_text: str
    ) -> None:
        has_import = bool(
            re.search(r"^\s*import\s+PencilKit\b", all_swift_text, re.MULTILINE)
        )
        has_can_import = bool(
            re.search(r"#if\s+canImport\s*\(\s*PencilKit\s*\)", all_swift_text)
        )
        has_else = bool(re.search(r"#else\b", all_swift_text))
        has_fallback = bool(
            re.search(
                r"(fallback|unavailable|typed signature|text field|manual entry)",
                all_swift_text,
                re.IGNORECASE,
            )
        )

        uses_signature_api = bool(SIGNATURE_CODE_HINT.search(signature_text))

        if uses_signature_api and not has_can_import:
            self._add(
                "PSC018",
                self.root / "PROJECT_ROOT",
                1,
                "Guard PencilKit usage with `#if canImport(PencilKit)` and provide fallback.",
                "missing #if canImport(PencilKit)",
            )
        elif has_import and not has_can_import:
            self._add(
                "PSC018",
                self.root / "PROJECT_ROOT",
                1,
                "Guard PencilKit imports using `#if canImport(PencilKit)` and provide fallback.",
                "missing #if canImport(PencilKit)",
            )
        elif has_can_import and not (has_else and has_fallback):
            self._add(
                "PSC018",
                self.root / "PROJECT_ROOT",
                1,
                "Add graceful non-PencilKit fallback path in `#else` branch.",
                "missing fallback behavior for PencilKit-unavailable environments",
            )

    def validate(self) -> ResultOutput:
        if not self.swift_files:
            self._add(
                "PSC000",
                self.root / "PROJECT_ROOT",
                1,
                "No Swift files found under root.",
                "missing *.swift files",
            )
            return self._report()

        signature_files = self._signature_files()
        if not signature_files:
            self._add(
                "PSC001",
                self.root / "PROJECT_ROOT",
                1,
                "No signature-capture implementation found. Add `PKCanvasView` via `UIViewRepresentable`.",
                "missing PencilKit signature module",
            )
            self._check_availability_guard(
                "\n".join("\n".join(self._read_lines(p)) for p in self.swift_files),
                "",
            )
            return self._report()

        signature_text = self._joined_text(signature_files)
        all_swift_text = self._joined_text(self.swift_files)

        self._check_structure(signature_files, signature_text)

        self._check_for_required_pattern(
            "PSC002",
            signature_files,
            re.compile(
                r"PKInkingTool\s*\(\s*\.pen\s*,\s*color:\s*UIColor\s*\(\s*named:\s*\"warmInk\"\s*\)\s*!\s*,\s*width:\s*2\.5\s*\)"
            ),
            'Signature tool must be `PKInkingTool(.pen, color: UIColor(named: "warmInk")!, width: 2.5)`.',
            "missing required warmInk pen tool",
        )
        self._check_forbidden_pattern(
            "PSC003",
            signature_files,
            re.compile(r"PKInkingTool\s*\(\s*\.(marker|pencil)\b"),
            "Pencil/marker tools are forbidden for signature capture.",
        )

        self._check_for_required_pattern(
            "PSC004",
            signature_files,
            re.compile(r"(#FBF7F0|251\s*/\s*255|251\.0\s*/\s*255)"),
            "Canvas background must use warm cream `#FBF7F0`.",
            "missing warm cream paper tone",
        )
        self._check_for_required_pattern(
            "PSC005",
            signature_files,
            re.compile(r"isRulerActive\s*=\s*false"),
            "Disable ruler on signature canvas (`isRulerActive = false`).",
            "missing isRulerActive = false",
        )

        toolpicker_uses = False
        toolpicker_hidden = False
        for path, line_no, line in self._all_rows(signature_files):
            if re.search(r"\bPKToolPicker\b", line):
                toolpicker_uses = True
            if re.search(r"setVisible\s*\(\s*false\s*,\s*forFirstResponder:", line):
                toolpicker_hidden = True
        if toolpicker_uses and not toolpicker_hidden:
            self._add(
                "PSC006",
                self.root / "PROJECT_ROOT",
                1,
                "Tool picker must be disabled for signature capture surfaces.",
                "PKToolPicker usage detected without explicit hidden state",
            )

        self._check_for_required_pattern(
            "PSC007",
            signature_files,
            re.compile(r"drawingPolicy\s*=\s*\.anyInput"),
            "Signature input must allow finger and pencil (`drawingPolicy = .anyInput`).",
            "missing drawingPolicy = .anyInput",
        )
        self._check_forbidden_pattern(
            "PSC007",
            signature_files,
            re.compile(r"drawingPolicy\s*=\s*\.pencilOnly"),
            "Apple Pencil-only input is forbidden; finger input must remain enabled.",
        )

        self._check_for_required_pattern(
            "PSC008",
            signature_files,
            re.compile(r"UIScreen\.main\.scale"),
            "Render signature export at Retina scale (`UIScreen.main.scale`).",
            "missing UIScreen.main.scale export",
        )
        self._check_for_required_pattern(
            "PSC009",
            signature_files,
            re.compile(r"(drawing|PKDrawing)\.bounds"),
            "Crop export using `PKDrawing.bounds`.",
            "missing drawing.bounds crop source",
        )
        self._check_for_required_pattern(
            "PSC009",
            signature_files,
            re.compile(
                r"insetBy\s*\(\s*dx:\s*-?8(?:\.0)?\s*,\s*dy:\s*-?8(?:\.0)?\s*\)"
            ),
            "Expand crop rect with ~8pt padding before export.",
            "missing ~8pt crop padding",
        )

        self._check_export_pipeline(signature_files)

        self._check_clear_behavior(signature_files, signature_text)
        self._check_guideline(signature_files, signature_text)
        self._check_undo_redo(signature_files, signature_text)
        self._check_binding_sync(signature_text)
        self._check_immutability(signature_text)
        self._check_availability_guard(all_swift_text, signature_text)

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
        description="Validate the Exhibit A PencilKit signature capture contract."
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
