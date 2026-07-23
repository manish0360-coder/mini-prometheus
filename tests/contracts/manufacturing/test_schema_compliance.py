"""Contract-compliance suite (RM1 spec §8): instances validate against the frozen schemas,
closed taxonomies are exactly as frozen, and content-hash identity is stable."""
from __future__ import annotations

import pytest

from mini_prometheus import _hashing as h
from mini_prometheus._contracts import (
    EngineeringVerificationStatus,
    ManufacturabilityReasonCode,
    ManufacturabilityVerdictStatus,
    ProcessOp,
    StockForm,
)
from mini_prometheus._validate import ContractValidationError, validate
from mini_prometheus.intake.request_intake import intake
from mini_prometheus.manufacturing_constraints.capability_model import default_model
from mini_prometheus.manufacturing_planning import planner
from mini_prometheus.orchestration import runner

from support import FIXED_TIME, load_json


def test_raw_request_fixture_validates():
    validate("manufacturing_request", load_json("engineer_request_machined_bracket.json"))


def test_closed_taxonomies_are_frozen_exactly():
    assert [s.value for s in ManufacturabilityVerdictStatus] == [
        "MANUFACTURABLE", "NOT_MANUFACTURABLE", "PLAN_INVALID", "INFRA_ERROR",
    ]
    assert {r.value for r in ManufacturabilityReasonCode} == {
        "CAPABILITY_MISSING", "PRECEDENCE_VIOLATION", "RESOURCE_UNAVAILABLE",
        "TOLERANCE_UNSUPPORTED", "MATERIAL_UNSUPPORTED", "PLAN_MALFORMED",
    }
    assert {s.value for s in StockForm} == {"bar", "plate", "sheet", "block", "tube"}
    assert {s.value for s in EngineeringVerificationStatus} == {"velith_verified", "engineer_declared"}
    assert len(list(ProcessOp)) == 7


def test_every_stage_instance_validates(engineer_request, store_path):
    design_input = intake(engineer_request, produced_at=FIXED_TIME)
    validate("design_input", h.to_contract_dict(design_input))
    task, plan = planner.plan(design_input, default_model(), produced_at=FIXED_TIME)
    validate("manufacturing_task", h.to_contract_dict(task))
    validate("production_plan", h.to_contract_dict(plan))
    result = runner.run(design_input, produced_at=FIXED_TIME, store_path=store_path)
    validate("manufacturing_episode", h.to_contract_dict(result.episode))


def test_invalid_request_is_rejected(engineer_request):
    bad = engineer_request
    bad.quantity = 0  # violates minimum 1
    with pytest.raises(ContractValidationError):
        intake(bad, produced_at=FIXED_TIME)


def test_content_hash_shape_and_stability(engineer_request):
    di1 = intake(engineer_request, produced_at="2026-01-01T00:00:00+00:00")
    di2 = intake(engineer_request, produced_at="2026-12-31T23:59:59+00:00")
    hid = h.content_hash(h.design_input_identity(di1))
    assert hid.startswith("sha256:") and len(hid) == len("sha256:") + 64
    # produced_at differs but identity (and derived id) are stable
    assert h.content_hash(h.design_input_identity(di1)) == h.content_hash(h.design_input_identity(di2))
    assert di1.design_input_id == di2.design_input_id
