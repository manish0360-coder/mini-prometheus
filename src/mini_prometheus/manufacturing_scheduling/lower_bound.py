"""RM11 lower-bound certificate (NOT an optimizer).

Under the RM11 model assumptions, every feasible schedule of a job set has

    makespan >= LB = max(longest job total duration, busiest machine total assigned duration)

because a job's operations run one after another (step order, non-preemptive) and a machine runs
at most one operation at a time. Hence ``makespan == LB`` proves the schedule optimal under the
RM11 model; when ``makespan > LB`` nothing is claimed beyond the gap ``makespan - LB`` (the bound
need not be attainable). Pure arithmetic on the RM10 durations and RM9 machine assignments carried
by each job's plan.
"""

from __future__ import annotations

from collections.abc import Sequence

from mini_prometheus.manufacturing_constraints.oracle import DURATION_PARAM
from mini_prometheus.manufacturing_scheduling.model import LowerBound, SchedulingJob


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
