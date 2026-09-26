"""RM9 — Resource Availability: outcomes, plan identity, versioning and validation.

Frozen rules (specs/milestones/RM9-resource-availability.md):
- known resources may be declared unavailable for one planning snapshot (unknown ids rejected first);
- the planner uses only available capable resources, rerouting to an available alternative when one
  exists; when every capable resource is unavailable -> RESOURCE_UNAVAILABLE -> NOT_MANUFACTURABLE;
- a resource absent from the model entirely -> CAPABILITY_MISSING (never RESOURCE_UNAVAILABLE);
- availability changes plan identity ONLY when it materially affects the requested plan;
- verifier/planner report 1.2.0 only when availability participates; otherwise 1.0.0 / 1.1.0 as before.
"""
from __future__ import annotations

import copy

import pytest

from mini_prometheus import _hashing as h
from mini_prometheus.intake.request_intake import intake
from mini_prometheus.manufacturing_constraints.capability_model import (
    ProcessCapabilityModel,
    UnknownResourceError,
    constrained_model,
    default_model,
    with_unavailable_resources,
)
from mini_prometheus.manufacturing_constraints.oracle import (
    UNAVAILABLE_RESOURCES_PARAM,
    ManufacturabilityOracle,
)
from mini_prometheus.manufacturing_planning import planner
from mini_prometheus.orchestration import runner

import support
from support import FIXED_TIME

BASE = support.load_json("engineer_request_machined_bracket.json")
# BASE ops: cut_stock(cap.saw) face_mill(cap.mill) drill(cap.drill) drill deburr(cap.bench) inspect(cap.cmm)


def twin_model() -> ProcessCapabilityModel:
    """The default shop plus a second machining centre mill02 (the only way to test rerouting)."""
    base = default_model()
    return ProcessCapabilityModel(
        version=base.version, op_capability=base.op_capability,
        resources={**base.resources, "mill02": frozenset({"cap.mill", "cap.drill"})},
        supported_materials=base.supported_materials,
    )


def no_lathe_model() -> ProcessCapabilityModel:
    base = default_model()
    return ProcessCapabilityModel(
        version=base.version, op_capability=base.op_capability,
        resources={k: v for k, v in base.resources.items() if k != "lathe01"},
        supported_materials=base.supported_materials,
    )


def _request(ops=None, tolerance="keep"):
    raw = copy.deepcopy(BASE)
    if ops is not None:
        raw["declared_operations"] = [{"op": o} for o in ops]
    if tolerance != "keep":
        raw["tolerances"] = {"general_tolerance_mm": tolerance}
    return support.build_request(raw)


def _run(model, request=None, produced_at=FIXED_TIME):
    design_input = intake(request or _request(), produced_at=produced_at)
    _task, plan = planner.plan(design_input, model, produced_at=produced_at)
    return plan, ManufacturabilityOracle().verify(plan, model)


def _assigned(plan) -> dict[int, str]:
    return {a.step_index: a.resource_id for a in plan.resource_assignments}


# ---------------- outcomes ----------------
def test_only_capable_machine_unavailable_is_resource_unavailable():
    plan, verdict = _run(with_unavailable_resources(default_model(), ["mill01"]))
    assert (verdict.status, verdict.reason_codes) == ("NOT_MANUFACTURABLE", ["RESOURCE_UNAVAILABLE"])
    assert verdict.detail == "RESOURCE_UNAVAILABLE: mill01" and verdict.grounded
    # face_mill (1) and both drills (2, 3) cannot be assigned; the other steps keep their machines.
    assert _assigned(plan) == {0: "saw01", 4: "bench01", 5: "cmm01"}
    affected = {s.index: s.params[UNAVAILABLE_RESOURCES_PARAM]
                for s in plan.steps if UNAVAILABLE_RESOURCES_PARAM in s.params}
    assert affected == {1: ["mill01"], 2: ["mill01"], 3: ["mill01"]}


def test_alternative_available_machine_is_used():
    plan, verdict = _run(with_unavailable_resources(twin_model(), ["mill01"]))
    assert (verdict.status, verdict.reason_codes, verdict.detail) == ("MANUFACTURABLE", [], None)
    assert _assigned(plan) == {0: "saw01", 1: "mill02", 2: "mill02", 3: "mill02", 4: "bench01", 5: "cmm01"}


def test_absent_machine_stays_capability_missing():
    # lathe01 is absent from the model: turning is CAPABILITY_MISSING even with availability declared.
    model = with_unavailable_resources(no_lathe_model(), ["mill01"])
    _plan, verdict = _run(model, _request(["turn"]))
    assert (verdict.status, verdict.reason_codes) == ("NOT_MANUFACTURABLE", ["CAPABILITY_MISSING"])
    assert verdict.detail is None


def test_known_machine_marked_unavailable_is_not_capability_missing():
    _plan, verdict = _run(with_unavailable_resources(default_model(), ["lathe01"]), _request(["turn"]))
    assert verdict.reason_codes == ["RESOURCE_UNAVAILABLE"] and verdict.detail == "RESOURCE_UNAVAILABLE: lathe01"


def test_irrelevant_unavailable_machine_changes_nothing():
    _plan, verdict = _run(with_unavailable_resources(default_model(), ["lathe01"]))
    assert (verdict.status, verdict.reason_codes, verdict.detail) == ("MANUFACTURABLE", [], None)


def test_multiple_unavailable_machines_are_all_named():
    _plan, verdict = _run(with_unavailable_resources(default_model(), ["mill01", "cmm01"]))
    assert (verdict.status, verdict.reason_codes) == ("NOT_MANUFACTURABLE", ["RESOURCE_UNAVAILABLE"])
    assert verdict.detail == "RESOURCE_UNAVAILABLE: cmm01, mill01"


def test_stored_plan_becomes_stale_when_its_machine_goes_down():
    stored, _ = _run(default_model())                                   # assigned to mill01
    verdict = ManufacturabilityOracle().verify(stored, with_unavailable_resources(default_model(), ["mill01"]))
    assert verdict.reason_codes == ["RESOURCE_UNAVAILABLE"] and verdict.status == "NOT_MANUFACTURABLE"
    # Even where an alternative exists, a stored plan still assigned to the down machine is stale.
    stored_twin, _ = _run(twin_model())
    verdict_twin = ManufacturabilityOracle().verify(stored_twin, with_unavailable_resources(twin_model(), ["mill01"]))
    assert verdict_twin.reason_codes == ["RESOURCE_UNAVAILABLE"] and verdict_twin.detail == "RESOURCE_UNAVAILABLE: mill01"


def test_availability_findings_combine_with_rm8_findings():
    model = with_unavailable_resources(constrained_model(), ["mill01"])
    _plan, verdict = _run(model, _request(["face_mill", "cut_stock", "drill", "inspect"], tolerance=0.001))
    assert (verdict.status, verdict.reason_codes) == (
        "PLAN_INVALID", ["PRECEDENCE_VIOLATION", "RESOURCE_UNAVAILABLE", "TOLERANCE_UNSUPPORTED"])
    _plan, verdict = _run(model, _request(tolerance=0.03))
    assert (verdict.status, verdict.reason_codes) == (
        "NOT_MANUFACTURABLE", ["RESOURCE_UNAVAILABLE", "TOLERANCE_UNSUPPORTED"])


# ---------------- plan identity ----------------
def test_irrelevant_unavailable_resource_does_not_change_plan_identity():
    normal, normal_verdict = _run(default_model())
    for model in (with_unavailable_resources(default_model(), ["lathe01"]),        # machine not used
                  ):
        plan, verdict = _run(model)
        assert h.to_contract_dict(plan) == h.to_contract_dict(normal)            # byte-identical plan
        assert plan.content_hash == normal.content_hash
        assert verdict == normal_verdict                                        # incl. version 1.0.0
    # a non-selected provider being down does not matter either
    twin_normal, twin_verdict = _run(twin_model())
    plan, verdict = _run(with_unavailable_resources(twin_model(), ["mill02"]))
    assert h.to_contract_dict(plan) == h.to_contract_dict(twin_normal) and verdict == twin_verdict


def test_relevant_unavailable_resource_changes_plan_identity():
    normal, _ = _run(twin_model())
    rerouted, _ = _run(with_unavailable_resources(twin_model(), ["mill01"]))
    assert rerouted.content_hash != normal.content_hash
    assert _assigned(normal)[1] == "mill01" and _assigned(rerouted)[1] == "mill02"


def test_identical_availability_gives_identical_hashes():
    a, va = _run(with_unavailable_resources(default_model(), ["cmm01", "mill01"]))
    b, vb = _run(with_unavailable_resources(default_model(), ["mill01", "cmm01"]), produced_at="2027-01-01T00:00:00+00:00")
    assert a.content_hash == b.content_hash and va == vb


def test_empty_availability_is_the_unchanged_model():
    assert with_unavailable_resources(default_model(), []) == default_model()


# ---------------- versioning ----------------
@pytest.mark.parametrize("model,verifier,planner_rule", [
    (with_unavailable_resources(default_model(), ["mill01"]), "1.2.0", "1.2.0"),       # unavailable
    (with_unavailable_resources(twin_model(), ["mill01"]), "1.2.0", "1.2.0"),          # rerouted
    (with_unavailable_resources(default_model(), ["lathe01"]), "1.0.0", "1.0.0"),      # irrelevant
    (with_unavailable_resources(constrained_model(), ["lathe01"]), "1.1.0", "1.1.0"),  # irrelevant, ECR
    (default_model(), "1.0.0", "1.0.0"),
])
def test_versions_stamp_1_2_0_only_when_availability_participates(model, verifier, planner_rule):
    plan, verdict = _run(model)
    assert verdict.produced_by.version == verifier
    assert plan.provenance.rule_version == planner_rule


# ---------------- validation ----------------
def test_unknown_resource_id_is_rejected_before_planning():
    with pytest.raises(UnknownResourceError, match="mill99"):
        with_unavailable_resources(default_model(), ["mill01", "mill99"])
    with pytest.raises(UnknownResourceError):                  # absent from THIS model => unknown
        with_unavailable_resources(no_lathe_model(), ["lathe01"])
    assert issubclass(UnknownResourceError, ValueError)


def test_availability_outcome_is_grounded_and_logged(tmp_path):
    store = tmp_path / "episodes.jsonl"
    result = runner.run_from_request(_request(), capability_model=with_unavailable_resources(default_model(), ["mill01"]),
                                     produced_at=FIXED_TIME, store_path=str(store))
    assert result.status == "NOT_MANUFACTURABLE" and result.verdict.grounded and not result.is_error
    assert result.episode.verdict.reason_codes == ["RESOURCE_UNAVAILABLE"]
    assert result.episode.verdict.detail == "RESOURCE_UNAVAILABLE: mill01"
    assert store.read_text(encoding="utf-8").count("\n") == 1
