# RuFaS style guide (for Gemini Code Assist)

Follow these conventions when reviewing RuFaS (MyForageSystem fork) pull requests. Review
**added/changed lines only** — never ask to "fix" untouched legacy code. Full,
example-driven reference: `docs/style_rules_explained.md`.

Context: this is a **fork** that is never merged back upstream. Flag changes that would
cause recurrent merge conflicts on re-sync with `RuFaS/dev` (e.g. reformatting or editing
large upstream-shared files unnecessarily).

## Enforce on new code

- **Named constants, not magic numbers** in `RUFAS/biophysical/**` and `RUFAS/EEE/**`:
  coefficients/thresholds belong in a `*_constants.py` with an NRC/published reference.
- **None-safe config parsing**: require an explicit `is None` check. Never
  `x.get(key) or default` (drops a real `0`/`0.0`); never `int(x.get(key))`/`float(...)`
  without a `None` guard.
- **Enums, not string literals** for domain values (sex, animal type, destination,
  reproduction protocol, event names), in production and tests. `Enum == "str"` is always
  `False`.
- **Return a copy** of a class-level `dict`/`list`/`set`, never the shared attribute.
- **NumPy-style docstring** on every added/modified function (incl. fixtures/test helpers),
  with `Parameters`/`Returns` matching the real signature.
- **Full type annotations** (mypy runs `--strict`); **top-level imports** (in-function only
  to break a real cycle); **cyclomatic complexity ≤ 10** (no new `# noqa: C901`).
- **Tests assert behaviour**, not just return type / `call_count`; use
  `mocker.patch.object` (never `Class.attr = MagicMock()`); `copy.deepcopy` for state
  isolation; `pytest.raises(..., match=...)`.
- **changelog.md**: exactly one bullet per PR; no `TBD`; not both `[OutputChange]` and
  `[NoOutputChange]`.

## Do NOT flag (accepted legacy style)

Scientific sigils (`TDN`, `NEm`, `DMI`, `pH`, `ADG`, `BW`); published SWAT/Parton/NRC
coefficients; `dict[str, Any]` / `Any` at JSON/config boundaries; god-object managers and
~20-parameter NRC calculators; `class X(object)`; long exception messages.
