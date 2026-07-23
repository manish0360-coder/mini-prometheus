"""Boundary/architecture tests (RM1 spec §8): the ownership rules enforced in code."""
from __future__ import annotations

import pathlib
import re

from mini_prometheus._verifier import Verifier
from mini_prometheus.manufacturing_constraints.oracle import ManufacturabilityOracle

_SRC = pathlib.Path(__file__).resolve().parents[2] / "src" / "mini_prometheus"
_IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+([\w\.]+)", re.MULTILINE)


def _imports(path: pathlib.Path) -> list[str]:
    return _IMPORT_RE.findall(path.read_text(encoding="utf-8"))


def test_no_source_imports_miniflywire():
    # Law 4: MiniFlyWire is imported by no one.
    for py in _SRC.rglob("*.py"):
        for mod in _imports(py):
            assert "miniflywire" not in mod.lower(), f"{py} imports {mod}"


def test_velith_adapter_does_not_reverify_or_plan():
    # Law 6/9: the adapter consumes the opaque design; it must not import the oracle or planner.
    adapter = _SRC / "integrations" / "velith" / "adapter.py"
    mods = _imports(adapter)
    assert not any("oracle" in m or "manufacturing_planning" in m for m in mods), mods


def test_oracle_conforms_to_noetica_verifier_protocol():
    # Law 15: MP's concrete oracle implements the Noetica Verifier protocol.
    assert isinstance(ManufacturabilityOracle(), Verifier)


def test_content_packages_do_not_import_orchestration_or_integrations():
    forbidden = ("mini_prometheus.orchestration", "mini_prometheus.integrations", "mini_prometheus.intake")
    for pkg in ("manufacturing_planning", "manufacturing_constraints"):
        for py in (_SRC / pkg).rglob("*.py"):
            for mod in _imports(py):
                assert not mod.startswith(forbidden), f"{py} imports {mod}"
