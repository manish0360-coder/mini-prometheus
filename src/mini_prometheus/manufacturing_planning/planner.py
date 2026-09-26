"""RM1 order 3 & 5: the deterministic planner and ProductionPlan generation.

Maps a DesignInput's ordered declared operations 1:1 to ProcessSteps (index 0..n-1), assigns each
a required capability and a resource from the capability model, and produces a content-hashed,
provenance-complete ProductionPlan. Fully deterministic (spec §9): same DesignInput + same model
version -> same plan and same content_hash. A model-based planner is a later seam (spec §9).

RM8 (C3): under a capability model that carries tolerance data (``constrained_model()``), a
request's ``general_tolerance_mm`` is carried on each tolerance-bearing step as
``params["required_tolerance_mm"]`` for the oracle, and the planning rule version becomes 1.1.0.
With ``default_model()`` nothing changes.
"""
from __future__ import annotations

from mini_prometheus import _hashing as h
from mini_prometheus._contracts import (
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
    capability_for_op,
    min_tolerance_for_capability,
    resource_for_capability,
)
from mini_prometheus.manufacturing_constraints.oracle import REQUIRED_TOLERANCE_PARAM

SCHEMA_VERSION = "1.0.0"
RULE_VERSION = "1.0.0"              # the RM1 planning rule (the default path)
RULE_VERSION_TOLERANCE = "1.1.0"    # RM1 rule + RM8 tolerance carriage (only when data is added)


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
    for i, declared in enumerate(design_input.declared_operations):
        capability = capability_for_op(capability_model, declared.op)
        params: dict[str, object] = {"source_op_index": i}
        tolerance_bearing = min_tolerance_for_capability(capability_model, capability) is not None
        if requested_tolerance is not None and tolerance_bearing:
            params[REQUIRED_TOLERANCE_PARAM] = requested_tolerance
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
    # The planning rule version records whether the RM8 tolerance rule actually introduced data.
    tolerance_introduced = any(REQUIRED_TOLERANCE_PARAM in (s.params or {}) for s in steps)
    rule_version = RULE_VERSION_TOLERANCE if tolerance_introduced else RULE_VERSION

    assignments: list[ResourceAssignment] = []
    for step in steps:
        resource_id = resource_for_capability(capability_model, step.required_capability)
        if resource_id is not None:
            assignments.append(
                ResourceAssignment(
                    step_index=step.index,
                    resource_id=resource_id,
                    capability_id=step.required_capability,
                )
            )

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
