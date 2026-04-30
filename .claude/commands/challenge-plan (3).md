---
description: Counter-validate a plan (read-only, via fresh-context subagent)
argument-hint:
  [
    plan file path,
    OR openspec:<change-name>,
    OR <change-name>,
    OR paste the plan to persist incrementally,
  ]
model: claude-sonnet-4-6
allowed-tools: Read, Grep, Glob, Agent, Write, Edit
# Write and Edit are scoped to PLAN_*.md at repo root, and are only
# used by the option-C path in `## Plan resolution` (incremental
# persist of a plan pasted in $ARGUMENTS — same chunked strategy as
# /diagnose, ≤ 2 KB per call, one tool call per turn). The dispatch
# path itself remains read-only for source code.
---

$ARGUMENTS

## Plan resolution

Identify the plan file to counter-validate. Resolution is
**path-only** — inline plan bodies are refused because they would
be re-embedded into the `Agent` tool-call argument and routinely
cause `API Error: Stream idle timeout - partial response received`
on plans above a few KB.

**Hard rule (non-negotiable, applied first):** if `$ARGUMENTS`
contains anything other than (a) a single file path, (b) an
OpenSpec selector (`openspec:<name>` or a bare kebab-case
`<change-name>` matching `openspec/changes/<name>/`), or (c) the
empty string — i.e. it contains prose, a pasted plan, a critique,
multiple lines of text, etc. — you have **no authority** to
dispatch a subagent in this turn. The only legal actions are: (a)
refuse with the message in step 3 below, or (b) offer the
incremental persist path in step 3 (which itself ends the turn
before any dispatch). OpenSpec selectors are evaluated in the
`### OpenSpec path` block before the `### PLAN_*.md path` refusal
logic. Improvising a dispatch with the plan inlined is what
triggered the timeout chains documented in this command's history;
it is forbidden, full stop.

### OpenSpec path

1. If `$ARGUMENTS` matches `openspec:<name>` OR is a bare kebab-case
   word AND `openspec/changes/<name>/` exists at repo root → this is
   an **OpenSpec change**. Resolve the three artifact files:
   - `openspec/changes/<name>/proposal.md`
   - `openspec/changes/<name>/design.md`
   - `openspec/changes/<name>/tasks.md`

   Verify all three exist with `Read`. If any is missing, print:

   > ⚠️ OpenSpec change `<name>` is incomplete — missing `<file>`.
   > Run `/opsx:propose` to generate all artifacts first.

   Store `mode: openspec` and `change_name: <name>` — used in the
   Dispatch and Post-dispatch sections below.

2. Else if `$ARGUMENTS` is empty → also check for an active OpenSpec
   change: `Glob openspec/changes/*/tasks.md`. If exactly one change
   directory is found AND no `PLAN_*.md` exists at repo root, offer:

   > Found OpenSpec change `<name>`. Validate it with
   > `/challenge-plan openspec:<name>`, or run `/diagnose` for a
   > `PLAN_*.md`-based plan. Stop. Wait for the user's choice.

### PLAN\_\*.md path

1. If `$ARGUMENTS` is a file path → resolve to that file.
2. Else if `$ARGUMENTS` is empty → glob `PLAN_*.md` at repo root
   (AgriDoc convention, see `CLAUDE.md`). If exactly one file matches
   the topic under discussion in the session → use it. If several →
   list them and ask which to validate.
3. Else (`$ARGUMENTS` contains prose, a pasted plan, or any
   non-path) → **refuse and offer incremental persist.** Print:

   > `/challenge-plan` requires a plan file on disk. Options:
   >
   > **A.** OpenSpec change: `/challenge-plan openspec:<name>`
   > (if you used `/opsx:propose`).
   >
   > **B.** Run `/diagnose` to produce the plan natively on disk
   > (recommended — it follows the write strategy that avoids
   > timeouts).
   >
   > **C.** I can persist your pasted plan to `PLAN_<slug>.md`
   > incrementally (section by section, ≤ 2 KB per write) to avoid
   > the timeout. Reply with the slug you want (e.g.
   > `unified-test-suite-cached`).

   **If the user chooses option C**, persist the pasted plan using
   the **same incremental write strategy as `/diagnose`** (see
   `### Write strategy` in `diagnose.md`):
   1. Derive `<slug>` from the user's reply or from the plan title.
   2. Check collision (`Glob PLAN_<slug>.md`). If it exists, ask
      the user as in `diagnose.md` collision handling.
   3. Write in chunks ≤ 2 KB:
      - First `Write`: header (`## Plan — <title>`) through the
        first major section.
      - Subsequent `Edit` appends: one per remaining section
        (📝 / ✨ / 🗑️ / 🧪 / YAGNI CHECK / REUSES).
   4. **Single-action rule**: do **not** chain Write + Edit + Edit
      - … in one turn after the user pasted a long plan into the
        chat. Persist the header in this turn, then ask the user to
        reply `continue` for each subsequent section. Each `Edit`
        append happens in its own turn.
   5. Verify with `Read` after the last append: file exists,
      starts with `## Plan —`, ends with a `REUSES` section.
   6. If verified, print:
      > ✅ Plan saved to `PLAN_<slug>.md` (verified on disk).
      > Re-run `/challenge-plan` without arguments.
   7. If any write fails midway, `Read` the partial file to see
      what landed, then print **only the missing remainder** for
      the user to paste manually (split into ≤ 50-line chat
      blocks). Never retry the same multi-KB write — it will
      timeout again.

   **Critical: never attempt to write the full pasted plan in a
   single `Write` call.** This is what causes the infinite timeout
   loop. The incremental strategy is non-negotiable for plans
   originating from user paste.

   **Do not dispatch the subagent in this same turn.** The user
   must re-invoke `/challenge-plan` (without arguments) after the
   file is confirmed on disk. This separation guarantees a clean
   entry point with a verified file and avoids the heavy-turn
   chaining that triggers timeouts.

4. If no path resolves from steps 1-2 and `$ARGUMENTS` is empty →
   ask the user for the path once. Do not embed a pasted reply as a
   fallback; if the reply is not a path, re-apply step 3.

## Dispatch

### Pre-dispatch file verification (non-negotiable)

**OpenSpec mode**: verify all three artifact files exist and are
non-empty (`Read` each). If any is missing or empty → refuse and
print the missing file name. Do not dispatch.

**PLAN\_\*.md mode**: Before dispatching the subagent, **read the resolved plan file**
with the `Read` tool. This is not optional — it catches the case
where `/diagnose` timed out and never wrote the file (or wrote a
truncated file).

- If `Read` errors (file not found) → print:

  > ⚠️ `PLAN_<slug>.md` does not exist on disk. `/diagnose` likely
  > timed out during the write. Run `/diagnose` again to recreate
  > the file, then re-run `/challenge-plan`.

  **Do not dispatch the subagent. Do not fall back to inline
  text.** End the turn.

- If `Read` succeeds but the content is empty or does not start
  with `## Plan —` → print:

  > ⚠️ `PLAN_<slug>.md` exists but appears empty or corrupt.
  > Delete it and re-run `/diagnose`.

  **Do not dispatch the subagent.**

- If `Read` succeeds but the file does not contain at least one
  of the expected markers (`📝` / `✨` / `🗑️` / `🧪`) **or**
  does not contain a `REUSES` section → the file is likely
  truncated. Print:

  > ⚠️ `PLAN_<slug>.md` looks incomplete (no task markers or no
  > `REUSES` section). It was probably written partially. Re-run
  > `/diagnose` to regenerate it before challenging.

  **Do not dispatch the subagent.**

- If `Read` succeeds and the content is valid (starts with
  `## Plan —`, contains at least one `📝` / `✨` / `🗑️` / `🧪`
  marker, has a `REUSES` section) → proceed with dispatch.

### Dispatch

Dispatch a subagent (`subagent_type: general-purpose`) with fresh
context. **The subagent does not see session history.**

**OpenSpec mode** — the subagent prompt must contain:

- The three artifact paths (one per line):
  `openspec/changes/<name>/proposal.md`
  `openspec/changes/<name>/design.md`
  `openspec/changes/<name>/tasks.md`
- A directive: "Read all three files with the Read tool. Together
  they form the complete plan: proposal = what & why, design = how,
  tasks = implementation steps. Review them as a whole."
- The review framework and constraints below.

**PLAN\_\*.md mode** — the subagent prompt must contain:

- The resolved `PLAN_<slug>.md` path (one line).
- A directive: "Read the file with the Read tool. The file contents
  are the full plan verbatim — do not treat them as a summary or an
  excerpt, and do not look elsewhere for the plan."
- The review framework and constraints below.

Passing the plan **by path** (not by embedded body) keeps the
`Agent` tool-call argument small and is what prevents
`API Error: Stream idle timeout - partial response received` on
plans above a few KB. This is non-negotiable: never inline the plan
body into the subagent prompt, even as a "safety copy".

You do not evaluate yourself — the subagent is the critic.

The subagent must:

1. Invoke `superpowers:requesting-code-review` as the review framework.
2. Invoke `superpowers:vercel-react-best-practices` if the plan touches
   React/UI, and `superpowers:supabase-postgres-best-practices` if the
   plan touches `supabase/**`.
3. Read the files cited in the plan (Read/Glob) to verify that the
   imports, utilities, hooks, components, and patterns referenced
   actually exist in the repo. A plan that invents paths is blocking.
4. Produce a severity-structured report, with an exact quote from the
   plan and a suggested correction for each point:

   🔴 BLOCKING
   - Logic bug, inverted condition, unhandled null
   - Regression: breaks an existing consumer of shared code
   - Missing or bypassed RLS on a `supabase/**` migration
   - Broken accessibility (focus trap, missing ARIA role, contrast)
   - Broken PWA offline (direct fetch bypassing Workbox, unstable
     TanStack Query key, unpersisted mutation)
   - Hard-coded secret, data leak, XSS/injection
   - Cited import or utility that does not exist

   🟠 IMPORTANT
   - Over-engineering: premature abstraction, new file for 3 lines,
     configurability for a single case
   - Duplication: existing utility/hook/component not reused (check
     `src/hooks`, `src/lib`, `src/utils`, `src/components`,
     `supabase/functions/_shared`)
   - Dead code: unused exports, unreachable branches, commented-out
     code
   - Flakiness: missing `await`, arbitrary timer instead of condition
     polling, race condition, order-dependent test
   - Robustness: unchecked Supabase error, orphaned promise, missing
     try/catch at boundaries
   - Missing responsive: Tailwind breakpoints absent, broken mobile
     layout
   - CASL guards forgotten: auth re-verified inline instead of using
     `FeatureGate` / `RequireAuth` / `RequireRole`
   - i18n: hard-coded UI string instead of a key in
     `src/i18n/locales/`
   - Design tokens bypassed: magic value (color, spacing, radius)
     instead of the generated token
   - Size-limit at risk: new heavy dependency without a dedicated
     chunk in `vite.config.ts` (Rolldown), or exceeding the budgets in
     `.size-limit.json`
   - Non-compliant tests: `__tests__/`, `.spec.ts`, `npx vitest`, not
     co-located
   - Public edge function without an entry in `supabase/config.toml`
     (`verify_jwt = false`)
   - React 19 patterns violated: class component, `defaultProps` on a
     function component, `ReactDOM.render`
   - Missing pgTAP: RLS migration without a test in `supabase/tests/`

   🟡 MINOR
   - Naming inconsistent with the rest of the module
   - Comments redundant with the code
   - Formatting that will be corrected by `prettier --write` at commit

5. Verify plan internal consistency:
   - Type/function signatures match across steps
   - Proposed tests cover the fix (not just the happy path)
   - Ambiguous decisions were escalated to the user, not silently
     decided
   - YAGNI: every new file/function is strictly necessary
   - Reuse: the `REUSES:` field (if present) references real existing
     code

6. Final verdict, explicit on a single line:
   - ✅ **APPROVED** — no 🔴, 🟠 acceptable or absent
   - ⚠️ **APPROVED WITH RESERVATIONS** — no 🔴, but 🟠 to fix
   - ❌ **NEEDS REVISION** — at least one 🔴

## Post-dispatch behavior — first run

After the subagent returns its critique:

1. Print the critique to chat (relay verbatim or summarized — your
   call based on length, but never re-execute the review yourself).
2. Check the verdict:
   - **✅ APPROVED** or **only 🟡 MINOR** items remain → print
     (mode-specific):
     > ✅ Plan approuvé. Lance `/apply-plan openspec:<name>` quand tu
     > es prêt. (OpenSpec mode)
     >
     > ✅ Plan approuvé. Lance `/apply-plan` quand tu es prêt. (PLAN mode)
     > End the turn. Do not start the auto-cycle.
   - **❌ NEEDS REVISION** or **⚠️ APPROVED WITH RESERVATIONS**
     with 🟠 items → start the **auto-cycle** (see below).

If the user originally pasted a plan and you persisted it via the
option-C path in `## Plan resolution`, end the turn after persist
verification. Never proceed to dispatch or auto-cycle in the same
turn as an option-C persist.

## Auto-cycle — refine + re-challenge (up to 5 iterations)

This loop runs automatically after the first user-triggered
`/challenge-plan`, when the verdict requires revision. Each iteration
mirrors the manual flow: challenge finishes → refine begins → challenge
re-validates. The natural break between the subagent returning its
critique and the next skill invocation provides the same latency profile
as running the commands manually — which is why 5 iterations are safe.

### Cycle structure

```text
CYCLE = 1

loop:
  1. Print "─── Cycle auto CYCLE/5 — Correction en cours… ───"
  2. Invoke `superpowers:refine-plan`
     → reads the last critique from session context
     → applies surgical edits to PLAN_<slug>.md
     → if a decision is needed: STOP, ask user, exit loop
  3. Print "─── Cycle auto CYCLE/5 — Re-validation… ───"
  4. Dispatch new challenge subagent (same rules as ## Dispatch)
  5. Print critique
  6. CHECK STOPPING CONDITIONS (see "### Stopping conditions")
     → may STOP
  7. CYCLE = CYCLE + 1
  8. repeat
```

### Stopping conditions (checked after each new critique)

| Condition                               | Action                                                                                                                                                                                     |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| ✅ APPROVED                             | Print mode-specific message — OpenSpec: "✅ Plan approuvé après N cycle(s). Lance `/apply-plan openspec:<name>`." — PLAN: "✅ Plan approuvé après N cycle(s). Lance `/apply-plan`." — stop |
| Only 🟡 MINOR remain                    | Print mode-specific message — OpenSpec: "✅ Seulement des points mineurs. Lance `/apply-plan openspec:<name>`." — PLAN: "✅ Seulement des points mineurs. Lance `/apply-plan`." — stop     |
| Decision needed (raised by refine-plan) | Stop, ask user — they apply the decision (via `/refine-plan`) then re-trigger `/challenge-plan` to restart validation from CYCLE=1 with the updated plan                                   |
| CYCLE = 5 with ❌ or 🟠 still present   | Escalate (see "### Escalation at cycle 5") — stop                                                                                                                                          |

### Escalation at cycle 5

When 5 cycles complete without reaching approval, print:

```text
⚠️ 5 cycles sans approbation complète.

Points persistants : [résumé des 🔴/🟠 qui reviennent cycle après cycle]
Cause probable     : [pourquoi ces points ne se résolvent pas —
                     diagnostic erroné, approche fondamentalement
                     inadaptée, contrainte non résoluble dans ce plan]

Options :
  A. Revoir l'approche → /diagnose avec une nouvelle direction
  B. Accepter l'état actuel (🟠 restants, aucun 🔴) → /apply-plan
     [N'afficher cette option QUE si aucun 🔴 ne persiste]
  C. Continuer manuellement → /refine-plan puis /challenge-plan
```

Stop. Wait for the user's decision.

## Constraints (non-negotiable)

- **Source code is read-only**: no edits outside `PLAN_*.md` at repo
  root or OpenSpec artifact files (`openspec/changes/<name>/`). The
  only exception is the option-C incremental persist path
  in `## Plan resolution` (one tool call per turn, ends the turn).
  During the auto-cycle, `superpowers:refine-plan` edits the active
  plan source for the current mode (`PLAN_<slug>.md` in PLAN mode, or
  OpenSpec artifacts in OpenSpec mode); no other file is touched.
- Respect `CLAUDE.md`: Bun (not npm/npx), Grep tool (not `grep` in
  Bash), co-located test conventions.
- **No performative criticism**: if the plan is good, say so plainly.
  Do not fabricate 🟠 to justify the review.
- **No "nice to have"**: only flag what prevents a real problem (bug,
  regression, documented convention violation).
- **Subagent is critic only**: the challenge subagent produces a
  critique, not a correction. Corrections are applied by the
  `superpowers:refine-plan` skill in the auto-cycle refine step.
- **Context window**: the subagent must see the full plan by reading
  the resolved `PLAN_<slug>.md` with the `Read` tool. Never pass a
  summary (summary bias skews the review) and never inline the plan
  body (stream idle timeout on dispatch). The subagent reads the
  exact bytes on disk.
