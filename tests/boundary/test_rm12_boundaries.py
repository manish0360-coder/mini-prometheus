"""RM12 boundaries (mirrored by the import-linter checker-independence contract):

- the checker never imports the downtime canonicalizer (it re-derives the canonical form itself);
- scheduling never touches RM9 availability — no code in the scheduling package references
  ``unavailable_resources`` or ``with_unavailable_resources`` (downtime delays; it never reroutes);
- downtime stays internal: no contract, schema or manufacturability reason code mentions it.
"""

from __future__ import annotations

import ast
import pathlib

from mini_prometheus._contracts import ManufacturabilityReasonCode

SRC = pathlib.Path(__file__).resolve().parents[2] / "src" / "mini_prometheus"
ROOT = SRC.parents[1]
SCHEDULING = SRC / "manufacturing_scheduling"


def _imports(path: pathlib.Path) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
            names.update(f"{node.module}.{alias.name}" for alias in node.names)
        elif isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
    return names


def _names(path: pathlib.Path) -> set[str]:
    names = {n.rsplit(".", 1)[-1] for n in _imports(path)}
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
    return names


def test_checker_does_not_import_the_downtime_canonicalizer():
    imported = _imports(SCHEDULING / "checker.py")
    assert not any(".manufacturing_scheduling.downtime" in n for n in imported), sorted(imported)
    assert not any(n.endswith((".canonical_downtime", ".relevant_downtime")) for n in imported)


def test_scheduling_never_touches_rm9_availability():
    for path in sorted(SCHEDULING.glob("*.py")):
        names = _names(path)
        assert (
            "unavailable_resources" not in names and "with_unavailable_resources" not in names
        ), path


def test_downtime_stays_internal():
    files = [
        p for p in (ROOT / "contracts").rglob("*") if p.is_file() and "__pycache__" not in p.parts
    ]
    assert not any(
        "downtime" in p.read_text(encoding="utf-8", errors="ignore").lower() for p in files
    )
    assert not any("DOWNTIME" in member.value for member in ManufacturabilityReasonCode)
