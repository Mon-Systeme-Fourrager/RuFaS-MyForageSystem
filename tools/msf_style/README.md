# MSF style gate

A **diff-aware** style gate that enforces the RuFaS review conventions on new/changed
code only. It exists because reviewers request the same handful of conventions on every
PR, while the legacy code base violates the stricter of those same rules on purpose
(scientific sigils, published coefficients, god-object calculators, `dict[str, Any]` at
JSON boundaries). A repo-wide linter would drown the signal — so, like the existing mypy
error-count ratchet, this judges only the lines a branch adds or changes versus
`origin/dev-msf` (plus whole new files).

See [`STYLE_RULES.md`](./STYLE_RULES.md) for the full rule catalogue, the codes, and
which past review comment each rule came from.

## What it runs

1. **Ruff** with a narrow, dedicated config ([`ruff_msf.toml`](./ruff_msf.toml)).
2. **Custom AST/text checks** (`custom_checks.py`) for project rules no stock linter
   covers — `MSF001` magic coefficients, `MSF010/011` None-unsafe config parsing,
   `MSF020` test-mock leakage, `MSF030` mutable-classvar returns, `MSF040/041/042`.
3. **Changelog format** checks (`changelog_check.py`) — `MSF050/051/052`.
4. **Per-file `mypy --strict`** (opt-in `--mypy`) closing the count-ratchet hole where
   new untyped code slips into an already-error-carrying module.

Findings are filtered to the new-code perimeter before display, so legacy is never
flagged.

## Usage

```bash
# Gate the whole branch against its base (auto-detects dev-msf / dev):
python -m tools.msf_style.lint_new_code

# Include the per-file mypy pass (what CI runs):
python -m tools.msf_style.lint_new_code --mypy

# Compare against an explicit ref, emit GitHub annotations:
python -m tools.msf_style.lint_new_code --base origin/dev-msf --format github

# Fast single-file check (what the editor hook runs):
python -m tools.msf_style.lint_new_code --paths RUFAS/biophysical/animal/pen.py --no-mypy
```

Exit codes: `0` clean, `1` in-scope violations, `2` no base ref to compare against.

## Where it runs

- **In-session hook** — `.claude/hooks/msf-style-check.sh` (PostToolUse on Edit/Write)
  checks each file Claude edits and blocks with the findings (set
  `MSF_STYLE_HOOK_BLOCKING=0` to make it advisory).
- **CI gate** — `.github/workflows/msf_style_gate.yml` fails a PR into `dev-msf`/`dev`
  when the diff violates a rule. Kept in its own workflow so upstream syncs don't
  conflict.
- **Review skill** — `/msf-style-review` covers the judgement rules a linter cannot
  decide (enum-over-string, docstring content, DRY, scientific references).

## Maintaining the rules

Run `/msf-style-audit` periodically (e.g. after a batch of PRs) to re-mine recent review
comments, diff them against `STYLE_RULES.md`, and propose config updates. The audit is
the "second phase" process: it keeps the gate aligned with what reviewers actually ask
for over time.

## Design notes

- **Diff-aware, not baseline** — matches the mypy ratchet mental model; no large baseline
  file to maintain or to conflict on upstream syncs.
- **Ruff complements flake8** — it does not replace the existing flake8 gate; the two run
  side by side. Ruff supplies rules flake8 lacks (no plugins are installed there).
- **Untracked files included** — the diff scope also picks up not-yet-staged new files so
  the hook catches them before they are committed.
- **Not a runtime dependency** — `tools/` is outside the model package and outside the CI
  mypy scope; it ships no import into `RUFAS/`.
