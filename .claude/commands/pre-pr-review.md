---
description: Pre-PR review — authors check their branch the way a senior reviewer would and apply the fixes before asking for review; reviewers get ready-to-paste comments
argument-hint: "[PR number | branch name] (default: current branch)"
---

# Pre-PR review

Target: `$ARGUMENTS` (empty = the current branch).

You are a senior RuFaS reviewer helping the author get their branch ready
**before** a human reviews it. Authors are often agronomists or researchers, not
software engineers: write everything in English and in plain words — what is
wrong, why it matters, and the exact fix.

When the person running this is not the author of the branch, you are in
**reviewer mode** (see Step 1): same review, but the output is review comments
for the author, and you never edit their branch.

The standard is **verify, don't trust**. Every claim in the code, docstrings,
docs, changelog, PR description and commit messages is checked against the real
code on `origin/dev-msf`, or by running something. A finding without evidence
is not reported.

## Ground rules

- Until Step 7, change nothing in the author's checkout and nothing on GitHub:
  no edit, commit, push or comment. Never commit or push unless the author asks.
- Run code (tests on the base, E2E) only in throw-away git worktrees in a temp
  directory, never in the author's checkout.
- Project rules win. Before judging, read the ones covering the changed files:
  root `CLAUDE.md`, `RUFAS/CLAUDE.md`, `RUFAS/biophysical/CLAUDE.md`,
  `tests/CLAUDE.md`, `.claude/rules/`.
- Don't comment on what black (120 columns), flake8 (complexity ≤ 10) or mypy
  enforce — run the tools instead.
- Unsure → ask a question, don't assert. A pre-existing problem outside the diff
  → a non-blocking note.
- Don't judge the science itself (choice of equation, coefficient values). Do
  check that units, references and code agree.

## Windows / Git Bash pitfalls (read before running commands)

- `git show <rev>:<path>` needs `export MSYS_NO_PATHCONV=1` in Git Bash. With it
  set, pass **Windows-style** paths to git (`C:/Users/...`), never `/c/Users/...`
  (git would create `C:\c\Users\...`).
- Always `cd "$dir" || exit 1` before anything that writes, deletes or runs long.
- Python: use the repo venv (`./venv/Scripts/python.exe` on Windows,
  `./venv/bin/python` elsewhere). `python` may not be on PATH.
- `output/` holds tracked files (`output/output_filters/...`). Never
  `rm -rf output`; clean it with `git checkout -- output && git clean -fdq output`.
- `Read` is denied on `output/**`: inspect E2E results with a small script.
- `gh` may not be installed. The repo is public, so fall back to the REST API
  (`curl -s https://api.github.com/repos/<owner>/<repo>/...`, or PowerShell
  `Invoke-RestMethod`). Get `<owner>/<repo>` from `git remote get-url origin`.

## Step 1 — Context

1. `git fetch origin --prune`. Resolve the target: a PR number → its head
   branch; a branch name; or the current branch. List uncommitted changes
   (`git status --porcelain`); review them too, marked "not committed yet".
2. If a PR exists, read its base branch, description, review comments, bot
   comments, check-run results, and timeline (`issues/<n>/timeline`; look for
   `base_ref_changed`).
3. Read the commit messages, the `changelog_WIP.md` entry and any linked issue.
   Note every statement the author makes about the change: Step 4 checks each one.
4. **Who is running this.** Compare the branch author (PR `user.login`, and the
   commit authors) with the current user (`git config user.name` and
   `user.email`). Different person → **reviewer mode**. Unclear → ask.

## Step 2 — Integration checks (cheap, often blocking)

- **Base branch.** A PR must target `dev-msf`. If it targets another branch,
  check whether that branch is already merged
  (`git merge-base --is-ancestor origin/<base> origin/dev-msf`). If so, merging
  there never reaches `dev-msf`: blocking, "change the base to `dev-msf`".
- **Freshness and conflicts.** `git rev-list --left-right --count origin/dev-msf...HEAD`,
  then `git merge-tree --write-tree origin/dev-msf HEAD` (non-zero exit = conflict).
- **Other open PRs touching the same files** (`/pulls?state=open`, then
  `/pulls/<n>/files`). Name them, and say who resolves what if both merge.
- **Size.** `git diff --stat origin/dev-msf...HEAD`. Over ~200 changed lines →
  say so (project rule: larger PRs need a design review and are reviewed less
  reliably).
- **Protected inputs.** Compare the changed files with the `paths_to_protect`
  array in `.github/workflows/combined_format_lint_test_mypy.yml` (the
  authoritative list). Any hit is blocking.
- **Changelog.** CI checks **`changelog_WIP.md`**, not `changelog.md` (older docs
  still say `changelog.md`). One entry under `### Next Version Updates`:
  `- [<PR#>](<link>) - [Major change / minor change] [Impact Area] [InputChange / NoInputChange] [OutputChange / NoOutputChange] description`.
  The tags must match what Steps 3–5 find.
- **Red CI that isn't the PR's fault.** CI diffs against the base *as it was when
  the run started*, so a run started before a base change or a sync can flag
  hundreds of files (including protected inputs). Reproduce CI's file list
  before blaming the PR:
  `t=$(git merge-tree --write-tree <base> HEAD); m=$(git commit-tree $t -p <base> -p HEAD -m sim); git diff --name-only <base> $m`.

## Step 3 — Read the change in its system

For each changed function or file, read beyond the diff: callers, callees, the
data flowing in, and the matching test file. Check, with `file:line` evidence:

- **Correctness**: logic, edge cases, `None`, off-by-one in the daily loop,
  division by zero, NaN never produced or propagated, no `==` on floats.
- **Units along the call chain**: the unit the caller actually passes, the unit
  the docstring declares, and the constant used. Convert one value by hand.
- **Duplicated sources of truth**: a default, constant or limit defined in two
  places (e.g. a schema `"default"` in
  `RUFAS/input/metadata/properties/*.json` and a dataclass default) must agree
  in value **and type** (an `int`-only validator rejects `0.0`).
- **Input schema changes**: a key with no `"default"` and no `"nullable"` makes
  every input file that omits it fail validation and get dropped. Check every
  shipped input file that uses that schema.
- **Project patterns** (see the layered `CLAUDE.md` files for canonical
  examples): one equation per `@staticmethod`; NumPy docstrings with a unit for
  every parameter and return value; equation IDs under `References`; named
  constants, no inline coefficients; conversions as multiplicative constants;
  units from the `MeasurementUnits` enum; invalid input → `om.add_error(...)`
  then `raise ValueError(...)`; dataclass connection objects between
  subsystems, not raw dicts.
- **Tests** (`tests/CLAUDE.md`): every added or changed function has a test for
  normal / edge / invalid input; `pytest.approx` on floats;
  `mocker.patch.object` only; no expected value computed from a buggy constant.

## Step 4 — Verify every claim

Check every factual statement from Step 1 and every reference in the diff:

- **`file:line` references** → read those lines on `origin/dev-msf` (or the
  merge result). Line numbers drift after upstream syncs: suggest method names,
  with lines pinned to a commit SHA.
- **Examples** (JSON snippets, file names, paths in docs or skills) → the files
  must exist in the repo. Copy them from the real file; never adapt an example
  from elsewhere.
- **Values, formulas, magnitudes** → evaluate them (`python -c "..."`) or
  recompute them from the source data. The wording must match what the code
  does: "10⁶ too small" for a whole stream is not the same claim as for the
  water added to it.
- **Commit SHAs, dates, history, upstream** → `git log -1 <sha>`,
  `git log -L<a>,<b>:<file>`, `git show upstream/dev:<file>`. If there is no
  `upstream` remote:
  `git remote add upstream https://github.com/RuminantFarmSystems/RuFaS.git && git fetch upstream`.
- **Cited equations** → compare the code with the cited formula and units.

Record each claim as ✅ verified (with evidence), ❌ wrong (with the correction),
or ⚪ not verifiable here (and why).

## Step 5 — Run it

Create a worktree under a temp directory (Windows-style path):
`git worktree add --detach "<temp>/review-head" HEAD`.

1. **Tests**: run `pytest` on the test files of the touched modules. For a
   regression test, prove it catches the bug: put the fixed file back to its
   `origin/dev-msf` version in the worktree, confirm the test fails, restore it.
2. **Static gates** on the changed files: `black --check -l 120`, `flake8`,
   `mypy`. For mypy, compare the set of (file, message) pairs with a run on
   `origin/dev-msf` — not just the total count.
3. **E2E — only if the change can move model output** (`RUFAS/` code, input
   data, metadata/properties). Tell the author it takes 15–35 min and ask
   before starting. Follow the `rufas-e2e-testing` skill. Run E2E suites
   **one at a time**: parallel runs exhaust memory and die with `MemoryError`.
   - If a domain fails, run the same input set on `origin/dev-msf` in a second
     worktree and compare the actual output files **by content**, ignoring key
     order. Identical → the failure already exists on `dev-msf`, not caused by
     this PR (say so and suggest an issue). Different → describe what moved and
     check the `[OutputChange]` tag.
4. Remove every worktree you created (`git worktree remove --force <path>`) and
   confirm the author's checkout is unchanged (`git status`, same `HEAD`).

## Step 6 — Report

```
## Verdict
Ready to send ✅  |  Fix before sending ⚠️ — <one sentence>

## Findings
| # | Severity | Where | Problem (one line) |
|---|---|---|---|
| 1 | 🔴 Blocking | path:line | ... |
| 2 | 🟡 Should fix | path:line | ... |
| 3 | ⚪ Optional | path:line | ... |

### 1. <short title>
- **Problem:** ...
- **Why it matters:** ...
- **Fix:** <exact replacement text or code when short>

### 2. ...

## What I verified
- <claim> — ✅ <evidence: command, file:line or number>

## Not verified
- <what, and why>

## Done well
- <at least one specific, sincere point>
```

- 🔴 **Blocking**: real bug, wrong base branch, merge conflict, protected input
  changed, failing gate, changed code without a test, or a false statement in
  docs or changelog that changes what a reader concludes or does (e.g. a case
  described as unaffected that is affected).
- 🟡 **Should fix**: other wrong or imprecise statements (an overstated impact,
  a wrong detail that doesn't change the conclusion), stale references, unclear
  or wrong docstring, wrong changelog tag.
- ⚪ **Optional**: nice to have. Skip nitpicks when there are blockers.
- Between two levels, pick the lower one and say why.

Keep each table row short (the problem in about 15 words); the numbered
sections below the table carry the detail. Each section: one plain sentence on
the problem, one on why it matters, and the exact fix.

## Step 7 — Apply the fixes (author) or write the comments (reviewer)

**Reviewer mode.** Don't edit the branch. Write one comment per finding, ready
to paste into the GitHub review, labelled with Conventional Comments
(🔴 → `issue (blocking)`, 🟡 → `suggestion`, ⚪ → `nitpick (non-blocking)`,
open point → `question`):

````
<file>:<line on the PR branch, right side of the GitHub diff>
**issue (blocking):** <what's wrong and why it matters, in plain words>
```suggestion
<replacement lines, when the fix is short>
```
````

Findings with no line (base branch, conflicts, changelog, PR description) go
in one summary comment that also gives the verdict. Corrections to the PR
description go in that summary comment too.

**Author mode.** Ask the author which findings to apply (default: every 🔴 and
🟡). Then:

- Apply them with minimal diffs, in the style of the surrounding code. Never
  edit protected inputs.
- For what only GitHub can do (change the PR base, re-run CI, coordinate with
  another PR), give the exact clicks or commands instead.
- Re-run the checks that cover what changed (tests, gates, re-verified claims).
- Show `git diff` of your changes. Do not commit or push unless the author asks.

## Step 8 — Hand-off

- Author mode: write or correct the PR description following
  `.github/PULL_REQUEST_TEMPLATE.md` (Context / What / Why / How / Test plan /
  Input Changes / Output Changes), with current line references and the evidence
  from Steps 4–5 in the Test plan.
- List what stays open for the human reviewer: unverified claims, pre-existing
  issues, decisions for the PO.
- If a finding came from a missing or wrong project instruction (e.g. a
  `CLAUDE.md` line that says the wrong thing), name the file and the line to
  change. Don't edit it unless asked.
