#!/usr/bin/env bash
# PostToolUse hook: run the diff-aware MSF style gate on the file Claude just edited.
#
# Only the lines the branch adds/changes versus its integration branch are judged, so
# touching legacy code never triggers a wall of pre-existing findings. Ruff + the custom
# AST/text checks run (mypy is skipped here for speed; the CI gate runs it).
#
# Exit codes fed back to Claude Code:
#   0  no new-code violations (or nothing to compare / non-Python edit) -> silent
#   2  new-code violations found and MSF_STYLE_HOOK_BLOCKING=1 (default) -> Claude must fix
# Set MSF_STYLE_HOOK_BLOCKING=0 to make the hook advisory (prints, never blocks).

set -euo pipefail

ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"

payload="$(cat)"
file_path="$(
  printf '%s' "$payload" | python3 -c \
    'import sys, json; print(json.load(sys.stdin).get("tool_input", {}).get("file_path", ""))' 2>/dev/null || true
)"
[ -z "$file_path" ] && exit 0

rel="${file_path#"$ROOT"/}"
case "$rel" in
  *.py | *changelog.md) ;;
  *) exit 0 ;;
esac

cd "$ROOT"
py="$(command -v python3.12 || command -v python3 || true)"
[ -z "$py" ] && exit 0

set +e
out="$("$py" -m tools.msf_style.lint_new_code --paths "$rel" --no-mypy --format human 2>&1)"
code=$?
set -e

if [ "$code" -eq 1 ]; then
  printf '%s\n' "$out" >&2
  if [ "${MSF_STYLE_HOOK_BLOCKING:-1}" = "1" ]; then
    exit 2
  fi
fi
exit 0
