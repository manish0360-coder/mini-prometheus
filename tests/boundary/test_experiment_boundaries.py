"""RM5 C5 boundary tests: the constitutional gates for the ``experiment/`` package.

Makes the RM5 experiment-package invariants executable. The experiment package (measurement harness)
must:
- import only the frozen contracts + RM1–RM4 read-only mechanisms + stdlib — never MiniFlyWire (Law 4)
  or Noetica (Law 6), and never any ML / embeddings / vector-DB or persistence/store engine;
- keep ``partition`` and ``protocol`` **pure** (contracts/``_hashing`` and the RM4 ``Assessment`` enum
  respectively; no RM1 pipeline, no I/O), so the evaluation runner can consume them without pulling the
  corpus generator's RM1 dependencies;
- be a **leaf consumer**: no RM1–RM4 module may import ``mini_prometheus.experiment`` (also enforced by
  import-linter — this test is the redundant in-suite gate);
- keep the evaluation sink **isolated**: the experiment layer never writes the RM2 episode store — it
  imports only the pure ``build_episode`` constructor + ``SCHEMA_VERSION`` constant from
  ``episode_store``, never the ``emit`` persistence function or the ``DEFAULT_STORE`` path;
- introduce no contract (the suite stays frozen at 0.4.0).

Scans the AST (imports + from-import names), so it never false-matches boundary words in docstrings.
"""
from __future__ import annotations

import ast
import pathlib

_REPO = pathlib.Path(__file__).resolve().parents[2]
_SRC = _REPO / "src" / "mini_prometheus"
_EXPERIMENT = _SRC / "experiment"
_TARGETS = sorted(_EXPERIMENT.glob("*.py"))

_FORBIDDEN_IMPORT = (
    "miniflywire",   # Law 4: never import the research lab
    "noetica",       # Law 6: no dependency on / re-implementation of a Noetica memory engine
    # no persistence / store engine (Law 6)
    "sqlite3", "sqlalchemy", "redis", "pymongo", "shelve", "dbm", "pickle",
    # no ML / embeddings / vector DB — deterministic measurement only
    "numpy", "scipy", "sklearn", "scikit", "pandas", "torch", "tensorflow", "keras", "jax",
    "faiss", "annoy", "hnswlib", "nmslib", "gensim", "transformers", "sentence_transformers",
    "chromadb", "pinecone", "weaviate", "qdrant", "milvus", "pgvector", "lancedb", "spacy", "nltk",
)
# stdlib the experiment layer legitimately uses (it DOES write files — corpus fixture + evaluation sink).
_ALLOWED_TOP = {
    "__future__", "dataclasses", "pathlib", "typing", "datetime", "collections",
    "hashlib", "json", "uuid", "enum", "abc", "functools",
}
_EXPERIMENT_MOD = "mini_prometheus.experiment"
_EPISODE_STORE_MOD = "mini_prometheus.orchestration.episode_store"
_ALLOWED_EPISODE_STORE_NAMES = {"build_episode", "SCHEMA_VERSION"}


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


def _import_targets(tree: ast.AST) -> list[str]:
    """Fully-qualified imported targets: ``from pkg import x`` -> ``pkg.x`` (so ``from mini_prometheus
    import _hashing`` resolves to ``mini_prometheus._hashing`` rather than the bare package)."""
    targets: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            targets.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            targets.extend(f"{base}.{alias.name}" for alias in node.names)
    return targets


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


def test_partition_and_protocol_are_pure():
    # partition: contracts + _hashing only. protocol: the RM4 Assessment enum only. No RM1 pipeline, no I/O.
    pure_allowed_prefixes = {
        "partition.py": ("mini_prometheus._hashing", "mini_prometheus._contracts"),
        "protocol.py": ("mini_prometheus.judgment.critic_model",),
    }
    for name, allowed in pure_allowed_prefixes.items():
        for target in _import_targets(_tree(_EXPERIMENT / name)):
            top = target.split(".")[0]
            if top in {"mini_prometheus", "contracts"}:
                assert any(target.startswith(p) for p in allowed), f"{name}: impure project import '{target}'"
            else:
                assert top in _ALLOWED_TOP, f"{name}: unexpected import '{target}'"


def test_experiment_is_a_leaf_no_rm1_rm4_imports_it():
    # No module OUTSIDE experiment/ may import the experiment package (leaf consumer).
    for path in _SRC.rglob("*.py"):
        if _EXPERIMENT in path.parents:
            continue
        for mod in _imported_modules(_tree(path)):
            assert not (mod == _EXPERIMENT_MOD or mod.startswith(_EXPERIMENT_MOD + ".")), (
                f"{path.relative_to(_SRC)} imports '{mod}' — experiment/ must remain a leaf consumer"
            )


def test_evaluation_sink_isolated_from_episode_store():
    # The experiment layer must never persist to the RM2 episode store: only the pure build_episode
    # constructor + SCHEMA_VERSION constant may be imported from episode_store — never emit / DEFAULT_STORE.
    for path in _TARGETS:
        for node in ast.walk(_tree(path)):
            if isinstance(node, ast.ImportFrom) and node.module == _EPISODE_STORE_MOD:
                names = {a.name for a in node.names}
                illegal = names - _ALLOWED_EPISODE_STORE_NAMES
                assert not illegal, f"{path.name} imports store-persistence symbol(s) {illegal} from episode_store"
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name != _EPISODE_STORE_MOD, (
                        f"{path.name} imports the episode_store module wholesale (could reach emit/DEFAULT_STORE)"
                    )


def test_contracts_frozen_at_0_4_0():
    # RM5 introduces no contract.
    assert (_REPO / "contracts" / "VERSION").read_text(encoding="utf-8").strip() == "0.4.0"
