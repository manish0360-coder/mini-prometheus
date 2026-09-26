"""RM1 order 4: the Manufacturability Oracle — MP's concrete oracle implementing the
Noetica `Verifier` protocol (Law 15).

Deterministic (spec §9). Checks are plan+model derivable only: well-formedness/precedence,
capability existence, and material support. Emits a Noetica `Verdict` whose status/reason_codes
come from MP's OWN closed taxonomies. INFRA_ERROR is never produced here (it is a runner-level
infrastructure fault, spec §5.3); the oracle only returns grounded outcomes.

RM8 — Engineering Constraint Reasoning (specs/milestones/RM8-engineering-constraint-reasoning.md).
Two checks driven ONLY by the capability model's declarative constraint data (empty on
``default_model()``, so the default path is byte-identical to RM1-RM5 and still reports 1.0.0):
- Declared precedence (C2): for each declared pair (A, B) meaning "A before B", if both ops are in
  the plan and some A step occurs after some B step -> PRECEDENCE_VIOLATION, status PLAN_INVALID.
  Only declared pairs are checked; unconstrained pairs can never fail. The RM1 structural
  step-numbering check is unchanged.
- Tolerance feasibility (C3): a step carrying params["required_tolerance_mm"] (written by the
  planner under a constrained model only) whose capability is tolerance-bearing is infeasible when
  the requested tolerance is strictly tighter than that capability's minimum ->
  TOLERANCE_UNSUPPORTED, status NOT_MANUFACTURABLE. Equal or looser is feasible; no requested
  tolerance, or a capability that is not tolerance-bearing, means no check.
All applicable findings are reported together; PLAN_INVALID takes precedence over
NOT_MANUFACTURABLE.
The Verifier signature and the closed taxonomies are unchanged.
"""
from __future__ import annotations

from mini_prometheus._contracts import (
    ManufacturabilityReasonCode as RC,
    ManufacturabilityVerdictStatus as Status,
    ProcessOp,
    ProducedBy,
    ProductionPlan,
    Verdict,
)
from mini_prometheus.manufacturing_constraints.capability_model import (
    ProcessCapabilityModel,
    material_supported,
    min_tolerance_for_capability,
    resource_for_capability,
)

_COMPONENT = "manufacturability-oracle"
_VERSION = "1.0.0"          # the RM1 rule set (the default path)
_VERSION_ECR = "1.1.0"      # RM1 rule set + RM8 declared-precedence and tolerance checks

# The step parameter through which the planner carries a requested tolerance (constrained model
# only).
REQUIRED_TOLERANCE_PARAM = "required_tolerance_mm"


def constraint_data_present(model: ProcessCapabilityModel) -> bool:
    """True iff the model carries RM8 declarative constraint data (never for default_model())."""
    return bool(model.ordering_constraints) or bool(model.capability_tolerance_mm)


def _declared_precedence_violated(plan: ProductionPlan, model: ProcessCapabilityModel) -> bool:
    """True iff a declared pair (A before B) has an A step after a B step. Self-pairs ignored."""
    positions: dict[ProcessOp, list[int]] = {}
    for step in plan.steps:
        positions.setdefault(step.op, []).append(step.index)
    for before, after in model.ordering_constraints:
        if before == after or before not in positions or after not in positions:
            continue
        if max(positions[before]) > min(positions[after]):
            return True
    return False


def _tolerance_unsupported(plan: ProductionPlan, model: ProcessCapabilityModel) -> bool:
    """True iff some step requests a tolerance strictly tighter than its capability's minimum."""
    for step in plan.steps:
        requested = (step.params or {}).get(REQUIRED_TOLERANCE_PARAM)
        if requested is None:
            continue
        minimum = min_tolerance_for_capability(model, step.required_capability)
        if minimum is None:
            continue
        if requested < minimum:
            return True
    return False


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
            # RM8: both checks are inert when the model has no constraint data (the default path).
            if _declared_precedence_violated(plan, capability_model):
                reasons.add(RC.PRECEDENCE_VIOLATION)
            if _tolerance_unsupported(plan, capability_model):
                reasons.add(RC.TOLERANCE_UNSUPPORTED)
            if RC.PRECEDENCE_VIOLATION in reasons:
                status = Status.PLAN_INVALID
            elif reasons:
                status = Status.NOT_MANUFACTURABLE

        version = _VERSION_ECR if constraint_data_present(capability_model) else _VERSION
        return Verdict(
            grounded=True,
            is_error=False,
            status=status.value,
            reason_codes=sorted(rc.value for rc in reasons),
            produced_by=ProducedBy(component=_COMPONENT, version=version),
            detail=None,
        )
