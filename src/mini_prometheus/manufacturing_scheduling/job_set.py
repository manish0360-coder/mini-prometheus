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

RM14: setup rules are validated before planning (``InvalidSetupError``). If the scheduling rule
needs a cross-job changeover on a machine with declared rules that has neither its transition rule
nor the machine default, the whole set is refused (UNSPECIFIED_SETUP_TRANSITION, one refusal per
such transition) — a changeover time is never invented; unneeded transitions are not required.

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
from mini_prometheus.manufacturing_scheduling.changeover import SetupInput, canonical_setup_rules
from mini_prometheus.manufacturing_scheduling.checker import schedule_issues
from mini_prometheus.manufacturing_scheduling.downtime import (
    DowntimeInput,
    canonical_downtime,
    relevant_downtime,
)
from mini_prometheus.manufacturing_scheduling.earliest_start import (
    earliest_start_v1,
    earliest_start_v1_most_work_remaining,
)
from mini_prometheus.manufacturing_scheduling.model import (
    SCHEDULING_RULE,
    SCHEDULING_RULE_MOST_WORK_REMAINING,
    SELECTABLE_RULES,
    JobInput,
    Refusal,
    RefusalReason,
    ScheduleIntegrityError,
    ScheduleOutcome,
    ScheduleStatus,
    SchedulingJob,
    UnknownSchedulingRuleError,
    UnspecifiedSetupTransitionError,
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
    downtime: DowntimeInput | None = None,
    rule: str = SCHEDULING_RULE,
    setup_rules: SetupInput | None = None,
) -> ScheduleOutcome:
    """RM12: ``downtime`` (machine id -> [start_min, end_min) pairs) is validated against the
    model's known machines first — invalid input raises ``InvalidDowntimeError`` before any
    planning; it is never a verdict or a refusal. Only machines the jobs use are relevant.
    RM13: ``rule`` selects the scheduling rule; the default is ``earliest_start_v1`` and
    ``earliest_start_v1_most_work_remaining`` is opt-in. Any other value raises
    ``UnknownSchedulingRuleError`` before planning. RM14: ``setup_rules`` (``SetupRule`` objects
    or (machine_id, prev_op, curr_op, duration_min) sequences; None ops = the machine default) are
    validated against the model before planning; invalid rules raise ``InvalidSetupError``."""
    if rule not in SELECTABLE_RULES:
        raise UnknownSchedulingRuleError(
            f"unknown scheduling rule {rule!r}; selectable: {', '.join(SELECTABLE_RULES)}"
        )
    canonical = canonical_downtime(downtime, capability_model.resources)
    canonical_setup = canonical_setup_rules(setup_rules, capability_model)
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

    relevant = relevant_downtime(canonical, jobs)
    generate = (
        earliest_start_v1_most_work_remaining
        if rule == SCHEDULING_RULE_MOST_WORK_REMAINING
        else earliest_start_v1
    )
    try:
        if relevant or canonical_setup:
            schedule = generate(
                jobs, capability_model.version, downtime=relevant, setup_rules=canonical_setup
            )
        else:  # no relevant downtime or setup rules: exactly the RM11 call
            schedule = generate(jobs, capability_model.version)
    except UnspecifiedSetupTransitionError as missing:  # RM14: never invent a changeover time
        undeclared = {
            Refusal(
                RefusalReason.UNSPECIFIED_SETUP_TRANSITION,
                None,
                f"{machine}: cross-job changeover {prev_op} -> {curr_op} is not declared and "
                f"{machine} has no declared default",
            )
            for machine, prev_op, curr_op in missing.transitions
        }
        return ScheduleOutcome(
            ScheduleStatus.NOT_SCHEDULED, None, tuple(sorted(undeclared, key=_refusal_key))
        )
    issues = schedule_issues(
        schedule, jobs, capability_model.version, downtime=downtime, setup_rules=setup_rules
    )
    if issues:
        raise ScheduleIntegrityError("; ".join(f"{issue.code}: {issue.detail}" for issue in issues))
    return ScheduleOutcome(ScheduleStatus.SCHEDULED, schedule, ())
