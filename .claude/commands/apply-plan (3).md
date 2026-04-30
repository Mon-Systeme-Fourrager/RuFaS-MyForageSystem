---
description: Execute an approved plan — per-task TDD, spec + code quality review, plan file cleanup, PR
argument-hint:
  [
    leave empty if a plan was approved in this session,
    OR openspec:<change-name>,
    OR PLAN_<slug>.md (explicit plan file path),
  ]
allowed-tools: Read, Grep, Glob, Agent, Bash(git:*), Bash(bun:*), Bash(bunx:*), Bash(rm:*), TodoWrite, mcp__github__*, subscribe_pr_activity
model: claude-sonnet-4-6
---

$ARGUMENTS

## Precondition

This command runs **only after** a `/challenge-plan` returned ✅
**APPROVED** or ⚠️ **APPROVED WITH RESERVATIONS** accepted by the user.
If the last verdict is ❌, missing, or stale (the plan changed since
the last `/challenge-plan`), refuse and ask the user to pass through
`/refine-plan` + `/challenge-plan` first.

## Plan resolution

Two plan formats are supported. Resolution precedence: explicit file
path > glob patterns > session context (including `openspec:<name>`).
Plans are always passed by path to keep `Agent` tool-call arguments
small (no inline plan body).

### OpenSpec mode

If `$ARGUMENTS` matches `openspec:<name>`, OR `$ARGUMENTS` is empty
and session context shows an OpenSpec change was approved → resolve
the three artifact files:

- `openspec/changes/<name>/proposal.md` — context (what & why)
- `openspec/changes/<name>/design.md` — context (how)
- `openspec/changes/<name>/tasks.md` — task list (source of truth)

Store `mode: openspec` and `change_name: <name>`. Tasks are read
from `tasks.md` as `- [ ]` / `- [x]` checkboxes. Mark each complete
by editing `- [ ]` → `- [x]` directly in `tasks.md`.

**No plan file cleanup** at the end — OpenSpec artifacts are
managed by `/opsx:archive`, not deleted by this command.

### PLAN\_\*.md mode

Path-based resolution is tried fully before any text-based resolution,
to keep every `Agent` tool-call argument small and avoid stream idle
timeouts (same rationale as `/challenge-plan`: no inline plan body).

1. If `$ARGUMENTS` is a file path → resolve to that file.
2. Else → glob `PLAN_*.md` at repo root (AgriDoc convention,
   `CLAUDE.md`). If exactly one file matches the topic under discussion
   in the session → use it. If several → list them and ask which to
   apply.
3. Else → retrieve the last approved plan file path from the current
   conversation (still a path, never inlined text).
4. Else → ask the user for the path. Do **not** fall back to embedding
   a pasted plan: `/apply-plan` requires a file on disk because every
   subagent dispatch references it by path (see Step 2).

The plan must be the **self-sufficient version** (as produced by
`/refine-plan`): body with BEFORE/AFTER, REUSES, YAGNI CHECK, expected
RED/GREEN tests.

Remember the exact filename `PLAN_<slug>.md` — it is passed to every
subagent dispatch (Step 2) and removed in the cleanup step (Step 4.3).
The file must remain on disk, unchanged, for the entire duration of
`/apply-plan`; do not delete or rename it before Step 4.3.

## Workflow (non-negotiable)

### 1. Pre-flight: verify the plan file and the active branch

**OpenSpec mode:** `Read` all three artifact files. If any is missing
or empty → refuse:

> ⚠️ `openspec/changes/<name>/<file>` is missing. Run `/opsx:propose`
> to regenerate artifacts, then `/challenge-plan openspec:<name>` to
> approve before running `/apply-plan`.

**PLAN\_\*.md mode:** `Read` the resolved `PLAN_<slug>.md` from the
repo root. The check has the same shape as `/challenge-plan`'s
pre-dispatch verification:

- If `Read` errors (file not found) → refuse:

  > ⚠️ `PLAN_<slug>.md` is missing on disk. Run `/diagnose` to
  > recreate it, then `/challenge-plan` to approve it, before
  > running `/apply-plan`.

- If `Read` succeeds but the file is empty, does not start with
  `## Plan —`, does not contain at least one `📝` / `✨` / `🗑️` /
  `🧪` marker, or has no `REUSES` section → refuse:

  > ⚠️ `PLAN_<slug>.md` is empty or truncated. Run `/diagnose` to
  > regenerate it, then `/challenge-plan` to approve it, before
  > running `/apply-plan`.

A missing or corrupt plan file would make every subagent dispatch
fail (each one reads the plan from disk by path, see step 2).

**Branch guard.** Verify the active branch is not `main` (protected
— see `.github/BRANCH_PROTECTION.md`). Run `git rev-parse
--abbrev-ref HEAD`. If the result is `main` → refuse:

> ⚠️ Cannot run `/apply-plan` directly on `main` (protected branch).
> Switch to a feature branch first.

This catches local misuse early; GitHub branch protection blocks
the push anyway, but only after task commits have already landed
on the wrong branch.

**Do not proceed** if either check fails.

Once the pre-flight passes, work proceeds directly on the repo's
active branch. `/apply-plan` no longer creates a worktree or a
branch: remote sessions (Claude Code Web) receive a branch
pre-assigned by the harness, and local sessions must place
themselves on their feature branch before invoking the command.

### 2. Task orchestration

Invoke `superpowers:subagent-driven-development`. All `Agent` tool
calls in this command use `model: "sonnet"` unless a step explicitly
overrides. For each task in the plan:

1. **Identify the next pending task.**

   **OpenSpec mode:** `Read` `tasks.md`, find the next `- [ ]` item.
   The task identifier is a stable locator (unchecked ordinal + line
   number), with checkbox text included as display context only.
   Context for the subagent comes from all three artifact paths
   (proposal, design, tasks) — passed by path, never inlined.

   **PLAN\_\*.md mode:** Read the plan file yourself (`Read`) to enumerate
   the tasks and pick a stable identifier for the next one — exact
   header text (e.g. the `📝` / `✨` / `🗑️` / `🧪` section title) or
   ordinal (`Task 3`). Every subagent dispatch below references the plan
   **by path**, the same way `/challenge-plan` does; this is what keeps
   the `Agent` tool-call argument small and avoids stream idle timeouts.

2. **Dispatch an implementer subagent** with:

   **OpenSpec mode:**
   - The three artifact paths (one per line) and the task identifier.
   - A directive: "Read all three files with the `Read` tool. Use
     `proposal.md` and `design.md` as context. The task to implement
     is the identified checkbox item in `tasks.md`."

   **PLAN\_\*.md mode:**
   - The resolved `PLAN_<slug>.md` path (one line) and the task
     identifier from step 1.
   - A directive: "Read the plan file with the `Read` tool, locate the
     identified task, and treat its body as the full task spec
     verbatim — do not summarize, do not look elsewhere for the plan."

   In both modes also include:
   - Relevant files and existing patterns to reuse (cite the
     `REUSES:` lines as hints, but the subagent still reads them from
     the plan).
   - AgriDoc constraints (see below).
   - Instruction to follow `superpowers:test-driven-development`
     (RED → GREEN → REFACTOR, watch the test fail before writing code).

3. **Dispatch both reviewer subagents in parallel** (single message,
   two simultaneous `Agent` tool calls):
   - **Spec-compliance reviewer**: same path + task identifier (no
     embedded task body) — verifies the implementation matches the plan
     exactly (no missing requirements, no extras). Reads the plan from
     disk for itself.
   - **Code-quality reviewer**: same path + task identifier, using
     `superpowers:requesting-code-review` as the framework, cross-
     referencing `REUSES:` and YAGNI CHECK from the plan file.
4. Collect both reviewer results, then loop corrections until both ✅.
   Never move to the next task with an open issue.
5. Mark the task complete:
   - **OpenSpec mode:** edit `tasks.md` at the captured stable
     locator (line/ordinal) — `- [ ]` → `- [x]` for that exact task.
     Also mark in TodoWrite.
   - **PLAN\_\*.md mode:** mark in TodoWrite only (plan file is not
     edited during implementation).

   In both modes: commit (atomic commit per task — stage implementation
   files explicitly by name and, in OpenSpec mode, also stage the
   updated `tasks.md`; pre-commit hooks MUST run; never use
   `--no-verify`).

### 3. Per-task verification (evidence, not claims)

After each task, the implementer subagent must run and verify (iron
law of `superpowers:verification-before-completion` — fresh evidence
required for every claim):

Run these three checks **in parallel** (single Bash call with `&` +
`wait`, capturing each exit code separately):

```bash
bun run typecheck &
PID_TC=$!
bun run lint &
PID_LINT=$!
bunx vitest run <affected test files> &
PID_VT=$!
TC=0; LINT=0; VT=0
wait $PID_TC || TC=$?
wait $PID_LINT || LINT=$?
wait $PID_VT || VT=$?
[ $TC -eq 0 ] && [ $LINT -eq 0 ] && [ $VT -eq 0 ]
```

All three must exit 0 before proceeding.

- If `supabase/migrations/**` touched → pgTAP tests (see
  `docs/PGTAP_TESTING.md`) must be added and pass
- If a new heavy dependency or bundle-impacting change → `bun run size`
  within budgets (`.size-limit.json`)
- If design tokens touched → `bun run tokens:check`
- If `supabase/functions/**` touched → `bun run deno:fmt` (not
  Prettier)

### 4. Final review and completion

After all tasks complete:

1. Dispatch a **final code-quality reviewer subagent** over the full
   diff against the base branch (not per-task this time — holistic
   view).
2. Run the full verification suite with the three core checks **in
   parallel** (single Bash call with `&` + `wait`):

   ```bash
   bun run typecheck &
   PID_TC=$!
   bun run lint &
   PID_LINT=$!
   bun run test &
   PID_TEST=$!
   TC=0; LINT=0; TEST=0
   wait $PID_TC || TC=$?
   wait $PID_LINT || LINT=$?
   wait $PID_TEST || TEST=$?
   [ $TC -eq 0 ] && [ $LINT -eq 0 ] && [ $TEST -eq 0 ]
   ```

   Then, sequentially if applicable:
   - `bun run size` if bundle-affecting changes

3. **Cleanup the plan file — non-negotiable, automatic, inline
   with the normal flow.**
   No user confirmation is requested: Step 4.3 runs automatically
   after Steps 4.1 and 4.2, in the same execution flow.

   **OpenSpec mode:** no cleanup. The artifacts in
   `openspec/changes/<name>/` are managed by `/opsx:archive` after
   the PR is merged. Skip this step entirely.

   **PLAN\_\*.md mode:** `PLAN_<slug>.md` is a work artifact,
   not product documentation; it MUST NOT appear in the PR diff.
   Branch on the file's git state:

   ```bash
   if git ls-files --error-unmatch PLAN_<slug>.md >/dev/null 2>&1; then
     # Plan file was committed during the run (rare, usually from an
     # accidental `git add .`): dedicated commit. `-f` is required
     # because the working tree may carry uncommitted edits from the
     # last refine pass.
     git rm -f PLAN_<slug>.md
     git commit -m "chore: remove plan file after implementation"
     # Pre-commit hooks must run — no `--no-verify`.
   else
     # Plan file is untracked (common case — never staged thanks to
     # the commit-hygiene guardrail).
     # Just delete the copy; no commit needed, nothing in the PR diff.
     rm PLAN_<slug>.md
   fi
   ```

   The commit (tracked case) is **atomic and separate** from task
   commits; it must not bundle any other change. Pre-commit hooks
   remain mandatory (never `--no-verify`). The only user
   confirmation point in Step 4 is the PR creation (Step 4.5) —
   deleting the plan does not require any.

4. Invoke `superpowers:finishing-a-development-branch` to decide how
   to integrate the work. Given `main` is protected, the output MUST
   be a **pull request**, not a direct merge.
5. **PR creation requires explicit user confirmation** — present the
   proposed PR title and body, then wait. Do not create the PR until
   the user replies with approval. Use **GitHub MCP tools**
   (`mcp__github__create_pull_request`) — the `gh` CLI is not
   available in this environment.
6. Immediately after the PR is created, call `subscribe_pr_activity`
   automatically (no user prompt needed) to receive CI and review
   events.

### 5. Post-PR review cycle

This section governs what happens after the PR exists. It runs
automatically in response to `<github-webhook-activity>` events and
loops until the PR is merge-ready.

#### 5.1 CI failure

When a CI failure event arrives:

1. Fetch the failing job logs via `mcp__github__*`.
2. Investigate the root cause directly — no user prompt needed for
   diagnosis.
3. If the fix is clearly caused by the PR changes (failing test, lint
   error, type error) → fix it, run the parallel verification suite
   (same pattern as §3), commit, push.
4. If the fix requires an architectural decision or touches scope
   outside the original plan → **stop and ask the user** before
   acting.

#### 5.2 Review comment triage (batch first, act second)

When review comments arrive, **triage the full batch before
implementing anything**. Invoke `superpowers:receiving-code-review`
as the evaluation framework. Classify every comment into one of four
buckets:

| Bucket              | Criteria                                                              |
| ------------------- | --------------------------------------------------------------------- |
| ✅ **Valid**        | Technically correct, within the original plan scope                   |
| ❓ **Ambiguous**    | Multiple valid interpretations, or an architectural trade-off         |
| 🔲 **Out-of-scope** | Correct but outside the original plan                                 |
| ❌ **Invalid**      | Technically wrong, misunderstands context, or contradicts `CLAUDE.md` |

After triage, send the user **one grouped message** listing only the
❓ and 🔲 items with a concrete question for each. Do not ask about
✅ or ❌ items — those are handled automatically. Wait for the user's
answers before proceeding.

#### 5.3 Implementation

Once triage decisions are complete:

1. Implement all ✅ items and user-approved ❓/🔲 items. Commit each
   fix atomically (pre-commit hooks must run; never `--no-verify`).
2. Run the parallel verification suite **once for the full batch**
   (not per fix):

   ```bash
   bun run typecheck &
   PID_TC=$!
   bun run lint &
   PID_LINT=$!
   bun run test &
   PID_TEST=$!
   TC=0; LINT=0; TEST=0
   wait $PID_TC || TC=$?
   wait $PID_LINT || LINT=$?
   wait $PID_TEST || TEST=$?
   [ $TC -eq 0 ] && [ $LINT -eq 0 ] && [ $TEST -eq 0 ]
   ```

3. Push.

#### 5.4 PR thread replies

After pushing, reply in **each individual comment thread** via
`mcp__github__add_reply_to_pull_request_comment` with a concise
explanation:

- ✅ Applied → what was changed and why.
- ❌ Rejected → the technical reason it was not applied.
- 🔲 Deferred (user said no) → note that it is out of scope for this
  PR and can be tracked separately.

Replying in every thread prevents the same point from being raised
again in a subsequent review round.

#### 5.5 Iterate

Repeat §5.1–5.4 for each new `<github-webhook-activity>` event until
both conditions are met:

- All CI checks pass (green).
- No unresolved review threads remain.

#### 5.6 Merge-ready signal

When both conditions are met, print exactly:

> ✅ PR ready to merge: `<PR URL>`
> All CI checks pass. No unresolved review threads.
> Merge via the GitHub interface when ready.

**Never merge automatically.** `main` is protected; the user merges
via the GitHub interface. Do not call any merge tool or command.

## AgriDoc constraints (injected into every subagent prompt)

- **Bun only**: `bun run …`, `bunx …`. Never `npm`, never `npx`.
- **Grep tool, not `grep` in Bash**: both for the main agent and every
  subagent.
- **Pre-commit hooks respected**: husky + lint-staged must run. Never
  `--no-verify`, never `--no-gpg-sign`. If a hook fails, fix the root
  cause; don't bypass.
- **Tests co-located**: `Foo.tsx` + `Foo.test.tsx`. Never `__tests__/`.
  Always `.test.ts(x)`, never `.spec.ts(x)`.
- **CASL authorization**: use `FeatureGate` / `RequireAuth` /
  `RequireRole` / `RequirePlatformAdmin`. Never re-verify auth inline.
- **i18n**: any new UI string goes in `src/i18n/locales/`. No
  hard-coded strings in components.
- **Design tokens**: no magic values for colors, spacing, radii. Use
  tokens; regenerate via `bun run tokens:generate` if needed.
- **PWA/offline**: data fetches via TanStack Query (stable keys so the
  IndexedDB persister works). No direct `fetch` that bypasses the
  Workbox strategies configured in `vite.config.ts`.
- **React 19**: function components + hooks. No class components, no
  `defaultProps` on function components, no `ReactDOM.render`.
- **Tailwind v4**: CSS-first via `@tailwindcss/vite`. No classic
  `tailwind.config.js`.
- **Edge functions**: `deno fmt`, not Prettier. Public functions must
  be registered in `supabase/config.toml` with `verify_jwt = false`.
- **Bundle chunking**: any new heavy dependency gets a dedicated
  vendor chunk in `vite.config.ts` (`build.rolldownOptions.output.codeSplitting.groups`).
- **Accessibility**: roles, labels, focus management, keyboard
  navigation, contrast. `pa11y-ci` is part of the test suite.
- **Commit hygiene**: never `git add .` or `git add -A`. Always stage
  task files by explicit name (`git add src/foo.ts src/foo.test.ts`).
  `PLAN_<slug>.md` stays at the repo root as an untracked artifact
  during execution; Step 4.3 deletes it just before the PR. A stray
  `git add .` would sweep it into a task commit.
- **Never push to `main`**: protected branch. Always via PR.

## Red flags — stop immediately

- A test fails in a way unrelated to the current fix → return to
  `superpowers:systematic-debugging`, don't patch.
- `bun run size` exceeds budgets → don't push through; stop, propose
  going back to `/refine-plan` to plan chunking.
- pgTAP RLS test fails → blocking. Don't disable the test.
- 3+ failed attempts on the same task → don't retry a 4th time.
  Question the plan itself (Phase 4.5 of systematic-debugging) and
  escalate to the user. Likely return to `/refine-plan`.
- An implementer subagent returns `BLOCKED` or `NEEDS_CONTEXT` → do
  not retry blindly. Provide missing context, or if the plan itself is
  wrong, escalate.

## Do not

- Push directly to `main` (protected).
- **Merge to `main` under any circumstance** — the user merges via
  the GitHub interface. Never call a merge tool or command.
- Create the PR without explicit user confirmation.
- Use `gh` CLI (not available — use `mcp__github__*` tools).
- Bypass pre-commit hooks.
- Expand scope: if something is missing from the plan, **stop** and
  ask whether to go back to `/refine-plan`. Never improvise additions
  mid-execution.
- Implement a review comment before triaging the full batch first.
- Implement an ❓ ambiguous or 🔲 out-of-scope comment without asking
  the user.
- Skip replying in PR comment threads after each fix/rejection.
- Skip the double review (spec compliance + code quality) per task.
- Start the next task while the previous one has open review issues.
- Dispatch multiple implementer subagents in parallel on the same
  codebase (conflicts).
- Skip the plan file cleanup (Step 4.3) in `PLAN_*.md` mode:
  `PLAN_<slug>.md` must be removed in a dedicated commit before the
  PR is opened. OpenSpec mode skips cleanup by design (artifacts
  managed by `/opsx:archive` after the PR is merged).

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
