"""Unit tests for the Manufacturability Oracle (RM1 order 4; Noetica Verifier protocol)."""
from __future__ import annotations

from mini_prometheus._contracts import (
    ProcessOp,
    ProcessStep,
    ProducedBy,
    ProductionPlan,
    Provenance,
    Ref,
)
from mini_prometheus._verifier import Verifier
from mini_prometheus.intake.request_intake import intake
from mini_prometheus.manufacturing_constraints.capability_model import (
    ProcessCapabilityModel,
    default_model,
)
from mini_prometheus.manufacturing_constraints.oracle import ManufacturabilityOracle
from mini_prometheus.manufacturing_planning import planner

from support import FIXED_TIME

_REF = Ref(id="00000000-0000-0000-0000-000000000000", content_hash="sha256:" + "0" * 64)
_PROV = Provenance(
    source_refs=[_REF], rule_id="test", rule_version="1.0.0",
    capability_model_version="1.0.0",
    produced_by=ProducedBy(component="test", version="1.0.0"), produced_at=FIXED_TIME,
)


def _plan(steps, material="Aluminum 6061"):
    for s in steps:
        s.inputs = [material]
    return ProductionPlan(
        schema_version="1.0.0", plan_id="x", task_ref=_REF, steps=steps,
        resource_assignments=[], capability_model_version="1.0.0",
        content_hash="sha256:" + "0" * 64, provenance=_PROV,
    )


def _step(index, op, cap):
    return ProcessStep(index=index, op=op, required_capability=cap, inputs=[], provenance_ref=_REF)


def test_oracle_implements_verifier_protocol():
    assert isinstance(ManufacturabilityOracle(), Verifier)


def test_manufacturable_has_no_reasons(engineer_request):
    di = intake(engineer_request, produced_at=FIXED_TIME)
    _task, plan = planner.plan(di, default_model(), produced_at=FIXED_TIME)
    verdict = ManufacturabilityOracle().verify(plan, default_model())
    assert verdict.status == "MANUFACTURABLE"
    assert verdict.reason_codes == []
    assert verdict.grounded and not verdict.is_error


def test_capability_missing_is_not_manufacturable():
    plan = _plan([_step(0, ProcessOp.turn, "cap.lathe")])
    model = ProcessCapabilityModel(
        version="1.0.0", op_capability=default_model().op_capability,
        resources={"mill01": frozenset({"cap.mill"})},  # no lathe
        supported_materials=default_model().supported_materials,
    )
    verdict = ManufacturabilityOracle().verify(plan, model)
    assert verdict.status == "NOT_MANUFACTURABLE"
    assert "CAPABILITY_MISSING" in verdict.reason_codes
    assert not verdict.is_error  # grounded outcome, not an error


def test_material_unsupported_is_not_manufacturable():
    plan = _plan([_step(0, ProcessOp.face_mill, "cap.mill")], material="Titanium")
    verdict = ManufacturabilityOracle().verify(plan, default_model())
    assert verdict.status == "NOT_MANUFACTURABLE"
    assert "MATERIAL_UNSUPPORTED" in verdict.reason_codes


def test_non_contiguous_plan_is_plan_invalid():
    plan = _plan([_step(0, ProcessOp.face_mill, "cap.mill"), _step(2, ProcessOp.drill, "cap.drill")])
    verdict = ManufacturabilityOracle().verify(plan, default_model())
    assert verdict.status == "PLAN_INVALID"
    assert "PRECEDENCE_VIOLATION" in verdict.reason_codes


def test_invariant_grounded_negative_has_reasons_and_positive_has_none():
    ok = ManufacturabilityOracle().verify(_plan([_step(0, ProcessOp.face_mill, "cap.mill")]), default_model())
    assert ok.status == "MANUFACTURABLE" and ok.reason_codes == []
    bad = ManufacturabilityOracle().verify(_plan([_step(0, ProcessOp.turn, "cap.lathe")]),
        ProcessCapabilityModel(version="1.0.0", op_capability=default_model().op_capability,
            resources={}, supported_materials=default_model().supported_materials))
    assert bad.status != "MANUFACTURABLE" and len(bad.reason_codes) >= 1
