---
paths:
  - "RUFAS/**/*.py"
  - "tests/**/*.py"
  - "main.py"
---

# Style — RuFaS new-code conventions

This is a fork: we try to avoid changes that would result in recurrent merge conflicts
since it will never be merged in the main repository. So these conventions apply to
**added/changed lines only** — never reformat or "fix" untouched legacy code; keeping the
diff minimal is itself the rule.

Only conventions that **no linter enforces** live here. Black, flake8 (`.flake8`) and mypy
`--strict` (`pyproject.toml`) already cover formatting, complexity, imports and typing —
read those config files, don't restate them.

## Semantic conventions (no tool checks these)

- **Enums, not string literals** for domain values (sex, animal type, post-weaning
  destination, reproduction protocol, event names) — production **and tests**.
  `Enum == "str"` is always `False`; that has caused real bugs.
- **Named constants, not magic numbers** in `RUFAS/biophysical/**` and `RUFAS/EEE/**`:
  put coefficients/thresholds in a `*_constants.py` with their NRC/published reference.
- **None-safe config parsing**: test `if x.get(key) is None:` — never `x.get(key) or
  default` (eats an explicit `0`/`0.0`), and never `int(x.get(key))`/`float(...)` without
  a `None` guard (`int(None)` raises `TypeError`).
- **NumPy-style docstring** on every added/modified function — including fixtures and test
  helpers, with `Parameters`/`Returns` matching the real signature.

## Tests

- Patch with `mocker.patch.object(Cls, "method")` / `with patch(...)` — **never**
  `SomeClass.attr = MagicMock()` (leaks across tests, no teardown).
- Assert **behaviour**, not just return type or `call_count`; seed real data.
- Isolate class state with an autouse save/restore fixture using `copy.deepcopy`.
- `pytest.raises(...)` needs `match=` so it can't pass on the wrong failure path.

## Recurring review nits (not caught by the base linters)

- Blind `except Exception:` — catch the specific type; re-raise with `raise ... from e`.
- Ambiguous unicode (`–`, `×`) in strings/docstrings/comments — use ASCII.
- `# type: ignore` → pin the code: `# type: ignore[code]`.

## Do NOT "fix" these — accepted RuFaS style

Scientific sigils (`TDN`, `NEm`, `DMI`, `pH`, `ADG`, `BW`, …); published SWAT/Parton/NRC
coefficients; `dict[str, Any]` / `Any` at JSON/config/pool boundaries; god-object managers
and ~20-parameter NRC calculators; `class X(object)`; long exception messages. These are
intentional — do not condemn them retroactively.
