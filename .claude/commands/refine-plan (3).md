---
description: Revise an existing plan in-place after /challenge-plan (surgical edit, read-only on source code)
argument-hint:
  [leave empty if /challenge-plan just ran, OR openspec:<change-name>, OR PLAN_<slug>.md path]
model: claude-sonnet-4-6
allowed-tools: Read, Grep, Glob, Edit, Bash(git log:*), Bash(git diff:*)
# Edit is scoped to PLAN_*.md at repo root OR OpenSpec artifact files
# under openspec/changes/<name>/. No source files may be written.
# The plan source is created by /diagnose or /opsx:propose and
# modified in place here — git holds the version history.
---

$ARGUMENTS

**When to use this command manually**: `/refine-plan` is for manual
use when you want to apply corrections yourself — typically when you
interrupted the `/challenge-plan` auto-cycle (e.g. a decision was
escalated to you), or when you want to apply your own changes before
re-challenging. During a normal auto-cycle, `/challenge-plan` handles
the refine step inline without requiring you to run this command.

**You are the main agent** — no subagent dispatch here. You have full
session context (original plan + `/challenge-plan` critique) and must
**surgically edit the active plan source** (`PLAN_<slug>.md` at repo
root in PLAN mode, or the OpenSpec artifact files in OpenSpec mode)
so it can be re-challenged.

## Input resolution

You need two things: the **plan source** and the
**`/challenge-plan` critique**. Two plan formats are supported.

### OpenSpec mode

If `$ARGUMENTS` matches `openspec:<name>`, OR `$ARGUMENTS` is empty
and the session context shows an OpenSpec change was challenged →
resolve:

- `openspec/changes/<name>/proposal.md` — scope/why changes
- `openspec/changes/<name>/design.md` — architecture/how changes
- `openspec/changes/<name>/tasks.md` — task list changes

Route each critique point to the right artifact:

- Scope, requirements, goals → `proposal.md`
- Architecture, tech choices, component design → `design.md`
- Task breakdown, order, missing steps → `tasks.md`

Store `mode: openspec` and `change_name: <name>`.

### PLAN\_\*.md mode

Identify the plan file path and critique in this order:

1. If `$ARGUMENTS` is a file path → resolve to that `PLAN_*.md`
   file. The critique is retrieved from the current conversation
   (the last `/challenge-plan` output).
2. Else if `$ARGUMENTS` is empty → retrieve from the current
   conversation both the last plan file path (typically
   `PLAN_<slug>.md` created by `/diagnose`) and the last critique
   produced (typically from `/challenge-plan`).
3. Else (`$ARGUMENTS` contains prose, a pasted plan, a pasted
   critique, or any non-path) → **refuse**. Print exactly:

   > `/refine-plan` requires the plan as a file path. The critique
   > is read from the current session (the last `/challenge-plan`
   > output). Re-run without arguments, or pass the
   > `PLAN_<slug>.md` path alone.

   Do not parse inline plan/critique bodies: coordinating around a
   single file is what keeps the chain safe from stream idle
   timeouts on the next `/challenge-plan` or `/apply-plan`.

4. If either the plan path or the critique is missing after steps
   1-2 → ask the user for it before proceeding. Do not guess.

The plan file already exists on disk (created by `/diagnose`). Do
**not** attempt to recreate it — you edit it in place.

## Step 1 — Counter-validate the diagnosis

Before touching the plan, **question the root cause itself**. The
critique may have revealed that the original diagnosis targeted a
symptom rather than a cause.

Invoke `superpowers:systematic-debugging` and redo Phase 1–2 in light
of the critique:

- Do the 🔴 points in the critique indicate a wrong root-cause
  analysis, or just wrong execution of the fix?
- Do the existing patterns cited by the critique suggest a different
  approach?
- If 3+ 🔴 points all target the same area → it may be an
  architectural problem, not an execution problem (Phase 4.5 of
  systematic-debugging).

**If the diagnosis must change**: state it explicitly in chat after
editing, and re-justify the new root cause. Reflect the change inside
the plan file by editing the relevant sections (not by appending a
"v2" marker — git history tracks versions).

## Step 2 — Triage the critique

For each point raised by `/challenge-plan`, decide:

| Decision                        | When                                                             | What you do                                                      |
| ------------------------------- | ---------------------------------------------------------------- | ---------------------------------------------------------------- |
| ✅ **Accepted**                 | Valid point, correction obvious                                  | Apply a surgical `Edit` to the impacted section of the plan file |
| 🔄 **Accepted with adaptation** | Valid point but the suggested correction doesn't fit the context | Propose a different correction via `Edit`, explain why in chat   |
| ❌ **Rejected**                 | Invalid point, out of scope, or subagent misunderstanding        | Do not edit. Justify the rejection in chat in 1–2 sentences      |
| ❓ **Needs clarification**      | Real ambiguity that changes the nature of the fix (see below)    | **STOP** and ask the question before editing                     |

**Do not accept out of politeness.** A performative critique from the
subagent deserves a reasoned rejection, not a cosmetic correction.

## Step 3 — Clarifying questions

Ask a question before editing **only if**:

- The critique reveals multiple valid approaches with real trade-offs
  (large refactor vs. targeted patch, hook extraction vs. inline,
  adding a dependency vs. implementing manually).
- The correction changes user-facing behavior (even subtly).
- The critique touches shared code and you don't know which consumers
  are impacted.
- Two points in the critique contradict each other.
- The critique rejects a choice the user explicitly validated in an
  earlier decision in the session.

**Question format**: one at a time, 2–3 concrete options with
trade-offs and your recommendation. Wait for the answer before
continuing.

**Do not ask** when:

- There is only one correct fix.
- The decision is purely technical with no user impact.
- The choice is obvious from project conventions (`CLAUDE.md`).

## Step 4 — Apply surgical edits to the active plan source

**PLAN\_\*.md mode:** the plan file `PLAN_<slug>.md` lives at repo root.
**OpenSpec mode:** edit the relevant artifact(s) — `proposal.md`,
`design.md`, and/or `tasks.md` under `openspec/changes/<name>/`.

In both modes, you **do not rewrite from scratch**. You use the `Edit`
tool with targeted `old_string` / `new_string` pairs on the sections
impacted by the critique.

### Before editing

0. **Verify the plan source exists and is non-empty** (`Read` tool).
   This is a non-negotiable pre-flight check.

   **OpenSpec mode:** `Read` each of the three artifact files. If
   any is missing or empty → print:

   > ⚠️ `openspec/changes/<name>/<file>` is missing. Run
   > `/opsx:propose` to regenerate artifacts before refining.
   > **Stop.**

   **PLAN\_\*.md mode:** it catches the case where `/diagnose` timed
   out and never finished writing the file (or wrote a truncated
   stub). Specifically:
   - If `Read` errors (file not found) → print:

     > ⚠️ `PLAN_<slug>.md` is missing on disk. `/diagnose` likely
     > timed out. Run `/diagnose` to recreate it before refining.

     **Stop.** Do not attempt to recreate the file from session
     memory — that is `/diagnose`'s job, and improvising here
     would re-trigger the same write timeout.

   - If `Read` succeeds but the file is empty, does not start
     with `## Plan —`, does not contain at least one `📝` /
     `✨` / `🗑️` / `🧪` marker, or has no `REUSES` section → print:

     > ⚠️ `PLAN_<slug>.md` is empty or truncated. Run `/diagnose`
     > to regenerate it before refining.

     **Stop.** Wait for the user.

   - Otherwise → proceed to step 1.

1. **Read the plan file** (`Read` tool) to see its current exact
   content. `old_string` must match byte-for-byte — no line-number
   prefixes, no whitespace drift.
2. **Verify the header**: the plan uses `## Plan — <title>` (no
   `v1`/`v2`/`v3` — git history tracks versions). If you find a
   legacy `## Plan v2 —` header, normalize it to `## Plan — <title>`
   in the same edit pass.

### What to edit

For each accepted (✅) or adapted (🔄) critique point, locate the
smallest block in the plan file that needs to change and edit it:

- 📝 sections where BEFORE/AFTER must be corrected.
- ✨ sections where a file creation must be removed (rejected on YAGNI
  grounds) or added (new file surfaced by the critique).
- 🗑️ sections where a deletion target must be adjusted.
- 🧪 sections where expected RED/GREEN tests must be revised.
- `REUSES:` lines where a cited path/utility needs correction (verify
  with `Read`/`Glob` before finalizing — a plan that cites
  non-existent paths is blocking per `/challenge-plan`).

Do **not** rewrite sections that the critique did not touch. Do
**not** introduce a "Summary of changes" block — the change log lives
in `git log` + the `/challenge-plan` critique that prompted this
revision.

### Rejected (❌) points

Do not edit the plan for rejected points. State the rejection in chat
after the edits land, in 1–2 sentences with the context that
contradicts the critique. The user can then decide whether to re-run
`/challenge-plan` or accept the rejection.

### Coherence checklist (self-check before concluding)

- Every 🔴 from the critique is either addressed by an `Edit` or
  rejected with justification in chat.
- Edited sections remain coherent with surrounding unchanged sections
  (no dangling cross-reference, no orphaned `REUSES:` line).
- No correction introduces new duplication or new dead code.
- Cited paths and utilities exist (verify with Read/Glob).
- YAGNI still respected.
- `CLAUDE.md` respected: Bun, co-located tests, no `npx`, no `grep`
  in Bash, CASL guards, i18n, design tokens, size-limit, RLS/pgTAP,
  edge function config.

### Chat output

After all edits land, print exactly one line to the user:

> Plan updated. Run `/challenge-plan` (PLAN mode) or
> `/challenge-plan openspec:<name>` (OpenSpec mode) to re-validate.

If you rejected any critique points, add the rejection justifications
in chat **after** that line (not inside the plan file).

## Constraints (non-negotiable)

- **Read-only for source code**: no edits to source files. In PLAN
  mode, edits are scoped to `PLAN_*.md` at repo root. In OpenSpec
  mode, edits are scoped to artifact files under
  `openspec/changes/<name>/`. No commits. The plan source itself
  (PLAN file or OpenSpec artifacts) is edited in place via `Edit`;
  its prior state lives in git history.
- **Surgical edits, not rewrite**: change only what the critique
  flagged. Sections the critique did not touch must not drift. If you
  feel the need to rewrite the whole file, stop and question the
  diagnosis (Step 1) instead.
- **No capitulation**: if the critique is wrong, reject and explain.
  The goal is a good plan, not a plan that appeases the critic.
- **No scope expansion**: corrections target the critique points only,
  not "while we're here, let's improve X".

## Full workflow

```
/diagnose         → questions interactives → PLAN_<slug>.md → récap
/challenge-plan   → critique (run 1, manuel)
                    → si ❌ ou ⚠️/🟠 : boucle auto démarre
                       refine inline → /challenge-plan → refine inline → …
                       (jusqu'à ✅, seulement 🟡, décision user, ou 5 cycles)
                    → si décision escaladée : /refine-plan (manuel) puis /challenge-plan
/apply-plan       → exécution du plan approuvé (toujours manuel)
```

En mode normal, `/challenge-plan` orchestre le cycle complet. Utilisez
`/refine-plan` manuellement seulement si vous interrompez le cycle
automatique.
