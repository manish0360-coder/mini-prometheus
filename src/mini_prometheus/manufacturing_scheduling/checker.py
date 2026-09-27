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

RM12 (ADR-0015), given the RAW downtime input of the run: it independently re-derives the relevant
canonical downtime (machines the jobs use; the union of their intervals by an event sweep in which
touching intervals join) and proves that the recorded downtime equals it (DOWNTIME_MISMATCH), that
no operation intersects downtime of its machine under half-open semantics (DOWNTIME_CONFLICT), and
that the window-aware lower bound is exact (WINDOW_LOWER_BOUND_MISMATCH; T_avail recomputed as the
least fixed point of T = W + downtime inside [0, T)); the gap is then checked against that bound.
It never imports the downtime canonicalizer (import-linter contract).

RM14 (ADR-0017), given the RAW setup-rule input of the run: it re-reads the declared rules itself,
re-derives the relevant ones (a transition rule whose transition can occur between two different
jobs on its machine; a machine default when such a transition has no rule of its own) and proves the
recorded rules equal them (SETUP_RULES_MISMATCH). From each machine's operation sequence in the
schedule it re-derives which operations need a changeover — a machine with any declared rule, and a
machine predecessor from another job — and its minutes (the transition rule, else the default; if
neither, UNSPECIFIED_SETUP_TRANSITION), then proves every required changeover is recorded
(SETUP_MISSING), none is fabricated (SETUP_UNEXPECTED: first operation, same job, undeclared
machine), each records the right machine, transition, matched rule and minutes (SETUP_MISMATCH),
integer times with end == start + minutes (SETUP_INVALID_TIME), ends exactly at its operation's
start (SETUP_NOT_ADJACENT), starts no earlier than the job's previous step ends
(SETUP_BEFORE_PREDECESSOR), avoids downtime (SETUP_DOWNTIME_CONFLICT), and that changeover +
operation blocks never overlap on a machine (SETUP_OVERLAP). It never imports the setup-rule
module (import-linter contract).
"""

from __future__ import annotations

import itertools
from collections.abc import Iterable, Mapping, Sequence
from typing import TypeGuard, cast

from mini_prometheus.manufacturing_constraints.oracle import DURATION_PARAM
from mini_prometheus.manufacturing_scheduling.model import (
    MODEL_ASSUMPTIONS,
    MODEL_ASSUMPTIONS_DOWNTIME,
    MODEL_ASSUMPTIONS_DOWNTIME_SETUP,
    MODEL_ASSUMPTIONS_SETUP,
    OPTIMIZATION_STATUS,
    BoundStatus,
    Downtime,
    DowntimeInterval,
    DowntimeIssueCode,
    IssueCode,
    MultiJobSchedule,
    ScheduledOperation,
    ScheduledSetup,
    ScheduleIssue,
    SchedulingJob,
    SetupIssueCode,
    SetupMatch,
    SetupRule,
    schedule_digest,
    schedule_input_identity,
)

_Key = tuple[str, int]
_Transition = tuple[str, str | None, str | None]  # (machine, prev_op, curr_op); None = default


def _union(spans: list[tuple[int, int]]) -> tuple[DowntimeInterval, ...]:
    """Union of half-open spans by an event sweep; at equal times starts precede ends, so touching
    spans join."""
    events = sorted(
        [(s, 1) for s, _ in spans] + [(e, -1) for _, e in spans], key=lambda x: (x[0], -x[1])
    )
    union: list[DowntimeInterval] = []
    depth, opened = 0, 0
    for time, delta in events:
        if delta == 1 and depth == 0:
            opened = time
        depth += delta
        if delta == -1 and depth == 0:
            union.append(DowntimeInterval(opened, time))
    return tuple(union)


def _relevant_downtime(
    downtime: Mapping[str, Iterable[object]] | None, jobs: Sequence[SchedulingJob]
) -> Downtime | None:
    """The canonical downtime of the machines the jobs use, re-derived from the raw input (None if
    the input is not valid downtime)."""
    if not downtime:
        return ()
    used = {a.resource_id for job in jobs for a in job.plan.resource_assignments}
    relevant: list[tuple[str, tuple[DowntimeInterval, ...]]] = []
    for machine in sorted(m for m in downtime if m in used):
        spans: list[tuple[int, int]] = []
        for raw in downtime[machine]:
            if isinstance(raw, DowntimeInterval):
                pair: tuple[object, ...] = (raw.start_min, raw.end_min)
            else:
                try:
                    pair = tuple(cast(Iterable[object], raw))
                except TypeError:
                    return None
            if len(pair) != 2 or not all(_minutes(v) for v in pair):
                return None
            start, end = cast(tuple[int, int], pair)
            if start < 0 or end <= start:
                return None
            spans.append((start, end))
        if spans:
            relevant.append((machine, _union(spans)))
    return tuple(relevant)


def _declared_setup_rules(setup_rules: Iterable[object] | None) -> dict[_Transition, int] | None:
    """RM14: the declared rules {(machine, prev_op, curr_op): minutes}, re-read from the raw input
    (None if the input is not valid setup rules)."""
    if not setup_rules:
        return {}
    declared: dict[_Transition, int] = {}
    for raw in setup_rules:
        if isinstance(raw, SetupRule):
            fields: tuple[object, ...] = (
                raw.machine_id,
                raw.prev_op,
                raw.curr_op,
                raw.duration_min,
            )
        elif isinstance(raw, str | bytes) or not isinstance(raw, Iterable):
            return None
        else:
            fields = tuple(raw)
        if len(fields) != 4:
            return None
        machine, prev_op, curr_op, minutes = fields
        default = prev_op is None and curr_op is None
        named = isinstance(prev_op, str) and isinstance(curr_op, str)
        if not isinstance(machine, str) or not (default or named):
            return None
        if not _minutes(minutes) or minutes < 0:
            return None
        key = (machine, cast(str | None, prev_op), cast(str | None, curr_op))
        if key in declared:
            return None
        declared[key] = minutes
    return declared


def _relevant_setup_rules(
    declared: Mapping[_Transition, int], jobs: Sequence[SchedulingJob]
) -> tuple[SetupRule, ...]:
    """RM14: the declared rules that can apply to a transition between two different jobs on the
    rule's machine, in canonical (machine, default first, prev_op, curr_op) order."""
    job_ops: dict[str, dict[str, set[str]]] = {}  # machine -> request_id -> operation codes
    for job in jobs:
        assigned = {a.step_index: a.resource_id for a in job.plan.resource_assignments}
        for step in job.plan.steps:
            if step.index in assigned:
                by_job = job_ops.setdefault(assigned[step.index], {})
                by_job.setdefault(job.request_id, set()).add(step.op.value)
    relevant: list[SetupRule] = []
    for (machine, prev_op, curr_op), minutes in declared.items():
        by_job = job_ops.get(machine, {})
        transitions = {
            (before, after)
            for one, one_ops in by_job.items()
            for other, other_ops in by_job.items()
            if one != other
            for before in one_ops
            for after in other_ops
        }
        if prev_op is None:
            applies = any((machine, b, a) not in declared for b, a in transitions)
        else:
            applies = (prev_op, curr_op) in transitions
        if applies:
            relevant.append(SetupRule(machine, prev_op, curr_op, minutes))
    return tuple(
        sorted(
            relevant,
            key=lambda r: (r.machine_id, r.prev_op is not None, r.prev_op or "", r.curr_op or ""),
        )
    )


def _machine_ready(work: int, downtime: Sequence[DowntimeInterval]) -> int:
    """T_avail(work), independently: the least fixed point of T = work + downtime inside [0, T)."""
    t = work
    while True:
        inside = sum(min(i.end_min, t) - i.start_min for i in downtime if i.start_min < t)
        if work + inside == t:
            return t
        t = work + inside


def _minutes(value: object) -> TypeGuard[int]:
    return isinstance(value, int) and not isinstance(value, bool)


def _label(request_id: str, step_index: int) -> str:
    return f"{request_id} step {step_index}"


def _interval(op: ScheduledOperation) -> str:
    return f"{_label(op.request_id, op.step_index)} [{op.start_min}, {op.end_min})"


def _setup_label(setup: ScheduledSetup) -> str:
    return f"changeover before {_label(setup.request_id, setup.step_index)}"


def schedule_issues(
    schedule: MultiJobSchedule,
    jobs: Sequence[SchedulingJob],
    capability_model_version: str,
    downtime: Mapping[str, Iterable[object]] | None = None,
    setup_rules: Iterable[object] | None = None,
) -> list[ScheduleIssue]:
    """``downtime`` is the raw downtime input of the run (RM12) and ``setup_rules`` its raw setup
    rules (RM14); None or empty means none."""
    issues: list[ScheduleIssue] = []

    def add(code: IssueCode | DowntimeIssueCode | SetupIssueCode, detail: str) -> None:
        issues.append(ScheduleIssue(code, detail))

    # --- RM12: the relevant canonical downtime, re-derived from the raw input ----------------
    relevant = _relevant_downtime(downtime, jobs)
    if relevant is None:
        add(DowntimeIssueCode.DOWNTIME_MISMATCH, "the downtime input is not valid downtime")
        relevant = ()
    if tuple(schedule.downtime) != relevant:
        add(DowntimeIssueCode.DOWNTIME_MISMATCH, "recorded downtime != relevant canonical input")
    blocked = dict(relevant)

    # --- RM14: the relevant canonical setup rules, re-derived from the raw input --------------
    declared = _declared_setup_rules(setup_rules)
    if declared is None:
        add(SetupIssueCode.SETUP_RULES_MISMATCH, "the setup-rule input is not valid setup rules")
        declared = {}
    relevant_setup = _relevant_setup_rules(declared, jobs)
    if tuple(schedule.setup_rules) != relevant_setup:
        add(SetupIssueCode.SETUP_RULES_MISMATCH, "recorded setup rules != relevant canonical input")

    # --- metadata and job set ---------------------------------------------------------------
    if schedule.optimization_status != OPTIMIZATION_STATUS:
        add(IssueCode.METADATA_MISMATCH, f"optimization_status {schedule.optimization_status!r}")
    model = {
        (False, False): MODEL_ASSUMPTIONS,
        (True, False): MODEL_ASSUMPTIONS_DOWNTIME,
        (False, True): MODEL_ASSUMPTIONS_SETUP,
        (True, True): MODEL_ASSUMPTIONS_DOWNTIME_SETUP,
    }[(bool(relevant), bool(relevant_setup))]
    if tuple(schedule.model_assumptions) != model:
        add(IssueCode.METADATA_MISMATCH, "model_assumptions differ from the model in force")
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
        relevant,
        relevant_setup,
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

    # --- RM12: no operation intersects downtime of its machine (half-open) --------------------
    for key in sorted(valid):
        op = valid[key]
        for down in blocked.get(op.resource_id, ()):
            if op.start_min < down.end_min and down.start_min < op.end_min:
                add(
                    DowntimeIssueCode.DOWNTIME_CONFLICT,
                    f"{_interval(op)} intersects {op.resource_id} downtime "
                    f"[{down.start_min}, {down.end_min})",
                )

    # --- RM14: changeovers required by each machine's sequence in this schedule --------------
    active = {machine for machine, _, _ in declared}  # machines with any declared rule
    required_setups: dict[_Key, tuple[str, str, str, str, SetupMatch, int]] = {}
    for resource_id in sorted(by_machine):
        sequence = sorted(
            by_machine[resource_id],
            key=lambda o: (o.start_min, o.end_min, o.request_id, o.step_index),
        )
        for previous, current in itertools.pairwise(sequence):
            if resource_id not in active or previous.request_id == current.request_id:
                continue  # no declared rule on the machine, or the same job: no changeover
            transition = (resource_id, previous.op, current.op)
            if transition in declared:
                match, minutes = SetupMatch.TRANSITION, declared[transition]
            elif (resource_id, None, None) in declared:
                match, minutes = SetupMatch.MACHINE_DEFAULT, declared[(resource_id, None, None)]
            else:
                add(
                    SetupIssueCode.UNSPECIFIED_SETUP_TRANSITION,
                    f"{resource_id}: {previous.op} -> {current.op} before "
                    f"{_label(current.request_id, current.step_index)} has no declared changeover",
                )
                continue
            required_setups[(current.request_id, current.step_index)] = (
                resource_id,
                previous.request_id,
                previous.op,
                current.op,
                match,
                minutes,
            )
    recorded_setups: dict[_Key, ScheduledSetup] = {}
    block_start: dict[_Key, int] = {}  # operation -> start of its changeover + operation block
    for setup in schedule.setups:
        key = (setup.request_id, setup.step_index)
        label = _setup_label(setup)
        if key in recorded_setups:
            add(SetupIssueCode.SETUP_MISMATCH, f"{label}: recorded more than once")
            continue
        recorded_setups[key] = setup
        if key not in required_setups or key not in valid:
            add(SetupIssueCode.SETUP_UNEXPECTED, f"{label}: no changeover applies here")
            continue
        found = (
            setup.resource_id,
            setup.prev_request_id,
            setup.prev_op,
            setup.curr_op,
            setup.matched,
            setup.duration_min,
        )
        if found != required_setups[key]:
            add(SetupIssueCode.SETUP_MISMATCH, f"{label}: {found}, required {required_setups[key]}")
        times = (setup.start_min, setup.end_min, setup.duration_min)
        if (
            not all(_minutes(t) for t in times)
            or setup.start_min < 0
            or setup.duration_min < 0
            or setup.end_min != setup.start_min + setup.duration_min
        ):
            add(SetupIssueCode.SETUP_INVALID_TIME, f"{label}: invalid changeover interval")
            continue
        op = valid[key]
        block_start[key] = setup.start_min
        if setup.end_min != op.start_min:
            add(
                SetupIssueCode.SETUP_NOT_ADJACENT,
                f"{label}: ends at {setup.end_min}, the operation starts at {op.start_min}",
            )
        steps = step_order.get(setup.request_id, [])
        position = steps.index(setup.step_index) if setup.step_index in steps else 0
        predecessor = valid.get((setup.request_id, steps[position - 1])) if position else None
        if predecessor is not None and setup.start_min < predecessor.end_min:
            add(
                SetupIssueCode.SETUP_BEFORE_PREDECESSOR,
                f"{label}: starts at {setup.start_min}, before {_interval(predecessor)} ends",
            )
        for down in blocked.get(op.resource_id, ()):
            if setup.start_min < down.end_min and down.start_min < setup.end_min:
                add(
                    SetupIssueCode.SETUP_DOWNTIME_CONFLICT,
                    f"{label} [{setup.start_min}, {setup.end_min}) intersects {op.resource_id} "
                    f"downtime [{down.start_min}, {down.end_min})",
                )
    for key in sorted(required_setups):
        if key not in recorded_setups:
            add(SetupIssueCode.SETUP_MISSING, f"{_label(*key)}: required changeover not recorded")
    if block_start:  # changeover + operation blocks never overlap on a machine (half-open)
        for resource_id in sorted(by_machine):
            blocks = sorted(
                (
                    block_start.get((o.request_id, o.step_index), o.start_min),
                    o.end_min,
                    _interval(o),
                )
                for o in by_machine[resource_id]
            )
            occupied_until: int | None = None
            occupant = ""
            for begin, finish, name in blocks:
                if occupied_until is not None and begin < occupied_until:
                    add(
                        SetupIssueCode.SETUP_OVERLAP,
                        f"{resource_id}: block of {name} from {begin} overlaps {occupant}",
                    )
                if occupied_until is None or finish > occupied_until:
                    occupied_until, occupant = finish, name
    if all(
        _minutes(c.start_min) and _minutes(c.step_index) and isinstance(c.request_id, str)
        for c in schedule.setups
    ):
        setup_order = [(c.start_min, c.request_id, c.step_index) for c in schedule.setups]
        if setup_order != sorted(setup_order):
            add(IssueCode.NON_CANONICAL_ORDER, "changeovers not in (start, request_id, step) order")

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
        # RM12: with relevant downtime the gap is measured to the window-aware bound.
        window = schedule.window_aware_lower_bound_min
        window_recorded = (window, tuple(schedule.window_aware_lower_bound_binding_resource_ids))
        if relevant and job_totals and machine_loads:
            ready = {m: _machine_ready(w, blocked.get(m, ())) for m, w in machine_loads.items()}
            rm11 = max(max(job_totals.values()), max(machine_loads.values()))
            value = max(rm11, max(ready.values()))
            window_expected = (value, tuple(sorted(m for m, t in ready.items() if t == value)))
            if window_recorded != window_expected:
                add(
                    DowntimeIssueCode.WINDOW_LOWER_BOUND_MISMATCH,
                    f"window-aware lower bound {window_recorded}, expected {window_expected}",
                )
        elif not relevant and window_recorded != (None, ()):
            add(
                DowntimeIssueCode.WINDOW_LOWER_BOUND_MISMATCH, "window-aware bound without downtime"
            )
        reference = window if relevant else recorded_bound
        if not _minutes(reference) or gap != makespan - reference:
            add(IssueCode.GAP_MISMATCH, f"gap {gap} != {makespan} - {reference}")
        expected_status = (
            BoundStatus.PROVABLY_OPTIMAL if gap == 0 else BoundStatus.GAP_ABOVE_LOWER_BOUND
        )
        if schedule.bound_status != expected_status:
            add(IssueCode.BOUND_STATUS_MISMATCH, f"{schedule.bound_status!r} with gap {gap}")

    # --- digest -------------------------------------------------------------------------------
    if schedule.schedule_digest != schedule_digest(schedule):
        add(IssueCode.DIGEST_MISMATCH, "schedule_digest does not match the artifact")
    return issues
