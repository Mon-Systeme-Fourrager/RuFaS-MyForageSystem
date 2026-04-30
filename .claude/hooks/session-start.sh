#!/bin/bash
# SessionStart hook: ensure OpenSpec CLI is installed in remote sandboxes so
# /opsx:* slash commands (committed in .claude/commands/opsx/) can invoke it.
# Idempotent, non-blocking, synchronous (see CLAUDE.md § Gotchas).

set -euo pipefail

# Derive project root from this script's location — robust even when
# CLAUDE_PROJECT_DIR is not exported (set -u would treat it as unset).
# BASH_SOURCE[0]:-$0 : fallback to $0 when sourced rather than executed.
# .claude/hooks/ sits exactly two levels below the project root → two .. hops.
_HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
_PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "${_HOOK_DIR}/../.." && pwd)}"

# Inject Graphify dependency graph into session context — BEFORE all guards so
# it runs in every context (local, remote cold, remote warm).
# Adjust GRAPHIFY_TRUNCATE_LINES after the first run once the report structure
# is known (verify that the summary fits within this line count).
readonly GRAPHIFY_TRUNCATE_LINES=160

if [ -f "${_PROJECT_DIR}/graphify-out/GRAPH_REPORT.md" ]; then
  report="${_PROJECT_DIR}/graphify-out/GRAPH_REPORT.md"
  size=$(wc -c < "$report" 2>/dev/null) || size=0  # || size=0 : TOCTOU guard — file removed between -f and wc
  if [ "$size" -lt 32768 ]; then
    cat "$report" || true   # || true : TOCTOU — file removed between wc and cat
  else
    head -n "${GRAPHIFY_TRUNCATE_LINES}" "$report" || true
    echo "[Graphify] Report truncated — full report at graphify-out/GRAPH_REPORT.md"
  fi
fi

# Remote-only (Claude Code web). Desktop/CLI users install manually.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Fast-path: already installed (cached from a previous container run).
if command -v openspec >/dev/null 2>&1; then
  exit 0
fi

# npm must be available. If not, surface on stderr and exit cleanly.
if ! command -v npm >/dev/null 2>&1; then
  echo "session-start: npm not on PATH; skipping OpenSpec install" >&2
  exit 0
fi

echo "session-start: installing @fission-ai/openspec..." >&2
if ! npm install -g @fission-ai/openspec@latest >&2; then
  echo "session-start: failed to install @fission-ai/openspec (non-fatal)" >&2
  exit 0
fi

# Post-install sanity check. Tolerate binary installed in a prefix not on PATH
# — the hook must not block session start in that edge case.
openspec --version >&2 || echo "session-start: openspec installed but not on PATH (non-fatal)" >&2
exit 0
