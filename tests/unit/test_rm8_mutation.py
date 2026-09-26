"""RM8 anti-vacuity: mutants of the ECR oracle logic must be caught by the RM8 gate cases.

Each mutant is built from the REAL oracle source by one exact textual substitution (the anchor must occur
exactly once, so a refactor cannot silently turn this test vacuous) and executed as an isolated module.
The same gate cases must PASS for the real oracle and FAIL for each mutant:
- M1 removes the declared-precedence check     -> the precedence-violation case must fail;
- M2 changes the tolerance comparison < to <=  -> the equal-tolerance case must fail.
"""
from __future__ import annotations

import copy
import pathlib
import types

import pytest

from mini_prometheus.intake.request_intake import intake
from mini_prometheus.manufacturing_constraints import oracle as real_oracle
from mini_prometheus.manufacturing_constraints.capability_model import constrained_model
from mini_prometheus.manufacturing_planning import planner

import support
from support import FIXED_TIME

ORACLE_SOURCE = pathlib.Path(real_oracle.__file__).read_text(encoding="utf-8")
BASE = support.load_json("engineer_request_machined_bracket.json")

MUTANTS = {
    "M1_remove_precedence_check": (
        "            if _declared_precedence_violated(plan, capability_model):\n"
        "                reasons.add(RC.PRECEDENCE_VIOLATION)\n",
        "",
    ),
    "M2_tolerance_lt_becomes_le": (
        "        if requested < minimum:\n",
        "        if requested <= minimum:\n",
    ),
}


def _request(ops=None, tolerance=0.1):
    raw = copy.deepcopy(BASE)
    if ops is not None:
        raw["declared_operations"] = [{"op": o} for o in ops]
    raw["tolerances"] = {"general_tolerance_mm": tolerance}
    return support.build_request(raw)


# name -> (request, expected (status, reason_codes)) — the RM8 gate cases the mutants must violate
GATE_CASES = {
    "precedence_violation": (_request(["face_mill", "cut_stock", "drill", "inspect"]),
                             ("PLAN_INVALID", ["PRECEDENCE_VIOLATION"])),
    "tolerance_equal_is_feasible": (_request(tolerance=0.05), ("MANUFACTURABLE", [])),
    "tolerance_tighter_unsupported": (_request(tolerance=0.03), ("NOT_MANUFACTURABLE", ["TOLERANCE_UNSUPPORTED"])),
    "valid_plan": (_request(), ("MANUFACTURABLE", [])),
}


def _failing_cases(oracle_cls) -> list[str]:
    model = constrained_model()
    failing = []
    for name, (request, expected) in GATE_CASES.items():
        design_input = intake(request, produced_at=FIXED_TIME)
        _task, plan = planner.plan(design_input, model, produced_at=FIXED_TIME)
        verdict = oracle_cls().verify(plan, model)
        if (verdict.status, verdict.reason_codes) != expected:
            failing.append(name)
    return failing


def _mutant_oracle(name: str):
    anchor, replacement = MUTANTS[name]
    assert ORACLE_SOURCE.count(anchor) == 1, f"{name}: mutation anchor must occur exactly once"
    module = types.ModuleType(f"oracle_{name}")
    exec(compile(ORACLE_SOURCE.replace(anchor, replacement), module.__name__, "exec"), module.__dict__)
    return module.ManufacturabilityOracle


def test_real_oracle_passes_every_gate_case():
    assert _failing_cases(real_oracle.ManufacturabilityOracle) == []


@pytest.mark.parametrize("name,must_fail", [
    ("M1_remove_precedence_check", "precedence_violation"),
    ("M2_tolerance_lt_becomes_le", "tolerance_equal_is_feasible"),
])
def test_mutant_is_caught_by_the_named_gate_case(name, must_fail):
    assert must_fail in _failing_cases(_mutant_oracle(name))
