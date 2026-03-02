#!/usr/bin/env bash
# check-em-dashes.sh
# Typographic Lint: Em Dash Detection in Source Code
# Repository: Exhibit A (iOS SwiftUI + FastAPI Backend)
#
# Scans source files for em dashes (U+2014) that indicate copy-paste from
# rich text editors or AI output. Em dashes do not belong in source code —
# use -- or proper string constants instead.
#
# Usage:
#   ./check-em-dashes.sh              # Scan entire codebase
#   ./check-em-dashes.sh --dir path   # Scan specific directory

set -euo pipefail

# Color definitions (ANSI escape codes)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Characters to detect
# U+2014 EM DASH: —
# U+2013 EN DASH: –
# U+201C LEFT DOUBLE QUOTATION MARK: \xe2\x80\x9c
# U+201D RIGHT DOUBLE QUOTATION MARK: \xe2\x80\x9d
# U+2018 LEFT SINGLE QUOTATION MARK: \xe2\x80\x98
# U+2019 RIGHT SINGLE QUOTATION MARK: \xe2\x80\x99
EM_DASH=$'\xe2\x80\x94'
EN_DASH=$'\xe2\x80\x93'
LEFT_DOUBLE_QUOTE=$'\xe2\x80\x9c'
RIGHT_DOUBLE_QUOTE=$'\xe2\x80\x9d'
LEFT_SINGLE_QUOTE=$'\xe2\x80\x98'
RIGHT_SINGLE_QUOTE=$'\xe2\x80\x99'

TYPOGRAPHIC_CHARS=(
    "$EM_DASH"
    "$EN_DASH"
    "$LEFT_DOUBLE_QUOTE"
    "$RIGHT_DOUBLE_QUOTE"
    "$LEFT_SINGLE_QUOTE"
    "$RIGHT_SINGLE_QUOTE"
)

TYPOGRAPHIC_NAMES=(
    "EM DASH (U+2014)"
    "EN DASH (U+2013)"
    "LEFT DOUBLE QUOTE (U+201C)"
    "RIGHT DOUBLE QUOTE (U+201D)"
    "LEFT SINGLE QUOTE (U+2018)"
    "RIGHT SINGLE QUOTE (U+2019)"
)

# Directory names to exclude from scanning
# Mirrors protocol-zero.sh exclusions for iOS/Xcode and Python/FastAPI
EXCLUDE_DIRS=(
    ".git"
    ".claude"
    "build"
    "dist"
    "DerivedData"
    "xcuserdata"
    ".swiftpm"
    ".build"
    ".venv"
    "__pycache__"
    ".mypy_cache"
    ".ruff_cache"
    ".pytest_cache"
    "data"
)

# Path patterns to exclude
EXCLUDE_PATH_PATTERNS=(
    ".github/"
    "docs/"
    ".claude/"
)

# Files to exclude
EXCLUDE_FILES=(
    "CLAUDE.md"
    "protocol-zero.sh"
    "check-em-dashes.sh"
    "settings.local.json"
    "MEMORY.md"
)

# Binary and non-code extensions to skip
# Mirrors protocol-zero.sh binary list, plus markdown (.md) where
# typographic characters are legitimate prose
BINARY_EXTENSIONS=(
    "png" "jpg" "jpeg" "gif" "ico" "svg" "webp"
    "woff" "woff2" "ttf" "eot" "otf"
    "pdf" "zip" "tar" "gz" "bz2"
    "mp3" "mp4" "wav" "avi" "mov"
    "m4a" "aac"
    "ipa" "car" "mobileprovision"
    "pyc" "pyo"
    "db" "db-wal" "db-shm"
    "lock" "lockb"
    "p8"
    "skill"
    "md"
)

# Track violations
VIOLATIONS_FOUND=0

# Print functions
print_pass() {
    echo -e "${GREEN}${BOLD}[PASS]${NC} ${GREEN}$1${NC}"
}

print_fail() {
    echo -e "${RED}${BOLD}[FAIL]${NC} ${RED}$1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_info() {
    echo -e "[INFO] $1"
}

print_violation() {
    local file="$1"
    local line_num="$2"
    local content="$3"
    local char_name="$4"
    echo -e "  ${RED}├─${NC} ${BOLD}$file${NC}:${line_num}"
    echo -e "  │  Character: ${YELLOW}$char_name${NC}"
    echo -e "  │  Content: ${content:0:80}"
}

# Build grep exclusion arguments
build_exclude_args() {
    local args=""
    for dir in "${EXCLUDE_DIRS[@]}"; do
        args="$args --exclude-dir=$dir"
    done
    for ext in "${BINARY_EXTENSIONS[@]}"; do
        args="$args --exclude=*.$ext"
    done
    for file in "${EXCLUDE_FILES[@]}"; do
        args="$args --exclude=$file"
    done
    echo "$args"
}

# Check if a file should be excluded
should_exclude_file() {
    local filepath="$1"
    local filename
    filename=$(basename "$filepath")

    for exclude in "${EXCLUDE_FILES[@]}"; do
        if [[ "$filename" == "$exclude" ]]; then
            return 0
        fi
    done

    for path_pattern in "${EXCLUDE_PATH_PATTERNS[@]}"; do
        if [[ "$filepath" == *"$path_pattern"* ]]; then
            return 0
        fi
    done

    return 1
}

# Scan entire codebase
scan_codebase() {
    local root_dir="${1:-.}"

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Typographic Lint: Em Dash & Smart Quote Detection"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    print_info "Scanning directory: $root_dir"
    print_info "Excluded directories: ${EXCLUDE_DIRS[*]}"
    print_info "Excluded files: ${EXCLUDE_FILES[*]}"
    echo ""

    local exclude_args
    exclude_args=$(build_exclude_args)

    local violations_in_files=()

    for i in "${!TYPOGRAPHIC_CHARS[@]}"; do
        local char="${TYPOGRAPHIC_CHARS[$i]}"
        local char_name="${TYPOGRAPHIC_NAMES[$i]}"

        local grep_cmd="grep -rlF $exclude_args \"$char\" \"$root_dir\" 2>/dev/null || true"
        local matches
        matches=$(eval "$grep_cmd")

        if [[ -n "$matches" ]]; then
            while IFS= read -r filepath; do
                if should_exclude_file "$filepath"; then
                    continue
                fi

                local line_matches
                line_matches=$(grep -nF "$char" "$filepath" 2>/dev/null || true)

                if [[ -n "$line_matches" ]]; then
                    VIOLATIONS_FOUND=1
                    while IFS= read -r line_match; do
                        local line_num
                        line_num=$(echo "$line_match" | cut -d: -f1)
                        local content
                        content=$(echo "$line_match" | cut -d: -f2-)
                        violations_in_files+=("$filepath:$line_num|$char_name|$content")
                    done <<< "$line_matches"
                fi
            done <<< "$matches"
        fi
    done

    # Count total files scanned (approximate)
    local files_scanned
    files_scanned=$(find "$root_dir" -type f \
        ! -path "*/.git/*" \
        ! -path "*/.claude/*" \
        ! -path "*/DerivedData/*" \
        ! -path "*/xcuserdata/*" \
        ! -path "*/.swiftpm/*" \
        ! -path "*/.build/*" \
        ! -path "*/.venv/*" \
        ! -path "*/__pycache__/*" \
        ! -path "*/.mypy_cache/*" \
        ! -path "*/.ruff_cache/*" \
        ! -path "*/.pytest_cache/*" \
        ! -path "*/data/*" \
        ! -name "*.png" ! -name "*.jpg" ! -name "*.ico" \
        ! -name "*.m4a" ! -name "*.aac" ! -name "*.mp3" \
        ! -name "*.woff*" ! -name "*.ttf" \
        ! -name "*.car" ! -name "*.ipa" \
        ! -name "*.pyc" ! -name "*.pyo" \
        ! -name "*.db" ! -name "*.db-wal" ! -name "*.db-shm" \
        ! -name "*.p8" ! -name "*.skill" ! -name "*.md" \
        ! -name "*.lock" ! -name "*.lockb" \
        2>/dev/null | wc -l | tr -d ' ')

    print_info "Files scanned: ~$files_scanned"
    echo ""

    if [[ $VIOLATIONS_FOUND -eq 1 ]]; then
        print_fail "Typographic characters detected in source code!"
        echo ""
        echo -e "${RED}${BOLD}Violations Found:${NC}"

        local prev_file=""
        for violation in "${violations_in_files[@]}"; do
            local filepath
            filepath=$(echo "$violation" | cut -d'|' -f1)
            local file_part
            file_part=$(echo "$filepath" | cut -d: -f1)
            local line_num
            line_num=$(echo "$filepath" | cut -d: -f2)
            local char_name
            char_name=$(echo "$violation" | cut -d'|' -f2)
            local content
            content=$(echo "$violation" | cut -d'|' -f3-)

            if [[ "$file_part" != "$prev_file" ]]; then
                echo ""
                prev_file="$file_part"
            fi
            print_violation "$file_part" "$line_num" "$content" "$char_name"
        done

        echo ""
        echo -e "${YELLOW}${BOLD}Action Required:${NC} Replace typographic characters with ASCII equivalents."
        echo -e "  — (em dash)  → --"
        echo -e "  – (en dash)  → -"
        echo -e "  \xe2\x80\x9c \xe2\x80\x9d (smart quotes) → \""
        echo -e "  \xe2\x80\x98 \xe2\x80\x99 (smart quotes) → '"
        echo ""
        return 1
    else
        print_pass "Typographic Lint: No em dashes or smart quotes detected in source code."
        return 0
    fi
}

# Main entry point
main() {
    local scan_dir="."

    while [[ $# -gt 0 ]]; do
        case $1 in
            --dir)
                scan_dir="$2"
                shift 2
                ;;
            --help|-h)
                echo "Typographic Lint: Em Dash & Smart Quote Detection"
                echo ""
                echo "Usage:"
                echo "  $0                  Scan entire codebase"
                echo "  $0 --dir <path>     Scan specific directory"
                echo ""
                echo "Detects:"
                echo "  — (U+2014)  Em dash"
                echo "  – (U+2013)  En dash"
                echo "  \xe2\x80\x9c (U+201C)  Left double quotation mark"
                echo "  \xe2\x80\x9d (U+201D)  Right double quotation mark"
                echo "  \xe2\x80\x98 (U+2018)  Left single quotation mark"
                echo "  \xe2\x80\x99 (U+2019)  Right single quotation mark"
                echo ""
                echo "Exit Codes:"
                echo "  0  No violations detected"
                echo "  1  Violation(s) detected"
                exit 0
                ;;
            *)
                print_warning "Unknown argument: $1"
                shift
                ;;
        esac
    done

    scan_codebase "$scan_dir"
}

main "$@"
