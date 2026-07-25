"""RM2-M4 boundary tests: Law-6 non-goals + import discipline + contract freeze.

Enforces that the RM2 read side (`experience/`, `orchestration/reuse_runner.py`) is a minimal read
index — not a Noetica memory/store/retention engine (Law 6, §11.11) — and imports only contracts +
RM1 (read-only) + stdlib; never MiniFlyWire (Law 4); and that contracts stay frozen at 0.2.0.
Scans AST (imports and symbol names), so it never false-matches boundary words in docstrings.
"""
from __future__ import annotations

import ast
import pathlib
import re

_REPO = pathlib.Path(__file__).resolve().parents[2]
_SRC = _REPO / "src" / "mini_prometheus"

_TARGETS = [
    _SRC / "experience" / "__init__.py",
    _SRC / "experience" / "episode_store_reader.py",
    _SRC / "experience" / "episode_index.py",
    _SRC / "orchestration" / "reuse_runner.py",
]

_FORBIDDEN_IMPORT = (
    "miniflywire",   # Law 4
    "noetica",       # Law 6: no re-implementation of / dependency on a Noetica memory engine
    "sqlite3", "sqlalchemy", "redis", "pymongo", "shelve", "dbm", "pickle",  # no persistence/store engine
)
_ALLOWED_TOP = {"__future__", "json", "pathlib", "dataclasses", "typing", "datetime", "collections"}
_LIFECYCLE_SYMBOL = re.compile(r"retention|prune|compress|evict|archival|retain", re.IGNORECASE)


def _imported_modules(tree: ast.AST) -> list[str]:
    mods: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            mods.append(node.module or "")
    return mods


def test_no_forbidden_imports():
    for path in _TARGETS:
        for mod in _imported_modules(ast.parse(path.read_text(encoding="utf-8"))):
            for bad in _FORBIDDEN_IMPORT:
                assert bad not in mod, f"{path.name} imports forbidden module '{mod}' (matched '{bad}')"


def test_all_imports_are_stdlib_or_mini_prometheus():
    for path in _TARGETS:
        for mod in _imported_modules(ast.parse(path.read_text(encoding="utf-8"))):
            top = mod.split(".")[0]
            assert top in _ALLOWED_TOP or top == "mini_prometheus", f"{path.name}: unexpected import '{mod}'"


def test_no_lifecycle_framework_symbols():
    # The read side must not define retention/compression/pruning machinery (that is Noetica's, §11.11).
    for path in _TARGETS:
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                assert not _LIFECYCLE_SYMBOL.search(node.name), f"{path.name}: lifecycle symbol '{node.name}'"


def test_contracts_frozen_at_0_2_0():
    assert (_REPO / "contracts" / "VERSION").read_text(encoding="utf-8").strip() == "0.2.0"
