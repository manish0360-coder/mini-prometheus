"""RM1 order 1 & 2: ManufacturingRequest intake -> DesignInput normalization.

Produces an ``engineer_declared`` DesignInput from the real engineer input. The optional STEP
attachment is carried **opaque** (never parsed — spec §7). Deterministic ids give reproducibility
(spec §5.5): ``design_input_id = uuid5(NS_MP, hash(identity))`` — valid UUID form, stricter than the
contract's minimum (which only mandates determinism for plan/episode ids); flagged in the milestone notes.
"""
from __future__ import annotations

from mini_prometheus import _hashing as h
from mini_prometheus._contracts import (
    DesignArtifactRef,
    DesignInput,
    DesignSource,
    DesignSourceKind,
    EngineeringVerificationStatus,
    ManufacturingRequest,
    Ref,
)
from mini_prometheus._provenance import make_provenance, now_rfc3339
from mini_prometheus._validate import validate

SCHEMA_VERSION = "1.0.0"
_RULE_ID = "intake.engineer_request"
_RULE_VERSION = "1.0.0"


def intake(request: ManufacturingRequest, *, produced_at: str | None = None) -> DesignInput:
    """Validate the request and normalize it into an engineer_declared DesignInput."""
    validate("manufacturing_request", h.to_contract_dict(request))
    produced_at = produced_at or now_rfc3339()

    source_ref = Ref(id=request.request_id, content_hash=h.content_hash(h.request_identity(request)))

    artifact_ref = None
    if request.step_artifact_ref is not None:
        # OPAQUE: carry the STEP reference; RM1 never reads its geometry (spec §7).
        artifact_ref = DesignArtifactRef(
            media_type=request.step_artifact_ref.media_type,
            id=request.step_artifact_ref.id,
            content_hash=request.step_artifact_ref.content_hash,
        )

    design_input = DesignInput(
        schema_version=SCHEMA_VERSION,
        design_input_id="",  # deterministic id filled after hashing
        engineering_verification_status=EngineeringVerificationStatus.engineer_declared,
        source=DesignSource(kind=DesignSourceKind.manufacturing_request, ref=source_ref),
        material=request.material,
        material_code=request.material_code,
        stock_form=request.stock_form,
        declared_operations=list(request.declared_operations),
        quantity=request.quantity,
        tolerances=request.tolerances,
        design_artifact_ref=artifact_ref,
        provenance=make_provenance(
            source_refs=[source_ref],
            rule_id=_RULE_ID,
            rule_version=_RULE_VERSION,
            produced_at=produced_at,
            component="intake",
            component_version="1.0.0",
        ),
    )
    design_input.design_input_id = h.derive_uuid(h.content_hash(h.design_input_identity(design_input)))
    validate("design_input", h.to_contract_dict(design_input))
    return design_input
