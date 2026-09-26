"""RM10 anti-vacuity: mutants of the timeline logic must be caught by named RM10 gate cases.

Each mutant is one exact textual substitution in the REAL source (the anchor must occur exactly once),
executed as an isolated module:
- T1 (planner) a missing duration defaults to zero         -> "missing_duration_reported" fails;
- T2 (planner) the start chain is shifted by one minute     -> "valid_chain" fails;
- T3 (oracle)  the timeline consistency check is removed    -> "tampered_start_rejected" fails.
"""
from __future__ import annotations

import copy
import dataclasses
import pathlib
import types

import pytest

from mini_prometheus.intake.request_intake import intake
from mini_prometheus.manufacturing_constraints import oracle as real_oracle
from mini_prometheus.manufacturing_constraints.capability_model import default_model
from mini_prometheus.manufacturing_planning import planner as real_planner

import support
from support import FIXED_TIME

SOURCES = {
    "oracle": pathlib.Path(real_oracle.__file__).read_text(encoding="utf-8"),
    "planner": pathlib.Path(real_planner.__file__).read_text(encoding="utf-8"),
}
MUTANTS = {
    "T1_missing_duration_defaults_to_zero": (
        "planner",
        "    return (declared.params or {}).get(DURATION_PARAM, _MISSING)\n",
        "    return (declared.params or {}).get(DURATION_PARAM, 0)\n",
    ),
    "T2_start_chain_shifted_by_one": ("planner", "        start = end\n", "        start = end + 1\n"),
    "T3_consistency_check_removed": (
        "oracle",
        "            if _timeline_inconsistent(plan):\n",
        "            if False:\n",
    ),
}
TIMED = support.load_json("engineer_request_with_durations.json")


def _missing_one():
    raw = copy.deepcopy(TIMED)
    del raw["declared_operations"][2]["params"]
    return raw


def _outcomes(planner_mod, oracle_cls) -> dict[str, bool]:
    model = default_model()

    def run(raw):
        design_input = intake(support.build_request(raw), produced_at=FIXED_TIME)
        _task, plan = planner_mod.plan(design_input, model, produced_at=FIXED_TIME)
        return design_input, plan

    di_ok, ok = run(TIMED)
    di_missing, missing = run(_missing_one())
    steps = [dataclasses.replace(s, params=dict(s.params)) for s in ok.steps]
    steps[2].params["schedule_start_min"] = 48
    tampered_verdict = oracle_cls().verify(dataclasses.replace(ok, steps=steps), model)
    return {
        "valid_chain": [(s.params.get("schedule_start_min"), s.params.get("schedule_end_min")) for s in ok.steps]
        == [(0, 12), (12, 47), (47, 65), (65, 83), (83, 93), (93, 108)],
        "missing_duration_reported": planner_mod.timeline_issues(di_missing, missing)
        == ["step 2 (drill): duration_min missing"]
        and all("schedule_start_min" not in s.params for s in missing.steps),
        "tampered_start_rejected": (tampered_verdict.status, tampered_verdict.reason_codes)
        == ("PLAN_INVALID", ["PLAN_MALFORMED"]),
    }


def _mutant(name: str):
    target, anchor, replacement = MUTANTS[name]
    source = SOURCES[target]
    assert source.count(anchor) == 1, f"{name}: mutation anchor must occur exactly once"
    module = types.ModuleType(f"{target}_{name}")
    exec(compile(source.replace(anchor, replacement), module.__name__, "exec"), module.__dict__)
    return module


def test_real_code_passes_every_gate_case():
    assert all(_outcomes(real_planner, real_oracle.ManufacturabilityOracle).values())


@pytest.mark.parametrize("name,must_fail", [
    ("T1_missing_duration_defaults_to_zero", "missing_duration_reported"),
    ("T2_start_chain_shifted_by_one", "valid_chain"),
    ("T3_consistency_check_removed", "tampered_start_rejected"),
])
def test_mutant_is_caught_by_the_named_gate_case(name, must_fail):
    target = MUTANTS[name][0]
    module = _mutant(name)
    if target == "planner":
        outcomes = _outcomes(module, real_oracle.ManufacturabilityOracle)
    else:
        outcomes = _outcomes(real_planner, module.ManufacturabilityOracle)
    assert outcomes[must_fail] is False
