"""RM11 lower-bound certificate (NOT an optimizer).

Under the RM11 model assumptions, every feasible schedule of a job set has

    makespan >= LB = max(longest job total duration, busiest machine total assigned duration)

because a job's operations run one after another (step order, non-preemptive) and a machine runs
at most one operation at a time. Hence ``makespan == LB`` proves the schedule optimal under the
RM11 model; when ``makespan > LB`` nothing is claimed beyond the gap ``makespan - LB`` (the bound
need not be attainable). Pure arithmetic on the RM10 durations and RM9 machine assignments carried
by each job's plan.

RM12 (ADR-0015) keeps that bound (still valid: downtime can only delay operations) and adds a
tighter diagnostic one under relevant downtime. For machine m with total assigned work W_m and
canonical downtime, T_avail(W_m) is the earliest T >= 0 with T - (downtime inside [0, T)) >= W_m:
the machine cannot finish its work sooner even if operations could be split around downtime (a
preemptive relaxation). LB_RM12 = max(LB_RM11, max_m T_avail(W_m)) is therefore still a lower
bound — never an optimum, never a distance from an optimum. Exact integer arithmetic.
"""

from __future__ import annotations

from collections.abc import Sequence

from mini_prometheus.manufacturing_constraints.oracle import DURATION_PARAM
from mini_prometheus.manufacturing_scheduling.model import (
    Downtime,
    DowntimeInterval,
    LowerBound,
    SchedulingJob,
)


def lower_bound(jobs: Sequence[SchedulingJob]) -> LowerBound:
    """The certificate for a non-empty set of schedulable jobs; binding terms in sorted order."""
    job_totals: dict[str, int] = {}
    machine_loads: dict[str, int] = {}
    for job in jobs:
        machine = {a.step_index: a.resource_id for a in job.plan.resource_assignments}
        total = 0
        for step in job.plan.steps:
            duration = (step.params or {})[DURATION_PARAM]
            total += duration
            machine_loads[machine[step.index]] = (
                machine_loads.get(machine[step.index], 0) + duration
            )
        job_totals[job.request_id] = total
    value = max(max(job_totals.values()), max(machine_loads.values()))
    return LowerBound(
        lower_bound_min=value,
        binding_request_ids=tuple(sorted(r for r, total in job_totals.items() if total == value)),
        binding_resource_ids=tuple(sorted(m for m, load in machine_loads.items() if load == value)),
    )


def available_by(work: int, downtime: Sequence[DowntimeInterval]) -> int:
    """T_avail(work) over canonical downtime (sorted, disjoint, non-touching intervals)."""
    t, remaining = 0, work
    for interval in downtime:
        capacity = interval.start_min - t
        if remaining <= capacity:
            return t + remaining
        remaining -= capacity
        t = interval.end_min
    return t + remaining


def window_aware_lower_bound(jobs: Sequence[SchedulingJob], downtime: Downtime) -> LowerBound:
    """LB_RM12 for a non-empty set of schedulable jobs; binding machines (T_avail == LB_RM12),
    sorted. ``binding_request_ids`` is always empty: the job term is in the retained RM11 bound."""
    loads: dict[str, int] = {}
    for job in jobs:
        machine = {a.step_index: a.resource_id for a in job.plan.resource_assignments}
        for step in job.plan.steps:
            resource_id = machine[step.index]
            loads[resource_id] = loads.get(resource_id, 0) + (step.params or {})[DURATION_PARAM]
    blocked = dict(downtime)
    ready = {m: available_by(work, blocked.get(m, ())) for m, work in loads.items()}
    value = max(lower_bound(jobs).lower_bound_min, max(ready.values()))
    return LowerBound(
        lower_bound_min=value,
        binding_request_ids=(),
        binding_resource_ids=tuple(sorted(m for m, t in ready.items() if t == value)),
    )
