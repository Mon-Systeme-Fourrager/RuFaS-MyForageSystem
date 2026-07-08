---
name: msf-style-review
description: Review a RuFaS branch diff for the judgement-level style conventions the deterministic MSF gate cannot decide (enum-over-string, docstring content, DRY, scientific references, test quality, diff-minimalism). Use before committing or opening a PR into dev-msf, after running the automated gate.
---

# MSF style review

The deterministic gate (`tools/msf_style/`, run by the hook and CI) catches the
mechanical conventions. This skill covers the **judgement** rules that recur in RuFaS
reviews but no linter can decide. Run it on your own diff **before** requesting human
review, so `jrobichaud`/CodeRabbit don't have to.

## Scope — new code only

Review only what the branch adds or changes versus `origin/dev-msf`. Never ask the
author to "fix" legacy lines the diff merely touches — diff-minimalism (T14) is itself
one of the rules below.

## Procedure

1. **Run the deterministic gate first** and let it handle the mechanical findings:

   ```bash
   python -m tools.msf_style.lint_new_code --base origin/dev-msf --mypy
   ```

   Do not re-report anything the gate already flagged. Your job is only what it cannot
   see. If the gate exits `1`, tell the author to clear the findings first. If it exits
   `2`, no base ref could be resolved — tell them to fix the base-ref setup or pass
   `--base` explicitly before you review.

2. **Get the diff** to review:

   ```bash
   git diff origin/dev-msf...HEAD
   ```

3. **Check each judgement rule below** against the added/changed lines. For every
   finding, cite `file:line`, quote the offending code, and give the concrete fix.

4. **Report** grouped by severity: **blocking** (correctness / a reviewer would reject),
   then **should-fix**, then **nits**. If nothing applies, say so plainly.

## Judgement checklist (source: `tools/msf_style/STYLE_RULES.md`)

- **Enum-over-string (T4 — the human SME's #1 theme).** Any raw string literal that is
  really a domain value (sex, animal type, post-weaning destination, reproduction
  protocol, event name) must use the existing enum, in production **and tests**. Flag
  `x == "sell"`, `sex="male"`, dict keys that shadow an enum. `Enum == "str"` is always
  `False` — a real bug source.
- **Scientific traceability (T1 semantic).** A constant moved to `*_constants.py` must
  carry the correct NRC 2016 table/equation reference in its name or a `why` comment. A
  test benchmark value must be physiologically meaningful (e.g. mid-gestation `DP≈150`,
  not a placeholder `30`). Verify the coefficient is used correctly (intercept vs slope,
  right equation variant).
- **Docstring content (T3 semantic).** Beyond presence (the gate checks that): does the
  NumPy docstring describe real behaviour, and do `Parameters`/`Returns` match the actual
  signature? Flag docstring↔signature drift and wrong ratio directions
  ("cows-per-bull" vs "bulls-per-cow").
- **Config validation semantics (T2 logic).** Validate the *merged* config, not the raw
  dict; validate only fields that are present; reject lossy coercion (raise on `25.9`
  rather than silently truncating). The gate catches the `or`/`int(None)` mechanics; you
  judge the intent.
- **Test quality (T13).** Tests must assert **behaviour**, not just return type or
  `call_count`. A patched mock must be asserted. Data must be seeded so the assertion
  isn't vacuously true. Does each test actually exercise what its docstring claims?
- **Mocking judgement (T5).** Prefer patching a real instance method over rewiring a
  whole collaborator into `MagicMock`; prefer a minimal typed stub when only 1–2
  attributes are read. (The gate only catches the blatant class-attribute assignment.)
- **DRY (T17).** Logic duplicated verbatim between twin methods (beef/feedlot/dairy), a
  recomputed expression (`sum(ration.values())`), or identical fixtures across files
  belong in a shared helper / `conftest.py`. Judge where the seam should be.
- **Guard symmetry & parallel cohorts.** When adding a branch to one of several twin
  paths, check the sibling paths have the matching guard, and parallel cohort lists stay
  in sync.
- **Deterministic defaults.** A missing field must not fall back to `random()` in a way
  that can produce a biologically invalid state (e.g. random `sex`). Any real `random()`
  use needs a `why` comment and a seed strategy.
- **Onion architecture / imports (T7 design).** Judge where new code should live and
  whether an in-function import is hiding a real circular-dependency / layering problem
  rather than being a legitimate cycle break.
- **Output-unit semantics.** A reported quantity must carry the right unit
  (`times_calved` is `UNITLESS`, not `ANIMALS`).
- **Diff-minimalism (T14).** Flag reformatting of untouched RuFaS code, unrelated
  churn, or temp/scaffolding files added to the PR.

## Output contract

Actionable findings only. For each: `severity — file:line — problem — fix`. End with a
one-line verdict: **ready for human review** or **address blocking items first**.
