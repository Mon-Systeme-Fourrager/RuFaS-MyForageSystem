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

  ```python
  # before
  if animal.destination == "sell":
      ...
  # after
  if animal.destination is PostWeaning.SELL:
      ...
  ```

- **Named constants, not magic numbers** in `RUFAS/biophysical/**` and `RUFAS/EEE/**`:
  put coefficients/thresholds in a `*_constants.py` with their NRC/published reference.

  ```python
  # before
  hot_carcass_weight = live_weight * 0.62
  # after  (in animal_constants.py)
  HCW_YIELD_FRACTION = 0.62  # NRC 2016 Table 12-1
  hot_carcass_weight = live_weight * HCW_YIELD_FRACTION
  ```

- **None-safe config parsing**: test `if x.get(key) is None:` — never `x.get(key) or
  default` (eats an explicit `0`/`0.0`), and never `int(x.get(key))`/`float(...)` without
  a `None` guard (`int(None)` raises `TypeError`).

  ```python
  # before  (a user-entered 0 becomes 10!)
  n = config.get("num_cows") or 10
  # after
  n = config.get("num_cows")
  if n is None:
      n = 10
  ```

- **NumPy-style docstring** on every added/modified function — including fixtures and test
  helpers, with `Parameters`/`Returns` matching the real signature.

## Tests

- Patch with `mocker.patch.object(Cls, "method")` / `with patch(...)` — **never**
  `SomeClass.attr = MagicMock()` (leaks across tests, no teardown).

  ```python
  # before
  HerdManager.update = MagicMock()
  # after
  mocker.patch.object(HerdManager, "update")
  ```

- Assert **behaviour**, not just return type or `call_count`; seed real data.
- Isolate class state with an autouse save/restore fixture using `copy.deepcopy`.
- `pytest.raises(...)` needs `match=` so it can't pass on the wrong failure path.

  ```python
  # before
  with pytest.raises(ValueError):
      parse(bad_input)
  # after
  with pytest.raises(ValueError, match="num_cows must be positive"):
      parse(bad_input)
  ```

## Recurring review nits (not caught by the base linters)

- Blind `except Exception:` — catch the specific type; re-raise with `raise ... from e`.

  ```python
  # before
  except Exception:
      raise RuntimeError("load failed")
  # after
  except KeyError as e:
      raise RuntimeError("load failed") from e
  ```

- Ambiguous unicode (`–`, `×`) in strings/docstrings/comments — use ASCII (`-`, `x`).
- `# type: ignore` → pin the code:

  ```python
  # before
  x = thing()  # type: ignore
  # after
  x = thing()  # type: ignore[assignment]
  ```

## Do NOT "fix" these — accepted RuFaS style

Scientific sigils (`TDN`, `NEm`, `DMI`, `pH`, `ADG`, `BW`, …); published SWAT/Parton/NRC
coefficients; `dict[str, Any]` / `Any` at JSON/config/pool boundaries; god-object managers
and ~20-parameter NRC calculators; `class X(object)`; long exception messages. These are
intentional — do not condemn them retroactively.
