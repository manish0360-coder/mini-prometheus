"""RM9 anti-vacuity: mutants of the availability logic must be caught by named RM9 gate cases.

Each mutant is one exact textual substitution in the REAL source (the anchor must occur exactly once)
executed as an isolated module:
- M3 (oracle)  disable the RESOURCE_UNAVAILABLE finding       -> "only_capable_unavailable" fails;
- M4 (planner) ignore availability when assigning machines    -> "alternative_reroute" fails;
- M5 (oracle)  treat a capability with NO provider as an
               availability matter (absent -> RESOURCE_UNAVAILABLE) -> "absent_is_capability_missing" fails.
"""
from __future__ import annotations

import pathlib
import types

import pytest

from mini_prometheus.intake.request_intake import intake
from mini_prometheus.manufacturing_constraints import oracle as real_oracle
from mini_prometheus.manufacturing_constraints.capability_model import (
    ProcessCapabilityModel,
    default_model,
    with_unavailable_resources,
)
from mini_prometheus.manufacturing_planning import planner as real_planner

import support
from support import FIXED_TIME

SOURCES = {
    "oracle": pathlib.Path(real_oracle.__file__).read_text(encoding="utf-8"),
    "planner": pathlib.Path(real_planner.__file__).read_text(encoding="utf-8"),
}
MUTANTS = {
    "M3_disable_resource_unavailable": ("oracle", "            if unavailable:\n", "            if False:\n"),
    "M4_planner_ignores_availability": (
        "planner",
        "        resource_id = available_resource_for_capability(capability_model, step.required_capability)\n",
        "        resource_id = (providers_for_capability(capability_model, step.required_capability) or [None])[0]\n",
    ),
    "M5_absent_machine_as_unavailable": (
        "oracle",
        "        if not availability_affects_capability(model, capability):\n",
        "        if resource_for_capability(model, capability) is not None and "
        "not availability_affects_capability(model, capability):\n",
    ),
}


def _twin() -> ProcessCapabilityModel:
    base = default_model()
    return ProcessCapabilityModel(version=base.version, op_capability=base.op_capability,
                                  resources={**base.resources, "mill02": frozenset({"cap.mill", "cap.drill"})},
                                  supported_materials=base.supported_materials)


def _no_lathe() -> ProcessCapabilityModel:
    base = default_model()
    return ProcessCapabilityModel(version=base.version, op_capability=base.op_capability,
                                  resources={k: v for k, v in base.resources.items() if k != "lathe01"},
                                  supported_materials=base.supported_materials)


def _request(ops=None):
    raw = support.load_json("engineer_request_machined_bracket.json")
    if ops is not None:
        raw["declared_operations"] = [{"op": o} for o in ops]
    return support.build_request(raw)


# name -> (model, request, expected (status, reason_codes, machine assigned to step 1 or None))
GATE_CASES = {
    "only_capable_unavailable": (with_unavailable_resources(default_model(), ["mill01"]), _request(),
                                 ("NOT_MANUFACTURABLE", ["RESOURCE_UNAVAILABLE"], None)),
    "alternative_reroute": (with_unavailable_resources(_twin(), ["mill01"]), _request(),
                            ("MANUFACTURABLE", [], "mill02")),
    # availability data is present (mill01 down) but irrelevant; the only finding must be the absent lathe
    "absent_is_capability_missing": (with_unavailable_resources(_no_lathe(), ["mill01"]), _request(["turn"]),
                                     ("NOT_MANUFACTURABLE", ["CAPABILITY_MISSING"], None)),
    "irrelevant_is_legacy": (with_unavailable_resources(default_model(), ["lathe01"]), _request(),
                             ("MANUFACTURABLE", [], "mill01")),
}


def _failing(planner_mod, oracle_cls) -> list[str]:
    failing = []
    for name, (model, request, expected) in GATE_CASES.items():
        design_input = intake(request, produced_at=FIXED_TIME)
        _task, plan = planner_mod.plan(design_input, model, produced_at=FIXED_TIME)
        verdict = oracle_cls().verify(plan, model)
        step1 = next((a.resource_id for a in plan.resource_assignments if a.step_index == 1), None)
        if (verdict.status, verdict.reason_codes, step1) != expected:
            failing.append(name)
    return failing


def _mutant(name: str):
    target, anchor, replacement = MUTANTS[name]
    source = SOURCES[target]
    assert source.count(anchor) == 1, f"{name}: mutation anchor must occur exactly once"
    module = types.ModuleType(f"{target}_{name}")
    exec(compile(source.replace(anchor, replacement), module.__name__, "exec"), module.__dict__)
    return module


def test_real_code_passes_every_gate_case():
    assert _failing(real_planner, real_oracle.ManufacturabilityOracle) == []


@pytest.mark.parametrize("name,must_fail", [
    ("M3_disable_resource_unavailable", "only_capable_unavailable"),
    ("M4_planner_ignores_availability", "alternative_reroute"),
    ("M5_absent_machine_as_unavailable", "absent_is_capability_missing"),
])
def test_mutant_is_caught_by_the_named_gate_case(name, must_fail):
    target = MUTANTS[name][0]
    module = _mutant(name)
    if target == "planner":
        failing = _failing(module, real_oracle.ManufacturabilityOracle)
    else:
        failing = _failing(real_planner, module.ManufacturabilityOracle)
    assert must_fail in failing
