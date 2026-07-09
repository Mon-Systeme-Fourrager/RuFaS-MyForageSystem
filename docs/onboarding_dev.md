# Developer onboarding — RuFaS MyForageSystem fork

A practical guide for anyone contributing to this fork (including new devs). It covers the
**fork discipline**, the **local tooling** (matching CI exactly), **Claude Code**,
**OpenSpec**, and **where every config lives** so you know what to tweak.

Read this once, then keep [`.claude/rules/style.md`](../.claude/rules/style.md) open as the
day-to-day style reference (it has before/after examples for every convention).

---

## 1. Context — this is a fork, avoid recurrent merge conflicts

This repository (`RuFaS-MyForageSystem`) is a **fork** of upstream
`RuminantFarmSystems/RuFaS`. It is **never merged back upstream**: instead `dev` is synced
from upstream and our integration branch **`dev-msf`** tracks it (see the diagram in
`README.md`). Tags cut from `dev-msf` feed `rufas-api` and `msf-rufas`.

Because of this, the single most important habit is **minimize divergence from upstream**:

- **Isolate fork-only changes in their own files** (e.g. `.pre-commit-config.yaml`,
  `.coderabbit.yaml`, `.gemini/`, `.claude/`, `docs/*`) rather than editing large
  upstream-shared files.
- **Do not reformat or churn** upstream code you are not functionally changing — every such
  edit becomes a merge conflict on the next upstream sync.
- Touch shared files (`pyproject.toml`, `README.md`, workflows) only when necessary, and keep
  the change small and localized.

Your PRs and the review bots are configured to flag violations of this.

---

## 2. One-time setup

```bash
# Python — use the version required by pyproject.toml (requires-python)
python -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"          # black, flake8, mypy, pytest, coverage, …
pip install pre-commit           # the pre-commit runner (not in [dev])

# Git hooks that mirror CI (see §4)
pre-commit install --hook-type pre-commit --hook-type pre-push

# OpenSpec CLI (Node tool; use npx or install globally)
npx @fission-ai/openspec --help  # or: npm i -g @fission-ai/openspec
```

---

## 3. Local dev commands — read config FROM the files, don't hard-code

These are the **exact commands the CI runs** (from
`.github/workflows/combined_format_lint_test_mypy.yml`). Each tool reads its own config file,
which is the single source of truth — never hard-code line length, ignore lists, etc.

| Tool | Command (local) | Config file |
| --- | --- | --- |
| Black (format) | `black .` | `pyproject.toml` `[tool.black]` |
| flake8 (lint) | `flake8 .` | `.flake8` |
| mypy (types, strict) | `python -m mypy .` | `pyproject.toml` `[tool.mypy]` (CI ratchets vs `dev`) |
| Tests + coverage | `coverage run --rcfile=.github/.coveragerc && coverage report --rcfile=.github/.coveragerc` | `.github/.coveragerc` |

Run every hook at once locally: `pre-commit run --all-files`.

---

## 4. Pre-commit = CI, locally

`.pre-commit-config.yaml` uses `local`/`system` hooks that invoke the **same tools installed by
`pip install -e ".[dev]"`**, reading the **same config files** — so what passes locally passes
in CI.

- **on `git commit`** (staged files): Black, flake8.
- **on `git push`** (whole project): `python -m mypy .` (mirrors CI).

Skip the mypy hook occasionally with `SKIP=mypy git push`, but never push red.

---

## 5. Style rules — where they come from and how they're enforced

The recurring RuFaS review conventions are enforced at three layers (no custom validation
script):

| Layer | Where | What it does |
| --- | --- | --- |
| Deterministic linters | `.flake8` + `pyproject.toml` (Black, mypy) via pre-commit and CI | mechanical rules: formatting, complexity, imports, typing |
| Review bots | `.coderabbit.yaml`, `.gemini/styleguide.md` | the conventions no linter expresses (magic numbers to constants, None-safe config, enum-over-string, mocking discipline) + fork guidance |
| Write-time rule | `.claude/rules/style.md` | steers Claude Code to write compliant code up front |

Human-readable reference for **every** rule (with before/after examples):
[`.claude/rules/style.md`](../.claude/rules/style.md). It also lists the **accepted legacy
style you must NOT "fix"** (scientific sigils, published coefficients, `dict[str, Any]`
boundaries, god-object calculators).

---

## 6. Claude Code

This repo is set up for [Claude Code](https://claude.com/claude-code).

- **Layered `CLAUDE.md`**: the root file is repo-wide; subsystem `CLAUDE.md` files load when you
  open files there (`RUFAS/`, `RUFAS/biophysical/animal/`, `tests/`, …).
- **Path-scoped rules** (`.claude/rules/`): load automatically when a matching file is in
  context — `protected-inputs.md` (never edit protected fixtures) and `style.md` (new-code
  conventions).
- **Skills / slash commands** (`.claude/skills/`, `.claude/commands/`): TDD, systematic
  debugging, writing plans, code review, the `rufas-design-doc` and `rufas-e2e-testing`
  skills, and the OpenSpec commands below.
- **Output style**: caveman lite by default (`/caveman lite`) — concise. Do **not** use
  `caveman full/ultra` on model logic, typing, or numeric outputs (see `AGENTS.md`).
- **Hooks** (`.claude/settings.json` and `.claude/hooks/`): a SessionStart hook injects the
  dependency graph and, on Claude Code Web, installs the caveman plugin.

Other AI tools (Cursor, Windsurf, Copilot) read `AGENTS.md`; Gemini reads `CLAUDE.md` via
`.gemini/settings.json`.

---

## 7. OpenSpec (spec-driven changes)

For non-trivial changes, use the OpenSpec flow to agree the spec before coding.

```
/opsx:propose      # create a change proposal + specs + tasks
/opsx:apply        # implement the tasks (TDD)
/opsx:sync         # sync delta specs into the main specs (the optional sync skill)
/opsx:archive      # archive the change after merge
```

- CLI: `openspec list`, `openspec validate` (`npx @fission-ai/openspec`).
- Project context and per-artifact rules live in **`openspec/config.yaml`** (fork constraint,
  tooling, conventions). Edit that file to tune what OpenSpec generates.

For very large work (~1 engineer-month), start with a **design doc** (`rufas-design-doc`
skill) before OpenSpec/coding.

---

## 8. Where to tweak what

| You want to change… | Edit |
| --- | --- |
| Black / mypy settings | `pyproject.toml` (`[tool.black]` / `[tool.mypy]`) |
| flake8 settings | `.flake8` |
| Which hooks run pre-commit | `.pre-commit-config.yaml` |
| What CodeRabbit enforces | `.coderabbit.yaml` (`path_instructions`) |
| What Gemini enforces | `.gemini/styleguide.md` (+ `.gemini/config.yaml`) |
| OpenSpec context / rules | `openspec/config.yaml` |
| New-code conventions (and the human style reference) | `.claude/rules/style.md` |
| Protected input list | `.claude/rules/protected-inputs.md` (matches the CI list) |
| CI itself | `.github/workflows/combined_format_lint_test_mypy.yml` |

---

## 9. PR checklist

1. Keep the diff minimal and fork-conflict-free (isolate fork-only changes in their own files).
2. `pre-commit run --all-files` green (Black, flake8, mypy).
3. Tests + coverage pass (`coverage run --rcfile=.github/.coveragerc`).
4. **`changelog.md`** updated for RuFaS model/system changes: one bullet, real PR link (no
   `TBD`), one of `[InputChange]`/`[NoInputChange]` and one of `[OutputChange]`/`[NoOutputChange]`.
5. No protected input fixtures edited.
6. PR description: what / why / how + a Test Plan; link the issue.
7. Two reviews + all CI green before merge (author merges and deletes the branch).
