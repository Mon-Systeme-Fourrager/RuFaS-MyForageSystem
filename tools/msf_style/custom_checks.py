"""Project-specific AST and text checks that no off-the-shelf linter covers.

These encode the RuFaS review conventions that recur across pull requests but are not
expressible as a stock Ruff/flake8 rule without unacceptable legacy noise. Each check
returns :class:`Violation` objects; the caller filters them to the new-code perimeter.

Codes
-----
MSF001
    Bare float coefficient in a biophysical/EEE module — move it to a ``*_constants.py``
    with an NRC/published reference.
MSF002
    Numeric literal used as a ``dict.get(key, <number>)`` default in a domain module —
    name the fallback in ``*_constants.py``.
MSF010
    ``config.get(key) or <default>`` — ``or`` silently treats an explicit ``0``/``0.0``
    as missing; test ``is None`` instead.
MSF011
    ``int(...get(key))`` / ``float(...)`` on a possibly-``None`` value — guard the
    ``None`` case before coercion or ``int(None)`` raises ``TypeError``.
MSF020
    Direct class-attribute assignment in a test (``SomeClass.method = MagicMock()``) —
    leaks across tests; use ``mocker.patch.object`` instead.
MSF030
    Classmethod/method returns a mutable class-level ``dict``/``list``/``set`` without
    ``.copy()`` — callers can mutate shared class state.
MSF040
    New ``# noqa: C901`` suppression — split the function under the complexity limit
    rather than silencing it.
MSF041
    ``Lesson N`` / ``Task N.N`` scaffolding reference left in committed code.
MSF042
    Bare ``# type: ignore`` without an error code.
"""

from __future__ import annotations

import ast
import io
import re
import tokenize
from collections.abc import Iterable, Iterator

from .violation import Violation

MAGIC_NUMBER_DIRS: tuple[str, ...] = ("RUFAS/biophysical", "RUFAS/EEE")
CONFIG_CHECK_ROOT = "RUFAS"
ALLOWED_FLOATS: frozenset[float] = frozenset({0.0, 1.0})
UPPER_SNAKE = re.compile(r"^_?[A-Z][A-Z0-9_]*$")
LESSON_REF = re.compile(r"\b(?:Lesson\s+\d+|Task\s+\d+\.\d+)\b")
BARE_TYPE_IGNORE = re.compile(r"#\s*type:\s*ignore(?!\[)")
NOQA_C901 = re.compile(r"#\s*noqa:\s*C901|#\s*noqa:C901")


def check_python_file(path: str, text: str) -> list[Violation]:
    """Run every applicable custom check against one Python source file.

    Parameters
    ----------
    path : str
        Repository-relative path (decides which directory-scoped checks apply).
    text : str
        Full source text of the file.

    Returns
    -------
    list of Violation
        Findings across the whole file; the caller filters them to changed lines.
    """
    path = path.replace("\\", "/")
    violations = list(_text_checks(path, text))
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return violations
    parents = _parent_map(tree)
    violations.extend(_scaffolding_in_docstrings(path, tree))
    violations.extend(_config_none_safety(path, tree))
    violations.extend(_magic_numbers(path, tree, parents))
    violations.extend(_mutable_classvar_returns(path, tree))
    if _is_test_path(path):
        violations.extend(_test_class_attr_assignment(path, tree))
    return violations


def _is_test_path(path: str) -> bool:
    """Return whether ``path`` lives under a ``tests`` tree."""
    return path.startswith("tests/") or "/tests/" in path


def _in_dirs(path: str, roots: Iterable[str]) -> bool:
    """Return whether ``path`` equals or lives under any of ``roots``."""
    return any(path == root or path.startswith(f"{root}/") for root in roots)


def _is_constants_module(path: str) -> bool:
    """Return whether ``path`` is a constants/enums module (exempt from magic numbers)."""
    name = path.rsplit("/", 1)[-1]
    return "constant" in name or name.endswith("_enums.py") or name == "enums.py"


def _parent_map(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    """Return a child-to-parent mapping for every node in ``tree``.

    Parameters
    ----------
    tree : ast.AST
        The parsed module.

    Returns
    -------
    dict of ast.AST to ast.AST
        Maps each child node to its immediate parent (roots are absent).
    """
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    return parents


def _comment_tokens(text: str) -> list[tuple[int, str]]:
    """Return ``(line, text)`` for every comment token, tolerating tokenizer errors.

    Parameters
    ----------
    text : str
        Full source text.

    Returns
    -------
    list of (int, str)
        One entry per ``# ...`` comment; empty when the source cannot be tokenized.
    """
    comments: list[tuple[int, str]] = []
    try:
        for token in tokenize.generate_tokens(io.StringIO(text).readline):
            if token.type == tokenize.COMMENT:
                comments.append((token.start[0], token.string))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        pass
    return comments


def _text_checks(path: str, text: str) -> Iterator[Violation]:
    """Yield comment-based findings (MSF040/041/042) for one file.

    Parameters
    ----------
    path : str
        Repository-relative path (stamped onto findings).
    text : str
        Full source text.

    Yields
    ------
    Violation
        A finding per offending comment.
    """
    for lineno, comment in _comment_tokens(text):
        if NOQA_C901.search(comment):
            yield Violation(
                path,
                lineno,
                "MSF040",
                "New '# noqa: C901' — split the function to satisfy "
                "the complexity limit (max 10) instead of suppressing it.",
                "custom",
            )
        if BARE_TYPE_IGNORE.search(comment):
            yield Violation(
                path,
                lineno,
                "MSF042",
                "Bare '# type: ignore' — pin the specific error code, e.g. '# type: ignore[assignment]'.",
                "custom",
            )
        if LESSON_REF.search(comment):
            yield _scaffolding_violation(path, lineno)


def _scaffolding_violation(path: str, lineno: int) -> Violation:
    """Build the shared ``MSF041`` scaffolding-reference finding."""
    return Violation(
        path,
        lineno,
        "MSF041",
        "Remove 'Lesson N'/'Task N.N' scaffolding reference from committed code.",
        "custom",
    )


def _scaffolding_in_docstrings(path: str, tree: ast.AST) -> Iterator[Violation]:
    """Yield ``MSF041`` for a ``Lesson N``/``Task N.N`` reference in any docstring.

    Parameters
    ----------
    path : str
        Repository-relative path (stamped onto findings).
    tree : ast.AST
        The parsed module.

    Yields
    ------
    Violation
        One finding per offending module/class/function docstring.
    """
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        docstring = ast.get_docstring(node, clean=False)
        if docstring and LESSON_REF.search(docstring):
            yield _scaffolding_violation(path, _docstring_lineno(node))


def _docstring_lineno(node: ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    """Return the 1-indexed line of ``node``'s docstring (or 1 when absent)."""
    first = node.body[0] if node.body else None
    if isinstance(first, ast.Expr):
        return first.value.lineno
    return 1


def _ancestors(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> Iterator[ast.AST]:
    """Yield ``node``'s ancestors from nearest to furthest using ``parents``."""
    current = parents.get(node)
    while current is not None:
        yield current
        current = parents.get(current)


def _is_named_constant_target(node: ast.AST) -> bool:
    """Return whether ``node`` is an assignment target named in UPPER_SNAKE_CASE."""
    if isinstance(node, ast.Name):
        return bool(UPPER_SNAKE.match(node.id))
    if isinstance(node, ast.Attribute):
        return bool(UPPER_SNAKE.match(node.attr))
    return False


def _declares_constant(assign: ast.AST) -> bool:
    """Return whether ``assign`` binds a value to an UPPER_SNAKE constant name."""
    if isinstance(assign, ast.Assign):
        return any(_is_named_constant_target(target) for target in assign.targets)
    if isinstance(assign, ast.AnnAssign):
        return _is_named_constant_target(assign.target)
    return False


def _float_is_exempt(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
    """Return whether a float literal is a declaration/default rather than magic.

    Parameters
    ----------
    node : ast.AST
        The float ``Constant`` node.
    parents : dict of ast.AST to ast.AST
        Child-to-parent map from :func:`_parent_map`.

    Returns
    -------
    bool
        ``True`` when the literal sits in a function-signature default or a named
        constant assignment.
    """
    for ancestor in _ancestors(node, parents):
        if isinstance(ancestor, ast.arguments):
            return True
        if _declares_constant(ancestor):
            return True
    return False


def _magic_numbers(path: str, tree: ast.AST, parents: dict[ast.AST, ast.AST]) -> Iterator[Violation]:
    """Yield ``MSF001`` for bare float coefficients in a domain module.

    Parameters
    ----------
    path : str
        Repository-relative path (only biophysical/EEE non-constants files apply).
    tree : ast.AST
        The parsed module.
    parents : dict of ast.AST to ast.AST
        Child-to-parent map used to exempt declarations/defaults.

    Yields
    ------
    Violation
        One finding per non-exempt float literal other than 0.0/1.0.
    """
    if not _in_dirs(path, MAGIC_NUMBER_DIRS) or _is_constants_module(path):
        return
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Constant) and isinstance(node.value, float)):
            continue
        if node.value in ALLOWED_FLOATS or _float_is_exempt(node, parents):
            continue
        yield Violation(
            path,
            node.lineno,
            "MSF001",
            f"Bare coefficient {node.value!r} in a domain module — "
            "move it to a '*_constants.py' with its NRC/published reference.",
            "custom",
        )


def _is_get_call(node: ast.AST) -> bool:
    """Return whether ``node`` is a ``<expr>.get(...)`` call."""
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get"


def _config_none_safety(path: str, tree: ast.AST) -> Iterator[Violation]:
    """Yield the None-safety config findings (MSF002/010/011) for a RUFAS module.

    Parameters
    ----------
    path : str
        Repository-relative path (only files under ``RUFAS`` apply).
    tree : ast.AST
        The parsed module.

    Yields
    ------
    Violation
        Findings from the three sub-checks.
    """
    if not _in_dirs(path, [CONFIG_CHECK_ROOT]):
        return
    for node in ast.walk(tree):
        yield from _numeric_get_default(path, node)
        yield from _get_or_default(path, node)
        yield from _coerce_possibly_none(path, node)


def _unwrap_unary(node: ast.expr) -> ast.expr:
    """Return the operand of a unary ``+``/``-`` node, else ``node`` unchanged."""
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        return node.operand
    return node


def _numeric_get_default(path: str, node: ast.AST) -> Iterator[Violation]:
    """Yield ``MSF002`` when ``node`` is a ``.get(key, <number>)`` in a domain module."""
    if not (_is_get_call(node) and isinstance(node, ast.Call) and len(node.args) == 2):
        return
    default = _unwrap_unary(node.args[1])
    if (
        isinstance(default, ast.Constant)
        and isinstance(default.value, (int, float))
        and not isinstance(default.value, bool)
    ):
        if _in_dirs(path, MAGIC_NUMBER_DIRS):
            yield Violation(
                path,
                node.lineno,
                "MSF002",
                "Numeric literal as a '.get(key, <number>)' default — name the fallback in a '*_constants.py'.",
                "custom",
            )


def _get_or_default(path: str, node: ast.AST) -> Iterator[Violation]:
    """Yield ``MSF010`` when a ``.get()`` precedes the last term of an ``or`` chain."""
    if not (isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or) and node.values):
        return
    if any(_is_get_call(value) for value in node.values[:-1]):
        yield Violation(
            path,
            node.lineno,
            "MSF010",
            "'config.get(key) or <default>' treats an explicit 0/0.0 as missing — test 'is None' instead.",
            "custom",
        )


def _coerce_possibly_none(path: str, node: ast.AST) -> Iterator[Violation]:
    """Yield ``MSF011`` for ``int()``/``float()`` wrapping a possibly-None ``.get()``."""
    if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"int", "float"}):
        return
    if not node.args:
        return
    inner = node.args[0]
    if _is_get_call(inner) and isinstance(inner, ast.Call) and _get_may_return_none(inner):
        yield Violation(
            path,
            node.lineno,
            "MSF011",
            f"'{node.func.id}(...get(key))' can be called on None — guard "
            "the None case before coercion (int(None) raises TypeError).",
            "custom",
        )


def _get_may_return_none(get_call: ast.Call) -> bool:
    """Return whether a ``.get()`` call can yield ``None`` (no/None default)."""
    if len(get_call.args) < 2:
        return True
    default = get_call.args[1]
    return isinstance(default, ast.Constant) and default.value is None


def _classvar_containers(class_node: ast.ClassDef) -> set[str]:
    """Return the names of class-level dict/list/set attributes in ``class_node``."""
    names: set[str] = set()
    for stmt in class_node.body:
        value = _assigned_value(stmt)
        if isinstance(value, (ast.Dict, ast.List, ast.Set)):
            names.update(_assignment_names(stmt))
    return names


def _assigned_value(stmt: ast.stmt) -> ast.expr | None:
    """Return the right-hand value of an assignment statement, else ``None``."""
    if isinstance(stmt, ast.Assign):
        return stmt.value
    if isinstance(stmt, ast.AnnAssign):
        return stmt.value
    return None


def _assignment_names(stmt: ast.stmt) -> Iterator[str]:
    """Yield the simple ``Name`` targets bound by an assignment statement."""
    if isinstance(stmt, ast.Assign):
        for target in stmt.targets:
            if isinstance(target, ast.Name):
                yield target.id
    elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
        yield stmt.target.id


def _returns_bare_container(func: ast.AST, names: set[str]) -> Iterator[int]:
    """Yield the line of each ``return cls/self.<name>`` where ``<name>`` is in ``names``."""
    for node in ast.walk(func):
        if not (isinstance(node, ast.Return) and isinstance(node.value, ast.Attribute)):
            continue
        owner = node.value.value
        if isinstance(owner, ast.Name) and owner.id in {"cls", "self"} and node.value.attr in names:
            yield node.lineno


def _mutable_classvar_returns(path: str, tree: ast.AST) -> Iterator[Violation]:
    """Yield ``MSF030`` for methods returning a class-level dict/list/set unguarded.

    Parameters
    ----------
    path : str
        Repository-relative path (only files under ``RUFAS`` apply).
    tree : ast.AST
        The parsed module.

    Yields
    ------
    Violation
        One finding per ``return cls/self.<container>`` without a copy.
    """
    if not _in_dirs(path, [CONFIG_CHECK_ROOT]):
        return
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        containers = _classvar_containers(node)
        if not containers:
            continue
        for method in node.body:
            if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for lineno in _returns_bare_container(method, containers):
                    yield Violation(
                        path,
                        lineno,
                        "MSF030",
                        "Returning a mutable class-level dict/list/set "
                        "directly — return '.copy()' (or deepcopy) to protect shared class state.",
                        "custom",
                    )


def _is_mock_call(value: ast.expr | None) -> bool:
    """Return whether ``value`` is a ``MagicMock``/``Mock``/``AsyncMock`` construction."""
    if not isinstance(value, ast.Call):
        return False
    func = value.func
    if isinstance(func, ast.Name):
        return func.id in {"MagicMock", "Mock", "AsyncMock"}
    if isinstance(func, ast.Attribute):
        return func.attr in {"MagicMock", "Mock", "AsyncMock"}
    return False


def _is_class_like_owner(target: ast.Attribute) -> bool:
    """Return whether ``target``'s owner is a CapWords name (a class, heuristically)."""
    owner = target.value
    return isinstance(owner, ast.Name) and bool(re.match(r"^[A-Z][A-Za-z0-9_]*$", owner.id))


def _test_class_attr_assignment(path: str, tree: ast.AST) -> Iterator[Violation]:
    """Yield ``MSF020`` for ``SomeClass.member = MagicMock()`` assignments in tests.

    Parameters
    ----------
    path : str
        Repository-relative path (stamped onto findings).
    tree : ast.AST
        The parsed test module.

    Yields
    ------
    Violation
        One finding per direct class-attribute mock assignment.
    """
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Assign) and len(node.targets) == 1):
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Attribute) or not _is_class_like_owner(target):
            continue
        if _is_mock_call(node.value):
            yield Violation(
                path,
                node.lineno,
                "MSF020",
                "Direct class-attribute assignment of a mock leaks across "
                "tests — use 'mocker.patch.object(Class, \"member\")' instead.",
                "custom",
            )
