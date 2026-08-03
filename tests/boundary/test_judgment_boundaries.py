"""RM4 Commit 5 boundary tests: the constitutional gates for Engineering Judgment.

Makes the RM4 invariants executable. The RM4 domain package (``judgment/``) and its composition entry
(``orchestration/judgment_runner.py``) must:
- import only the frozen contracts + RM1/RM2/RM3 read-only mechanisms + stdlib — never MiniFlyWire
  (Law 4) or Noetica (Law 6), and never any ML / embeddings / vector-DB or persistence/store engine;
- perform **no re-derivation**: import no construction/reasoning mechanism (planner, oracle, RM2 read
  side, precedent retriever/reasoner, intake) — RM4 consumes already-produced *output types* only;
- keep ``EngineeringSituation`` strictly internal to RM4 (no module outside the RM4 set imports it);
- write nothing (read-only advisory); define no memory-lifecycle machinery;
- introduce no contract (the suite stays frozen at 0.4.0).

Scans the AST (imports + symbol names + calls), so it never false-matches boundary words in docstrings.
"""
from __future__ import annotations

import ast
import pathlib
import re

_REPO = pathlib.Path(__file__).resolve().parents[2]
_SRC = _REPO / "src" / "mini_prometheus"

_JUDGMENT = _SRC / "judgment"
_RUNNER = _SRC / "orchestration" / "judgment_runner.py"
_TARGETS = [
    _JUDGMENT / "__init__.py",
    _JUDGMENT / "engineering_situation.py",
    _JUDGMENT / "critic_model.py",
    _JUDGMENT / "engineering_critique.py",
    _RUNNER,
]

_FORBIDDEN_IMPORT = (
    "miniflywire",   # Law 4: never import the research lab
    "noetica",       # Law 6: no dependency on / re-implementation of a Noetica memory engine
    # no persistence / store engine (Law 6; RM4 is read-only, no persistence)
    "sqlite3", "sqlalchemy", "redis", "pymongo", "shelve", "dbm", "pickle",
    # no ML / embeddings / vector DB — deterministic structural judgment only
    "numpy", "scipy", "sklearn", "scikit", "pandas", "torch", "tensorflow", "keras", "jax",
    "faiss", "annoy", "hnswlib", "nmslib", "gensim", "transformers", "sentence_transformers",
    "chromadb", "pinecone", "weaviate", "qdrant", "milvus", "pgvector", "lancedb", "spacy", "nltk",
)
_ALLOWED_TOP = {
    "__future__", "dataclasses", "pathlib", "typing", "datetime", "collections",
    "hashlib", "json", "uuid", "enum", "abc", "functools",
}
# RM4 must consume already-produced OUTPUT TYPES only — never a construction/reasoning MECHANISM.
_NO_REDERIVE = (
    "mini_prometheus.manufacturing_planning",     # no re-planning
    "mini_prometheus.manufacturing_constraints",  # no re-verification (oracle/capability model)
    "mini_prometheus.experience",                 # no RM2 read side
    "mini_prometheus.precedent",                   # no re-retrieval / re-scoring (RM3 mechanisms)
    "mini_prometheus.intake",                      # no re-intake
    "mini_prometheus.integrations",
    "mini_prometheus.orchestration.runner",
    "mini_prometheus.orchestration.reuse_runner",
    "mini_prometheus.orchestration.precedent_runner",
)
_LIFECYCLE_SYMBOL = re.compile(r"retention|prune|compress|evict|archival|retain", re.IGNORECASE)
_WRITE_ATTR = {"write", "writelines", "write_text", "write_bytes", "emit", "dump"}

_SITUATION_MOD = "mini_prometheus.judgment.engineering_situation"
_ALLOWED_SITUATION_IMPORTERS = {
    _JUDGMENT / "critic_model.py",
    _JUDGMENT / "engineering_critique.py",
    _RUNNER,
}


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


def test_no_re_derivation_imports():
    # RM4 consumes output types only — never a construction/reasoning mechanism.
    for path in _TARGETS:
        for mod in _imported_modules(_tree(path)):
            for bad in _NO_REDERIVE:
                assert not (mod == bad or mod.startswith(bad + ".")), (
                    f"{path.name} imports mechanism '{mod}' — RM4 must consume output types only (no re-derivation)"
                )


def test_engineering_situation_stays_internal_to_rm4():
    # No module outside the RM4 set may import EngineeringSituation (it never leaves judgment/).
    for path in _SRC.rglob("*.py"):
        mods = _imported_modules(_tree(path))
        if any(m == _SITUATION_MOD for m in mods):
            assert path in _ALLOWED_SITUATION_IMPORTERS, (
                f"{path} imports EngineeringSituation — it must stay internal to RM4"
            )


def test_no_lifecycle_framework_symbols():
    for path in _TARGETS:
        for node in ast.walk(_tree(path)):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                assert not _LIFECYCLE_SYMBOL.search(node.name), f"{path.name}: lifecycle symbol '{node.name}'"


def test_judgment_layer_performs_no_filesystem_writes():
    for path in _TARGETS:
        for node in ast.walk(_tree(path)):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id != "open", f"{path.name}: uses open() (no persistence / read-only)"
            elif isinstance(func, ast.Attribute):
                assert func.attr not in _WRITE_ATTR, f"{path.name}: write-like call '.{func.attr}(...)'"


def test_contracts_frozen_at_0_4_0():
    # RM4 introduces no contract.
    assert (_REPO / "contracts" / "VERSION").read_text(encoding="utf-8").strip() == "0.4.0"
