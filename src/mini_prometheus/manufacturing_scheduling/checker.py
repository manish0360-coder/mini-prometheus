"""RM11 independent schedule checker — built before the generator is trusted.

``schedule_issues(schedule, jobs, capability_model_version)`` re-derives everything it checks from
the jobs' plans alone (their step order, RM9 machine assignments and RM10 durations). It never
imports the generator (``earliest_start``) or the bound calculator (``lower_bound``) — an
import-linter contract enforces this — so a defect in either cannot hide itself. It is
generator-agnostic: any schedule claiming to satisfy the RM11 model is checked the same way. An
empty list means the schedule is valid. It proves:

- every scheduled operation belongs to exactly one input job, and every required operation is
  scheduled exactly once (UNKNOWN / DUPLICATE / MISSING_OPERATION);
- all times are integer minutes, start >= 0 (INVALID_TIME);
- the machine is the plan's fixed assignment (MACHINE_MISMATCH); duration equals the RM10
  duration (DURATION_MISMATCH); end == start + duration exactly (ARITHMETIC_MISMATCH);
- operation order is preserved: every step starts no earlier than its predecessor ends
  (JOB_ORDER_VIOLATION);
- no two operations overlap on one machine, intervals half-open ``[start, end)``
  (MACHINE_OVERLAP);
- operations are listed in the canonical ``(start, request_id, step_index)`` order
  (NON_CANONICAL_ORDER);
- job completions, makespan (= max operation end), lower bound, gap and bound status are exact
  (COMPLETION / MAKESPAN / LOWER_BOUND / GAP / BOUND_STATUS_MISMATCH);
- the metadata, job set, input identity and digest match (METADATA / JOB_SET / DIGEST_MISMATCH).
"""

from __future__ import annotations

import itertools
from collections.abc import Sequence
from typing import TypeGuard

from mini_prometheus.manufacturing_constraints.oracle import DURATION_PARAM
from mini_prometheus.manufacturing_scheduling.model import (
    MODEL_ASSUMPTIONS,
    OPTIMIZATION_STATUS,
    BoundStatus,
    IssueCode,
    MultiJobSchedule,
    ScheduledOperation,
    ScheduleIssue,
    SchedulingJob,
    schedule_digest,
    schedule_input_identity,
)

_Key = tuple[str, int]


def _minutes(value: object) -> TypeGuard[int]:
    return isinstance(value, int) and not isinstance(value, bool)


def _label(request_id: str, step_index: int) -> str:
    return f"{request_id} step {step_index}"


def _interval(op: ScheduledOperation) -> str:
    return f"{_label(op.request_id, op.step_index)} [{op.start_min}, {op.end_min})"


def schedule_issues(
    schedule: MultiJobSchedule,
    jobs: Sequence[SchedulingJob],
    capability_model_version: str,
) -> list[ScheduleIssue]:
    issues: list[ScheduleIssue] = []

    def add(code: IssueCode, detail: str) -> None:
        issues.append(ScheduleIssue(code, detail))

    # --- metadata and job set ---------------------------------------------------------------
    if schedule.optimization_status != OPTIMIZATION_STATUS:
        add(IssueCode.METADATA_MISMATCH, f"optimization_status {schedule.optimization_status!r}")
    if tuple(schedule.model_assumptions) != MODEL_ASSUMPTIONS:
        add(IssueCode.METADATA_MISMATCH, "model_assumptions differ from the RM11 model")
    if schedule.capability_model_version != capability_model_version:
        add(IssueCode.METADATA_MISMATCH, f"capability model {schedule.capability_model_version!r}")
    for job in jobs:
        if job.plan.capability_model_version != capability_model_version:
            add(
                IssueCode.METADATA_MISMATCH,
                f"{job.request_id}: planned under model {job.plan.capability_model_version}",
            )
    expected_identity = schedule_input_identity(
        schedule.scheduling_rule,
        schedule.scheduling_rule_version,
        capability_model_version,
        [(job.request_id, job.plan.content_hash) for job in jobs],
    )
    if schedule.schedule_input_identity != expected_identity:
        add(IssueCode.METADATA_MISMATCH, "schedule_input_identity does not match the inputs")
    expected_jobs = sorted((job.request_id, job.task_id, job.plan.content_hash) for job in jobs)
    recorded_jobs = [(c.request_id, c.task_id, c.plan_content_hash) for c in schedule.jobs]
    if recorded_jobs != expected_jobs:
        add(IssueCode.JOB_SET_MISMATCH, "jobs are not exactly the input jobs in request_id order")

    # --- what the plans require (independent of any generator) ------------------------------
    required: dict[_Key, tuple[str, str, str | None, object]] = {}  # task, op, machine, duration
    step_order: dict[str, list[int]] = {}
    job_totals: dict[str, int] = {}
    machine_loads: dict[str, int] = {}
    for job in sorted(jobs, key=lambda j: j.request_id):
        machine = {a.step_index: a.resource_id for a in job.plan.resource_assignments}
        step_order[job.request_id] = [step.index for step in job.plan.steps]
        for step in job.plan.steps:
            duration = (step.params or {}).get(DURATION_PARAM)
            required[(job.request_id, step.index)] = (
                job.task_id,
                step.op.value,
                machine.get(step.index),
                duration,
            )
            if _minutes(duration) and step.index in machine:
                assigned = machine[step.index]
                job_totals[job.request_id] = job_totals.get(job.request_id, 0) + duration
                machine_loads[assigned] = machine_loads.get(assigned, 0) + duration

    # --- each scheduled operation -----------------------------------------------------------
    seen: set[_Key] = set()
    valid: dict[_Key, ScheduledOperation] = {}
    for op in schedule.operations:
        key = (op.request_id, op.step_index)
        label = _label(op.request_id, op.step_index)
        if key not in required:
            add(IssueCode.UNKNOWN_OPERATION, f"{label}: not an operation of any input job")
            continue
        task_id, op_code, resource_id, duration = required[key]
        if op.task_id != task_id or op.op != op_code:
            add(IssueCode.UNKNOWN_OPERATION, f"{label}: task/operation differs from the input job")
            continue
        if key in seen:
            add(IssueCode.DUPLICATE_OPERATION, f"{label}: scheduled more than once")
            continue
        seen.add(key)
        times = (op.start_min, op.end_min, op.duration_min)
        if not all(_minutes(t) for t in times) or op.start_min < 0:
            add(IssueCode.INVALID_TIME, f"{label}: times must be integer minutes, start >= 0")
            continue
        valid[key] = op
        if op.resource_id != resource_id:
            add(IssueCode.MACHINE_MISMATCH, f"{label}: on {op.resource_id}, assigned {resource_id}")
        if op.duration_min != duration:
            add(IssueCode.DURATION_MISMATCH, f"{label}: {op.duration_min} min, RM10 {duration}")
        if op.end_min != op.start_min + op.duration_min:
            add(IssueCode.ARITHMETIC_MISMATCH, f"{label}: end != start + duration")
    for key in sorted(required):
        if key not in seen:
            add(IssueCode.MISSING_OPERATION, f"{_label(*key)}: not scheduled")

    # --- operation order within each job ------------------------------------------------------
    for request_id in sorted(step_order):
        steps = step_order[request_id]
        for before, after in itertools.pairwise(steps):
            first, second = valid.get((request_id, before)), valid.get((request_id, after))
            if first is not None and second is not None and second.start_min < first.end_min:
                add(
                    IssueCode.JOB_ORDER_VIOLATION,
                    f"{_interval(second)} starts before {_interval(first)} ends",
                )

    # --- machine no-overlap, half-open intervals [start, end) ---------------------------------
    by_machine: dict[str, list[ScheduledOperation]] = {}
    for key in sorted(valid):
        by_machine.setdefault(valid[key].resource_id, []).append(valid[key])
    for resource_id in sorted(by_machine):
        holder: ScheduledOperation | None = None  # the operation with the latest end so far
        for op in sorted(
            by_machine[resource_id],
            key=lambda o: (o.start_min, o.end_min, o.request_id, o.step_index),
        ):
            if holder is not None and op.start_min < holder.end_min:
                add(
                    IssueCode.MACHINE_OVERLAP,
                    f"{resource_id}: {_interval(op)} overlaps {_interval(holder)}",
                )
            if holder is None or op.end_min > holder.end_min:
                holder = op

    # --- canonical ordering -------------------------------------------------------------------
    if all(
        _minutes(op.start_min) and _minutes(op.step_index) and isinstance(op.request_id, str)
        for op in schedule.operations
    ):
        order = [(op.start_min, op.request_id, op.step_index) for op in schedule.operations]
        if order != sorted(order):
            add(IssueCode.NON_CANONICAL_ORDER, "operations not in (start, request_id, step) order")

    # --- completions, makespan, lower bound, gap, bound status --------------------------------
    for completion in schedule.jobs:
        job_steps = step_order.get(completion.request_id)
        final = valid.get((completion.request_id, job_steps[-1])) if job_steps else None
        if final is not None and completion.completion_min != final.end_min:
            add(
                IssueCode.COMPLETION_MISMATCH,
                f"{completion.request_id}: completion {completion.completion_min}, "
                f"final step ends at {final.end_min}",
            )
    makespan = schedule.makespan_min
    recorded_bound = schedule.lower_bound_min
    gap = schedule.gap_to_lower_bound_min
    if not (_minutes(makespan) and _minutes(recorded_bound) and _minutes(gap)):
        add(IssueCode.INVALID_TIME, "makespan, lower bound and gap must be integer minutes")
    else:
        latest_end = max((op.end_min for op in valid.values()), default=None)
        if latest_end is not None and makespan != latest_end:
            add(IssueCode.MAKESPAN_MISMATCH, f"makespan {makespan}, latest end {latest_end}")
        if job_totals and machine_loads:
            bound = max(max(job_totals.values()), max(machine_loads.values()))
            expected = (
                bound,
                tuple(sorted(r for r, total in job_totals.items() if total == bound)),
                tuple(sorted(m for m, load in machine_loads.items() if load == bound)),
            )
            recorded = (
                recorded_bound,
                tuple(schedule.lower_bound_binding_request_ids),
                tuple(schedule.lower_bound_binding_resource_ids),
            )
            if recorded != expected:
                add(IssueCode.LOWER_BOUND_MISMATCH, f"lower bound {recorded}, expected {expected}")
        if gap != makespan - recorded_bound:
            add(IssueCode.GAP_MISMATCH, f"gap {gap} != {makespan} - {recorded_bound}")
        expected_status = (
            BoundStatus.PROVABLY_OPTIMAL if gap == 0 else BoundStatus.GAP_ABOVE_LOWER_BOUND
        )
        if schedule.bound_status != expected_status:
            add(IssueCode.BOUND_STATUS_MISMATCH, f"{schedule.bound_status!r} with gap {gap}")

    # --- digest -------------------------------------------------------------------------------
    if schedule.schedule_digest != schedule_digest(schedule):
        add(IssueCode.DIGEST_MISMATCH, "schedule_digest does not match the artifact")
    return issues
