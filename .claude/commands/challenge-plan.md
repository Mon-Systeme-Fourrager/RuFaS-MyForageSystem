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
# persist of a plan pasted in $ARGUMENTS).
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
incremental persist path in step 3.

### OpenSpec path

1. If `$ARGUMENTS` matches `openspec:<name>` OR is a bare kebab-case
   word AND `openspec/changes/<name>/` exists at repo root → resolve
   the three artifact files and proceed as in OpenSpec mode.

2. Else if `$ARGUMENTS` is empty → check for an active OpenSpec
   change: `Glob openspec/changes/*/tasks.md`. If exactly one change
   directory is found AND no `PLAN_*.md` exists at repo root, offer:

   > Found OpenSpec change `<name>`. Validate it with
   > `/challenge-plan openspec:<name>`, or run `/diagnose` for a
   > `PLAN_*.md`-based plan. Stop. Wait for the user's choice.

### PLAN\_\*.md path

1. If `$ARGUMENTS` is a file path → resolve to that file.
2. Else if `$ARGUMENTS` is empty → glob `PLAN_*.md` at repo root.
   If exactly one file matches the topic → use it. If several →
   list them and ask which to validate.
3. Else (`$ARGUMENTS` contains prose, a pasted plan, or any
   non-path) → **refuse and offer incremental persist.** Print:

   > `/challenge-plan` requires a plan file on disk. Options:
   >
   > **A.** OpenSpec change: `/challenge-plan openspec:<name>`
   > (if you used `/opsx:propose`).
   >
   > **B.** Run `/diagnose` to produce the plan natively on disk
   > (recommended).
   >
   > **C.** I can persist your pasted plan to `PLAN_<slug>.md`
   > incrementally (section by section, ≤ 2 KB per write).
   > Reply with the slug you want (e.g. `fix-simulation-loop`).

   **If the user chooses option C**, persist the pasted plan using
   the same incremental write strategy as `/diagnose` (see
   `### Write strategy` in `diagnose.md`).

4. If no path resolves from steps 1-2 and `$ARGUMENTS` is empty →
   ask the user for the path once.

## Dispatch

### Pre-dispatch file verification (non-negotiable)

Before dispatching the subagent, **read the resolved plan file**
with the `Read` tool.

- If `Read` errors → print:
  > ⚠️ `PLAN_<slug>.md` does not exist on disk. Run `/diagnose`
  > again to recreate the file, then re-run `/challenge-plan`.
  **Do not dispatch the subagent.**

- If `Read` succeeds but the content is empty or does not start
  with `## Plan —` → print:
  > ⚠️ `PLAN_<slug>.md` exists but appears empty or corrupt.
  > Delete it and re-run `/diagnose`.
  **Do not dispatch the subagent.**

- If the file does not contain at least one of the expected markers
  (`📝` / `✨` / `🗑️` / `🧪`) **or** does not contain a `REUSES`
  section → the file is likely truncated. Print:
  > ⚠️ `PLAN_<slug>.md` looks incomplete. Re-run `/diagnose`.
  **Do not dispatch the subagent.**

- If `Read` succeeds and content is valid → proceed with dispatch.

### Dispatch

Dispatch a subagent (`subagent_type: general-purpose`) with fresh
context. **The subagent does not see session history.**

The subagent prompt must contain:

- The resolved `PLAN_<slug>.md` path (one line).
- A directive: "Read the file with the Read tool. The file contents
  are the full plan verbatim — do not treat them as a summary or an
  excerpt, and do not look elsewhere for the plan."
- The review framework and constraints below.

Passing the plan **by path** (not by embedded body) keeps the
`Agent` tool-call argument small. This is non-negotiable.

The subagent must:

1. Invoke `superpowers:requesting-code-review` as the review framework.
2. Read the files cited in the plan (Read/Glob) to verify that the
   imports, modules, classes, and functions referenced actually exist
   in the repo. A plan that invents paths is blocking.
3. Produce a severity-structured report, with an exact quote from the
   plan and a suggested correction for each point:

   🔴 BLOCKING
   - Logic bug, inverted condition, unhandled exception
   - Regression: breaks an existing consumer of shared code
   - Missing or broken pytest test for a new behaviour
   - Mypy error introduced by the proposed changes
   - Cited import, class, or function that does not exist in the repo

   🟠 IMPORTANT
   - Over-engineering: premature abstraction, new file for 3 lines,
     configurability for a single case
   - Duplication: existing utility/class/function not reused (check
     `RUFAS/util.py`, `RUFAS/general_constants.py`, existing managers)
   - Dead code: unused exports, unreachable branches
   - Flakiness: non-deterministic test (no random seed, order-dependent)
   - Robustness: unchecked return value, unhandled edge case at module
     boundary
   - Missing test: new public function without a corresponding test
     in `tests/`
   - Incorrect test location: test not mirroring source structure
     under `tests/`
   - Flake8 violation: line > 120 chars, complexity > 10
   - Black formatting issue (line length 120)
   - YAGNI violation: new abstraction not warranted by actual usage
   - changelog.md not updated when the plan modifies public behaviour

   🟡 MINOR
   - Naming inconsistent with surrounding module conventions
   - Comments redundant with the code
   - Minor style drift (will be caught by Black at commit)

4. Verify plan internal consistency:
   - Type/function signatures match across steps
   - Proposed tests cover the fix (not just the happy path)
   - Ambiguous decisions were escalated to the user, not silently decided
   - YAGNI: every new file/function is strictly necessary
   - Reuse: the `REUSES:` field references real existing code

5. Final verdict, explicit on a single line:
   - ✅ **APPROVED** — no 🔴, 🟠 acceptable or absent
   - ⚠️ **APPROVED WITH RESERVATIONS** — no 🔴, but 🟠 to fix
   - ❌ **NEEDS REVISION** — at least one 🔴

## Post-dispatch behavior — first run

After the subagent returns its critique:

1. Print the critique to chat.
2. Check the verdict:
   - **✅ APPROVED** or **only 🟡 MINOR** items remain → print:
     > ✅ Plan approuvé. Lance `/apply-plan` quand tu es prêt.
     End the turn. Do not start the auto-cycle.
   - **❌ NEEDS REVISION** or **⚠️ APPROVED WITH RESERVATIONS**
     with 🟠 items → start the **auto-cycle** (see below).

## Auto-cycle — refine + re-challenge (up to 5 iterations)

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
  6. CHECK STOPPING CONDITIONS
  7. CYCLE = CYCLE + 1
  8. repeat
```

### Stopping conditions

| Condition                               | Action                                                                                       |
| --------------------------------------- | -------------------------------------------------------------------------------------------- |
| ✅ APPROVED                             | Print "✅ Plan approuvé après N cycle(s). Lance `/apply-plan`." — stop                      |
| Only 🟡 MINOR remain                    | Print "✅ Seulement des points mineurs. Lance `/apply-plan`." — stop                        |
| Decision needed (raised by refine-plan) | Stop, ask user — they apply the decision then re-trigger `/challenge-plan` from CYCLE=1     |
| CYCLE = 5 with ❌ or 🟠 still present   | Escalate (see below) — stop                                                                  |

### Escalation at cycle 5

```text
⚠️ 5 cycles sans approbation complète.

Points persistants : [résumé des 🔴/🟠 qui reviennent cycle après cycle]
Cause probable     : [pourquoi ces points ne se résolvent pas]

Options :
  A. Revoir l'approche → /diagnose avec une nouvelle direction
  B. Accepter l'état actuel (🟠 restants, aucun 🔴) → /apply-plan
     [N'afficher cette option QUE si aucun 🔴 ne persiste]
  C. Continuer manuellement → /refine-plan puis /challenge-plan
```

## Constraints (non-negotiable)

- **Source code is read-only**: no edits outside `PLAN_*.md` at repo
  root or OpenSpec artifact files.
- Respect `CLAUDE.md`: pytest (not unittest directly), Black (line
  length 120), flake8 (max complexity 10), mypy strict, Grep tool
  (not `grep` in Bash), changelog.md required on public API changes.
- **No performative criticism**: if the plan is good, say so plainly.
- **No "nice to have"**: only flag what prevents a real problem.
- **Subagent is critic only**: produces a critique, not a correction.
