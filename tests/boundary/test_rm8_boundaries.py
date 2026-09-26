"""RM8 boundaries: protocol, contracts and dependencies are unchanged by Engineering Constraint Reasoning.

- the Noetica ``Verifier`` signature ``verify(plan, capability_model) -> Verdict`` is unchanged;
- the closed taxonomies are exactly the frozen ones (RM8 uses existing members only);
- the contract suite stays at 0.4.0 (the whole contracts/ tree is also pinned by the rm5-complete golden);
- the four RM8-modified modules import only the standard library and mini_prometheus (no new dependency);
- nothing in src imports FutureScore or MiniFlyWire (Law 4; RM8 ADR-0010).
"""
from __future__ import annotations

import ast
import inspect
import pathlib
import sys

from mini_prometheus._contracts import ManufacturabilityReasonCode, ManufacturabilityVerdictStatus
from mini_prometheus._verifier import Verifier
from mini_prometheus.manufacturing_constraints.oracle import ManufacturabilityOracle

SRC = pathlib.Path(__file__).resolve().parents[2] / "src" / "mini_prometheus"
ROOT = SRC.parents[1]
RM8_MODULES = [
    "manufacturing_constraints/capability_model.py",
    "manufacturing_constraints/oracle.py",
    "manufacturing_planning/planner.py",
    "orchestration/runner.py",
]


def _imports(path: pathlib.Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module.split(".")[0])
    return names


def test_verifier_signature_unchanged():
    params = list(inspect.signature(ManufacturabilityOracle.verify).parameters)
    assert params == ["self", "plan", "capability_model"]
    assert list(inspect.signature(Verifier.verify).parameters) == ["self", "plan", "capability_model"]
    assert isinstance(ManufacturabilityOracle(), Verifier)


def test_closed_taxonomies_unchanged():
    assert [m.value for m in ManufacturabilityVerdictStatus] == [
        "MANUFACTURABLE", "NOT_MANUFACTURABLE", "PLAN_INVALID", "INFRA_ERROR"]
    assert [m.value for m in ManufacturabilityReasonCode] == [
        "CAPABILITY_MISSING", "PRECEDENCE_VIOLATION", "RESOURCE_UNAVAILABLE",
        "TOLERANCE_UNSUPPORTED", "MATERIAL_UNSUPPORTED", "PLAN_MALFORMED"]


def test_contract_suite_version_unchanged():
    assert (ROOT / "contracts" / "VERSION").read_text(encoding="utf-8").strip() == "0.4.0"


def test_rm8_modules_add_no_dependency():
    allowed = set(sys.stdlib_module_names) | {"mini_prometheus", "__future__"}
    for rel in RM8_MODULES:
        foreign = _imports(SRC / rel) - allowed
        assert not foreign, f"{rel} imports non-stdlib modules {sorted(foreign)}"


def test_no_futurescore_or_miniflywire_import_anywhere_in_src():
    for path in SRC.rglob("*.py"):
        for name in _imports(path):
            assert "futurescore" not in name.lower() and "miniflywire" not in name.lower(), (path, name)
