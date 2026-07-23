"""Velith adapter: EngineeringResult -> DesignInput (velith_verified).

Adapters ONLY, no business logic (Law 14; spec §7). Reads ``verified`` and the OPAQUE design
artifact; NEVER parses the artifact and NEVER re-verifies engineering (Law 6/9). The manufacturing
intent (material/stock_form/operations/quantity/tolerances) is supplied alongside the verified
design, since RM1 does not extract intent from geometry (opaque). Produces the SAME DesignInput
contract as the engineer path, differing only in status/source/artifact — proving both paths converge.
"""
from __future__ import annotations

from mini_prometheus import _hashing as h
from mini_prometheus._contracts import (
    DesignArtifactRef,
    DesignInput,
    DesignSource,
    DesignSourceKind,
    EngineeringResult,
    EngineeringVerificationStatus,
    ManufacturingRequest,
    Ref,
)
from mini_prometheus._provenance import make_provenance, now_rfc3339
from mini_prometheus._validate import validate

SCHEMA_VERSION = "1.0.0"
_RULE_ID = "integrations.velith.adapter"
_RULE_VERSION = "1.0.0"


def from_engineering_result(
    result: EngineeringResult,
    manufacturing_intent: ManufacturingRequest,
    *,
    produced_at: str | None = None,
) -> DesignInput:
    if result.verified is not True:  # velith_verified path requires a verified result
        raise ValueError("Velith EngineeringResult is not verified; cannot use velith_verified path.")
    validate("manufacturing_request", h.to_contract_dict(manufacturing_intent))
    produced_at = produced_at or now_rfc3339()

    source_ref = Ref(id=result.result_id, content_hash=result.content_hash)
    # OPAQUE Velith design artifact — carried, never parsed.
    artifact_ref = DesignArtifactRef(
        media_type=result.design_artifact.media_type,
        id=result.design_artifact.ref,
        content_hash=result.design_artifact.content_hash,
    )

    design_input = DesignInput(
        schema_version=SCHEMA_VERSION,
        design_input_id="",
        engineering_verification_status=EngineeringVerificationStatus.velith_verified,
        source=DesignSource(kind=DesignSourceKind.velith_engineering_result, ref=source_ref),
        material=manufacturing_intent.material,
        material_code=manufacturing_intent.material_code,
        stock_form=manufacturing_intent.stock_form,
        declared_operations=list(manufacturing_intent.declared_operations),
        quantity=manufacturing_intent.quantity,
        tolerances=manufacturing_intent.tolerances,
        design_artifact_ref=artifact_ref,
        provenance=make_provenance(
            source_refs=[source_ref],
            rule_id=_RULE_ID,
            rule_version=_RULE_VERSION,
            produced_at=produced_at,
            component="velith-adapter",
            component_version="1.0.0",
        ),
    )
    design_input.design_input_id = h.derive_uuid(h.content_hash(h.design_input_identity(design_input)))
    validate("design_input", h.to_contract_dict(design_input))
    return design_input
