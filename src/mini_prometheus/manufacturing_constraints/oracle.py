"""RM1 order 4: the Manufacturability Oracle — MP's concrete oracle implementing the
Noetica `Verifier` protocol (Law 15).

Deterministic (spec §9). Checks are plan+model derivable only: well-formedness/precedence,
capability existence, and material support. Emits a Noetica `Verdict` whose status/reason_codes
come from MP's OWN closed taxonomies. INFRA_ERROR is never produced here (it is a runner-level
infrastructure fault, spec §5.3); the oracle only returns grounded outcomes.
"""
from __future__ import annotations

from mini_prometheus._contracts import (
    ManufacturabilityReasonCode as RC,
    ManufacturabilityVerdictStatus as Status,
    ProducedBy,
    ProductionPlan,
    Verdict,
)
from mini_prometheus.manufacturing_constraints.capability_model import (
    ProcessCapabilityModel,
    material_supported,
    resource_for_capability,
)

_COMPONENT = "manufacturability-oracle"
_VERSION = "1.0.0"


class ManufacturabilityOracle:
    """Implements the Noetica `Verifier` protocol for machined-part manufacturability."""

    def verify(self, plan: ProductionPlan, capability_model: ProcessCapabilityModel) -> Verdict:
        reasons: set[RC] = set()
        status = Status.MANUFACTURABLE

        indices = [s.index for s in plan.steps]
        if not plan.steps:
            reasons.add(RC.PLAN_MALFORMED)
            status = Status.PLAN_INVALID
        elif indices != list(range(len(plan.steps))):
            # RM1 precedence is the linear step order; non-contiguous/out-of-order == violation.
            reasons.add(RC.PRECEDENCE_VIOLATION)
            status = Status.PLAN_INVALID
        else:
            for step in plan.steps:
                if resource_for_capability(capability_model, step.required_capability) is None:
                    reasons.add(RC.CAPABILITY_MISSING)
            for material in {m for step in plan.steps for m in step.inputs}:
                if not material_supported(capability_model, material):
                    reasons.add(RC.MATERIAL_UNSUPPORTED)
            if reasons:
                status = Status.NOT_MANUFACTURABLE

        return Verdict(
            grounded=True,
            is_error=False,
            status=status.value,
            reason_codes=sorted(rc.value for rc in reasons),
            produced_by=ProducedBy(component=_COMPONENT, version=_VERSION),
            detail=None,
        )
