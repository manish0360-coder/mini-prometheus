"""RM8 — Engineering Constraint Reasoning: declared precedence (C2), tolerance feasibility (C3),
multiple findings, versioning, determinism and hash stability.

Cases run the real pipeline (intake -> planner -> oracle -> episode) on requests derived from the
engineer fixture, so each assertion is about what an engineer would actually receive. The frozen
RM8 rules (specs/milestones/RM8-engineering-constraint-reasoning.md):
- declared pair (A before B), both present, some A after some B -> PRECEDENCE_VIOLATION, PLAN_INVALID;
- requested tolerance strictly tighter than a tolerance-bearing capability's minimum ->
  TOLERANCE_UNSUPPORTED, NOT_MANUFACTURABLE; equal/looser feasible; absent or non-bearing -> no check;
- all findings reported; PLAN_INVALID over NOT_MANUFACTURABLE; verifier 1.1.0 only with constraint data.
"""
from __future__ import annotations

import copy

import pytest

from mini_prometheus._contracts import (
    ProcessOp,
    ProcessStep,
    ProducedBy,
    ProductionPlan,
    Provenance,
    Ref,
)
from mini_prometheus.intake.request_intake import intake
from mini_prometheus.manufacturing_constraints.capability_model import (
    constrained_model,
    default_model,
)
from mini_prometheus.manufacturing_constraints.oracle import (
    REQUIRED_TOLERANCE_PARAM,
    ManufacturabilityOracle,
    constraint_data_present,
)
from mini_prometheus.manufacturing_planning import planner
from mini_prometheus.orchestration import runner

import support
from support import FIXED_TIME

BASE = support.load_json("engineer_request_machined_bracket.json")
# BASE ops: cut_stock, face_mill, drill, drill, deburr, inspect; tolerance 0.1 mm; Aluminum 6061.


def _request(ops=None, tolerance="keep", material=None):
    raw = copy.deepcopy(BASE)
    if ops is not None:
        raw["declared_operations"] = [{"op": o} for o in ops]
    if tolerance is None:
        raw.pop("tolerances", None)
    elif tolerance != "keep":
        raw["tolerances"] = {"general_tolerance_mm": tolerance}
    if material is not None:
        raw["material"] = material
    return support.build_request(raw)


def _verify(request, model, produced_at=FIXED_TIME):
    design_input = intake(request, produced_at=produced_at)
    _task, plan = planner.plan(design_input, model, produced_at=produced_at)
    return plan, ManufacturabilityOracle().verify(plan, model)


def _outcome(request, model=None):
    _plan, verdict = _verify(request, model or constrained_model())
    return verdict.status, verdict.reason_codes


# ---------------- C2: declared precedence ----------------
def test_precedence_violating_order_cut_stock_after_machining():
    assert _outcome(_request(["face_mill", "cut_stock", "drill", "inspect"])) == (
        "PLAN_INVALID", ["PRECEDENCE_VIOLATION"])


def test_precedence_violating_order_inspect_not_last():
    assert _outcome(_request(["cut_stock", "inspect", "face_mill"])) == (
        "PLAN_INVALID", ["PRECEDENCE_VIOLATION"])


def test_precedence_valid_order_is_manufacturable():
    assert _outcome(_request()) == ("MANUFACTURABLE", [])


@pytest.mark.parametrize("ops", [
    ["cut_stock", "deburr", "face_mill", "drill", "inspect"],       # deburr before machining
    ["cut_stock", "face_mill", "drill", "deburr", "inspect"],       # deburr after machining
    ["cut_stock", "drill", "face_mill", "inspect"],                 # inter-machining order swapped
    ["cut_stock", "turn", "pocket_mill", "deburr", "drill", "inspect"],
])
def test_unconstrained_pairs_never_fail(ops):
    assert _outcome(_request(ops)) == ("MANUFACTURABLE", [])


def test_absent_constrained_ops_means_no_precedence_finding():
    # No cut_stock and no inspect: no declared pair applies, whatever the order.
    assert _outcome(_request(["drill", "face_mill", "deburr"])) == ("MANUFACTURABLE", [])


def test_absent_constraint_data_means_no_precedence_finding():
    # The default model declares no precedence: a misordered plan is legacy-MANUFACTURABLE.
    assert _outcome(_request(["inspect", "face_mill", "cut_stock"]), default_model()) == ("MANUFACTURABLE", [])


_REF = Ref(id="00000000-0000-0000-0000-000000000000", content_hash="sha256:" + "0" * 64)
_PROV = Provenance(source_refs=[_REF], rule_id="test", rule_version="1.0.0", capability_model_version="1.1.0",
                   produced_by=ProducedBy(component="test", version="1.0.0"), produced_at=FIXED_TIME)


def _hand_plan(indices_ops):
    steps = [ProcessStep(index=i, op=op, required_capability=cap, inputs=["Aluminum 6061"], provenance_ref=_REF)
             for i, op, cap in indices_ops]
    return ProductionPlan(schema_version="1.0.0", plan_id="x", task_ref=_REF, steps=steps,
                          resource_assignments=[], capability_model_version="1.1.0",
                          content_hash="sha256:" + "0" * 64, provenance=_PROV)


@pytest.mark.parametrize("model_factory,version", [(default_model, "1.0.0"), (constrained_model, "1.1.0")])
def test_structural_step_numbering_check_unchanged(model_factory, version):
    plan = _hand_plan([(0, ProcessOp.cut_stock, "cap.saw"), (2, ProcessOp.drill, "cap.drill")])
    verdict = ManufacturabilityOracle().verify(plan, model_factory())
    assert (verdict.status, verdict.reason_codes) == ("PLAN_INVALID", ["PRECEDENCE_VIOLATION"])
    assert verdict.produced_by.version == version


# ---------------- C3: tolerance feasibility ----------------
def test_tolerance_tighter_than_machine_minimum_is_unsupported():
    # drill minimum 0.05 mm; 0.03 requested
    assert _outcome(_request(tolerance=0.03)) == ("NOT_MANUFACTURABLE", ["TOLERANCE_UNSUPPORTED"])


def test_tolerance_tighter_than_lathe_minimum_is_unsupported():
    assert _outcome(_request(["cut_stock", "turn", "inspect"], tolerance=0.005)) == (
        "NOT_MANUFACTURABLE", ["TOLERANCE_UNSUPPORTED"])


def test_tolerance_equal_to_machine_minimum_is_feasible():
    assert _outcome(_request(tolerance=0.05)) == ("MANUFACTURABLE", [])                      # drill == 0.05
    assert _outcome(_request(["cut_stock", "face_mill", "inspect"], tolerance=0.02)) == ("MANUFACTURABLE", [])


def test_tolerance_looser_than_machine_minimum_is_feasible():
    assert _outcome(_request(tolerance=0.1)) == ("MANUFACTURABLE", [])


def test_absent_tolerance_means_no_tolerance_finding():
    plan, verdict = _verify(_request(tolerance=None), constrained_model())
    assert (verdict.status, verdict.reason_codes) == ("MANUFACTURABLE", [])
    assert all(REQUIRED_TOLERANCE_PARAM not in (s.params or {}) for s in plan.steps)
    assert plan.provenance.rule_version == "1.0.0"


def test_non_tolerance_bearing_operations_are_never_checked():
    # 0.001 mm is tighter than every machine, but saw/bench/cmm do not establish tolerance.
    plan, verdict = _verify(_request(["cut_stock", "deburr", "inspect"], tolerance=0.001), constrained_model())
    assert (verdict.status, verdict.reason_codes) == ("MANUFACTURABLE", [])
    assert all(REQUIRED_TOLERANCE_PARAM not in (s.params or {}) for s in plan.steps)


def test_tolerance_carried_only_on_tolerance_bearing_steps():
    plan, _ = _verify(_request(tolerance=0.1), constrained_model())
    carried = {s.op.value for s in plan.steps if REQUIRED_TOLERANCE_PARAM in (s.params or {})}
    assert carried == {"face_mill", "drill"}
    assert all(s.params[REQUIRED_TOLERANCE_PARAM] == 0.1 for s in plan.steps if s.op.value in carried)
    assert plan.provenance.rule_version == "1.1.0"


# ---------------- multiple findings ----------------
def test_multiple_independent_findings_reported_together():
    assert _outcome(_request(tolerance=0.001, material="Titanium")) == (
        "NOT_MANUFACTURABLE", ["MATERIAL_UNSUPPORTED", "TOLERANCE_UNSUPPORTED"])


def test_precedence_does_not_discard_tolerance_finding():
    assert _outcome(_request(["face_mill", "cut_stock", "drill", "inspect"], tolerance=0.001)) == (
        "PLAN_INVALID", ["PRECEDENCE_VIOLATION", "TOLERANCE_UNSUPPORTED"])


# ---------------- versioning ----------------
def test_default_path_reports_rm1_versions_and_carries_no_tolerance():
    plan, verdict = _verify(_request(tolerance=0.001), default_model())
    assert verdict.produced_by.version == "1.0.0"
    assert plan.provenance.rule_version == "1.0.0"
    assert all(REQUIRED_TOLERANCE_PARAM not in (s.params or {}) for s in plan.steps)
    assert (verdict.status, verdict.reason_codes) == ("MANUFACTURABLE", [])       # no tolerance reasoning
    assert not constraint_data_present(default_model())


def test_constrained_path_reports_verifier_1_1_0():
    _plan, verdict = _verify(_request(), constrained_model())
    assert verdict.produced_by.version == "1.1.0"
    assert constraint_data_present(constrained_model())


# ---------------- determinism, hash stability, grounded episodes ----------------
def test_constrained_path_is_deterministic():
    a_plan, a_verdict = _verify(_request(tolerance=0.001), constrained_model())
    b_plan, b_verdict = _verify(_request(tolerance=0.001), constrained_model())
    assert a_plan.content_hash == b_plan.content_hash
    assert a_verdict == b_verdict


def test_constrained_hashes_stable_across_timestamps(tmp_path):
    r1 = runner.run_from_request(_request(tolerance=0.03), capability_model=constrained_model(),
                                 produced_at="2026-01-01T00:00:00+00:00", store_path=str(tmp_path / "a.jsonl"))
    r2 = runner.run_from_request(_request(tolerance=0.03), capability_model=constrained_model(),
                                 produced_at="2027-06-30T12:34:56+00:00", store_path=str(tmp_path / "b.jsonl"))
    assert r1.plan.content_hash == r2.plan.content_hash
    assert r1.episode.content_hash == r2.episode.content_hash
    assert r1.status == r2.status == "NOT_MANUFACTURABLE"


@pytest.mark.parametrize("ops,tolerance,status", [
    (["face_mill", "cut_stock", "inspect"], 0.1, "PLAN_INVALID"),
    (None, 0.001, "NOT_MANUFACTURABLE"),
])
def test_ecr_findings_are_grounded_and_logged(tmp_path, ops, tolerance, status):
    store = tmp_path / "episodes.jsonl"
    result = runner.run_from_request(_request(ops, tolerance=tolerance), capability_model=constrained_model(),
                                     produced_at=FIXED_TIME, store_path=str(store))
    assert result.status == status and result.verdict.grounded and not result.is_error
    assert result.episode is not None and store.read_text(encoding="utf-8").count("\n") == 1
    assert result.episode.capability_model_version == "1.1.0"
