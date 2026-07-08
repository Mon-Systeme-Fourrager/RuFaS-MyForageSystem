# MSF style rules — catalogue & provenance

Canonical mapping of every convention the MSF style gate enforces (or defers to the
review skill), where it came from in past reviews, and how it is checked. **This file is
the source of truth** that `/msf-style-audit` compares fresh PR feedback against and
updates. Keep it in sync with `ruff_msf.toml` and `custom_checks.py`.

Rules were mined from PRs #18, #25, #26, #32, #33, #34, #35, #36, #38 (reviewers:
`jrobichaud` human SME, `coderabbitai`, `gemini-code-assist`, `github-actions` ratchets,
CodeQL).

## Enforcement layers

| Layer | Where | What |
| --- | --- | --- |
| Ruff (`ruff_msf.toml`) | gate + hook + CI | stock rules, diff-filtered |
| Custom AST/text (`custom_checks.py`) | gate + hook + CI | project-specific `MSF0xx` |
| Changelog (`changelog_check.py`) | gate + CI | `changelog.md` format |
| Per-file mypy (`mypy_checker.py`) | gate + CI (`--mypy`) | closes count-ratchet hole |
| Review skill (`/msf-style-review`) | in-session, pre-PR | judgement rules (no linter can decide) |

All deterministic layers are **diff-aware**: only lines the branch adds/changes versus
`origin/dev-msf` (and whole new files) are judged. This is the deliberate mechanism that
keeps accepted legacy patterns from being flagged.

## Automated rules

| Theme (review tag) | Code(s) | Checker | Notes |
| --- | --- | --- | --- |
| T1 magic coefficient in domain code | `MSF001` | custom | floats ≠0.0/1.0 in `RUFAS/biophysical`+`RUFAS/EEE`, excl. `*_constants.py` |
| T1 numeric `.get` default in domain code | `MSF002` | custom | name the fallback in `*_constants.py` |
| T2 `.get(k) or default` | `MSF010` | custom | `or` eats explicit `0`/`0.0` |
| T2 `int()/float()` on possibly-None `.get` | `MSF011` | custom | guard `is None` first |
| T3 docstring presence on new API | `D101 D102 D103 D106 D419` | ruff | numpy convention; content quality → skill |
| T5 class-attr mock in tests | `MSF020` | custom | use `mocker.patch.object` |
| T6/T19 mutable classvar returned raw | `MSF030` | custom | return `.copy()`/deepcopy |
| T8 redundant quoted annotation | `UP037` | ruff | under `from __future__ import annotations` |
| T8 missing `from __future__` | `FA102` | ruff | |
| T10 broad `pytest.raises` | `PT011` | ruff | add `match=` |
| T11 new `# noqa: C901` | `MSF040` | custom | split under complexity 10 |
| T12 blind except / no chaining | `BLE001 B904` | ruff | |
| T15 ambiguous unicode | `RUF001 RUF002 RUF003` | ruff | en-dash, ×, … |
| T18 deprecated typing import | `UP035` | ruff | use `collections.abc` |
| T18 `dict()`/`list()` call | `C408` | ruff | literal |
| T18 `.get(k, None)` | `SIM910` | ruff | |
| T18 suppressible try/except-pass | `SIM105` | ruff | `contextlib.suppress` |
| T18 fixture parens / tuple names | `PT001 PT006` | ruff | |
| T18 unused arguments | `ARG001 ARG003 ARG004` | ruff | |
| T18 one-line implicit str concat | `ISC001` | ruff | |
| RUF012 mutable ClassVar | `RUF012` | ruff | annotate `ClassVar` |
| T19 blanket noqa | `PGH004` | ruff | pin a code |
| T19 bare `# type: ignore` | `MSF042` | custom | pin `[code]` |
| T19 scaffolding reference | `MSF041` | custom | comments/docstrings only |
| T7 import outside top level | `PLC0415` | ruff | tolerated only to break real cycles |
| T9 changelog `TBD` placeholder | `MSF050` | changelog | |
| T9 contradictory output tags | `MSF051` | changelog | one of `[OutputChange]`/`[NoOutputChange]` |
| T9 duplicate PR bullet | `MSF052` | changelog | one entry per PR |
| ratchet hole: new untyped code | `mypy:*` | mypy | per-file strict, added lines only |

## Deliberately NOT enforced (accepted legacy style)

Turning these on — even on new code — would fight conventions the project has agreed to.
Do **not** add them without team sign-off (documented in `ruff_msf.toml`):

- **pep8-naming `N8xx`** — scientific sigils are intentional (`TDN`, `NEm`, `DMI`, `pH`,
  `ADG`, `BW`, `CP`, `NDF`, `ME`, `TBV`, …). A naming rule needs a sigil allowlist first.
- **`PLR2004` magic values** — published SWAT/Parton/NRC coefficients are everywhere;
  `MSF001`/`MSF002` are the scoped, softer replacement.
- **`PLR09xx` too-many-\*** — NRC calculators legitimately take ~20 parameters; managers
  are large by design.
- **`ANN401` / `dict[str, Any]`** — `Any` is accepted at JSON/config/pool boundaries
  (~468 occurrences in legacy).
- **`UP004`/`UP008`, `TRY003`** — `class X(object)`, `super(X, cls)`, long exception
  messages are tolerated.
- **pydocstyle `D203`/`D212`/`D213`** — disabled via the numpy convention to match the
  existing docstring layout.

## Judgement rules — handled by `/msf-style-review`, not a linter

No deterministic checker can decide these; the review skill covers them:

- **T1 semantic** — does the named constant carry the correct NRC 2016 table/equation
  reference? Is a benchmark value physiologically meaningful?
- **T3 content** — meaningful prose; docstring ↔ signature in sync; ratio direction.
- **T4 enum-over-string** — replace raw string literals with the domain enum in prod
  *and* tests (`Enum == "str"` is always False). The single human reviewer's #1 theme.
- **T5 mocking judgement** — patch a real method vs rewiring a whole collaborator to
  `MagicMock`; minimal typed stub vs `MagicMock`.
- **T13** — tests assert behaviour, not just return type / `call_count`.
- **T14 diff-minimal** — do not reformat untouched RuFaS code just to satisfy a linter.
- **T17 DRY** — where to extract the shared helper; right abstraction level.
- Guard symmetry across twin beef/feedlot/dairy paths; deterministic vs random defaults;
  onion-architecture placement; output-unit semantics.

---

Last audited: PRs #18–#38 (initial catalogue). Update this line from `/msf-style-audit`.
