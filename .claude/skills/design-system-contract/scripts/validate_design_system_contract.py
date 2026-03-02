#!/usr/bin/env python3
"""Validate Exhibit A design-system contract."""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypedDict

CONTRACT_NAME = "design-system-contract"

RULE_TITLES = {
    "DSC000": "Swift source files must exist",
    "DSC001": "Theme struct with semantic namespaces must exist",
    "DSC002": "Theme colors must use Color(light:..., dark:...) paired tokens",
    "DSC003": "Required semantic color tokens must exist",
    "DSC004": "Views must not contain inline colors, hex values, or raw color APIs",
    "DSC005": "Header typography tokens must use Cormorant Garamond",
    "DSC006": "Body typography tokens must use Crimson Pro",
    "DSC007": "Cormorant Garamond and Crimson Pro fonts must be bundled",
    "DSC008": "Theme.Spacing must use 4pt base increments",
    "DSC009": "Views must not use inline numeric spacing values",
    "DSC010": "Raw font-size APIs are forbidden in views",
    "DSC011": "Views must consume Theme.Typography semantic tokens",
    "DSC012": "Paper texture must only be applied via PaperTexture modifier",
    "DSC013": "Shadows must use warm token values and avoid gray/black drop shadows",
    "DSC014": "Default SwiftUI Divider is forbidden; divider styling must use goldLeaf",
    "DSC015": "Stamp components must follow dustyRose/uppercase/tracking/thin-border rules",
    "DSC016": "Wax seal components must use sealBurgundy with emboss shadow",
    "DSC017": "Wax seal components may only appear on cover and home screens",
    "DSC018": "Signature styling must use goldLeaf lines, warmInk names, and fadedInk italic titles",
    "DSC019": "Dark mode background must include #1E1B16 and never pure black backgrounds",
    "DSC020": "Component files must declare DESIGN_TOKEN markers tied to Theme tokens",
    "DSC021": "Contrast checks require parseable semantic text/background hex tokens",
    "DSC022": "WCAG AA contrast must pass (4.5 body, 3.0 large)",
    "DSC023": "Paper texture must provide warm-noise adaptation for dark mode",
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

HEX_PATTERN = re.compile(r"#(?:[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})")
PAIR_COLOR_PATTERN = re.compile(
    r"static\s+let\s+(?P<name>\w+)\s*=\s*Color\s*\(\s*light\s*:\s*\"(?P<light>[^\"]+)\"\s*,\s*dark\s*:\s*\"(?P<dark>[^\"]+)\"\s*\)"
)
COLOR_DECL_PATTERN = re.compile(r"static\s+let\s+(?P<name>\w+)\s*=\s*Color\s*\(")
STRUCT_THEME_PATTERN = re.compile(r"\bstruct\s+Theme\b")
TEXT_PATTERN = re.compile(r"\bText\s*\(")
SWIFTUI_IMPORT_PATTERN = re.compile(r"^\s*import\s+SwiftUI\s*$", re.MULTILINE)
VIEW_CONFORMANCE_PATTERN = re.compile(r"\bstruct\s+\w+\s*:\s*View\b")
SYSTEM_FONT_PATTERN = re.compile(r"\.font\s*\(\s*\.system\s*\(\s*size\s*:")
CUSTOM_FONT_PATTERN = re.compile(r"(?:Font|\.font)\s*\.\s*custom\s*\(")
INLINE_COLOR_CALL_PATTERN = re.compile(r"\bColor\s*\(")
RAW_COLOR_LITERAL_PATTERN = re.compile(
    r"\.(?:red|green|blue|black|white|gray|orange|yellow|pink|purple|indigo|teal|mint|brown)\b"
)
INLINE_PADDING_PATTERN = re.compile(
    r"\.padding\s*\(\s*(?:\.(?:top|bottom|leading|trailing|horizontal|vertical)\s*,\s*)?(?P<value>\d+(?:\.\d+)?)\s*\)"
)
STACK_SPACING_PATTERN = re.compile(
    r"\b(?:VStack|HStack|LazyVStack|LazyHStack|LazyVGrid|LazyHGrid|Grid)\s*\(\s*spacing\s*:\s*(?P<value>\d+(?:\.\d+)?)"
)
TEXTURE_IMAGE_PATTERN = re.compile(
    r"\bImage\s*\(\s*\"[^\"]*(paper|texture|noise)[^\"]*\"", re.IGNORECASE
)
TEXTURE_BG_PATTERN = re.compile(
    r"\.background\s*\([^)]*(paper|texture|noise)", re.IGNORECASE
)
SHADOW_PATTERN = re.compile(r"\.shadow\s*\(")
DIVIDER_PATTERN = re.compile(r"\bDivider\s*\(\s*\)")
STAMP_DECL_PATTERN = re.compile(r"\bstruct\s+\w*Stamp\w*\s*:\s*View\b")
WAX_DECL_PATTERN = re.compile(
    r"\bstruct\s+(?P<name>\w*(?:WaxSeal|Seal)\w*)\s*:\s*View\b"
)
SIGNATURE_DECL_PATTERN = re.compile(r"\bstruct\s+\w*Signature\w*\s*:\s*View\b")
TOKEN_MARKER_PATTERN = re.compile(
    r"//\s*DESIGN_TOKEN:\s*Theme\.(?:Colors|Typography|Spacing|Shadows|Textures)\.(?P<token>\w+)"
)
PURE_BLACK_PATTERN = re.compile(
    r"#000000\b|(?:\bColor\s*\(\s*)?\.black\b", re.IGNORECASE
)

REQUIRED_COLOR_TOKENS = {
    "goldleaf",
    "dustyrose",
    "sealburgundy",
    "warmink",
    "fadedink",
    "shadowwarm",
}
TEXT_TOKEN_HINTS = ("ink", "text", "body", "title", "heading", "name")
LARGE_TEXT_HINTS = ("header", "title", "heading", "display")
BG_TOKEN_HINTS = ("background", "paper", "surface")


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


@dataclass(frozen=True)
class ColorToken:
    """Parsed color token declaration from Theme."""

    name: str
    light: str
    dark: str
    file: Path
    line: int
    snippet: str


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


def _is_ignored(path: Path) -> bool:
    return any(part in IGNORED_DIRS for part in path.parts)


def _is_comment(line: str) -> bool:
    stripped = line.strip()
    return (
        stripped.startswith("//")
        or stripped.startswith("/*")
        or stripped.startswith("*")
    )


def _snippet(line: str) -> str:
    return line.strip()[:220]


def _normalize_token(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _normalize_hex(value: str) -> str | None:
    text = value.strip()
    if not text.startswith("#"):
        return None
    digits = text[1:]
    if len(digits) == 8:
        digits = digits[:6]
    if len(digits) != 6 or re.search(r"[^0-9a-fA-F]", digits):
        return None
    return digits.lower()


def _hex_to_rgb(value: str) -> tuple[float, float, float] | None:
    normalized = _normalize_hex(value)
    if normalized is None:
        return None
    r = int(normalized[0:2], 16) / 255.0
    g = int(normalized[2:4], 16) / 255.0
    b = int(normalized[4:6], 16) / 255.0
    return (r, g, b)


def _srgb_to_linear(channel: float) -> float:
    if channel <= 0.04045:
        return channel / 12.92
    return ((channel + 0.055) / 1.055) ** 2.4


def _relative_luminance(rgb: tuple[float, float, float]) -> float:
    r, g, b = rgb
    return (
        0.2126 * _srgb_to_linear(r)
        + 0.7152 * _srgb_to_linear(g)
        + 0.0722 * _srgb_to_linear(b)
    )


def _contrast_ratio(fg_hex: str, bg_hex: str) -> float | None:
    fg_rgb = _hex_to_rgb(fg_hex)
    bg_rgb = _hex_to_rgb(bg_hex)
    if fg_rgb is None or bg_rgb is None:
        return None
    l1 = _relative_luminance(fg_rgb)
    l2 = _relative_luminance(bg_rgb)
    light = max(l1, l2)
    dark = min(l1, l2)
    return (light + 0.05) / (dark + 0.05)


class ContractValidator:
    """Deterministic validator for the Exhibit A design-system contract."""

    def __init__(self, root: Path):
        self.root = root.resolve()
        self.swift_files = self._collect_swift_files()
        self.cache: dict[Path, list[str]] = {}
        self.violations: list[Violation] = []
        self.violation_index: set[tuple[str, str, int]] = set()
        self.files_scanned = len(self.swift_files)
        self.rule_count = len(RULE_TITLES)

        self.theme_files = self._find_theme_files()
        self.theme_color_tokens: dict[str, ColorToken] = {}
        self.theme_typography_tokens: set[str] = set()
        self.theme_spacing_tokens: set[str] = set()
        self.view_files = self._find_view_files()

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

    def _relative_path(self, path: Path) -> str:
        try:
            rel = path.resolve().relative_to(self.root.resolve())
        except ValueError:
            rel = path
        return rel.as_posix()

    def _add(
        self,
        rule_id: str,
        file_path: Path,
        line_no: int,
        rejection: str,
        snippet: str,
    ) -> None:
        rel = self._relative_path(file_path)
        key = (rule_id, rel, max(1, line_no))
        if key in self.violation_index:
            return
        self.violation_index.add(key)
        self.violations.append(
            Violation(
                rule_id=rule_id,
                title=RULE_TITLES[rule_id],
                rejection=f"REJECT: {rejection}",
                file=rel,
                line=max(1, line_no),
                snippet=snippet[:220],
            )
        )

    def _find_theme_files(self) -> list[Path]:
        theme_files: list[Path] = []
        for path in self.swift_files:
            text = "\n".join(self._read_lines(path))
            if STRUCT_THEME_PATTERN.search(text):
                theme_files.append(path)
        return sorted(theme_files)

    def _is_test_file(self, path: Path) -> bool:
        lowered = path.as_posix().lower()
        return "/tests/" in lowered or lowered.endswith("tests.swift")

    def _find_view_files(self) -> list[Path]:
        files: list[Path] = []
        for path in self.swift_files:
            if self._is_test_file(path):
                continue
            text = "\n".join(self._read_lines(path))
            if SWIFTUI_IMPORT_PATTERN.search(text) or VIEW_CONFORMANCE_PATTERN.search(
                text
            ):
                files.append(path)
        return sorted(files)

    def _parse_theme_blocks(self) -> None:
        if not self.theme_files:
            return

        for path in self.theme_files:
            lines = self._read_lines(path)
            for idx, line in enumerate(lines, start=1):
                pair_match = PAIR_COLOR_PATTERN.search(line)
                if pair_match:
                    token = ColorToken(
                        name=pair_match.group("name"),
                        light=pair_match.group("light"),
                        dark=pair_match.group("dark"),
                        file=path,
                        line=idx,
                        snippet=_snippet(line),
                    )
                    self.theme_color_tokens[_normalize_token(token.name)] = token
                    continue

                color_decl = COLOR_DECL_PATTERN.search(line)
                if color_decl and not _is_comment(line):
                    self._add(
                        "DSC002",
                        path,
                        idx,
                        'Theme color tokens must use Color(light: "...", dark: "...") exactly.',
                        _snippet(line),
                    )

            self.theme_typography_tokens |= self._parse_enum_tokens(path, "Typography")
            self.theme_spacing_tokens |= self._parse_enum_tokens(path, "Spacing")

    def _parse_enum_tokens(self, path: Path, enum_name: str) -> set[str]:
        lines = self._read_lines(path)
        start_line: int | None = None
        for idx, line in enumerate(lines, start=1):
            if re.search(rf"\benum\s+{re.escape(enum_name)}\b", line):
                start_line = idx
                break
        if start_line is None:
            return set()

        brace_depth = 0
        started = False
        tokens: set[str] = set()
        for idx in range(start_line - 1, len(lines)):
            line = lines[idx]
            if "{" in line:
                brace_depth += line.count("{")
                started = True
            if started:
                match = re.search(r"static\s+let\s+(?P<name>\w+)\b", line)
                if match:
                    tokens.add(_normalize_token(match.group("name")))
            if "}" in line and started:
                brace_depth -= line.count("}")
                if brace_depth <= 0:
                    break
        return tokens

    def _check_baseline_presence(self) -> None:
        if self.swift_files:
            return
        placeholder = self.root / "."
        self._add(
            "DSC000",
            placeholder,
            1,
            "No Swift files detected. Design-system contract cannot be validated.",
            "No *.swift files under --root",
        )

    def _check_theme_presence(self) -> None:
        if self.theme_files:
            return
        target = self.swift_files[0] if self.swift_files else self.root / "."
        self._add(
            "DSC001",
            target,
            1,
            "Missing `struct Theme` with semantic token namespaces.",
            "Expected: struct Theme { enum Colors ... enum Typography ... enum Spacing ... }",
        )

    def _check_required_color_tokens(self) -> None:
        if not self.theme_files:
            return
        present = set(self.theme_color_tokens.keys())
        missing = sorted(REQUIRED_COLOR_TOKENS - present)
        if not missing:
            return
        target = self.theme_files[0]
        self._add(
            "DSC003",
            target,
            1,
            f"Missing required semantic color tokens: {', '.join(missing)}.",
            "Required: goldLeaf, dustyRose, sealBurgundy, warmInk, fadedInk, shadowWarm",
        )

    def _check_typography_contract(self) -> None:
        if not self.theme_files:
            return
        theme_text = self._joined_text(self.theme_files)
        lowered = theme_text.lower()
        target = self.theme_files[0]
        if "cormorant garamond" not in lowered:
            self._add(
                "DSC005",
                target,
                1,
                "Header typography tokens must map to Cormorant Garamond.",
                "Expected Cormorant Garamond in Theme.Typography",
            )
        if "crimson pro" not in lowered:
            self._add(
                "DSC006",
                target,
                1,
                "Body typography tokens must map to Crimson Pro.",
                "Expected Crimson Pro in Theme.Typography",
            )

    def _check_font_bundle_contract(self) -> None:
        plist_files = sorted(
            path
            for path in self.root.rglob("Info.plist")
            if not _is_ignored(path) and not self._is_test_file(path)
        )
        if not plist_files:
            target = (
                self.theme_files[0]
                if self.theme_files
                else (self.swift_files[0] if self.swift_files else self.root / ".")
            )
            self._add(
                "DSC007",
                target,
                1,
                "Info.plist not found; cannot verify bundled Cormorant Garamond and Crimson Pro fonts.",
                "Expected UIAppFonts entries for Cormorant Garamond and Crimson Pro",
            )
            return

        found_cormorant = False
        found_crimson = False
        for plist in plist_files:
            try:
                root = ET.fromstring(plist.read_text(encoding="utf-8", errors="ignore"))
            except ET.ParseError:
                continue
            text_values = " ".join(
                (elem.text or "") for elem in root.iter() if elem.text
            ).lower()
            if "cormorant" in text_values:
                found_cormorant = True
            if "crimson" in text_values:
                found_crimson = True
        if found_cormorant and found_crimson:
            return
        target = plist_files[0]
        missing = []
        if not found_cormorant:
            missing.append("Cormorant Garamond")
        if not found_crimson:
            missing.append("Crimson Pro")
        self._add(
            "DSC007",
            target,
            1,
            f"Missing bundled fonts in Info.plist: {', '.join(missing)}.",
            "Expected UIAppFonts to include both font families",
        )

    def _check_spacing_tokens(self) -> None:
        if not self.theme_files:
            return
        has_spacing_enum = bool(self.theme_spacing_tokens)
        target = self.theme_files[0]
        if not has_spacing_enum:
            self._add(
                "DSC008",
                target,
                1,
                "Theme.Spacing enum with 4pt scale tokens is required.",
                "Expected enum Spacing with static token values",
            )
            return

        found_base_unit = False
        for path in self.theme_files:
            lines = self._read_lines(path)
            in_spacing = False
            brace_depth = 0
            for idx, line in enumerate(lines, start=1):
                if re.search(r"\benum\s+Spacing\b", line):
                    in_spacing = True
                    brace_depth = line.count("{") - line.count("}")
                    continue
                if not in_spacing:
                    continue
                brace_depth += line.count("{") - line.count("}")
                if brace_depth < 0:
                    in_spacing = False
                    continue
                if _is_comment(line):
                    continue
                number_matches = re.findall(r"(?<![\w.])(\d+(?:\.\d+)?)", line)
                for raw in number_matches:
                    value = float(raw)
                    if abs(value - 4.0) < 1e-9:
                        found_base_unit = True
                    if abs(value % 4.0) > 1e-9:
                        self._add(
                            "DSC008",
                            path,
                            idx,
                            "Spacing token values must be multiples of 4pt.",
                            _snippet(line),
                        )
                if brace_depth == 0:
                    in_spacing = False
        if not found_base_unit:
            self._add(
                "DSC008",
                target,
                1,
                "Theme.Spacing must define an explicit 4pt base unit token.",
                "Expected a spacing token with value 4",
            )

    def _check_view_inline_styling(self) -> None:
        for path in self.view_files:
            if path in self.theme_files:
                continue
            lines = self._read_lines(path)
            has_text = False
            uses_typography_token = False
            for idx, line in enumerate(lines, start=1):
                if _is_comment(line):
                    continue
                if TEXT_PATTERN.search(line):
                    has_text = True
                if "Theme.Typography." in line:
                    uses_typography_token = True

                if HEX_PATTERN.search(line):
                    self._add(
                        "DSC004",
                        path,
                        idx,
                        "Hex literals are forbidden in views; use Theme color tokens.",
                        _snippet(line),
                    )
                if INLINE_COLOR_CALL_PATTERN.search(line):
                    self._add(
                        "DSC004",
                        path,
                        idx,
                        "Inline Color(...) calls are forbidden in views; use Theme.Colors tokens.",
                        _snippet(line),
                    )
                if RAW_COLOR_LITERAL_PATTERN.search(line) and any(
                    key in line
                    for key in (
                        "foreground",
                        "background",
                        "shadow",
                        "stroke",
                        "fill",
                        "tint",
                    )
                ):
                    self._add(
                        "DSC004",
                        path,
                        idx,
                        "Raw color literals are forbidden in view styling.",
                        _snippet(line),
                    )

                if INLINE_PADDING_PATTERN.search(line) and "Theme.Spacing." not in line:
                    self._add(
                        "DSC009",
                        path,
                        idx,
                        "Inline numeric padding is forbidden; use Theme.Spacing tokens.",
                        _snippet(line),
                    )
                if STACK_SPACING_PATTERN.search(line) and "Theme.Spacing." not in line:
                    self._add(
                        "DSC009",
                        path,
                        idx,
                        "Inline stack spacing is forbidden; use Theme.Spacing tokens.",
                        _snippet(line),
                    )

                if SYSTEM_FONT_PATTERN.search(line) or CUSTOM_FONT_PATTERN.search(line):
                    self._add(
                        "DSC010",
                        path,
                        idx,
                        "Raw font APIs in views are forbidden; use Theme.Typography tokens.",
                        _snippet(line),
                    )

                if TEXTURE_IMAGE_PATTERN.search(line) or (
                    TEXTURE_BG_PATTERN.search(line) and "PaperTexture" not in line
                ):
                    self._add(
                        "DSC012",
                        path,
                        idx,
                        "Paper/noise texture implementations are forbidden outside PaperTexture modifier.",
                        _snippet(line),
                    )

                if SHADOW_PATTERN.search(line):
                    lowered = line.lower()
                    if (
                        ".gray" in lowered
                        or ".black" in lowered
                        or "#808080" in lowered
                    ):
                        self._add(
                            "DSC013",
                            path,
                            idx,
                            "Gray/black drop shadows are forbidden; use warm shadow tokens.",
                            _snippet(line),
                        )
                    elif (
                        "Theme.Shadows." not in line
                        and "Theme.Colors.shadowWarm" not in line
                        and "shadowWarm" not in line
                        and "emboss" not in lowered
                    ):
                        self._add(
                            "DSC013",
                            path,
                            idx,
                            "Shadow declarations must use semantic warm tokens.",
                            _snippet(line),
                        )

                if DIVIDER_PATTERN.search(line):
                    self._add(
                        "DSC014",
                        path,
                        idx,
                        "Default Divider() is forbidden; use tokenized divider component.",
                        _snippet(line),
                    )

                if PURE_BLACK_PATTERN.search(line) and "background" in line.lower():
                    self._add(
                        "DSC019",
                        path,
                        idx,
                        "Pure black backgrounds are forbidden in dark mode.",
                        _snippet(line),
                    )

            if has_text and not uses_typography_token:
                self._add(
                    "DSC011",
                    path,
                    1,
                    "Text-bearing views must consume Theme.Typography semantic tokens.",
                    "Expected at least one Theme.Typography.* usage in this view file",
                )

    def _check_divider_token_usage(self) -> None:
        for path in self.view_files:
            text = "\n".join(self._read_lines(path))
            if "Divider" in path.name and "struct" in text and "goldLeaf" not in text:
                self._add(
                    "DSC014",
                    path,
                    1,
                    "Custom divider components must use the goldLeaf token.",
                    "Expected Theme.Colors.goldLeaf in divider styling",
                )

    def _check_stamp_rules(self) -> None:
        for path in self.view_files:
            text = "\n".join(self._read_lines(path))
            if "stamp" not in path.name.lower() and not STAMP_DECL_PATTERN.search(text):
                continue
            lowered = text.lower()
            if "dustyrose" not in lowered:
                self._add(
                    "DSC015",
                    path,
                    1,
                    "Stamp components must use dustyRose token.",
                    "Expected Theme.Colors.dustyRose",
                )
            if ".uppercased(" not in lowered and ".textcase(.uppercase)" not in lowered:
                self._add(
                    "DSC015",
                    path,
                    1,
                    "Stamp components must use uppercase styling.",
                    "Expected .uppercased() or .textCase(.uppercase)",
                )
            if ".tracking(" not in lowered:
                self._add(
                    "DSC015",
                    path,
                    1,
                    "Stamp components must include tracked letter spacing.",
                    "Expected .tracking(...)",
                )
            has_thin_rounded_border = (
                "roundedrectangle" in lowered
                and "linewidth" in lowered
                and bool(re.search(r"lineWidth\s*:\s*(0?\.\d+|1(?:\.0+)?)", text))
            )
            if not has_thin_rounded_border:
                self._add(
                    "DSC015",
                    path,
                    1,
                    "Stamp components must include a thin rounded border.",
                    "Expected RoundedRectangle stroke with lineWidth <= 1.0",
                )
            if ".red" in lowered or "#ff0000" in lowered or "#cc0000" in lowered:
                self._add(
                    "DSC015",
                    path,
                    1,
                    "Stamp components must never use alarm-red visuals.",
                    "Remove red literals and use dustyRose token",
                )

    def _check_wax_rules(self) -> None:
        wax_components: dict[str, Path] = {}
        for path in self.view_files:
            text = "\n".join(self._read_lines(path))
            for match in WAX_DECL_PATTERN.finditer(text):
                name = match.group("name")
                wax_components[name] = path
                lowered = text.lower()
                if "sealburgundy" not in lowered:
                    self._add(
                        "DSC016",
                        path,
                        1,
                        "Wax seal components must use sealBurgundy token.",
                        "Expected Theme.Colors.sealBurgundy",
                    )
                if ".shadow(" not in lowered:
                    self._add(
                        "DSC016",
                        path,
                        1,
                        "Wax seal components must include subtle emboss shadow.",
                        "Expected tokenized emboss shadow",
                    )

        if not wax_components:
            return

        for component_name, definition_path in wax_components.items():
            call_pattern = re.compile(rf"\b{re.escape(component_name)}\s*\(")
            for path in self.view_files:
                if path == definition_path:
                    continue
                lowered_path = path.as_posix().lower()
                for idx, line in enumerate(self._read_lines(path), start=1):
                    if _is_comment(line):
                        continue
                    if not call_pattern.search(line):
                        continue
                    if "cover" in lowered_path or "home" in lowered_path:
                        continue
                    self._add(
                        "DSC017",
                        path,
                        idx,
                        f"{component_name} is restricted to cover/home screens only.",
                        _snippet(line),
                    )

    def _check_signature_rules(self) -> None:
        for path in self.view_files:
            text = "\n".join(self._read_lines(path))
            if (
                "signature" not in path.name.lower()
                and not SIGNATURE_DECL_PATTERN.search(text)
            ):
                continue
            lowered = text.lower()
            if "goldleaf" not in lowered:
                self._add(
                    "DSC018",
                    path,
                    1,
                    "Signature styling must include goldLeaf lines.",
                    "Expected Theme.Colors.goldLeaf",
                )
            if "warmink" not in lowered:
                self._add(
                    "DSC018",
                    path,
                    1,
                    "Signature name styling must include warmInk.",
                    "Expected Theme.Colors.warmInk",
                )
            if "fadedink" not in lowered:
                self._add(
                    "DSC018",
                    path,
                    1,
                    "Signature title styling must include fadedInk.",
                    "Expected Theme.Colors.fadedInk",
                )
            if ".italic(" not in lowered and ".italic()" not in lowered:
                self._add(
                    "DSC018",
                    path,
                    1,
                    "Signature titles must be italicized.",
                    "Expected .italic() for fadedInk title text",
                )

    def _check_dark_mode_background(self) -> None:
        if not self.theme_files:
            return
        has_required_dark_background = False
        for token in self.theme_color_tokens.values():
            if (
                "background" in token.name.lower()
                and _normalize_hex(token.dark) == "1e1b16"
            ):
                has_required_dark_background = True
                break
        if not has_required_dark_background:
            target = self.theme_files[0]
            self._add(
                "DSC019",
                target,
                1,
                "Theme must define a background token with dark value #1E1B16.",
                'Expected Color(light: "...", dark: "#1E1B16") for background',
            )

    def _check_warm_noise_texture(self) -> None:
        if not self.swift_files:
            return
        warm_noise_declared = False
        paper_texture_with_warm_noise = False

        for path in self.theme_files:
            text = "\n".join(self._read_lines(path)).lower()
            if "warmnoise" in text or "warm_noise" in text:
                warm_noise_declared = True

        for path in self.view_files:
            text = "\n".join(self._read_lines(path)).lower()
            if "papertexture" not in text:
                continue
            if "warmnoise" in text or "warm_noise" in text:
                paper_texture_with_warm_noise = True

        if warm_noise_declared and paper_texture_with_warm_noise:
            return
        target = (
            self.theme_files[0]
            if self.theme_files
            else (self.view_files[0] if self.view_files else self.swift_files[0])
        )
        self._add(
            "DSC023",
            target,
            1,
            "Dark-mode paper texture must adapt using a warm-noise token.",
            "Expected warmNoise token + PaperTexture dark-mode usage",
        )

    def _check_component_token_markers(self) -> None:
        available_tokens = (
            set(self.theme_color_tokens.keys())
            | self.theme_typography_tokens
            | self.theme_spacing_tokens
        )
        for path in self.view_files:
            lowered = path.as_posix().lower()
            if "/components/" not in lowered:
                continue
            text = "\n".join(self._read_lines(path))
            if not VIEW_CONFORMANCE_PATTERN.search(text):
                continue
            marker_matches = list(TOKEN_MARKER_PATTERN.finditer(text))
            if not marker_matches:
                self._add(
                    "DSC020",
                    path,
                    1,
                    "Component files must declare // DESIGN_TOKEN: Theme.<Namespace>.<token> markers.",
                    "Missing DESIGN_TOKEN marker",
                )
                continue
            for match in marker_matches:
                token = _normalize_token(match.group("token"))
                if token in available_tokens:
                    continue
                line_no = text[: match.start()].count("\n") + 1
                self._add(
                    "DSC020",
                    path,
                    line_no,
                    "DESIGN_TOKEN marker references a token not defined in Theme.",
                    _snippet(match.group(0)),
                )

    def _check_contrast(self) -> None:
        if not self.theme_color_tokens:
            return

        text_tokens = [
            token
            for token in self.theme_color_tokens.values()
            if any(hint in token.name.lower() for hint in TEXT_TOKEN_HINTS)
        ]
        bg_tokens = [
            token
            for token in self.theme_color_tokens.values()
            if any(hint in token.name.lower() for hint in BG_TOKEN_HINTS)
        ]
        if not text_tokens or not bg_tokens:
            target = self.theme_files[0]
            self._add(
                "DSC021",
                target,
                1,
                "Contrast validation requires semantic text and background tokens with parseable hex values.",
                "Add text/background semantic tokens in Theme.Colors",
            )
            return

        for token in [*text_tokens, *bg_tokens]:
            if (
                _normalize_hex(token.light) is None
                or _normalize_hex(token.dark) is None
            ):
                self._add(
                    "DSC021",
                    token.file,
                    token.line,
                    "Contrast validation requires hex values in token light/dark pairs.",
                    token.snippet,
                )

        failures = 0
        for text_token in text_tokens:
            for bg_token in bg_tokens:
                for mode, text_color, bg_color in (
                    ("light", text_token.light, bg_token.light),
                    ("dark", text_token.dark, bg_token.dark),
                ):
                    ratio = _contrast_ratio(text_color, bg_color)
                    if ratio is None:
                        continue
                    threshold = (
                        3.0
                        if any(
                            hint in text_token.name.lower() for hint in LARGE_TEXT_HINTS
                        )
                        else 4.5
                    )
                    if ratio + 1e-9 >= threshold:
                        continue
                    failures += 1
                    self._add(
                        "DSC022",
                        text_token.file,
                        text_token.line,
                        (
                            f"Contrast {text_token.name}/{bg_token.name} ({mode}) is {ratio:.2f}:1; "
                            f"minimum required is {threshold:.1f}:1."
                        ),
                        text_token.snippet,
                    )
                    if failures >= 30:
                        return

    def run(self) -> None:
        self._check_baseline_presence()
        if not self.swift_files:
            return

        self._check_theme_presence()
        self._parse_theme_blocks()
        self._check_required_color_tokens()
        self._check_typography_contract()
        self._check_font_bundle_contract()
        self._check_spacing_tokens()
        self._check_view_inline_styling()
        self._check_divider_token_usage()
        self._check_stamp_rules()
        self._check_wax_rules()
        self._check_signature_rules()
        self._check_dark_mode_background()
        self._check_warm_noise_texture()
        self._check_component_token_markers()
        self._check_contrast()

    def report(self) -> ResultOutput:
        ordered = sorted(self.violations, key=lambda v: (v.rule_id, v.file, v.line))
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


def _print_text_report(report: ResultOutput) -> None:
    print(f"Contract: {report['contract']}")
    print(f"Verdict: {report['verdict']}")
    summary = report["summary"]
    print(
        "Summary: files_scanned={files_scanned}, rules_checked={rules_checked}, violations={violations}".format(
            **summary
        )
    )
    for violation in report["violations"]:
        print(
            f"- {violation['rule_id']} {violation['file']}:{violation['line']} {violation['rejection']} :: {violation['snippet']}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Exhibit A design-system contract."
    )
    parser.add_argument("--root", type=Path, default=Path())
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Output format for validation report.",
    )
    args = parser.parse_args()

    validator = ContractValidator(args.root)
    validator.run()
    report = validator.report()

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        _print_text_report(report)

    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
