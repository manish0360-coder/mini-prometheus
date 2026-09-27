"""RM11 internal schedule model: frozen assumptions, result types, input identity, schedule digest.

NOT a contract (the suite stays 0.4.0; no ProductionSchedule / ScheduleVerdict schema): the
representation is immature and must not be frozen into the cross-layer contract (ruling D3).

Two distinct hashes (``sha256(canonical_json(view))`` via the existing ``_hashing``; no timestamps):
- ``schedule_input_identity`` answers "what scheduling problem and rule are being evaluated?" —
  the scheduling rule and its version, the capability-model version, and every job's
  ``request_id`` + plan content hash in canonical ``request_id`` order. It is computable before
  any scheduling and never contains a derived output (placements, makespan, lower bound). A job's
  plan hash already covers its machines, declared durations and any RM9 availability that
  materially affected it, so irrelevant unavailability leaves the identity unchanged.
- ``schedule_digest`` answers "what exact schedule artifact was produced?" — every field of the
  artifact (metadata, input identity, job completions, placements, makespan, lower bound, gap,
  bound status) except the digest itself.

RM12 downtime and RM14 setup rules enter both hashes only when they are relevant, so a run without
them keeps exactly the earlier identity and digest.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from mini_prometheus import _hashing as h
from mini_prometheus._contracts import DesignInput, ProductionPlan

SCHEDULING_RULE = "earliest_start_v1"
SCHEDULING_RULE_VERSION = "1.0.0"
# RM12 (ADR-0015): the same earliest-start family, recorded only when relevant downtime exists.
SCHEDULING_RULE_DOWNTIME = "earliest_start_v1_downtime"
# RM13 (ADR-0016): OPT-IN rule — exact earliest-start ties go to the job with the most remaining
# processing work (RM10 durations only), then request_id, then step_index. Never the default.
SCHEDULING_RULE_MOST_WORK_REMAINING = "earliest_start_v1_most_work_remaining"
SCHEDULING_RULE_MOST_WORK_REMAINING_DOWNTIME = "earliest_start_v1_most_work_remaining_downtime"
# RM14 (ADR-0017): the same rules, recorded with a _setup suffix only when relevant setup rules
# (declared sequence-dependent cross-job changeovers) exist.
SCHEDULING_RULE_SETUP = "earliest_start_v1_setup"
SCHEDULING_RULE_DOWNTIME_SETUP = "earliest_start_v1_downtime_setup"
SCHEDULING_RULE_MOST_WORK_REMAINING_SETUP = "earliest_start_v1_most_work_remaining_setup"
SCHEDULING_RULE_MOST_WORK_REMAINING_DOWNTIME_SETUP = (
    "earliest_start_v1_most_work_remaining_downtime_setup"
)
# The rules a caller may select (the _downtime/_setup ids are provenance, recorded automatically).
SELECTABLE_RULES: tuple[str, ...] = (SCHEDULING_RULE, SCHEDULING_RULE_MOST_WORK_REMAINING)
OPTIMIZATION_STATUS = "NOT_OPTIMIZED"

# RM11 MODEL ASSUMPTIONS (Director ruling D1): assumptions of this model, not universal claims.
MODEL_ASSUMPTIONS: tuple[str, ...] = (
    "one machine processes at most one operation at a time",
    "operations are non-preemptive",
    "each job is available at time 0",
    "each job preserves its RM10 step order",
    "each operation retains the machine assignment produced by RM9",
    "duration is the RM10 duration_min",
    "no setup/changeover time",
    "no transfer time",
    "no calendars/shifts/maintenance",
    "no due dates/release dates",
    "no flexible machine reassignment during RM11",
    "no optimization",
    "no execution/dispatch",
)

# RM12 MODEL ASSUMPTIONS (ADR-0015): recorded instead of the RM11 list under relevant downtime.
MODEL_ASSUMPTIONS_DOWNTIME: tuple[str, ...] = (
    *MODEL_ASSUMPTIONS,
    "a machine is unavailable exactly during its declared finite downtime [start_min, end_min)"
    " and available at all other times",
    "an operation never overlaps downtime on its machine; it waits for the downtime to end",
    "downtime never reroutes an operation to another machine",
)

# RM14 MODEL ASSUMPTIONS (ADR-0017): recorded under relevant setup rules. The RM11 assumption
# "no setup/changeover time" is withdrawn and the declared changeover model is stated instead.
NO_SETUP_ASSUMPTION = "no setup/changeover time"
SETUP_ASSUMPTIONS: tuple[str, ...] = (
    "a declared changeover occupies the machine immediately before an operation whose predecessor"
    " on that machine in this run belongs to another job: the declared (machine, previous"
    " operation, operation) minutes, else the machine's declared default",
    "no changeover between operations of the same job (duration_min is the declared total"
    " operation time) and none before a machine's first operation in the run",
    "a machine without declared setup rules has no changeover; on a machine with any declared"
    " rule, a cross-job transition the rule needs without a rule or default is refused, never zero",
    "a changeover starts no earlier than the job's predecessor completion and the machine's"
    " available time; changeover and operation form one uninterrupted block that never overlaps"
    " downtime",
)
MODEL_ASSUMPTIONS_SETUP: tuple[str, ...] = (
    *(a for a in MODEL_ASSUMPTIONS if a != NO_SETUP_ASSUMPTION),
    *SETUP_ASSUMPTIONS,
)
MODEL_ASSUMPTIONS_DOWNTIME_SETUP: tuple[str, ...] = (
    *(a for a in MODEL_ASSUMPTIONS_DOWNTIME if a != NO_SETUP_ASSUMPTION),
    *SETUP_ASSUMPTIONS,
)


class ScheduleStatus(StrEnum):
    SCHEDULED = "SCHEDULED"
    NOT_SCHEDULED = "NOT_SCHEDULED"  # all-or-nothing: no partial schedule is ever returned


class RefusalReason(StrEnum):
    """Why a job set was not scheduled (closed, internal; declaration order is the report order)."""

    EMPTY_JOB_SET = "EMPTY_JOB_SET"
    DUPLICATE_REQUEST_ID = "DUPLICATE_REQUEST_ID"
    JOB_NOT_MANUFACTURABLE = "JOB_NOT_MANUFACTURABLE"
    JOB_OPERATION_UNASSIGNED = "JOB_OPERATION_UNASSIGNED"
    JOB_TIMELINE_MISSING = "JOB_TIMELINE_MISSING"
    # RM14: a cross-job transition the scheduling rule needs, on a machine with declared setup
    # rules, has neither a transition rule nor a machine default (refuse to invent a changeover)
    UNSPECIFIED_SETUP_TRANSITION = "UNSPECIFIED_SETUP_TRANSITION"


class BoundStatus(StrEnum):
    PROVABLY_OPTIMAL = "PROVABLY_OPTIMAL"  # makespan == lower bound: optimal UNDER THE RM11 MODEL
    GAP_ABOVE_LOWER_BOUND = (
        "GAP_ABOVE_LOWER_BOUND"  # only the gap is stated; no suboptimality claim
    )


class IssueCode(StrEnum):
    """What the independent checker found wrong with a schedule (closed, internal)."""

    METADATA_MISMATCH = "METADATA_MISMATCH"
    JOB_SET_MISMATCH = "JOB_SET_MISMATCH"
    UNKNOWN_OPERATION = "UNKNOWN_OPERATION"
    DUPLICATE_OPERATION = "DUPLICATE_OPERATION"
    MISSING_OPERATION = "MISSING_OPERATION"
    INVALID_TIME = "INVALID_TIME"
    MACHINE_MISMATCH = "MACHINE_MISMATCH"
    DURATION_MISMATCH = "DURATION_MISMATCH"
    ARITHMETIC_MISMATCH = "ARITHMETIC_MISMATCH"
    JOB_ORDER_VIOLATION = "JOB_ORDER_VIOLATION"
    MACHINE_OVERLAP = "MACHINE_OVERLAP"
    NON_CANONICAL_ORDER = "NON_CANONICAL_ORDER"
    COMPLETION_MISMATCH = "COMPLETION_MISMATCH"
    MAKESPAN_MISMATCH = "MAKESPAN_MISMATCH"
    LOWER_BOUND_MISMATCH = "LOWER_BOUND_MISMATCH"
    GAP_MISMATCH = "GAP_MISMATCH"
    BOUND_STATUS_MISMATCH = "BOUND_STATUS_MISMATCH"
    DIGEST_MISMATCH = "DIGEST_MISMATCH"


class DowntimeIssueCode(StrEnum):
    """RM12 checker findings about downtime (closed, internal; RM11's IssueCode set unchanged)."""

    DOWNTIME_MISMATCH = "DOWNTIME_MISMATCH"  # recorded downtime != canonical relevant input
    DOWNTIME_CONFLICT = "DOWNTIME_CONFLICT"  # an operation intersects its machine's downtime
    WINDOW_LOWER_BOUND_MISMATCH = "WINDOW_LOWER_BOUND_MISMATCH"


class SetupIssueCode(StrEnum):
    """RM14 checker findings about changeovers (closed, internal; earlier code sets unchanged)."""

    SETUP_RULES_MISMATCH = "SETUP_RULES_MISMATCH"  # recorded rules != relevant canonical input
    UNSPECIFIED_SETUP_TRANSITION = "UNSPECIFIED_SETUP_TRANSITION"  # no rule for a used transition
    SETUP_MISSING = "SETUP_MISSING"  # a required changeover is not recorded
    SETUP_UNEXPECTED = "SETUP_UNEXPECTED"  # a changeover where none applies (fabricated)
    SETUP_MISMATCH = "SETUP_MISMATCH"  # wrong machine, transition, matched rule or minutes
    SETUP_INVALID_TIME = "SETUP_INVALID_TIME"  # non-integer, negative, end != start + minutes
    SETUP_NOT_ADJACENT = "SETUP_NOT_ADJACENT"  # changeover end != operation start
    SETUP_OVERLAP = "SETUP_OVERLAP"  # changeover + operation block overlaps another on the machine
    SETUP_DOWNTIME_CONFLICT = "SETUP_DOWNTIME_CONFLICT"  # changeover intersects machine downtime
    SETUP_BEFORE_PREDECESSOR = "SETUP_BEFORE_PREDECESSOR"  # starts before the job's previous step


class SetupMatch(StrEnum):
    """RM14: which declared rule gave a changeover its minutes."""

    TRANSITION = "transition"  # the (machine, prev_op, curr_op) rule
    MACHINE_DEFAULT = "machine_default"  # the machine's default cross-job rule


@dataclass(frozen=True, order=True)
class DowntimeInterval:
    """RM12: a machine is unavailable on [start_min, end_min), minutes from schedule origin 0."""

    start_min: int
    end_min: int


# Relevant canonical downtime: (machine id, sorted pairwise disjoint and non-touching intervals),
# machines in sorted order — only machines assigned to at least one operation of the job set.
Downtime = tuple[tuple[str, tuple[DowntimeInterval, ...]], ...]


@dataclass(frozen=True)
class SetupRule:
    """RM14: a declared cross-job changeover on ``machine_id``, integer minutes >= 0. With operation
    codes, ``prev_op -> curr_op`` is one transition; ``prev_op = curr_op = None`` is the machine's
    default for every cross-job transition without its own rule (never a wildcard string)."""

    machine_id: str
    prev_op: str | None
    curr_op: str | None
    duration_min: int


# Relevant canonical setup rules in (machine_id, default first, prev_op, curr_op) order: only the
# rules that can apply to a possible cross-job transition of the job set.
SetupRules = tuple[SetupRule, ...]


class InvalidDowntimeError(ValueError):
    """Invalid downtime input (rejected before scheduling; never a manufacturing verdict)."""


class InvalidSetupError(ValueError):
    """Invalid setup-rule input (rejected before planning; never a manufacturing verdict)."""


class UnspecifiedSetupTransitionError(ValueError):
    """RM14: the scheduling rule needs cross-job changeovers that have neither a transition rule nor
    a machine default. ``transitions``: sorted (machine, prev_op, curr_op). Reported by the job set
    as UNSPECIFIED_SETUP_TRANSITION refusals — a changeover time is never invented."""

    def __init__(self, transitions: Sequence[tuple[str, str, str]]) -> None:
        self.transitions = tuple(sorted(set(transitions)))
        super().__init__("; ".join(f"{m}: {p} -> {c}" for m, p, c in self.transitions))


class UnknownSchedulingRuleError(ValueError):
    """A scheduling rule that is not selectable (rejected before planning)."""


@dataclass(frozen=True)
class JobInput:
    """One job of a scheduling request: the engineer's ``request_id`` and its design input."""

    request_id: str
    design_input: DesignInput


@dataclass(frozen=True)
class SchedulingJob:
    """A schedulable job: planned and verified MANUFACTURABLE under the run's single capability
    model, every step assigned a machine, and a valid RM10 timeline carried on its plan."""

    request_id: str
    task_id: str
    plan: ProductionPlan


@dataclass(frozen=True)
class ScheduledOperation:
    request_id: str
    task_id: str
    step_index: int
    op: str
    resource_id: str
    duration_min: int
    start_min: int
    end_min: int


@dataclass(frozen=True)
class ScheduledSetup:
    """RM14: a changeover occupying ``resource_id`` on [start_min, end_min) immediately before the
    operation (request_id, step_index), whose predecessor on the machine is ``prev_op`` of job
    ``prev_request_id``: end_min == the operation's start_min and
    end_min - start_min == duration_min."""

    request_id: str
    step_index: int
    resource_id: str
    prev_request_id: str
    prev_op: str
    curr_op: str
    matched: SetupMatch
    duration_min: int
    start_min: int
    end_min: int


@dataclass(frozen=True)
class JobCompletion:
    request_id: str
    task_id: str
    plan_content_hash: str
    completion_min: int


@dataclass(frozen=True)
class LowerBound:
    lower_bound_min: int
    binding_request_ids: tuple[str, ...]  # jobs whose total duration equals the bound
    binding_resource_ids: tuple[str, ...]  # machines whose total assigned duration equals the bound


@dataclass(frozen=True)
class MultiJobSchedule:
    """The internal RM11 schedule artifact. Times are integer minutes from schedule origin 0."""

    scheduling_rule: str
    scheduling_rule_version: str
    optimization_status: str
    model_assumptions: tuple[str, ...]
    capability_model_version: str
    schedule_input_identity: str
    jobs: tuple[JobCompletion, ...]  # canonical request_id order
    # canonical (start_min, request_id, step_index) order
    operations: tuple[ScheduledOperation, ...]
    makespan_min: int
    lower_bound_min: int
    lower_bound_binding_request_ids: tuple[str, ...]
    lower_bound_binding_resource_ids: tuple[str, ...]
    gap_to_lower_bound_min: int
    bound_status: BoundStatus
    schedule_digest: str
    # RM12: set only when relevant downtime exists; otherwise the artifact is exactly RM11's. Then
    # the gap is measured to the window-aware bound; lower_bound_min stays the RM11 bound.
    downtime: Downtime = ()
    window_aware_lower_bound_min: int | None = None
    window_aware_lower_bound_binding_resource_ids: tuple[str, ...] = ()
    # RM14: set only when relevant setup rules exist; otherwise the artifact is exactly RM13's.
    # Changeovers are in canonical (start_min, request_id, step_index) order.
    setup_rules: SetupRules = ()
    setups: tuple[ScheduledSetup, ...] = ()


@dataclass(frozen=True)
class Refusal:
    reason: RefusalReason
    request_id: str | None
    detail: str


@dataclass(frozen=True)
class ScheduleOutcome:
    status: ScheduleStatus
    schedule: MultiJobSchedule | None
    refusals: tuple[Refusal, ...]


@dataclass(frozen=True)
class ScheduleIssue:
    code: IssueCode | DowntimeIssueCode | SetupIssueCode
    detail: str


class ScheduleIntegrityError(RuntimeError):
    """A generated schedule failed the independent checker. It is never returned (fail closed)."""


def downtime_view(downtime: Downtime) -> dict[str, list[list[int]]]:
    """Canonical JSON form of relevant downtime: {machine: [[start_min, end_min], ...]}."""
    return {m: [[i.start_min, i.end_min] for i in ivs] for m, ivs in sorted(downtime)}


def setup_rules_view(rules: SetupRules) -> list[dict[str, object]]:
    """Canonical JSON form of relevant setup rules (a machine default has null operations)."""
    return [dataclasses.asdict(rule) for rule in rules]


def schedule_input_identity(
    scheduling_rule: str,
    scheduling_rule_version: str,
    capability_model_version: str,
    jobs: Sequence[tuple[str, str]],
    downtime: Downtime = (),
    setup_rules: SetupRules = (),
) -> str:
    """Identity of the scheduling problem + rule. ``jobs`` = (request_id, plan content hash)
    pairs, in any order (canonicalized here). Never includes a derived output such as makespan.
    RM12: relevant canonical downtime enters only when there is some, so a run without relevant
    downtime keeps exactly the RM11 identity. RM14: likewise for relevant canonical setup rules."""
    view: dict[str, object] = {
        "scheduling_rule": scheduling_rule,
        "scheduling_rule_version": scheduling_rule_version,
        "capability_model_version": capability_model_version,
        "jobs": [{"request_id": r, "plan_content_hash": p} for r, p in sorted(jobs)],
    }
    if downtime:
        view["downtime"] = downtime_view(downtime)
    if setup_rules:
        view["setup_rules"] = setup_rules_view(setup_rules)
    return h.content_hash(view)


def schedule_view(schedule: MultiJobSchedule) -> dict[str, object]:
    """The canonical view of the artifact: every field except ``schedule_digest`` (the RM12
    fields only when relevant downtime exists, the RM14 fields only when relevant setup rules exist,
    so an RM11-shaped artifact digests as in RM11)."""
    view: dict[str, object] = {
        "scheduling_rule": schedule.scheduling_rule,
        "scheduling_rule_version": schedule.scheduling_rule_version,
        "optimization_status": schedule.optimization_status,
        "model_assumptions": list(schedule.model_assumptions),
        "capability_model_version": schedule.capability_model_version,
        "schedule_input_identity": schedule.schedule_input_identity,
        "jobs": [dataclasses.asdict(job) for job in schedule.jobs],
        "operations": [dataclasses.asdict(op) for op in schedule.operations],
        "makespan_min": schedule.makespan_min,
        "lower_bound_min": schedule.lower_bound_min,
        "lower_bound_binding_request_ids": list(schedule.lower_bound_binding_request_ids),
        "lower_bound_binding_resource_ids": list(schedule.lower_bound_binding_resource_ids),
        "gap_to_lower_bound_min": schedule.gap_to_lower_bound_min,
        "bound_status": str(schedule.bound_status),
    }
    if schedule.downtime:
        view["downtime"] = downtime_view(schedule.downtime)
        view["window_aware_lower_bound_min"] = schedule.window_aware_lower_bound_min
        view["window_aware_lower_bound_binding_resource_ids"] = list(
            schedule.window_aware_lower_bound_binding_resource_ids
        )
    if schedule.setup_rules:
        view["setup_rules"] = setup_rules_view(schedule.setup_rules)
        view["setups"] = [dataclasses.asdict(setup) for setup in schedule.setups]
    return view


def schedule_digest(schedule: MultiJobSchedule) -> str:
    """Digest of the exact artifact produced (the digest field itself excluded)."""
    return h.content_hash(schedule_view(schedule))
