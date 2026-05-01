---
description: Diagnose, produce a fix plan, and persist it to PLAN_<slug>.md
argument-hint: [description, file path, or paste logs]
model: claude-sonnet-4-6
allowed-tools: Read, Grep, Glob, Write, Edit, Bash(git log:*), Bash(git diff:*)
# Write and Edit are scoped to PLAN_<slug>.md at repo root (RuFaS convention,
# CLAUDE.md). No other file may be written by this command. The incremental
# write strategy (see ### Write strategy) uses Write for the header section
# and Edit for each subsequent section append.
---

$ARGUMENTS

## Step 1 — Silent analysis

Invoke `superpowers:systematic-debugging` to find the root cause, then
`superpowers:writing-plans` to draft the plan structure internally.

**Read-only at this stage**: explore with Read, Grep, Glob only.
No files may be written until Step 3.

### 1a — Graphify impact check

If `graphify-out/GRAPH_REPORT.md` exists, read it before exploring source files.
Identify which god nodes (high-degree files) are in the blast radius of the
reported problem. Use this to prioritize which files to read first and to
anticipate ripple effects in the plan.

## Step 2 — Interactive confirmation

Before writing anything to disk, confirm direction with the user.

### 2a — Problem and approach

Ask 2–4 targeted questions about:

- The root cause identified (e.g. « J'ai trouvé X comme cause — est-ce bien
  le problème observé ? »)
- Scope or behavior ambiguities
- Preferred approach when multiple valid solutions exist: present 2–3 concrete
  options with trade-offs and a recommendation

One question set per message. **Wait for the user's answers before continuing.**

### 2b — UI wireframes (UI changes only)

If the plan involves visible output or report changes, render a compact ASCII
before/after sketch alongside the confirmation questions. Keep it brief (≤ 10
lines per frame).

## Constraints

- **Do not modify source files.** The only write allowed is the final
  `PLAN_<slug>.md` at repo root (see Step 3 below).
- Respect CLAUDE.md: pytest (not unittest directly), Grep tool (not `grep`
  in Bash), Black formatting, line length 120.
- YAGNI: the minimum required to fix the identified problem, nothing more.

## Step 3 — Persist

Once the user has confirmed the direction in Step 2, write the plan to disk.

### Slug derivation

From the plan title, derive `<slug>` as kebab-case, ASCII only,
≤ 40 characters. Examples:

- "Fix race condition in simulation loop" → `fix-race-condition-simulation-loop`
- "Add field manager unit tests" → `add-field-manager-unit-tests`

### Collision handling (non-negotiable)

Before writing, check whether `PLAN_<slug>.md` already exists at repo
root (use `Glob` with pattern `PLAN_<slug>.md`).

- If **no existing file** → write `PLAN_<slug>.md` with the plan
  verbatim (header included, nothing else), following the
  `### Write strategy` below.
- If **an existing file is present** → **STOP**. Do not overwrite.
  Do not auto-append a numeric suffix. Ask the user:

  > `PLAN_<slug>.md` already exists. Should I (a) choose a different
  > slug, (b) overwrite (previous plan lost unless committed), or
  > (c) abort?

  Wait for the answer before writing.

### Write strategy (non-negotiable)

Plans above ~3 KB routinely cause `Stream idle timeout` on a single
`Write` call. To prevent this, never persist a plan in one call —
even if it looks short:

1. **Split the plan into logical sections** before writing. Each
   tool call targets one section (≤ 2 KB of text). Sections map to
   the plan's own structure:
   - Header (`## Plan — <title>`) + scope summary → first `Write`
     call (this creates the file).
   - Each `📝` / `✨` / `🗑️` block → one `Edit` append each.
   - `🧪` Tests block → one `Edit` append.
   - `YAGNI CHECK` + `REUSES` → one final `Edit` append.

   If a single section exceeds 2 KB, split it further at logical
   boundaries. **Never produce a tool call whose text payload
   exceeds 2 KB.**

2. **Verify after the first `Write`**: immediately `Read` the file
   path. If the `Read` errors or returns empty content → the write
   failed silently. Print:

   > ⚠️ L'écriture de `PLAN_<slug>.md` a échoué (timeout probable).
   > Relance `/diagnose` — le plan sera ré-écrit. Si le problème
   > persiste, copie manuellement le contenu ci-dessous dans le
   > fichier `PLAN_<slug>.md` à la racine du repo.

   Then print **only the header + first section** (≤ 50 lines) as
   a fallback the user can copy. Never print the full plan body.

3. **Chain the section writes automatically.** Issue the header
   `Write` and each subsequent `Edit` append in succession, one
   section per tool call, without pausing to ask the user to
   confirm between sections.

4. **Verify after the last `Edit` append**: `Read` the file and
   confirm it ends with the `REUSES` section. If truncated, print:

   > ⚠️ `PLAN_<slug>.md` est incomplet (écriture partielle). Les
   > sections manquantes sont listées ci-dessous — ajoute-les
   > manuellement à la fin du fichier.

   Then print only the missing sections (≤ 50 lines per chat block).

5. **Never retry a full-file write after a timeout.** Always `Read`
   first to determine what is already on disk, then append only
   the missing sections incrementally.

## Step 4 — Récap et remise

After all writes and verification complete, print the summary block:

```text
─── Récap du plan ──────────────────────────────────────────
Problème : [root cause in 1 sentence]
Solution  : [approach in 1-2 sentences]
Fichiers  : [short file list]
Tests     : [what will be verified]
────────────────────────────────────────────────────────────
Modifications avant challenge ? Réponds en chat.
Sinon tape /challenge-plan pour lancer la validation.
```

If the user replies with adjustments:

1. Apply surgical `Edit` calls to `PLAN_<slug>.md` (≤ 2 KB per call).
2. Re-display the summary block above.
3. Repeat until the user types `/challenge-plan` or confirms readiness.

**Do not proceed to challenge automatically.** The user always
triggers `/challenge-plan` manually for the first run.
