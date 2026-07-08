---
name: msf-style-audit
description: Periodically re-mine recent RuFaS pull-request review comments, diff the recurring style conventions against the current MSF gate config, and propose concrete rule updates. Use after a batch of merged PRs, when reviewers keep raising something the gate misses, or on a schedule to keep tools/msf_style aligned with what reviewers actually ask for.
---

# MSF style audit

The "second phase" maintenance loop for the style gate. Reviewers' expectations drift and
new conventions appear; this re-runs the original analysis over the latest PRs and keeps
`tools/msf_style/` and `STYLE_RULES.md` in sync with reality. Read-only until it proposes
a diff — it never silently changes config.

## When to run

- After a batch of PRs has merged into `dev-msf`.
- When a reviewer (human or bot) keeps flagging something the gate doesn't catch.
- On a cadence (e.g. monthly) as a scheduled trigger.

## Inputs

- Optional `args`: PR numbers or a date/`updated:>=` window to analyse. Default: all PRs
  updated since the last audit (see the "Last audited" line at the bottom of
  `STYLE_RULES.md`, if present) or the 10 most recently updated PRs.

## Procedure

### 1. Gather the review feedback

Repo: `mon-systeme-fourrager/rufas-myforagesystem`. Use the GitHub MCP tools (load via
`ToolSearch` → `select:mcp__github__pull_request_read,mcp__github__list_pull_requests`).
For each PR in scope, pull **every** feedback channel and paginate to exhaustion:

- `method="get_review_comments"` (inline threads — the richest source)
- `method="get_reviews"` and `method="get_comments"`
- `method="get_commits"` — commit subjects like "fix review comments" reveal what was
  changed in response.

For a large batch, fan this out with the `Workflow` tool: one agent per PR returning a
structured list of `{category, quote, reviewer, file, automatable}`, then a synthesis
agent. (This mirrors how the gate was originally built.)

### 2. Categorise

Bucket each style/quality comment (ignore purely functional/scientific bug comments
unless they reveal a *recurring rule*). Use the existing `T1…T19` themes in
`STYLE_RULES.md`; add a new `T##` only for a genuinely new recurring convention (seen in
≥2 PRs or explicitly declared a standing rule by the human SME). Note for each: is it
**mechanical** (a linter/AST/text check can decide it) or **judgement** (skill only)?

### 3. Diff against the current gate

For every recurring theme, classify:

- **Already covered** — a code exists in `STYLE_RULES.md` and fires correctly.
- **Covered but noisy / wrong** — fires with false positives or misses cases → propose a
  refinement.
- **Not covered, mechanical** → propose a new Ruff rule (check it exists in the installed
  Ruff version) or a new `MSF0xx` AST/text check in `custom_checks.py`.
- **Not covered, judgement** → propose a new bullet in the `/msf-style-review` checklist.

### 4. Guard against legacy noise (mandatory)

Before proposing any new mechanical rule, estimate its false-positive rate on legacy by
running it repo-wide and comparing to the diff-scoped count:

```bash
# Example for a candidate Ruff rule XXX:
ruff check --select XXX --statistics RUFAS/ | head
```

If it lights up legacy heavily, it is still fine — the gate is **diff-aware** — but say so
explicitly, and never propose making it a repo-wide check. Re-confirm it belongs to the
"deliberately NOT enforced" list if it targets an accepted sigil/coefficient/god-object
pattern.

### 5. Propose the update (do not apply silently)

Produce, for the user to approve:

1. A short report: new/changed themes, with 1–2 verbatim quotes each and the PRs.
2. The concrete config diff — edits to `ruff_msf.toml` `select`, new `MSF0xx` functions
   in `custom_checks.py` (**with unit tests** in
   `tests/test_tools/test_msf_style/` covering normal + edge + invalid), the
   `STYLE_RULES.md` table rows, and any `/msf-style-review` checklist bullets.
3. A refreshed "Last audited: <PR range / date>" line at the bottom of `STYLE_RULES.md`.

### 6. On approval — implement and self-verify

Apply the diff, then run the gate's own quality bar before proposing a commit:

```bash
black --line-length 120 tools/ tests/test_tools/
flake8 --max-line-length=120 --max-complexity=10 --extend-ignore=E203,W503 tools/ tests/test_tools/
mypy --strict --follow-imports=silent tools/msf_style/*.py
mypy tests/test_tools/
pytest tests/test_tools/ -q
python -m tools.msf_style.lint_new_code --base origin/dev-msf --mypy   # self-gate must pass
```

Add a `changelog.md` entry and keep the change on the working feature branch. Do **not**
touch the CI-protected input fixtures listed in `.claude/rules/protected-inputs.md`.

## Guardrails

- Never weaken a rule just because the current branch trips it — fix the code or discuss.
- A new mechanical rule needs a passing unit test and a `STYLE_RULES.md` row in the same
  change, or it doesn't ship.
- Keep proposals small and reviewable; batch unrelated rules separately.
