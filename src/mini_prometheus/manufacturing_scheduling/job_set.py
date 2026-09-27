"""RM11 job-set scheduling: prerequisites, all-or-nothing refusals, the check-before-return gate.

``schedule_job_set(job_inputs, capability_model)`` plans and verifies every job itself, with the
unchanged RM1-RM10 planner and oracle, under ONE capability model (including its RM9 availability
snapshot), so every job is aligned to the same shop state by construction. A job is schedulable
iff its verdict is MANUFACTURABLE, every step has an assigned machine, and its plan carries a
valid RM10 timeline. The run is all-or-nothing: if the set is empty, a request_id repeats, or any
job fails a prerequisite, the outcome is NOT_SCHEDULED with every applicable refusal (sorted by
request_id, then reason) and no schedule at all. Otherwise ``earliest_start_v1`` builds the
schedule and the independent checker must find no issue, or ``ScheduleIntegrityError`` is
raised — a schedule that fails the checker is never returned.

Pure and read-only (Director ruling D5): nothing is persisted (no episode, schedule, memory or
state), nothing is executed or dispatched; the result depends only on the inputs (never on their
order, the clock or randomness — the planner's provenance timestamp is in no identity).
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence

from mini_prometheus._contracts import (
    DesignInput,
    ManufacturabilityVerdictStatus,
    ProductionPlan,
    Verdict,
)
from mini_prometheus.manufacturing_constraints.capability_model import ProcessCapabilityModel
from mini_prometheus.manufacturing_constraints.oracle import ManufacturabilityOracle
from mini_prometheus.manufacturing_planning import planner
from mini_prometheus.manufacturing_scheduling.checker import schedule_issues
from mini_prometheus.manufacturing_scheduling.earliest_start import earliest_start_v1
from mini_prometheus.manufacturing_scheduling.model import (
    JobInput,
    Refusal,
    RefusalReason,
    ScheduleIntegrityError,
    ScheduleOutcome,
    ScheduleStatus,
    SchedulingJob,
)

MANUFACTURABLE = ManufacturabilityVerdictStatus.MANUFACTURABLE.value
_REASON_ORDER = {reason: position for position, reason in enumerate(RefusalReason)}


def job_prerequisite_refusals(
    request_id: str, design_input: DesignInput, plan: ProductionPlan, verdict: Verdict
) -> list[Refusal]:
    """Every scheduling prerequisite this job fails (empty = schedulable); each stands alone."""
    refusals: list[Refusal] = []
    if verdict.status != MANUFACTURABLE:
        found = f"{verdict.status} [{', '.join(verdict.reason_codes)}]"
        refusals.append(
            Refusal(
                RefusalReason.JOB_NOT_MANUFACTURABLE,
                request_id,
                found + (f" ({verdict.detail})" if verdict.detail else ""),
            )
        )
    assigned = {a.step_index for a in plan.resource_assignments}
    unassigned = [
        f"step {step.index} ({step.op.value})" for step in plan.steps if step.index not in assigned
    ]
    if unassigned:
        refusals.append(
            Refusal(
                RefusalReason.JOB_OPERATION_UNASSIGNED,
                request_id,
                "no machine assigned: " + ", ".join(unassigned),
            )
        )
    if planner.lead_time_min(plan) is None:
        issues = planner.timeline_issues(design_input, plan) or [
            "no operation declares duration_min (RM10 timing not requested)"
        ]
        refusals.append(Refusal(RefusalReason.JOB_TIMELINE_MISSING, request_id, "; ".join(issues)))
    return refusals


def _refusal_key(refusal: Refusal) -> tuple[str, int, str]:
    return (refusal.request_id or "", _REASON_ORDER[refusal.reason], refusal.detail)


def schedule_job_set(
    job_inputs: Sequence[JobInput],
    capability_model: ProcessCapabilityModel,
    *,
    produced_at: str | None = None,
) -> ScheduleOutcome:
    if not job_inputs:
        refusal = Refusal(RefusalReason.EMPTY_JOB_SET, None, "no job was given")
        return ScheduleOutcome(ScheduleStatus.NOT_SCHEDULED, None, (refusal,))
    refusals: set[Refusal] = set()
    counts = Counter(job.request_id for job in job_inputs)
    for request_id, count in counts.items():
        if count > 1:
            refusals.add(
                Refusal(
                    RefusalReason.DUPLICATE_REQUEST_ID,
                    request_id,
                    f"request_id appears {count} times; each job must be unique",
                )
            )
    oracle = ManufacturabilityOracle()
    jobs: list[SchedulingJob] = []
    for job_input in job_inputs:
        task, plan = planner.plan(job_input.design_input, capability_model, produced_at=produced_at)
        verdict = oracle.verify(plan, capability_model)
        failed = job_prerequisite_refusals(
            job_input.request_id, job_input.design_input, plan, verdict
        )
        refusals.update(failed)
        if not failed:
            jobs.append(SchedulingJob(job_input.request_id, task.task_id, plan))
    if refusals:
        return ScheduleOutcome(
            ScheduleStatus.NOT_SCHEDULED, None, tuple(sorted(refusals, key=_refusal_key))
        )

    schedule = earliest_start_v1(jobs, capability_model.version)
    issues = schedule_issues(schedule, jobs, capability_model.version)
    if issues:
        raise ScheduleIntegrityError("; ".join(f"{issue.code}: {issue.detail}" for issue in issues))
    return ScheduleOutcome(ScheduleStatus.SCHEDULED, schedule, ())
