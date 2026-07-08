---
description: Review the current branch diff for RuFaS judgement-level style conventions the automated gate cannot decide (enum-over-string, docstring content, DRY, scientific refs, test quality).
allowed-tools: Read, Grep, Glob, Bash(git:*), Bash(python:*), Bash(python3:*), Bash(python3.12:*)
---

$ARGUMENTS

Invoke the **`msf-style-review`** skill (`.claude/skills/msf-style-review/SKILL.md`) and
follow its procedure exactly: run the deterministic gate first, then review only the
added/changed lines versus `origin/dev-msf` against the judgement checklist, and report
actionable findings grouped by severity.
