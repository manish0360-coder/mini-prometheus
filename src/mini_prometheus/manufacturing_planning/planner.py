"""RM1 order 3 & 5: the deterministic planner and ProductionPlan generation.

Maps a DesignInput's ordered declared operations 1:1 to ProcessSteps (index 0..n-1), assigns each
a required capability and a resource from the capability model, and produces a content-hashed,
provenance-complete ProductionPlan. Fully deterministic (spec §9): same DesignInput + same model
version -> same plan and same content_hash. A model-based planner is a later seam (spec §9).

RM8 (C3): under a capability model that carries tolerance data (``constrained_model()``), a
request's ``general_tolerance_mm`` is carried on each tolerance-bearing step as
``params["required_tolerance_mm"]`` for the oracle, and the planning rule version becomes 1.1.0.
With ``default_model()`` nothing changes.

RM9: resources are assigned from the AVAILABLE providers only (declared ``unavailable_resources``).
A step is touched only when availability materially affects it (its RM1-selected resource is
unavailable): it is rerouted to the next available provider or left unassigned, and its
``params["unavailable_resources"]`` names that capability's unavailable providers; the planning rule
version becomes 1.2.0. Unavailability irrelevant to the request leaves the plan byte-identical.

RM10 (single-job timeline — NOT a production scheduler): an engineer may declare, per operation,
``params["duration_min"]`` = the total manufacturing time of that operation for this request, in
integer minutes (>= 1; no float, bool or string; no conversion). When at least one operation
declares it (timing requested) AND every operation declares a valid one AND every step has an
assigned machine, the planner derives a serialized timeline on the steps — ``duration_min`` (the
declared input, copied), ``schedule_start_min`` / ``schedule_end_min`` (derived: start_0 = 0,
start_i = end_(i-1), end_i = start_i + duration_i) and, on the final step only,
``schedule_lead_time_min`` (= the final end) — and the planning rule version becomes 1.3.0.
Otherwise no timeline value of any kind is written (no default, estimate or partial timeline); the
missing prerequisites are reported by ``timeline_issues``. Start/end values supplied in a request
are never read. Requests that declare no duration are unchanged.
"""
from __future__ import annotations

from mini_prometheus import _hashing as h
from mini_prometheus._contracts import (
    DeclaredOperation,
    DesignInput,
    ManufacturingTask,
    ProcessStep,
    ProductionPlan,
    ProductIntent,
    Ref,
    ResourceAssignment,
)
from mini_prometheus._provenance import make_provenance, now_rfc3339
from mini_prometheus._validate import validate
from mini_prometheus.manufacturing_constraints.capability_model import (
    ProcessCapabilityModel,
    availability_affects_capability,
    available_resource_for_capability,
    capability_for_op,
    min_tolerance_for_capability,
    providers_for_capability,
)
from mini_prometheus.manufacturing_constraints.oracle import (
    DURATION_PARAM,
    REQUIRED_TOLERANCE_PARAM,
    SCHEDULE_END_PARAM,
    SCHEDULE_LEAD_TIME_PARAM,
    SCHEDULE_START_PARAM,
    UNAVAILABLE_RESOURCES_PARAM,
)

SCHEMA_VERSION = "1.0.0"
RULE_VERSION = "1.0.0"              # the RM1 planning rule (the default path)
RULE_VERSION_TOLERANCE = "1.1.0"    # RM1 rule + RM8 tolerance carriage (only when data is added)
RULE_VERSION_AVAILABILITY = "1.2.0"  # + RM9 availability-aware selection (only when it mattered)
RULE_VERSION_TIMELINE = "1.3.0"     # + RM10 single-job timeline (only when a valid one is derived)

_MISSING = object()


def _declared_duration(declared: DeclaredOperation) -> object:
    """The engineer-declared ``duration_min`` of an operation, or ``_MISSING`` if not declared."""
    return (declared.params or {}).get(DURATION_PARAM, _MISSING)


def valid_duration(value: object) -> bool:
    """RM10: integer minutes >= 1. No bool, float or string, and no conversion of any kind."""
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1


def timing_requested(design_input: DesignInput) -> bool:
    """True iff the engineer declared ``duration_min`` on at least one operation."""
    return any(DURATION_PARAM in (d.params or {}) for d in design_input.declared_operations)


def _timeline_issues(design_input: DesignInput, assigned: set[int]) -> list[str]:
    if not timing_requested(design_input):
        return []
    issues: list[str] = []
    for i, declared in enumerate(design_input.declared_operations):
        label = f"step {i} ({declared.op.value})"
        value = _declared_duration(declared)
        if value is _MISSING:
            issues.append(f"{label}: {DURATION_PARAM} missing")
        elif not valid_duration(value):
            issues.append(f"{label}: {DURATION_PARAM} invalid ({value!r}); must be an integer >= 1")
        if i not in assigned:
            issues.append(f"{label}: no machine assigned")
    return issues


def timeline_issues(design_input: DesignInput, production_plan: ProductionPlan) -> list[str]:
    """RM10: why no timeline can be derived for this request/plan (empty when timing was not
    requested, or when a valid timeline exists). Derivable from the persisted episode (its design
    input and plan), so the report is grounded in recorded evidence."""
    assigned = {a.step_index for a in production_plan.resource_assignments}
    return _timeline_issues(design_input, assigned)


def lead_time_min(production_plan: ProductionPlan) -> int | None:
    """RM10: the job lead time recorded on the final step, or None when the plan has no timeline."""
    if not production_plan.steps:
        return None
    value = (production_plan.steps[-1].params or {}).get(SCHEDULE_LEAD_TIME_PARAM)
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _attach_timeline(step_params: list[dict[str, object]], design_input: DesignInput) -> None:
    """Serialized single-job timeline in plan order, exact integer arithmetic."""
    end = 0
    for params, declared in zip(step_params, design_input.declared_operations, strict=True):
        duration = _declared_duration(declared)
        assert isinstance(duration, int)
        start = end
        end = start + duration
        params[DURATION_PARAM] = duration
        params[SCHEDULE_START_PARAM] = start
        params[SCHEDULE_END_PARAM] = end
    step_params[-1][SCHEDULE_LEAD_TIME_PARAM] = end


def _summary(design_input: DesignInput) -> str:
    return (
        f"Manufacture {design_input.quantity}x from {design_input.material} "
        f"({design_input.stock_form.value})"
    )


def build_task(design_input: DesignInput) -> ManufacturingTask:
    di_ref = Ref(
        id=design_input.design_input_id,
        content_hash=h.content_hash(h.design_input_identity(design_input)),
    )
    task = ManufacturingTask(
        schema_version=SCHEMA_VERSION,
        task_id="",
        product_intent=ProductIntent(summary=_summary(design_input)),
        design_input_ref=di_ref,
    )
    task.task_id = h.derive_uuid(h.content_hash(h.task_identity(task)))
    validate("manufacturing_task", h.to_contract_dict(task))
    return task


def plan(
    design_input: DesignInput,
    capability_model: ProcessCapabilityModel,
    *,
    produced_at: str | None = None,
) -> tuple[ManufacturingTask, ProductionPlan]:
    produced_at = produced_at or now_rfc3339()
    task = build_task(design_input)

    di_ref = task.design_input_ref
    task_ref = Ref(id=task.task_id, content_hash=h.content_hash(h.task_identity(task)))

    # RM8 (C3): carry the requested tolerance to the oracle through the open step params — ONLY
    # when the model carries tolerance data and the request states a tolerance. Never on
    # default_model() (empty tolerance map), so default-path plans stay byte-identical to RM1-RM5.
    requested_tolerance = (
        design_input.tolerances.general_tolerance_mm
        if capability_model.capability_tolerance_mm and design_input.tolerances is not None
        else None
    )
    steps: list[ProcessStep] = []
    step_params: list[dict[str, object]] = []
    for i, declared in enumerate(design_input.declared_operations):
        capability = capability_for_op(capability_model, declared.op)
        params: dict[str, object] = {"source_op_index": i}
        step_params.append(params)
        tolerance_bearing = min_tolerance_for_capability(capability_model, capability) is not None
        if requested_tolerance is not None and tolerance_bearing:
            params[REQUIRED_TOLERANCE_PARAM] = requested_tolerance
        # RM9: record availability ONLY on a step it materially affects (its selected resource is
        # unavailable -> rerouted or unassignable), naming just that capability's unavailable
        # providers.
        if availability_affects_capability(capability_model, capability):
            params[UNAVAILABLE_RESOURCES_PARAM] = [
                r for r in providers_for_capability(capability_model, capability)
                if r in capability_model.unavailable_resources
            ]
        steps.append(
            ProcessStep(
                index=i,
                op=declared.op,
                required_capability=capability,
                inputs=[design_input.material],
                provenance_ref=di_ref,
                params=params,
            )
        )
    assignments: list[ResourceAssignment] = []
    for step in steps:
        # RM9: the first AVAILABLE provider in the deterministic order. With no declared
        # unavailability this is exactly RM1's selection; an unavailable selected resource reroutes
        # to the next available provider, or leaves the step unassigned when none is available.
        resource_id = available_resource_for_capability(capability_model, step.required_capability)
        if resource_id is not None:
            assignments.append(
                ResourceAssignment(
                    step_index=step.index,
                    resource_id=resource_id,
                    capability_id=step.required_capability,
                )
            )

    # RM10: a timeline only when timing was requested and every prerequisite holds; never partial.
    assigned = {a.step_index for a in assignments}
    timeline_derived = (
        timing_requested(design_input) and not _timeline_issues(design_input, assigned))
    if timeline_derived:
        _attach_timeline(step_params, design_input)

    # The planning rule version records which rule actually introduced data into this plan.
    tolerance_introduced = any(REQUIRED_TOLERANCE_PARAM in (s.params or {}) for s in steps)
    availability_introduced = any(UNAVAILABLE_RESOURCES_PARAM in (s.params or {}) for s in steps)
    if timeline_derived:
        rule_version = RULE_VERSION_TIMELINE
    elif availability_introduced:
        rule_version = RULE_VERSION_AVAILABILITY
    else:
        rule_version = RULE_VERSION_TOLERANCE if tolerance_introduced else RULE_VERSION

    production_plan = ProductionPlan(
        schema_version=SCHEMA_VERSION,
        plan_id="",
        task_ref=task_ref,
        steps=steps,
        resource_assignments=assignments,
        capability_model_version=capability_model.version,
        content_hash="",
        provenance=make_provenance(
            source_refs=[di_ref],
            rule_id="planner.deterministic",
            rule_version=rule_version,
            produced_at=produced_at,
            capability_model_version=capability_model.version,
            component="manufacturing-planner",
            component_version="1.0.0",
        ),
    )
    plan_hash = h.content_hash(h.plan_identity(production_plan))
    production_plan.content_hash = plan_hash
    production_plan.plan_id = h.derive_uuid(plan_hash)
    validate("production_plan", h.to_contract_dict(production_plan))
    return task, production_plan
