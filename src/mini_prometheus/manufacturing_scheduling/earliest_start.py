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

RM13 ``earliest_start_v1_most_work_remaining`` (ADR-0016) is an OPT-IN, separately named rule that
differs in step 4 only: among candidates with EXACTLY the same earliest feasible start, the job with
the most remaining processing work goes first (then request_id, then step_index). It can never
choose a later-starting candidate; downtime, machines and placement are exactly as above. It is
recorded as ``earliest_start_v1_most_work_remaining_downtime`` under relevant downtime.

RM14 (ADR-0017), for both rules, recorded with a ``_setup`` suffix only when relevant setup rules
exist (otherwise exactly the rules above): an operation whose predecessor on its machine in this run
belongs to ANOTHER job, on a machine with declared setup rules, needs a changeover of the declared
(machine, previous operation, operation) minutes, else the machine's declared default. There is no
changeover before a machine's first operation or between operations of the same job. Step 2 then
finds the earliest block start S >= max(job predecessor completion, machine available time) such
that the whole block [S, S + changeover + duration_min) avoids downtime; the changeover occupies
[S, S + changeover) and the operation starts exactly at its end (one uninterrupted block, never
started before the job's predecessor completes). Selection uses the block start S, so blocks are
still placed in non-decreasing start order, append-only on the fixed machine. RM13's remaining work
stays processing time only (no changeover). The changeover of every candidate is evaluated at each
decision (its block depends on it); if any evaluated cross-job transition on a machine with declared
rules has neither a transition rule nor a default, the run is refused
(``UnspecifiedSetupTransitionError``, all such transitions of that decision) — never assumed zero.
A possible transition the rule never evaluates is not required.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Sequence
from dataclasses import dataclass

from mini_prometheus.manufacturing_constraints.oracle import DURATION_PARAM
from mini_prometheus.manufacturing_scheduling.changeover import relevant_setup_rules
from mini_prometheus.manufacturing_scheduling.lower_bound import (
    lower_bound,
    window_aware_lower_bound,
)
from mini_prometheus.manufacturing_scheduling.model import (
    MODEL_ASSUMPTIONS,
    MODEL_ASSUMPTIONS_DOWNTIME,
    MODEL_ASSUMPTIONS_DOWNTIME_SETUP,
    MODEL_ASSUMPTIONS_SETUP,
    OPTIMIZATION_STATUS,
    SCHEDULING_RULE,
    SCHEDULING_RULE_DOWNTIME,
    SCHEDULING_RULE_DOWNTIME_SETUP,
    SCHEDULING_RULE_MOST_WORK_REMAINING,
    SCHEDULING_RULE_MOST_WORK_REMAINING_DOWNTIME,
    SCHEDULING_RULE_MOST_WORK_REMAINING_DOWNTIME_SETUP,
    SCHEDULING_RULE_MOST_WORK_REMAINING_SETUP,
    SCHEDULING_RULE_SETUP,
    SCHEDULING_RULE_VERSION,
    BoundStatus,
    Downtime,
    DowntimeInterval,
    JobCompletion,
    MultiJobSchedule,
    ScheduledOperation,
    ScheduledSetup,
    SchedulingJob,
    SetupMatch,
    SetupRules,
    UnspecifiedSetupTransitionError,
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
class _Setup:
    prev_request_id: str
    prev_op: str
    matched: SetupMatch
    duration_min: int


@dataclass(frozen=True)
class _Candidate:
    start_min: int  # RM14: the block start — the changeover's start when there is one
    request_id: str
    step_index: int
    task_id: str
    operation: _Operation
    priority: int = 0  # RM13: -(remaining processing work) for the opt-in rule; always 0 otherwise
    setup: _Setup | None = None  # RM14: the changeover before the operation, if any


def _decision_key(candidate: _Candidate) -> tuple[int, int, str, int]:
    """Earliest feasible start FIRST — a tie-break can never prefer a later-starting candidate —
    then the rule's priority (constant 0 for earliest_start_v1, so exactly the RM11 order), then
    request_id, then step_index."""
    return (candidate.start_min, candidate.priority, candidate.request_id, candidate.step_index)


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


_MachineRules = dict[str, tuple[dict[tuple[str, str], int], int | None]]


def _machine_rules(setup_rules: SetupRules) -> _MachineRules:
    """Per machine with declared rules: its transition minutes and its default (None if none)."""
    rules: _MachineRules = {}
    for rule in setup_rules:
        transitions, default = rules.get(rule.machine_id, ({}, None))
        if rule.prev_op is None or rule.curr_op is None:
            default = rule.duration_min
        else:
            transitions[(rule.prev_op, rule.curr_op)] = rule.duration_min
        rules[rule.machine_id] = (transitions, default)
    return rules


def _changeover(
    rules: _MachineRules,
    previous: tuple[str, str] | None,
    request_id: str,
    operation: _Operation,
) -> _Setup | None:
    """RM14: the declared changeover before ``operation`` given its machine's previous operation
    (request_id, op) in this run; None when the machine has no declared rule, when this is its first
    operation, or when the previous operation is of the same job."""
    machine_rules = rules.get(operation.resource_id)
    if machine_rules is None or previous is None:
        return None
    prev_request_id, prev_op = previous
    if prev_request_id == request_id:
        return None  # cross-job only: duration_min is the job's declared total operation time
    transitions, default = machine_rules
    minutes = transitions.get((prev_op, operation.op))
    if minutes is not None:
        return _Setup(prev_request_id, prev_op, SetupMatch.TRANSITION, minutes)
    if default is not None:
        return _Setup(prev_request_id, prev_op, SetupMatch.MACHINE_DEFAULT, default)
    raise UnspecifiedSetupTransitionError([(operation.resource_id, prev_op, operation.op)])


def earliest_start_v1(
    jobs: Sequence[SchedulingJob],
    capability_model_version: str,
    downtime: Downtime = (),
    setup_rules: SetupRules = (),
) -> MultiJobSchedule:
    """Schedule a non-empty set of schedulable jobs with unique request_ids (module rule).
    ``downtime`` is the relevant canonical downtime (RM12) and ``setup_rules`` the declared
    canonical setup rules (RM14; only the relevant ones are recorded); both empty means exactly
    RM11."""
    return _earliest_start(
        jobs, capability_model_version, downtime, setup_rules, most_work_remaining=False
    )


def earliest_start_v1_most_work_remaining(
    jobs: Sequence[SchedulingJob],
    capability_model_version: str,
    downtime: Downtime = (),
    setup_rules: SetupRules = (),
) -> MultiJobSchedule:
    """RM13 opt-in rule (ADR-0016): exactly earliest_start_v1 — same earliest feasible start
    (RM12 downtime fit included), same append-only placement, same machines — except that among
    candidates with EXACTLY the same earliest feasible start the job with the most remaining
    processing work goes first: remaining_work = the candidate's duration_min + the duration_min
    of every later unscheduled operation of that job (RM10 durations only: no downtime, waiting,
    idle, calendar or setup time). Further ties: request_id, then step_index."""
    return _earliest_start(
        jobs, capability_model_version, downtime, setup_rules, most_work_remaining=True
    )


def _earliest_start(
    jobs: Sequence[SchedulingJob],
    capability_model_version: str,
    downtime: Downtime,
    setup_rules: SetupRules,
    *,
    most_work_remaining: bool,
) -> MultiJobSchedule:
    blocked = dict(downtime)
    rules = _machine_rules(setup_rules)
    machine_last: dict[str, tuple[str, str]] = {}  # RM14: (request_id, op) last placed per machine
    setups: list[ScheduledSetup] = []
    operations = {job.request_id: _operations(job) for job in jobs}
    next_step = {job.request_id: 0 for job in jobs}
    job_ready = {job.request_id: 0 for job in jobs}
    machine_free: dict[str, int] = {}
    placed: list[ScheduledOperation] = []
    remaining = sum(len(ops) for ops in operations.values())
    while remaining:
        candidates: list[_Candidate] = []
        undeclared: list[tuple[str, str, str]] = []  # RM14: needed changeovers with no rule
        for job in jobs:
            ops = operations[job.request_id]
            if next_step[job.request_id] >= len(ops):
                continue
            operation = ops[next_step[job.request_id]]
            try:
                setup = _changeover(
                    rules, machine_last.get(operation.resource_id), job.request_id, operation
                )
            except UnspecifiedSetupTransitionError as missing:
                undeclared += missing.transitions
                continue
            setup_min = setup.duration_min if setup is not None else 0
            start = max(job_ready[job.request_id], machine_free.get(operation.resource_id, 0))
            machine_downtime = blocked.get(operation.resource_id, ())
            start = _earliest_fit(start, setup_min + operation.duration_min, machine_downtime)
            remaining_ops = ops[next_step[job.request_id] :]
            priority = -sum(o.duration_min for o in remaining_ops) if most_work_remaining else 0
            candidates.append(
                _Candidate(
                    start,
                    job.request_id,
                    operation.step_index,
                    job.task_id,
                    operation,
                    priority,
                    setup,
                )
            )
        if undeclared:
            raise UnspecifiedSetupTransitionError(undeclared)
        chosen = min(candidates, key=_decision_key)
        start = chosen.start_min
        if chosen.setup is not None:  # RM14: the changeover occupies the machine first
            setup_end = start + chosen.setup.duration_min
            setups.append(
                ScheduledSetup(
                    request_id=chosen.request_id,
                    step_index=chosen.operation.step_index,
                    resource_id=chosen.operation.resource_id,
                    prev_request_id=chosen.setup.prev_request_id,
                    prev_op=chosen.setup.prev_op,
                    curr_op=chosen.operation.op,
                    matched=chosen.setup.matched,
                    duration_min=chosen.setup.duration_min,
                    start_min=start,
                    end_min=setup_end,
                )
            )
            start = setup_end
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
        machine_last[chosen.operation.resource_id] = (chosen.request_id, chosen.operation.op)
        next_step[chosen.request_id] += 1
        remaining -= 1

    makespan = max(op.end_min for op in placed)
    bound = lower_bound(jobs)
    # RM12: with relevant downtime the gap is measured to the tighter window-aware bound.
    window = window_aware_lower_bound(jobs, downtime) if downtime else None
    reference = window.lower_bound_min if window else bound.lower_bound_min
    gap = makespan - reference
    recorded = relevant_setup_rules(setup_rules, jobs)  # RM14: only rules that can apply
    rule = {
        (False, False, False): SCHEDULING_RULE,
        (False, True, False): SCHEDULING_RULE_DOWNTIME,
        (True, False, False): SCHEDULING_RULE_MOST_WORK_REMAINING,
        (True, True, False): SCHEDULING_RULE_MOST_WORK_REMAINING_DOWNTIME,
        (False, False, True): SCHEDULING_RULE_SETUP,
        (False, True, True): SCHEDULING_RULE_DOWNTIME_SETUP,
        (True, False, True): SCHEDULING_RULE_MOST_WORK_REMAINING_SETUP,
        (True, True, True): SCHEDULING_RULE_MOST_WORK_REMAINING_DOWNTIME_SETUP,
    }[(most_work_remaining, bool(downtime), bool(recorded))]
    assumptions = {
        (False, False): MODEL_ASSUMPTIONS,
        (True, False): MODEL_ASSUMPTIONS_DOWNTIME,
        (False, True): MODEL_ASSUMPTIONS_SETUP,
        (True, True): MODEL_ASSUMPTIONS_DOWNTIME_SETUP,
    }[(bool(downtime), bool(recorded))]
    ordered_jobs = sorted(jobs, key=lambda job: job.request_id)
    schedule = MultiJobSchedule(
        scheduling_rule=rule,
        scheduling_rule_version=SCHEDULING_RULE_VERSION,
        optimization_status=OPTIMIZATION_STATUS,
        model_assumptions=assumptions,
        capability_model_version=capability_model_version,
        schedule_input_identity=schedule_input_identity(
            rule,
            SCHEDULING_RULE_VERSION,
            capability_model_version,
            [(job.request_id, job.plan.content_hash) for job in jobs],
            downtime,
            recorded,
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
        setup_rules=recorded,
        setups=tuple(sorted(setups, key=lambda c: (c.start_min, c.request_id, c.step_index))),
    )
    return dataclasses.replace(schedule, schedule_digest=schedule_digest(schedule))
