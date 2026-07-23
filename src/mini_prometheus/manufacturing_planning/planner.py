"""RM1 order 3 & 5: the deterministic planner and ProductionPlan generation.

Maps a DesignInput's ordered declared operations 1:1 to ProcessSteps (index 0..n-1), assigns each
a required capability and a resource from the capability model, and produces a content-hashed,
provenance-complete ProductionPlan. Fully deterministic (spec §9): same DesignInput + same model
version -> same plan and same content_hash. A model-based planner is a later seam (spec §9).
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
    resource_for_capability,
)

SCHEMA_VERSION = "1.0.0"


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

    steps: list[ProcessStep] = []
    for i, declared in enumerate(design_input.declared_operations):
        capability = capability_for_op(capability_model, declared.op)
        steps.append(
            ProcessStep(
                index=i,
                op=declared.op,
                required_capability=capability,
                inputs=[design_input.material],
                provenance_ref=di_ref,
                params={"source_op_index": i},
            )
        )

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
            rule_version="1.0.0",
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
