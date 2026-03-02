#!/usr/bin/env bash
# run-hooks.sh
# Pre-Commit Quality Gate Runner
# Repository: Exhibit A (iOS SwiftUI + FastAPI Backend)
#
# Runs all pre-commit hooks with report-style output.
# Suitable for local development and CI pipelines.
#
# Usage:
#   ./scripts/run-hooks.sh              # Run all hooks on all files
#   ./scripts/run-hooks.sh --staged     # Run only on staged files
#   ./scripts/run-hooks.sh --hook <id>  # Run a specific hook

set -uo pipefail

# ── ANSI escape codes ─────────────────────────────────────────────
BOLD='\033[1m'
DIM='\033[2m'
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

WIDTH=64
SEPARATOR="${BOLD}$(printf '━%.0s' $(seq 1 $WIDTH))${NC}"

# ── Argument parsing ──────────────────────────────────────────────
MODE="--all-files"
HOOK_ID=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --staged)
            MODE=""
            shift
            ;;
        --hook)
            HOOK_ID="$2"
            shift 2
            ;;
        --help|-h)
            echo "Pre-Commit Quality Gate Runner"
            echo ""
            echo "Usage:"
            echo "  $0                  Run all hooks on all files"
            echo "  $0 --staged         Run hooks on staged files only"
            echo "  $0 --hook <id>      Run a specific hook by ID"
            echo ""
            echo "Hook IDs:"
            echo "  protocol-zero       Protocol Zero attribution scan"
            echo "  check-em-dashes     Typographic lint (em dashes, smart quotes)"
            echo "  no-db-artifacts     Block database file commits"
            echo "  no-env-files        Block .env file commits"
            echo "  no-credential-files Block credential file commits"
            echo "  ruff-check          Python linter"
            echo "  ruff-format         Python formatter"
            echo "  gitleaks            Secret scanning"
            echo "  (any pre-commit hook ID from .pre-commit-config.yaml)"
            exit 0
            ;;
        *)
            echo -e "${YELLOW}[WARN]${NC} Unknown argument: $1"
            shift
            ;;
    esac
done

# ── Pre-flight checks ────────────────────────────────────────────
if ! command -v pre-commit &> /dev/null; then
    echo -e "${RED}${BOLD}[ERROR]${NC} pre-commit is not installed."
    echo "  Install: brew install pre-commit"
    exit 1
fi

if [[ ! -d ".git" ]]; then
    echo -e "${RED}${BOLD}[ERROR]${NC} Not a git repository."
    echo "  Run: git init"
    exit 1
fi

if [[ ! -f ".pre-commit-config.yaml" ]]; then
    echo -e "${RED}${BOLD}[ERROR]${NC} .pre-commit-config.yaml not found."
    exit 1
fi

# ── Header ────────────────────────────────────────────────────────
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo ""
echo -e "$SEPARATOR"
echo -e "${BOLD}  Exhibit A -- Pre-Commit Quality Gate${NC}"
echo -e "${DIM}  $TIMESTAMP${NC}"
if [[ -n "$HOOK_ID" ]]; then
    echo -e "${DIM}  Hook: $HOOK_ID${NC}"
elif [[ "$MODE" == "--all-files" ]]; then
    echo -e "${DIM}  Scope: all files${NC}"
else
    echo -e "${DIM}  Scope: staged files${NC}"
fi
echo -e "$SEPARATOR"
echo ""

# ── Execute pre-commit ────────────────────────────────────────────
# Scope to pre-commit stage to avoid duplicate output from commit-msg hooks.
# Commit-msg validation runs automatically during git commit.
CMD="pre-commit run --hook-stage pre-commit"
if [[ -n "$HOOK_ID" ]]; then
    CMD="$CMD $HOOK_ID $MODE"
elif [[ -n "$MODE" ]]; then
    CMD="$CMD $MODE"
fi

TMPFILE=$(mktemp)
trap 'rm -f "$TMPFILE"' EXIT

eval "$CMD" 2>&1 | tee "$TMPFILE"
EXIT_CODE=${PIPESTATUS[0]}

# ── Parse results ─────────────────────────────────────────────────
PASSED=$(grep -c '\.\.\..*Passed$' "$TMPFILE" 2>/dev/null || true)
FAILED=$(grep -c '\.\.\..*Failed$' "$TMPFILE" 2>/dev/null || true)
SKIPPED=$(grep -c '\.\.\..*Skipped$' "$TMPFILE" 2>/dev/null || true)
PASSED=${PASSED:-0}
FAILED=${FAILED:-0}
SKIPPED=${SKIPPED:-0}
TOTAL=$((PASSED + FAILED + SKIPPED))

# ── Footer ────────────────────────────────────────────────────────
echo ""
echo -e "$SEPARATOR"
echo -e "${BOLD}  Summary${NC}"
echo ""

SUMMARY="  "
if [[ $PASSED -gt 0 ]]; then
    SUMMARY="${SUMMARY}${GREEN}${BOLD}${PASSED}${NC} ${GREEN}passed${NC}  "
fi
if [[ $FAILED -gt 0 ]]; then
    SUMMARY="${SUMMARY}${RED}${BOLD}${FAILED}${NC} ${RED}failed${NC}  "
fi
if [[ $SKIPPED -gt 0 ]]; then
    SUMMARY="${SUMMARY}${DIM}${SKIPPED} skipped${NC}  "
fi
SUMMARY="${SUMMARY}${DIM}(${TOTAL} total)${NC}"
echo -e "$SUMMARY"
echo ""

if [[ $EXIT_CODE -eq 0 ]]; then
    echo -e "  ${GREEN}${BOLD}RESULT: ALL CHECKS PASSED${NC}"
else
    echo -e "  ${RED}${BOLD}RESULT: CHECKS FAILED${NC}"
    if [[ $FAILED -gt 0 ]]; then
        FAILED_NAMES=$(grep '\.\.\..*Failed$' "$TMPFILE" | sed 's/\.\.\..*Failed$//' | sed 's/^/    - /')
        echo -e "${DIM}${FAILED_NAMES}${NC}"
    fi
fi

echo -e "$SEPARATOR"
echo ""

exit "$EXIT_CODE"
