"""Unit tests for ManufacturingRequest intake -> DesignInput (RM1 order 1 & 2)."""
from __future__ import annotations

from mini_prometheus._contracts import DesignSourceKind, EngineeringVerificationStatus
from mini_prometheus.intake.request_intake import intake

from support import FIXED_TIME


def test_intake_produces_engineer_declared_design_input(engineer_request):
    di = intake(engineer_request, produced_at=FIXED_TIME)
    assert di.engineering_verification_status is EngineeringVerificationStatus.engineer_declared
    assert di.source.kind is DesignSourceKind.manufacturing_request
    # status consistent with source.kind (contract invariant)
    assert di.source.ref.id == engineer_request.request_id


def test_intake_normalizes_manufacturing_intent(engineer_request):
    di = intake(engineer_request, produced_at=FIXED_TIME)
    assert di.material == engineer_request.material
    assert di.stock_form == engineer_request.stock_form
    assert len(di.declared_operations) == len(engineer_request.declared_operations)
    assert di.quantity == engineer_request.quantity


def test_step_attachment_is_carried_opaque(engineer_request):
    di = intake(engineer_request, produced_at=FIXED_TIME)
    assert di.design_artifact_ref is not None
    assert di.design_artifact_ref.media_type == "model/step"
    assert di.design_artifact_ref.content_hash == engineer_request.step_artifact_ref.content_hash
