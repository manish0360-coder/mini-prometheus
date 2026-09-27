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
    code: IssueCode
    detail: str


class ScheduleIntegrityError(RuntimeError):
    """A generated schedule failed the independent checker. It is never returned (fail closed)."""


def schedule_input_identity(
    scheduling_rule: str,
    scheduling_rule_version: str,
    capability_model_version: str,
    jobs: Sequence[tuple[str, str]],
) -> str:
    """Identity of the scheduling problem + rule. ``jobs`` = (request_id, plan content hash)
    pairs, in any order (canonicalized here). Never includes a derived output such as makespan."""
    return h.content_hash(
        {
            "scheduling_rule": scheduling_rule,
            "scheduling_rule_version": scheduling_rule_version,
            "capability_model_version": capability_model_version,
            "jobs": [{"request_id": r, "plan_content_hash": p} for r, p in sorted(jobs)],
        }
    )


def schedule_view(schedule: MultiJobSchedule) -> dict[str, object]:
    """The canonical view of the artifact: every field except ``schedule_digest``."""
    return {
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


def schedule_digest(schedule: MultiJobSchedule) -> str:
    """Digest of the exact artifact produced (the digest field itself excluded)."""
    return h.content_hash(schedule_view(schedule))
