"""RM11 baseline generator ``earliest_start_v1`` — deterministic, NOT an optimizer.

Exact rule (frozen; specs/milestones/RM11-multi-job-schedule.md §5):

    state:  per job, its next unscheduled operation (first step) and predecessor completion (0);
            per machine, its available time (0).
    repeat until every operation is placed:
      1. take the next unscheduled operation (plan step order) of each unfinished job;
      2. earliest feasible start = max(job predecessor completion,
                                       assigned machine available time);
      3. select the candidate with the smallest earliest feasible start;
      4. break exact ties by request_id (ascending, code-point order), then step_index;
      5. place it: start = earliest feasible start, end = start + duration_min;
      6. set the job's predecessor completion and the machine's available time to end;
      7. repeat.

The decision key ``(start, request_id, step_index)`` is total (request_ids are unique in a job
set), so the schedule never depends on the order in which jobs are passed, on set/dict iteration,
randomness, the clock or threads. Operations are placed in non-decreasing start order, so
appending at a machine's available time never leaves a gap a later operation could have used;
the placement order is the canonical ``(start, request_id, step_index)`` order. A one-job set
reproduces the RM10 serial timeline exactly. Every generated schedule must pass the independent
checker before it is returned (``job_set``).

RM12 ``earliest_start_v1_downtime`` (ADR-0015), recorded only when relevant downtime exists (the
no-downtime path is exactly ``earliest_start_v1``): step 2 becomes the earliest S >= max(job
predecessor completion, machine available time) such that [S, S + duration_min) intersects no
canonical downtime interval of the ASSIGNED machine — whenever it would, S := that downtime's end
(half-open: ending exactly at a downtime start, or starting exactly at its end, is allowed). The
machine is never changed (no rerouting), placement stays append-only (the machine's available time
advances to the operation's end), and selection uses that downtime-adjusted start. Because every
downtime interval is finite, every operation eventually fits. Placements still come in
non-decreasing start order, so no idle gap before a placed operation can later be used by any
operation: idle time created by downtime is a property of this rule, not a missed insertion.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Sequence
from dataclasses import dataclass

from mini_prometheus.manufacturing_constraints.oracle import DURATION_PARAM
from mini_prometheus.manufacturing_scheduling.lower_bound import (
    lower_bound,
    window_aware_lower_bound,
)
from mini_prometheus.manufacturing_scheduling.model import (
    MODEL_ASSUMPTIONS,
    MODEL_ASSUMPTIONS_DOWNTIME,
    OPTIMIZATION_STATUS,
    SCHEDULING_RULE,
    SCHEDULING_RULE_DOWNTIME,
    SCHEDULING_RULE_VERSION,
    BoundStatus,
    Downtime,
    DowntimeInterval,
    JobCompletion,
    MultiJobSchedule,
    ScheduledOperation,
    SchedulingJob,
    schedule_digest,
    schedule_input_identity,
)


@dataclass(frozen=True)
class _Operation:
    step_index: int
    op: str
    resource_id: str
    duration_min: int


@dataclass(frozen=True)
class _Candidate:
    start_min: int
    request_id: str
    step_index: int
    task_id: str
    operation: _Operation


def _decision_key(candidate: _Candidate) -> tuple[int, str, int]:
    return (candidate.start_min, candidate.request_id, candidate.step_index)


def _operations(job: SchedulingJob) -> list[_Operation]:
    """The job's operations in plan step order: RM9-assigned machine, RM10 duration."""
    machine = {a.step_index: a.resource_id for a in job.plan.resource_assignments}
    operations = [
        _Operation(
            step.index, step.op.value, machine[step.index], (step.params or {})[DURATION_PARAM]
        )
        for step in job.plan.steps
    ]
    return operations


def _earliest_fit(start: int, duration: int, downtime: Sequence[DowntimeInterval]) -> int:
    """The earliest S >= start with [S, S + duration) disjoint from every canonical downtime
    interval (sorted, disjoint, non-touching) of the machine."""
    for interval in downtime:
        if start + duration <= interval.start_min:
            break
        if start < interval.end_min:
            start = interval.end_min
    return start


def earliest_start_v1(
    jobs: Sequence[SchedulingJob], capability_model_version: str, downtime: Downtime = ()
) -> MultiJobSchedule:
    """Schedule a non-empty set of schedulable jobs with unique request_ids (module rule).
    ``downtime`` is the relevant canonical downtime (RM12); empty means exactly RM11."""
    blocked = dict(downtime)
    operations = {job.request_id: _operations(job) for job in jobs}
    next_step = {job.request_id: 0 for job in jobs}
    job_ready = {job.request_id: 0 for job in jobs}
    machine_free: dict[str, int] = {}
    placed: list[ScheduledOperation] = []
    remaining = sum(len(ops) for ops in operations.values())
    while remaining:
        candidates: list[_Candidate] = []
        for job in jobs:
            ops = operations[job.request_id]
            if next_step[job.request_id] >= len(ops):
                continue
            operation = ops[next_step[job.request_id]]
            start = max(job_ready[job.request_id], machine_free.get(operation.resource_id, 0))
            machine_downtime = blocked.get(operation.resource_id, ())
            start = _earliest_fit(start, operation.duration_min, machine_downtime)
            candidates.append(
                _Candidate(start, job.request_id, operation.step_index, job.task_id, operation)
            )
        chosen = min(candidates, key=_decision_key)
        start = chosen.start_min
        end = start + chosen.operation.duration_min
        placed.append(
            ScheduledOperation(
                request_id=chosen.request_id,
                task_id=chosen.task_id,
                step_index=chosen.operation.step_index,
                op=chosen.operation.op,
                resource_id=chosen.operation.resource_id,
                duration_min=chosen.operation.duration_min,
                start_min=start,
                end_min=end,
            )
        )
        job_ready[chosen.request_id] = end
        machine_free[chosen.operation.resource_id] = end
        next_step[chosen.request_id] += 1
        remaining -= 1

    makespan = max(op.end_min for op in placed)
    bound = lower_bound(jobs)
    # RM12: with relevant downtime the gap is measured to the tighter window-aware bound.
    window = window_aware_lower_bound(jobs, downtime) if downtime else None
    reference = window.lower_bound_min if window else bound.lower_bound_min
    gap = makespan - reference
    rule = SCHEDULING_RULE_DOWNTIME if downtime else SCHEDULING_RULE
    ordered_jobs = sorted(jobs, key=lambda job: job.request_id)
    schedule = MultiJobSchedule(
        scheduling_rule=rule,
        scheduling_rule_version=SCHEDULING_RULE_VERSION,
        optimization_status=OPTIMIZATION_STATUS,
        model_assumptions=MODEL_ASSUMPTIONS_DOWNTIME if downtime else MODEL_ASSUMPTIONS,
        capability_model_version=capability_model_version,
        schedule_input_identity=schedule_input_identity(
            rule,
            SCHEDULING_RULE_VERSION,
            capability_model_version,
            [(job.request_id, job.plan.content_hash) for job in jobs],
            downtime,
        ),
        jobs=tuple(
            JobCompletion(
                job.request_id, job.task_id, job.plan.content_hash, job_ready[job.request_id]
            )
            for job in ordered_jobs
        ),
        operations=tuple(
            sorted(placed, key=lambda op: (op.start_min, op.request_id, op.step_index))
        ),
        makespan_min=makespan,
        lower_bound_min=bound.lower_bound_min,
        lower_bound_binding_request_ids=bound.binding_request_ids,
        lower_bound_binding_resource_ids=bound.binding_resource_ids,
        gap_to_lower_bound_min=gap,
        bound_status=(
            BoundStatus.PROVABLY_OPTIMAL if gap == 0 else BoundStatus.GAP_ABOVE_LOWER_BOUND
        ),
        schedule_digest="",
        downtime=tuple(downtime),
        window_aware_lower_bound_min=window.lower_bound_min if window else None,
        window_aware_lower_bound_binding_resource_ids=window.binding_resource_ids if window else (),
    )
    return dataclasses.replace(schedule, schedule_digest=schedule_digest(schedule))
