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
"""

from __future__ import annotations

import dataclasses
from collections.abc import Sequence
from dataclasses import dataclass

from mini_prometheus.manufacturing_constraints.oracle import DURATION_PARAM
from mini_prometheus.manufacturing_scheduling.lower_bound import lower_bound
from mini_prometheus.manufacturing_scheduling.model import (
    MODEL_ASSUMPTIONS,
    OPTIMIZATION_STATUS,
    SCHEDULING_RULE,
    SCHEDULING_RULE_VERSION,
    BoundStatus,
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


def earliest_start_v1(
    jobs: Sequence[SchedulingJob], capability_model_version: str
) -> MultiJobSchedule:
    """Schedule a non-empty set of schedulable jobs with unique request_ids (module rule)."""
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
    gap = makespan - bound.lower_bound_min
    ordered_jobs = sorted(jobs, key=lambda job: job.request_id)
    schedule = MultiJobSchedule(
        scheduling_rule=SCHEDULING_RULE,
        scheduling_rule_version=SCHEDULING_RULE_VERSION,
        optimization_status=OPTIMIZATION_STATUS,
        model_assumptions=MODEL_ASSUMPTIONS,
        capability_model_version=capability_model_version,
        schedule_input_identity=schedule_input_identity(
            SCHEDULING_RULE,
            SCHEDULING_RULE_VERSION,
            capability_model_version,
            [(job.request_id, job.plan.content_hash) for job in jobs],
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
    )
    return dataclasses.replace(schedule, schedule_digest=schedule_digest(schedule))
