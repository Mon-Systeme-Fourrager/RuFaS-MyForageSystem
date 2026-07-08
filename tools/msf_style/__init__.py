"""Diff-aware style gate enforcing RuFaS review conventions on new/changed code only.

The package exists because RuFaS reviewers (human SME + CodeRabbit/Gemini) repeatedly
request the same handful of conventions on every pull request, while the legacy code
base pervasively violates the stricter of those same rules on purpose (scientific
sigils, hard-coded published coefficients, god-object calculators, ``dict[str, Any]``
at JSON boundaries). A repo-wide linter would therefore drown the signal.

Every checker here is applied *only* to the lines a branch adds or changes versus its
base (mirroring the existing mypy error-count ratchet), so accepted legacy patterns are
never flagged retroactively. See ``STYLE_RULES.md`` for the rule/code mapping and the
provenance of each rule in past reviews.
"""
