"""RM3-M5 boundary tests: the constitutional gates for Engineering Precedent Reasoning.

Makes the RM3 invariants executable. The RM3 domain package (``precedent/``) and its composition entry
(``orchestration/precedent_runner.py``) must:
- import only the frozen contracts + RM1/RM2 read-only + stdlib — never MiniFlyWire (Law 4) or Noetica
  (Law 6), and never any ML / embeddings / vector-DB or persistence/store engine (spec §6, non-goals);
- define no memory-lifecycle machinery (retention/prune/compress/evict/archival — Noetica's, §11.11);
- keep the seed/identity separation: the **retriever** is the sole consumer of the RM2 read side, and
  the **reasoner** imports only the ``RankedPrecedent`` hand-off from the retriever (not its functions);
- write nothing (read-only advisory).

Scans the AST (imports + symbol names + calls), so it never false-matches boundary words in docstrings.
"""
from __future__ import annotations

import ast
import pathlib
import re

_REPO = pathlib.Path(__file__).resolve().parents[2]
_SRC = _REPO / "src" / "mini_prometheus"

_PRECEDENT = _SRC / "precedent"
_RUNNER = _SRC / "orchestration" / "precedent_runner.py"
_TARGETS = [
    _PRECEDENT / "__init__.py",
    _PRECEDENT / "precedent_model.py",
    _PRECEDENT / "retriever.py",
    _PRECEDENT / "reasoner.py",
    _RUNNER,
]

_FORBIDDEN_IMPORT = (
    "miniflywire",   # Law 4: never import the research lab
    "noetica",       # Law 6: no dependency on / re-implementation of a Noetica memory engine
    # no persistence / store engine (Law 6; RM3 is read-only, no persistence)
    "sqlite3", "sqlalchemy", "redis", "pymongo", "shelve", "dbm", "pickle",
    # no ML / embeddings / vector DB — deterministic structural reasoning only (spec §6, non-goals)
    "numpy", "scipy", "sklearn", "scikit", "pandas", "torch", "tensorflow", "keras", "jax",
    "faiss", "annoy", "hnswlib", "nmslib", "gensim", "transformers", "sentence_transformers",
    "chromadb", "pinecone", "weaviate", "qdrant", "milvus", "pgvector", "lancedb", "spacy", "nltk",
)
_ALLOWED_TOP = {
    "__future__", "dataclasses", "pathlib", "typing", "datetime", "collections",
    "hashlib", "json", "uuid", "enum", "abc", "functools",
}
_LIFECYCLE_SYMBOL = re.compile(r"retention|prune|compress|evict|archival|retain", re.IGNORECASE)
_WRITE_ATTR = {"write", "writelines", "write_text", "write_bytes", "emit", "dump"}

_EXPERIENCE = "mini_prometheus.experience"
_RETRIEVER_MOD = "mini_prometheus.precedent.retriever"


def _tree(path: pathlib.Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"))


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
        for mod in _imported_modules(_tree(path)):
            for bad in _FORBIDDEN_IMPORT:
                assert bad not in mod, f"{path.name} imports forbidden module '{mod}' (matched '{bad}')"


def test_all_imports_are_stdlib_or_project():
    for path in _TARGETS:
        for mod in _imported_modules(_tree(path)):
            top = mod.split(".")[0]
            assert top in _ALLOWED_TOP or top in {"mini_prometheus", "contracts"}, (
                f"{path.name}: unexpected import '{mod}'"
            )


def test_no_lifecycle_framework_symbols():
    # No retention/compression/pruning machinery here — that is Noetica's lifecycle framework (§11.11).
    for path in _TARGETS:
        for node in ast.walk(_tree(path)):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                assert not _LIFECYCLE_SYMBOL.search(node.name), f"{path.name}: lifecycle symbol '{node.name}'"


def test_retriever_is_sole_rm2_read_side_consumer():
    # Only the retriever may touch the RM2 read side (experience/). Seed/identity separation.
    for path in _TARGETS:
        if path.name == "retriever.py":
            continue
        for mod in _imported_modules(_tree(path)):
            assert not mod.startswith(_EXPERIENCE), (
                f"{path.name} imports the RM2 read side '{mod}' — only the retriever may (seed isolation)"
            )


def test_reasoner_imports_only_the_ranked_precedent_handoff():
    # The reasoner (RM3 identity) must not reach into retriever internals beyond the RankedPrecedent
    # hand-off — no `import ...retriever` module access, and only the RankedPrecedent name via from-import.
    tree = _tree(_PRECEDENT / "reasoner.py")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name != _RETRIEVER_MOD, (
                    "reasoner must not import the retriever module (would expose its functions)"
                )
        elif isinstance(node, ast.ImportFrom) and node.module == _RETRIEVER_MOD:
            names = {a.name for a in node.names}
            assert names <= {"RankedPrecedent"}, (
                f"reasoner imports retriever internals beyond the hand-off: {names - {'RankedPrecedent'}}"
            )


def test_precedent_layer_performs_no_filesystem_writes():
    # Read-only advisory: no open() and no write/emit/dump calls anywhere in the precedent layer.
    for path in _TARGETS:
        for node in ast.walk(_tree(path)):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id != "open", f"{path.name}: uses open() (no persistence / read-only)"
            elif isinstance(func, ast.Attribute):
                assert func.attr not in _WRITE_ATTR, f"{path.name}: write-like call '.{func.attr}(...)'"
