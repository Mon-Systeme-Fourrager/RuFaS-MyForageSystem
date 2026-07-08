# RuFaS style rules — explained

A plain-language reference for every style rule enforced on **new / changed** RuFaS code.
Each rule has a simple definition and a **before → after** example.

These conventions were mined from recurring RuFaS review feedback (the wiki
[Code review](https://github.com/RuminantFarmSystems/RuFaS/wiki/Code-review) guide plus
what reviewers ask for on nearly every PR). They apply to **added or changed lines only** —
never to untouched legacy code — and they sit **on top of** Black / flake8 / mypy (they do
not replace them).

Legend: 🟥 correctness (real bug risk) · 🟦 readability/style · 🟩 documentation ·
🟨 tests · 🟪 process (changelog).

**Who checks what:**
- **Mechanical linter** (deterministic, free) = the **custom `MSF0xx`** rules (§1) + the
  **Ruff** rules (§2) + the **mypy** pass (§3). Automatic, in the editor hook and CI.
- **AI / review agent** (judgement) = the §4 items no linter can decide, because they
  require understanding what the code *means*.
- **Accepted legacy style** (§5) = what we deliberately do **not** touch.

---

## 1. RuFaS custom rules (`MSF0xx`)

These encode the conventions RuFaS reviewers repeat on every PR and that no off-the-shelf
linter covers.

### 🟥 MSF001 — No "magic" number in domain code
A hard-coded scientific coefficient (a float other than `0.0`/`1.0`) in
`RUFAS/biophysical/**` or `RUFAS/EEE/**` must live in a `*_constants.py`, named, with its
NRC/published reference — otherwise nobody knows where the number came from.

```python
# before
hot_carcass_weight = live_weight * 0.62

# after  (in animal_constants.py)
HCW_YIELD_FRACTION = 0.62  # NRC 2016 Table 12-1
# then
hot_carcass_weight = live_weight * HCW_YIELD_FRACTION
```

### 🟥 MSF002 — No magic number as a `.get()` default
Same idea, for a config-read fallback. Name the default.

```python
# before
days = config.get("anestrus_days", 45)
# after
days = config.get("anestrus_days", BEEF_POSTPARTUM_ANESTRUS_DAYS)
```

### 🟥 MSF010 — Don't use `or` for a config default
`x.get(key) or default` also replaces a deliberate `0` or `0.0` (because `0` is "falsy").
Test `is None` explicitly.

```python
# before  (a user-entered 0 becomes 10!)
n = config.get("num_cows") or 10
# after
n = config.get("num_cows")
if n is None:
    n = 10
```

### 🟥 MSF011 — Don't coerce a possibly-`None` value with `int()`/`float()`
`int(config.get("x"))` crashes (`TypeError`) if the JSON key is `null`. Guard the `None`
case first.

```python
# before
count = int(config.get("num_cows"))
# after
raw = config.get("num_cows")
count = int(raw) if raw is not None else 0
```

### 🟨 MSF020 — In tests, don't assign a mock to a class attribute
`MyClass.method = MagicMock()` leaks from one test to the next (no teardown). Use
`mocker.patch.object`, which restores automatically after the test.

```python
# before
HerdManager.update = MagicMock()
# after
mocker.patch.object(HerdManager, "update")
```

### 🟥 MSF030 — Don't return a class-level dict/list/set as-is
Returning a mutable class attribute directly lets the caller mutate shared class state.
Return a copy.

```python
class RationManager:
    RATIONS = {"a": 1}

    @classmethod
    def all_rations(cls):
        return cls.RATIONS          # before: shared, caller can mutate class state

    @classmethod
    def all_rations(cls):
        return cls.RATIONS.copy()   # after: protected
```

### 🟦 MSF040 — No new `# noqa: C901`
flake8 enforces complexity ≤ 10, but you can **bypass** it with `# noqa: C901`. Forbidden
on new code: split the function into helpers instead of silencing it.

### 🟦 MSF041 — No `Lesson N` / `Task N.N` scaffolding reference
Leftover development notes (`# Lesson 3 ...`) must not stay in committed code.

### 🟦 MSF042 — No bare `# type: ignore`
Always pin the error code, so you don't accidentally mask something else.

```python
# before
x = thing()  # type: ignore
# after
x = thing()  # type: ignore[assignment]
```

### 🟪 MSF050 — No `TBD` placeholder in the changelog
Replace it with the real PR number and link before merge.

### 🟪 MSF051 — A changelog entry can't be both `[OutputChange]` and `[NoOutputChange]`
One entry = exactly one of the two tags.

### 🟪 MSF052 — No duplicate bullet for the same PR number
One changelog entry per PR.

---

## 2. Enabled Ruff rules

Ruff is a fast linter that adds rules flake8 (without plugins) does not have.

### Typing modernization
- **UP035** — 🟦 deprecated `typing` import: use `collections.abc`.
  `from typing import Mapping` → `from collections.abc import Mapping`
- **UP037** — 🟦 unnecessary quotes around a type when
  `from __future__ import annotations` is present.
  `def f(x: "int")` → `def f(x: int)`
- **FA102** — 🟦 uses modern syntax (`int | None`, `list[str]`) without importing
  `from __future__ import annotations` → add that import.

### pytest hygiene
- **PT001** — 🟨 fixture parenthesis style: `@pytest.fixture` → `@pytest.fixture()`.
- **PT006** — 🟨 `parametrize` names as a tuple: `"a,b"` → `("a", "b")`.
- **PT011** — 🟥 `pytest.raises` too broad: add `match=` so it can't pass on the wrong
  error.
  `pytest.raises(ValueError)` → `pytest.raises(ValueError, match="negative")`

### Simplification / style
- **SIM105** — 🟦 `try/except/pass` → `with contextlib.suppress(Error):`.
- **SIM910** — 🟦 `d.get(k, None)` → `d.get(k)` (`None` is already the default).
- **C408** — 🟦 `dict(a=1)` → `{"a": 1}` (the literal is faster and clearer).
- **ISC001** — 🟦 two strings stuck together on one line `"a" "b"` → one `"ab"` (usually a
  forgotten space).

### Ambiguous unicode
- **RUF001 / RUF002 / RUF003** — 🟦 deceptive characters (en-dash `–`, `×` sign, special
  spaces) in code / docstrings / comments → use proper ASCII (`-`, `*`).
- **RUF012** — 🟥 mutable class attribute without annotation: `X = {}` in a class →
  `X: ClassVar[dict] = {}` (avoids accidental shared state between instances).

### Correctness reviewers flagged
- **B904** — 🟥 inside an `except`, re-raise with `raise ... from err` (or `from None`) to
  keep the original traceback.
- **BLE001** — 🟥 no blind `except Exception:`: catch the specific exception
  (`KeyError`, `ValueError`, …).
- **ARG001 / ARG003 / ARG004** — 🟦 unused argument in a function / classmethod /
  staticmethod → remove it or prefix it `_`.
- **PGH004** — 🟦 `# noqa` without a code → say which one: `# noqa: E501`.
- **PLC0415** — 🟦 import in the middle of a function → move it to the top of the file
  (tolerated only to break a real circular import, and say why).

### Docstring presence (content is judged separately)
- **D101 / D102 / D103 / D106** — 🟩 missing docstring on a **public** class / method /
  function / nested class.
- **D419** — 🟩 empty docstring.

> The `numpy` convention is enabled: it disables the mutually contradictory
> `D203/D212/D213` rules to match the docstring layout already used throughout `RUFAS/`.

---

## 3. Per-file mypy pass

- 🟥 **`mypy --strict` on each changed file** — the CI ratchet only compares the *total*
  error count, so new untyped code can slip into an already-"dirty" file. This pass catches
  type errors on the added lines even there.

---

## 4. AI-reviewed rules (judgement — the review agent)

No mechanical linter can settle these: they require **understanding the meaning** of the
code. This is the review agent's job — it reads the diff and applies the checklist below.
Each with an example.

### 🟥 Enum over string literal (the human reviewer's #1 theme)
A domain value (sex, animal type, post-weaning destination, reproduction protocol, event
name) must go through the existing enum, in production **and** tests. `Enum == "string"` is
**always** `False` → a branch never taken (silent bug).

```python
# before
if animal.destination == "sell":
    ...
# after
if animal.destination is PostWeaning.SELL:
    ...
```

### 🟥 Scientific traceability of the constant
Does the named constant carry the **correct** NRC reference (right table/equation)? Is the
coefficient used correctly (intercept vs slope, right equation variant)? Is a test
benchmark value **physiologically** plausible?

```python
# suspicious: a placeholder instead of a real mid-gestation value
days_pregnant = 30      # should be ~150 to actually test gestation
# and: does the reference truly match the equation?
NEM_COEF = 0.077  # NRC 2016 Eq.19-1  <- the AI checks it's the right equation
```

### 🟩 Docstring quality and accuracy
Beyond presence (checked by `D103`): does the prose describe the real behaviour? Do the
`Parameters`/`Returns` sections **match the actual signature** (no drift)? Is a ratio's
direction correct ("cows per bull" vs "bulls per cow")?

```python
def bull_ratio(cows, bulls):
    """Return bulls per cow."""   # but the code returns cows / bulls: docstring is wrong
    return cows / bulls
```

### 🟥 Config-validation semantics
Validate the **merged** config (defaults applied), not the raw dict; validate only the
fields that are **present**; reject a lossy coercion (raise on `25.9` rather than silently
truncating it to `25`).

### 🟨 The test checks **behaviour**, not shape
Not just the return type or `call_count`. A patched mock must be **asserted**. Seed real
data so the assertion isn't vacuously true.

```python
# before: proves nothing
result = animal.daily_routines()
assert result is not None
# after: proves the right calculator is called with the right arguments
spy = mocker.patch.object(BeefCowCalfRequirementsCalculator, "compute")
animal.daily_routines()
spy.assert_called_once_with(expected_inputs)
```

### 🟦 Mocking discipline (the substance, not just the form)
Prefer patching a **real method** over replacing a whole collaborator with a `MagicMock`;
prefer a minimal typed stub when only 1–2 attributes are read. Follow the existing sibling
test pattern (feedlot) rather than inventing one.

### 🟦 DRY — where to put the helper
Logic duplicated verbatim between twin methods (beef/feedlot/dairy), a recomputed
expression (`sum(ration.values())` twice), identical fixtures across files → factor it out.
The AI judges **where** to cut and at what abstraction level.

### 🟥 Guard symmetry across twin paths
When adding a branch to one of the beef/feedlot/dairy paths, check the sibling paths have
the matching guard, and that parallel cohort lists stay in sync.

### 🟥 Deterministic, not random, defaults
A missing field must not fall back to a `random()` that produces a biologically invalid
state (e.g. a randomly assigned `sex`). Any real `random()` use must be justified
(Monte Carlo) with a seeding strategy.

### 🟦 Correct attribute name (semantics)
E.g. `times_calved` (an integer) vs `calves` (a list of objects): mypy won't catch it — it's
a naming mistake only review can see.

### 🟦 Output-unit semantics
A reported quantity must carry the right unit: `times_calved` → `UNITLESS`, not `ANIMALS`.

### 🟦 Onion architecture / placement
Where should this code **really** live? Does an in-function import hide a real
circular-dependency / layering problem rather than a legitimate cycle?

### 🟦 Minimal diff
Don't reformat untouched RuFaS code just to please a linter; no temp/unused files added to
the PR.

---

## 5. Deliberately **NOT** enforced (accepted legacy style — do not "fix")

Enabling these would harass intentional code:

- **Naming `N8xx`** — the scientific sigils (`TDN`, `NEm`, `DMI`, `pH`, `ADG`, `BW`) are
  intended.
- **`PLR2004`** (magic values) — published coefficients (SWAT, Parton, NRC) are everywhere;
  replaced by `MSF001/002` (domain-scoped and tolerating named constants).
- **`PLR09xx`** (too-many arguments / methods) — NRC calculators legitimately take ~20
  parameters.
- **`ANN401` / `dict[str, Any]`** — `Any` is accepted at JSON/config boundaries.
- **`UP004`/`UP008`, `TRY003`** — `class X(object)`, `super(X, cls)`, long exception
  messages: tolerated.

---

*A companion PR proposes a diff-aware "style gate" (`tools/msf_style/`) that enforces the
mechanical rules above automatically, plus a `.claude/rules/style.md` write-time rule and an
`msf-style-review` skill for the §4 judgement checks. This document is the standalone,
human-readable reference and does not depend on that tooling being present.*
