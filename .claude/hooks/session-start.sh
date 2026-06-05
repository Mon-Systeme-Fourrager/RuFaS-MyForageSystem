#!/bin/bash
# SessionStart hook: inject the graphify dependency-graph report into context so
# Claude knows the model's god nodes + community structure before searching.
# Idempotent, non-blocking. Graph artifacts are produced by `graphify update .`
# (locally) or by .github/workflows/update-graphify.yml (CI).

set -euo pipefail

# Derive project root from this script's location (robust without CLAUDE_PROJECT_DIR).
_HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
_PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "${_HOOK_DIR}/../.." && pwd)}"

readonly GRAPHIFY_TRUNCATE_LINES=160

report="${_PROJECT_DIR}/graphify-out/GRAPH_REPORT.md"
if [ -f "$report" ]; then
  size=$(wc -c < "$report" 2>/dev/null) || size=0   # || size=0 : TOCTOU guard
  if [ "$size" -lt 32768 ]; then
    cat "$report" || true
  else
    head -n "${GRAPHIFY_TRUNCATE_LINES}" "$report" || true
    echo "[graphify] Report truncated — full report at graphify-out/GRAPH_REPORT.md"
  fi
fi

exit 0
