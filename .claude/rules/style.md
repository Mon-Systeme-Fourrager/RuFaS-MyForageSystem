---
paths:
  - "RUFAS/**/*.py"
  - "tests/**/*.py"
  - "main.py"
---

# Style — RuFaS new-code conventions

The recurring RuFaS review conventions (from the wiki
[Code review](https://github.com/RuminantFarmSystems/RuFaS/wiki/Code-review) guide and
repeated PR feedback). Follow them while writing **new/changed** code so it clears review
in one pass.

Applies to **added/changed lines only** — never reformat or "fix" untouched legacy code
to satisfy these; keeping the diff minimal is itself a rule.

## Always, in new code

- **Enums, not string literals** for domain values (sex, animal type, post-weaning
  destination, reproduction protocol, event names) — in production **and tests**.
  `Enum == "str"` is always `False`; that has caused real bugs.
- **Named constants, not magic numbers** in `RUFAS/biophysical/**` and `RUFAS/EEE/**`:
  put coefficients/thresholds in a `*_constants.py` with their NRC/published reference.
- **None-safe config parsing**:
  - Test `if x.get(key) is None:` — never `x.get(key) or default` (it eats an explicit
    `0`/`0.0`), and never `int(x.get(key))`/`float(...)` without a `None` guard
    (`int(None)` raises `TypeError`).
- **NumPy-style docstring on every added/modified function** — including pytest fixtures
  and test helpers, with `Parameters`/`Returns` matching the real signature.
- **Full type annotations** — mypy runs `--strict`; every function needs complete types.
- **Imports at top level.** In-function imports only to break a real circular import, and
  say why.
- **Cyclomatic complexity ≤ 10** (flake8 `max-complexity`) — extract helpers; do **not**
  add `# noqa: C901`.

## Tests

- Patch with `mocker.patch.object(Cls, "method")` / `with patch(...)` — **never**
  `SomeClass.attr = MagicMock()` (leaks across tests, no teardown).
- Assert **behaviour**, not just return type or `call_count`; seed real data so
  assertions aren't vacuously true.
- Isolate class state with an autouse save/restore fixture using `copy.deepcopy`
  (a shallow `dict()` shares nested objects).
- `pytest.raises(...)` needs a `match=` so it can't pass on the wrong failure path.

## Small stuff reviewers flag

Redundant quoted annotations under `from __future__ import annotations`; `.get(k, None)`
→ `.get(k)`; `dict()`→literal; blind `except Exception` and `raise ... from e`; ambiguous
unicode `–`/`×` in strings/docstrings/comments; bare `# type: ignore` (pin `[code]`); no
`Lesson N`/`Task N.N` scaffolding references left in committed code.

## changelog.md (mandatory every PR)

One bullet per PR:
`- [NN](https://github.com/.../pull/NN) - [Major/minor change] [Impact Area] [NoInputChange|InputChange] [NoOutputChange|OutputChange] description`.
No `TBD`; never tag the same PR both `[OutputChange]` and `[NoOutputChange]`; no duplicate
bullets for the same PR.

## Do NOT "fix" these — they are accepted RuFaS style

Scientific sigils (`TDN`, `NEm`, `DMI`, `pH`, `ADG`, `BW`, …); published SWAT/Parton/NRC
coefficients; `dict[str, Any]` / `Any` at JSON/config/pool boundaries; god-object managers
and ~20-parameter NRC calculators; `class X(object)`; long exception messages. These are
intentional — do not condemn them retroactively.
