"""Unit tests for the deterministic planner (RM1 order 3 & 5)."""
from __future__ import annotations

from mini_prometheus import _hashing as h
from mini_prometheus.intake.request_intake import intake
from mini_prometheus.manufacturing_constraints.capability_model import default_model
from mini_prometheus.manufacturing_planning import planner

from support import FIXED_TIME


def test_steps_map_one_to_one_and_are_contiguous(engineer_request):
    di = intake(engineer_request, produced_at=FIXED_TIME)
    _task, plan = planner.plan(di, default_model(), produced_at=FIXED_TIME)
    assert [s.index for s in plan.steps] == list(range(len(di.declared_operations)))
    assert [s.op for s in plan.steps] == [o.op for o in di.declared_operations]
    for s in plan.steps:
        assert s.required_capability
        assert s.provenance_ref.id == di.design_input_id


def test_supported_ops_get_resource_assignments(engineer_request):
    di = intake(engineer_request, produced_at=FIXED_TIME)
    _task, plan = planner.plan(di, default_model(), produced_at=FIXED_TIME)
    assert len(plan.resource_assignments) == len(plan.steps)  # all supported in default model
    for a in plan.resource_assignments:
        assert a.capability_id


def test_plan_id_is_deterministic_from_content_hash(engineer_request):
    di = intake(engineer_request, produced_at=FIXED_TIME)
    _t1, p1 = planner.plan(di, default_model(), produced_at="2026-01-01T00:00:00+00:00")
    _t2, p2 = planner.plan(di, default_model(), produced_at="2026-12-31T23:59:59+00:00")
    assert p1.content_hash == p2.content_hash          # produced_at excluded
    assert p1.plan_id == p2.plan_id
    assert p1.plan_id == h.derive_uuid(p1.content_hash)
