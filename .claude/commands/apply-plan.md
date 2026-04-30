---
description: Execute an approved plan — per-task TDD, spec + code quality review, plan file cleanup, PR
argument-hint:
  [
    leave empty if a plan was approved in this session,
    OR openspec:<change-name>,
    OR PLAN_<slug>.md (explicit plan file path),
  ]
allowed-tools: Read, Grep, Glob, Agent, Bash(git:*), Bash(pytest:*), Bash(python:*), Bash(flake8:*), Bash(mypy:*), Bash(black:*), Bash(coverage:*), Bash(rm:*), TodoWrite, mcp__github__*, subscribe_pr_activity
model: claude-sonnet-4-6
---

$ARGUMENTS

## Precondition

This command runs **only after** a `/challenge-plan` returned ✅
**APPROVED** or ⚠️ **APPROVED WITH RESERVATIONS** accepted by the user.
If the last verdict is ❌, missing, or stale, refuse and ask the user to
pass through `/refine-plan` + `/challenge-plan` first.

## Plan resolution

Two plan formats are supported. Resolution precedence: explicit file
path > glob patterns > session context (including `openspec:<name>`).

### OpenSpec mode

If `$ARGUMENTS` matches `openspec:<name>`, OR `$ARGUMENTS` is empty
and session context shows an OpenSpec change was approved → resolve:

- `openspec/changes/<name>/proposal.md` — context (what & why)
- `openspec/changes/<name>/design.md` — context (how)
- `openspec/changes/<name>/tasks.md` — task list (source of truth)

Store `mode: openspec` and `change_name: <name>`. Mark tasks complete
by editing `- [ ]` → `- [x]` directly in `tasks.md`.

**No plan file cleanup** at the end — OpenSpec artifacts are
managed by `/opsx:archive`, not deleted by this command.

### PLAN\_\*.md mode

1. If `$ARGUMENTS` is a file path → resolve to that file.
2. Else → glob `PLAN_*.md` at repo root. If exactly one file matches
   the topic → use it. If several → list them and ask which to apply.
3. Else → retrieve the last approved plan file path from the current
   conversation.
4. Else → ask the user for the path. Do **not** fall back to embedding
   a pasted plan.

Remember the exact filename — it is passed to every subagent dispatch
and removed in the cleanup step. The file must remain on disk,
unchanged, for the entire duration of `/apply-plan`.

## Workflow (non-negotiable)

### 1. Pre-flight: verify the plan file and the active branch

**OpenSpec mode:** `Read` all three artifact files. If any is missing
or empty → refuse and explain.

**PLAN\_\*.md mode:** `Read` the resolved `PLAN_<slug>.md`.

- If `Read` errors (file not found) → refuse:
  > ⚠️ `PLAN_<slug>.md` is missing on disk. Run `/diagnose` to
  > recreate it, then `/challenge-plan` to approve it, before
  > running `/apply-plan`.

- If `Read` succeeds but the file is empty or malformed → refuse:
  > ⚠️ `PLAN_<slug>.md` is empty or truncated. Run `/diagnose` to
  > regenerate it, then `/challenge-plan` to approve it, before
  > running `/apply-plan`.

**Branch guard.** Run `git rev-parse --abbrev-ref HEAD`. If the result
is `main` or `dev-msf` → refuse:

> ⚠️ Cannot run `/apply-plan` directly on `main` or `dev-msf` (protected branches).
> Switch to a feature branch first.

### 2. Task orchestration

Invoke `superpowers:subagent-driven-development`. All `Agent` tool
calls use `model: "sonnet"` unless a step explicitly overrides.
For each task in the plan:

1. **Identify the next pending task.**

2. **Dispatch an implementer subagent** with:
   - The plan path (or artifact paths in OpenSpec mode) and the task
     identifier.
   - A directive to read the plan file(s) with the `Read` tool.
   - RuFaS constraints (see below).
   - Instruction to follow `superpowers:test-driven-development`
     (RED → GREEN → REFACTOR, watch the test fail before writing code).

3. **Dispatch both reviewer subagents in parallel** (single message,
   two simultaneous `Agent` tool calls):
   - **Spec-compliance reviewer**: verifies the implementation matches
     the plan exactly.
   - **Code-quality reviewer**: using `superpowers:requesting-code-review`
     as the framework, cross-referencing `REUSES:` and YAGNI CHECK.

4. Collect both reviewer results, loop corrections until both ✅.
   Never move to the next task with an open issue.

5. Mark the task complete and commit (atomic commit per task — stage
   implementation files explicitly by name; pre-commit hooks MUST run;
   never use `--no-verify`).

### 3. Per-task verification (evidence, not claims)

After each task, the implementer subagent must run and verify (iron
law of `superpowers:verification-before-completion`):

Run these three checks **in parallel** (single Bash call with `&` +
`wait`, capturing each exit code separately):

```bash
python -m mypy . &
PID_TC=$!
flake8 . &
PID_LINT=$!
pytest <affected test files — use specific paths matching changed source, or bare `pytest` if uncertain> &
PID_VT=$!
TC=0; LINT=0; VT=0
wait $PID_TC  || TC=$?
wait $PID_LINT || LINT=$?
wait $PID_VT   || VT=$?
[ $TC -eq 0 ] && [ $LINT -eq 0 ] && [ $VT -eq 0 ]
```

All three must exit 0 before proceeding.

### 4. Final review and completion

After all tasks complete:

1. Dispatch a **final code-quality reviewer subagent** over the full
   diff against the base branch (holistic view).

2. Run the full verification suite **in parallel**:

   ```bash
   python -m mypy . &
   PID_TC=$!
   flake8 . &
   PID_LINT=$!
   pytest &
   PID_TEST=$!
   TC=0; LINT=0; TEST=0
   wait $PID_TC   || TC=$?
   wait $PID_LINT || LINT=$?
   wait $PID_TEST || TEST=$?
   [ $TC -eq 0 ] && [ $LINT -eq 0 ] && [ $TEST -eq 0 ]
   ```

3. **Cleanup the plan file — non-negotiable, automatic.**

   **OpenSpec mode:** no cleanup. Artifacts managed by `/opsx:archive`.

   **PLAN\_\*.md mode:** `PLAN_<slug>.md` is a work artifact,
   not product documentation; it MUST NOT appear in the PR diff.

   ```bash
   if git ls-files --error-unmatch "$PLAN_FILE" >/dev/null 2>&1; then
     git rm -f "$PLAN_FILE"
     git commit -m "chore: remove plan file after implementation"
   else
     rm "$PLAN_FILE"
   fi
   ```

4. Invoke `superpowers:finishing-a-development-branch`. Given `main` is
   protected, the output MUST be a **pull request**, not a direct merge.

5. **PR creation requires explicit user confirmation** — present the
   proposed PR title and body, then wait. Do not create the PR until
   the user replies with approval. Use **GitHub MCP tools**
   (`mcp__github__create_pull_request`) — the `gh` CLI is not
   available in this environment.

6. Immediately after the PR is created, call `subscribe_pr_activity`
   automatically to receive CI and review events.

### 5. Post-PR review cycle

#### 5.1 CI failure

When a CI failure event arrives:

1. Fetch the failing job logs via `mcp__github__*`.
2. Investigate the root cause directly.
3. If the fix is clearly caused by the PR changes → fix it, run the
   parallel verification suite, commit, push.
4. If the fix requires an architectural decision → **stop and ask
   the user** before acting.

#### 5.2 Review comment triage (batch first, act second)

When review comments arrive, **triage the full batch before
implementing anything**. Invoke `superpowers:receiving-code-review`
as the evaluation framework. Classify every comment:

| Bucket              | Criteria                                                             |
| ------------------- | -------------------------------------------------------------------- |
| ✅ **Valid**        | Technically correct, within the original plan scope                  |
| ❓ **Ambiguous**    | Multiple valid interpretations, or an architectural trade-off        |
| 🔲 **Out-of-scope** | Correct but outside the original plan                                |
| ❌ **Invalid**      | Technically wrong, misunderstands context, or contradicts `CLAUDE.md`|

Send the user **one grouped message** listing only ❓ and 🔲 items
with a concrete question for each. Wait for answers before proceeding.

#### 5.3 Implementation

1. Implement all ✅ items and user-approved ❓/🔲 items. Commit each
   fix atomically.
2. Run the parallel verification suite **once for the full batch**.
3. Push.

#### 5.4 PR thread replies

After pushing, reply in **each individual comment thread** via
`mcp__github__add_reply_to_pull_request_comment`:

- ✅ Applied → what was changed and why.
- ❌ Rejected → the technical reason.
- 🔲 Deferred → note that it is out of scope for this PR.

#### 5.5 Merge-ready signal

When all CI checks pass and no unresolved review threads remain:

> ✅ PR ready to merge: `<PR URL>`
> All CI checks pass. No unresolved review threads.
> Merge via the GitHub interface when ready.

**Never merge automatically.** `main` is protected; the user merges
via the GitHub interface.

## RuFaS constraints (injected into every subagent prompt)

- **Python only**: `python`, `pytest`, `flake8`, `mypy`, `black`. Never
  `bun`, `npm`, `npx`, or any JavaScript tooling.
- **Grep tool, not `grep` in Bash**: both for the main agent and every
  subagent.
- **Pre-commit hooks respected**: if a hook fails, fix the root cause;
  never `--no-verify`.
- **Tests mirror source structure**: `tests/` directory mirrors
  `RUFAS/`. Both `test_*.py` (new) and `_test_*.py` (legacy) naming
  are collected by pytest.
- **Type annotations required**: new functions and methods must be
  fully annotated. New code must not increase the mypy error count
  compared to `dev`.
- **Black formatting**: line length 120, target Python 3.12.
- **Flake8**: max line length 120, max complexity 10, ignore E203/W503.
- **changelog.md**: must be updated for any PR that changes public
  behaviour (CI enforces this).
- **Protected input files**: files under `input/` listed in the CI
  workflow must not be modified without maintainer approval.
- **Commit hygiene**: never `git add .` or `git add -A`. Always stage
  files explicitly by name.
- **Never push to `main`**: protected branch. Always via PR.
- **GitHub MCP tools**: use `mcp__github__*` for all GitHub operations.
  The `gh` CLI is not available.

## Red flags — stop immediately

- A test fails in a way unrelated to the current fix → invoke
  `superpowers:systematic-debugging`, don't patch blindly.
- 3+ failed attempts on the same task → don't retry a 4th time.
  Escalate to the user. Likely return to `/refine-plan`.
- An implementer subagent returns `BLOCKED` or `NEEDS_CONTEXT` → do
  not retry blindly. Provide missing context or escalate.
- Mypy error count increases compared to `dev` → blocking. Do not push.

## Do not

- Push directly to `main` (protected).
- **Merge to `main` under any circumstance** — the user merges via
  the GitHub interface.
- Create the PR without explicit user confirmation.
- Use `gh` CLI (not available — use `mcp__github__*` tools).
- Bypass pre-commit hooks.
- Expand scope mid-execution: if something is missing from the plan,
  **stop** and ask whether to return to `/refine-plan`.
- Skip the double review (spec compliance + code quality) per task.
- Start the next task while the previous one has open review issues.
- Dispatch multiple implementer subagents in parallel on the same
  codebase (risk of conflicts).

## Full workflow recap

```
[OpenSpec] /opsx:propose       → proposal + design + tasks
[PLAN]     /diagnose            → PLAN_<slug>.md
/challenge-plan [openspec:<name>] → critique
/refine-plan      → plan v2
/challenge-plan   → critique v2
... iterate ...
/apply-plan       → per-task TDD + double review + PR
                    ↓ user confirms PR
                    → subscribe_pr_activity (automatic)
                    → CI failure? fix directly → push
                    → review comments? triage batch →
                        ✅ implement / ❓🔲 ask user / ❌ reject
                        → parallel verify → commit → push
                        → reply in each PR thread
                    → iterate until CI green + no pending threads
                    → "✅ PR ready to merge" (user merges via GitHub)
```
