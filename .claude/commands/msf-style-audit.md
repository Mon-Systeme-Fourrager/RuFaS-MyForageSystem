---
description: Re-mine recent PR review comments, diff the recurring style conventions against the current MSF gate config, and propose concrete rule updates (the gate's maintenance loop).
argument-hint: "[optional: PR numbers or an updated:>=YYYY-MM-DD window; defaults to the latest PRs]"
allowed-tools: Read, Grep, Glob, Edit, Write, Agent, Workflow, ToolSearch, Bash(git:*), Bash(python:*), Bash(python3:*), Bash(python3.12:*), Bash(ruff:*), Bash(black:*), Bash(flake8:*), Bash(mypy:*), Bash(pytest:*)
---

$ARGUMENTS

Invoke the **`msf-style-audit`** skill (`.claude/skills/msf-style-audit/SKILL.md`) and
follow its procedure exactly: gather the review feedback for the PRs in scope,
categorise it against the `T##` themes in `tools/msf_style/STYLE_RULES.md`, diff against
the current gate, guard new mechanical rules against legacy noise, and **propose** the
config/test/doc updates for approval before applying anything.
