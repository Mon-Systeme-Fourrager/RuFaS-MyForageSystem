---
description: Execute an approved plan — per-task TDD, spec + code quality review, plan cleanup, PR
argument-hint:
  [
    empty if a plan was approved in this session,
    OR openspec:<change-name>,
    OR PLAN_<slug>.md (explicit plan file path),
  ]
allowed-tools: Read, Grep, Glob, Agent, Bash(git:*), Bash(gh:*), Bash(python:*), Bash(python3:*), Bash(pytest:*), Bash(flake8:*), Bash(black:*), Bash(coverage:*), Bash(graphify:*), TodoWrite
---

$ARGUMENTS

## Precondition

Runs **only after** a `/challenge-plan` returned ✅ **APPROVED** or ⚠️
**APPROVED WITH RESERVATIONS** accepted by the user. If the last verdict is ❌,
missing, or stale (the plan changed since the last `/challenge-plan`), refuse and
ask the user to pass through `/refine-plan` + `/challenge-plan` first.

## Plan resolution

Two formats. Precedence: explicit file path > glob > session context (incl.
`openspec:<name>`). Plans are always passed **by path** to keep `Agent`
tool-call arguments small (no inline plan body).

### OpenSpec mode

If `$ARGUMENTS` matches `openspec:<name>`, OR is empty and the session shows an
approved OpenSpec change → resolve:
`openspec/changes/<name>/proposal.md` (what & why), `design.md` (how),
`tasks.md` (task list, source of truth). Store `mode: openspec`. Tasks are the
`- [ ]`/`- [x]` checkboxes in `tasks.md`; mark complete by editing the box.
**No plan-file cleanup** at the end — OpenSpec artifacts are managed by
`/opsx:archive`.

### PLAN_*.md mode

1. `$ARGUMENTS` is a file path → that file.
2. Else `Glob PLAN_*.md` at repo root. One match for the session topic → use it;
   several → list and ask which.
3. Else retrieve the last approved plan path from the session.
4. Else ask for the path. Do **not** embed a pasted plan — every subagent
   dispatch references it by path.

The plan must be the self-sufficient version (BEFORE/AFTER, REUSES, YAGNI CHECK,
expected RED/GREEN tests). Remember the exact `PLAN_<slug>.md` filename — it is
passed to every dispatch and removed in cleanup (§4.3); keep it on disk,
unchanged, for the whole run.

## Workflow (non-negotiable)

### 1. Pre-flight: verify the plan file and the active branch

**OpenSpec mode:** `Read` all three artifacts. If any is missing/empty → refuse
and tell the user to run `/opsx:propose` then `/challenge-plan openspec:<name>`.

**PLAN mode:** `Read` `PLAN_<slug>.md`. Refuse if it errors (run `/diagnose`),
or is empty / doesn't start with `## Plan —` / has no `📝`/`✨`/`🗑️`/`🧪`
marker / has no `REUSES` section (run `/diagnose` to regenerate).

**Branch guard.** Run `git rev-parse --abbrev-ref HEAD`. If the branch is
`dev-msf`, `dev`, or `main_msf` (integration/protected) → refuse: "Switch to a
feature branch first." Work proceeds on the repo's active feature branch;
`/apply-plan` does not create a worktree or branch.

**Do not proceed** if any check fails.

### 2.0 Group detection and dossier pre-pass (one-shot, PLAN mode only)

OpenSpec mode skips §2.0 (print "§2.0 skipped (OpenSpec mode)") — `tasks.md`
carries no `EDITS`/`READS`/`PARALLEL_GROUP` fields.

1. `Read` `PLAN_<slug>.md`, collect each task's `EDITS`, `READS`,
   `PARALLEL_GROUP`. Tasks without `EDITS` → log one line and treat as
   individual.
2. Re-verify `/refine-plan`'s guarantees: disjoint `EDITS` within each group; no
   pivot file inside a tagged task (`RUFAS/general_constants.py`,
   `RUFAS/input_manager.py`, `RUFAS/output_manager.py`,
   `RUFAS/data_validator.py`, `RUFAS/simulation_engine.py`,
   `RUFAS/task_manager.py`, any `__init__.py`, `pyproject.toml`, `changelog.md`).
   On violation, strip the `PARALLEL_GROUP` tag (log one line) and process
   individually. Group of N < 2 after stripping dissolves to individual tasks.
3. For each valid group of N ≥ 2, dispatch **N read-only investigator subagents
   in parallel** (single message). Each gets: the plan path + its task id +
   RuFaS constraints (read-only subset). Directive: "Read the plan, locate the
   task, build a dossier ≤ 200 lines: exact line ranges to edit (BEFORE snippets
   verbatim, omit for new-file `✨`), resolved REUSES symbol paths, a one-line
   'no surprise' verdict on whether the codebase still matches the plan. Do not
   write code, do not edit files." Tool allowlist (prompt-level): `Read`,
   `Grep`, `Glob`, `graphify` only.
4. Collect dossiers keyed by task id. When the implementer is dispatched (§2),
   prepend its dossier.
5. **Dossier invalidation.** Before dispatching the implementer for task K,
   iterate over every task J already done in `TodoWrite`. If `J.EDITS ∩
   (K.READS ∪ K.EDITS)` is non-empty → discard K's cached dossier and dispatch a
   fresh investigator for K only. Else reuse.

Implementer dispatches under §2 remain strictly **sequential**.

### 2. Task orchestration

Invoke `superpowers:subagent-driven-development`. For each task:

1. **Identify the next pending task.** OpenSpec: next `- [ ]` in `tasks.md`
   (context from all three artifacts, by path). PLAN: enumerate from the plan
   file, pick a stable id (header text or ordinal). Every dispatch references the
   plan **by path**.
2. **Dispatch an implementer subagent** with the plan path(s) + task id and:
   - "Read the plan with the Read tool, locate the identified task, treat its
     body as the full spec verbatim."
   - Relevant files / patterns to reuse (cite `REUSES:` as hints; the subagent
     reads them).
   - RuFaS constraints (below).
   - Follow `superpowers:test-driven-development` (RED → GREEN → REFACTOR; watch
     the test fail before writing code).
3. **Dispatch both reviewer subagents in parallel** (single message):
   - **Spec-compliance reviewer** (same path + task id): implementation matches
     the plan exactly (no missing requirement, no extras).
   - **Code-quality reviewer** (same path + task id) using
     `superpowers:requesting-code-review`, cross-referencing `REUSES:` and YAGNI.
4. Collect both, loop corrections until both ✅. Never advance with an open issue.
5. Mark complete: OpenSpec → edit `- [ ]`→`- [x]` in `tasks.md` (+ TodoWrite);
   PLAN → TodoWrite only. Commit (atomic per task — stage files explicitly by
   name; in OpenSpec mode also stage the updated `tasks.md`; never `--no-verify`).

### 3. Per-task verification (evidence, not claims)

After each task, run the three checks **in parallel** (single Bash call), each
exit code captured:

```bash
python -m mypy . & PID_TC=$!
flake8 . & PID_LINT=$!
pytest <affected test files> & PID_PT=$!
TC=0; LINT=0; PT=0
wait $PID_TC || TC=$?
wait $PID_LINT || LINT=$?
wait $PID_PT || PT=$?
[ $TC -eq 0 ] && [ $LINT -eq 0 ] && [ $PT -eq 0 ]
```

All three must exit 0 before proceeding.

- mypy is strict and CI ratchets the error count vs `dev` — do not add errors.
- Black: run `black <changed files>` (line-length 120) before committing; don't
  hand-format against it.
- If the change could alter numeric model output, run the relevant e2e/regression
  test and confirm the output diff is intended.

### 4. Final review and completion

1. Dispatch a **final code-quality reviewer subagent** over the full diff against
   the base branch (holistic).
2. Run the full suite in parallel (single Bash call):

```bash
python -m mypy . & PID_TC=$!
flake8 . & PID_LINT=$!
pytest & PID_PT=$!
TC=0; LINT=0; PT=0
wait $PID_TC || TC=$?; wait $PID_LINT || LINT=$?; wait $PID_PT || PT=$?
[ $TC -eq 0 ] && [ $LINT -eq 0 ] && [ $PT -eq 0 ]
```

3. **`changelog.md` — mandatory.** Add an entry under `### Next Version Updates`
   (`- [PR#](url) - [minor change/Major change] [Area] [In/NoInputChange]
   [In/NoOutputChange] description`). CI fails the PR without it. Use `TBD` for
   the PR number, fill it after the PR is created.
4. **Cleanup the plan file (PLAN mode only) — automatic, no confirmation.**
   `PLAN_<slug>.md` is a work artifact and MUST NOT appear in the PR diff:

```bash
if git ls-files --error-unmatch PLAN_<slug>.md >/dev/null 2>&1; then
  git rm -f PLAN_<slug>.md
  git commit -m "chore: remove plan file after implementation"   # hooks run
else
  rm PLAN_<slug>.md   # untracked — nothing in the PR diff
fi
```

   OpenSpec mode: no cleanup (artifacts archived by `/opsx:archive` post-merge).
5. Invoke `superpowers:finishing-a-development-branch`. The output MUST be a
   **pull request** into `dev-msf` (the fork's integration branch), not a direct
   merge.
6. **PR creation requires explicit user confirmation** — present the proposed
   title + body, then wait. Use the **`gh` CLI**
   (`gh pr create --base dev-msf ...`). After creation, fill the real PR number
   into the changelog entry, commit, push.
7. After the PR exists, watch CI with `gh pr checks <num> --watch` (or poll
   `gh pr checks <num>`).

### 5. Post-PR review cycle

#### 5.1 CI failure
Fetch failing logs (`gh run view <run-id> --log-failed`). Diagnose. If clearly
caused by the PR (failing test, flake8, mypy) → fix, run the §3 parallel suite,
commit, push. If it needs an architectural decision or out-of-scope change →
**stop and ask** the user.

#### 5.2 Review comment triage (batch first)
Invoke `superpowers:receiving-code-review`. Classify every comment: ✅ Valid
(correct, in scope) / ❓ Ambiguous / 🔲 Out-of-scope / ❌ Invalid. Send the user
**one grouped message** listing only ❓ and 🔲 with a concrete question each.
Don't ask about ✅/❌. Wait for answers.

#### 5.3 Implementation
Implement all ✅ and user-approved ❓/🔲. Commit each fix atomically (hooks run;
never `--no-verify`). Run the §3 parallel suite once for the full batch. Push.

#### 5.4 PR thread replies
Reply in each thread (`gh pr comment` / review reply): ✅ Applied → what & why;
❌ Rejected → the technical reason; 🔲 Deferred → out of scope, trackable
separately.

#### 5.5 Iterate
Repeat 5.1–5.4 per new CI/review event until all checks pass and no unresolved
threads remain.

#### 5.6 Merge-ready signal
Print exactly:
> ✅ PR ready to merge: `<PR URL>`
> All CI checks pass. No unresolved review threads.
> Merge via the GitHub interface when ready.

**Never merge automatically** — the user merges via GitHub.

## RuFaS constraints (injected into every subagent prompt)

- **Python tooling**: `pip`, `python -m mypy .`, `flake8 .`, `pytest`, `black .`
  (line-length 120). Never Bun/npm/npx/vitest.
- **Grep tool, not `grep` in Bash** — main agent and every subagent.
- **Full type hints everywhere** — mypy strict rejects untyped defs; do not add
  errors vs `dev`.
- **flake8 complexity ≤ 10** — refactor rather than suppress.
- **Tests mirror `RUFAS/`** under `tests/` (`test_<module>.py`, `test_<pkg>/`);
  `pytest-mock`, fixtures, `freezegun` for time. See `tests/CLAUDE.md`.
- **Constants over magic numbers** — use the relevant `*_constants.py`.
- **Protected inputs** — never edit `example_*`/`no_*` fixtures
  (`.claude/rules/protected-inputs.md`).
- **`changelog.md` mandatory** on the PR.
- **Pre-commit hooks respected** — never `--no-verify`. Fix the root cause.
- **Commit hygiene** — never `git add .`/`git add -A`. Stage by explicit name.
  `PLAN_<slug>.md` stays untracked during the run; §4.4 deletes it before the PR.
- **Never push to `dev-msf`/`dev`/`main_msf`** — always via PR.

## Red flags — stop immediately

- A test fails unrelated to the current fix → return to
  `superpowers:systematic-debugging`, don't patch.
- Unexpected change in numeric model output / broken mass balance → stop, surface
  to the user.
- 3+ failed attempts on the same task → don't retry a 4th; question the plan
  (Phase 4.5 of systematic-debugging) and escalate.
- An implementer returns `BLOCKED`/`NEEDS_CONTEXT` → provide context or escalate;
  don't retry blindly.

## Do not

- Push directly to `dev-msf`/`dev`/`main_msf`, or merge under any circumstance.
- Create the PR without explicit user confirmation.
- Bypass pre-commit hooks.
- Expand scope: if something is missing from the plan, **stop** and ask whether
  to go back to `/refine-plan`.
- Implement a review comment before triaging the full batch.
- Implement an ❓/🔲 comment without asking the user.
- Skip the double review (spec + quality) per task.
- Dispatch multiple implementers in parallel on the same checkout (conflicts) —
  only investigators (§2.0) and reviewers (§2.3) run in parallel.
- Skip the plan-file cleanup (§4.4) in PLAN mode.

## Full workflow recap

```
[OpenSpec] /opsx:propose          → proposal + design + tasks
[PLAN]     /diagnose              → PLAN_<slug>.md
/challenge-plan [openspec:<name>] → critique (auto-cycle refine/re-challenge)
/apply-plan                      → per-task TDD + double review + changelog + PR
                                   ↓ user confirms PR (gh pr create --base dev-msf)
                                   → watch CI (gh pr checks)
                                   → CI failure? fix → push
                                   → review comments? triage → implement/ask/reject
                                     → parallel verify → commit → push → reply in threads
                                   → iterate until green + no pending threads
                                   → "✅ PR ready to merge" (user merges via GitHub)
```
