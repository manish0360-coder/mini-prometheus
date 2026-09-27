"""RM11 — the independent schedule checker (Director test 17: every tampering class is caught).

Each tamper below corrupts one aspect of a valid schedule and then RE-COMPUTES the digest (a forger
who fixes the digest), so the checker must find the defect itself; digest-only tampering is tested
separately. The checker is generator-agnostic: a hand-built valid schedule from another "rule"
passes, which is the hook a future RM12 comparison would use (makespan, lower bound, gap).
"""

from __future__ import annotations

import dataclasses

import pytest

import rm11_support as s
from mini_prometheus.manufacturing_scheduling.checker import schedule_issues
from mini_prometheus.manufacturing_scheduling.earliest_start import earliest_start_v1
from mini_prometheus.manufacturing_scheduling.lower_bound import lower_bound
from mini_prometheus.manufacturing_scheduling.model import (
    MODEL_ASSUMPTIONS,
    OPTIMIZATION_STATUS,
    BoundStatus,
    IssueCode,
    JobCompletion,
    MultiJobSchedule,
    ScheduledOperation,
    schedule_digest,
    schedule_input_identity,
)
from rm11_support import ID_A, ID_B, ID_C

VERSION = "1.0.0"


def _base():
    jobs = s.scheduling_jobs(s.three_job_requests())
    return jobs, earliest_start_v1(jobs, VERSION)


def _redigest(sched: MultiJobSchedule) -> MultiJobSchedule:
    return dataclasses.replace(sched, schedule_digest=schedule_digest(sched))


def _with_ops(sched, mutate):
    ops = list(sched.operations)
    mutate(ops)
    return dataclasses.replace(sched, operations=tuple(ops))


def _replace_op(sched, request_id, step_index, **changes):
    def mutate(ops):
        i = next(
            k for k, o in enumerate(ops) if (o.request_id, o.step_index) == (request_id, step_index)
        )
        ops[i] = dataclasses.replace(ops[i], **changes)

    return _with_ops(sched, mutate)


def _codes(sched, jobs) -> set[IssueCode]:
    return {issue.code for issue in schedule_issues(sched, jobs, VERSION)}


TAMPERS = [
    (
        "foreign_operation",
        lambda sc: _with_ops(
            sc,
            lambda ops: ops.append(
                dataclasses.replace(ops[-1], request_id="dddddddd-0000-4000-8000-000000000004")
            ),
        ),
        IssueCode.UNKNOWN_OPERATION,
    ),
    (
        "foreign_task",
        lambda sc: _replace_op(sc, ID_A, 0, task_id="not-this-job"),
        IssueCode.UNKNOWN_OPERATION,
    ),
    (
        "duplicated_operation",
        lambda sc: _with_ops(sc, lambda ops: ops.append(ops[-1])),
        IssueCode.DUPLICATE_OPERATION,
    ),
    (
        "omitted_operation",
        lambda sc: _with_ops(sc, lambda ops: ops.pop()),
        IssueCode.MISSING_OPERATION,
    ),
    ("float_minutes", lambda sc: _replace_op(sc, ID_A, 0, start_min=0.0), IssueCode.INVALID_TIME),
    (
        "negative_start",
        lambda sc: _replace_op(sc, ID_A, 0, start_min=-1, end_min=9),
        IssueCode.INVALID_TIME,
    ),
    (
        "boolean_minutes",
        lambda sc: _replace_op(sc, ID_A, 0, start_min=False),
        IssueCode.INVALID_TIME,
    ),
    (
        "machine_reassigned",
        lambda sc: _replace_op(sc, ID_A, 1, resource_id="mill02"),
        IssueCode.MACHINE_MISMATCH,
    ),
    (
        "duration_altered",
        lambda sc: _replace_op(sc, ID_A, 1, duration_min=31, end_min=41),
        IssueCode.DURATION_MISMATCH,
    ),
    (
        "end_not_start_plus_duration",
        lambda sc: _replace_op(sc, ID_A, 1, end_min=41),
        IssueCode.ARITHMETIC_MISMATCH,
    ),
    (
        "start_before_predecessor_end",
        lambda sc: _replace_op(sc, ID_B, 1, start_min=12, end_min=32),
        IssueCode.JOB_ORDER_VIOLATION,
    ),
    (
        "machine_overlap",
        lambda sc: _replace_op(sc, ID_C, 0, start_min=12, end_min=20),
        IssueCode.MACHINE_OVERLAP,
    ),
    (
        "non_canonical_order",
        lambda sc: dataclasses.replace(sc, operations=tuple(reversed(sc.operations))),
        IssueCode.NON_CANONICAL_ORDER,
    ),
    (
        "completion_corrupted",
        lambda sc: dataclasses.replace(
            sc, jobs=(dataclasses.replace(sc.jobs[0], completion_min=46), *sc.jobs[1:])
        ),
        IssueCode.COMPLETION_MISMATCH,
    ),
    (
        "makespan_corrupted",
        lambda sc: dataclasses.replace(sc, makespan_min=67),
        IssueCode.MAKESPAN_MISMATCH,
    ),
    (
        "lower_bound_corrupted",
        lambda sc: dataclasses.replace(sc, lower_bound_min=45),
        IssueCode.LOWER_BOUND_MISMATCH,
    ),
    (
        "lower_bound_binding_corrupted",
        lambda sc: dataclasses.replace(sc, lower_bound_binding_resource_ids=()),
        IssueCode.LOWER_BOUND_MISMATCH,
    ),
    (
        "gap_corrupted",
        lambda sc: dataclasses.replace(sc, gap_to_lower_bound_min=15),
        IssueCode.GAP_MISMATCH,
    ),
    (
        "claims_provably_optimal_with_a_gap",
        lambda sc: dataclasses.replace(sc, bound_status=BoundStatus.PROVABLY_OPTIMAL),
        IssueCode.BOUND_STATUS_MISMATCH,
    ),
    (
        "claims_optimization",
        lambda sc: dataclasses.replace(sc, optimization_status="OPTIMIZED"),
        IssueCode.METADATA_MISMATCH,
    ),
    (
        "assumption_dropped",
        lambda sc: dataclasses.replace(sc, model_assumptions=sc.model_assumptions[:-1]),
        IssueCode.METADATA_MISMATCH,
    ),
    (
        "other_capability_model",
        lambda sc: dataclasses.replace(sc, capability_model_version="1.1.0"),
        IssueCode.METADATA_MISMATCH,
    ),
    (
        "input_identity_forged",
        lambda sc: dataclasses.replace(sc, schedule_input_identity="sha256:" + "0" * 64),
        IssueCode.METADATA_MISMATCH,
    ),
    (
        "job_dropped",
        lambda sc: dataclasses.replace(sc, jobs=sc.jobs[:-1]),
        IssueCode.JOB_SET_MISMATCH,
    ),
]


def test_valid_schedules_have_no_issues():
    for requests in (
        s.three_job_requests,
        s.shared_machine_requests,
        s.independent_requests,
        lambda: [s.timed_request()],
    ):
        jobs = s.scheduling_jobs(requests())
        assert schedule_issues(earliest_start_v1(jobs, VERSION), jobs, VERSION) == []


@pytest.mark.parametrize("name,tamper,code", TAMPERS, ids=[t[0] for t in TAMPERS])
def test_17_checker_catches_every_tampering_class(name, tamper, code):
    jobs, sched = _base()
    assert code in _codes(_redigest(tamper(sched)), jobs), name


def test_17_every_issue_code_is_exercised():
    exercised = {code for _name, _tamper, code in TAMPERS} | {IssueCode.DIGEST_MISMATCH}
    assert exercised == set(IssueCode)


def test_17_digest_only_tampering_is_caught():
    jobs, sched = _base()
    assert [
        i.code
        for i in schedule_issues(
            dataclasses.replace(sched, schedule_digest="sha256:" + "f" * 64), jobs, VERSION
        )
    ] == [IssueCode.DIGEST_MISMATCH]
    unsigned = dataclasses.replace(sched, makespan_min=67)  # tampered, digest not recomputed
    assert {IssueCode.MAKESPAN_MISMATCH, IssueCode.DIGEST_MISMATCH} <= _codes(unsigned, jobs)


def test_checker_reports_malformed_values_instead_of_raising():
    jobs, sched = _base()
    malformed = _redigest(dataclasses.replace(sched, makespan_min="68"))
    assert IssueCode.INVALID_TIME in _codes(malformed, jobs)


def test_checker_rejects_jobs_planned_under_another_model():
    jobs, sched = _base()
    assert IssueCode.METADATA_MISMATCH in {i.code for i in schedule_issues(sched, jobs, "1.1.0")}


def _hand_built(jobs, rule, placements):
    """Assemble a schedule from explicit placements (another 'rule'), with its own metrics."""
    by_key = {(j.request_id, st.index): (j, st) for j in jobs for st in j.plan.steps}
    ops = []
    for request_id, step_index, start in placements:
        job, step = by_key[(request_id, step_index)]
        machine = next(
            a.resource_id for a in job.plan.resource_assignments if a.step_index == step_index
        )
        duration = step.params["duration_min"]
        ops.append(
            ScheduledOperation(
                request_id,
                job.task_id,
                step_index,
                step.op.value,
                machine,
                duration,
                start,
                start + duration,
            )
        )
    ops.sort(key=lambda o: (o.start_min, o.request_id, o.step_index))
    makespan = max(o.end_min for o in ops)
    bound = lower_bound(jobs)
    ordered = sorted(jobs, key=lambda j: j.request_id)
    sched = MultiJobSchedule(
        scheduling_rule=rule,
        scheduling_rule_version="0.0.1",
        optimization_status=OPTIMIZATION_STATUS,
        model_assumptions=MODEL_ASSUMPTIONS,
        capability_model_version=VERSION,
        schedule_input_identity=schedule_input_identity(
            rule, "0.0.1", VERSION, [(j.request_id, j.plan.content_hash) for j in jobs]
        ),
        jobs=tuple(
            JobCompletion(
                j.request_id,
                j.task_id,
                j.plan.content_hash,
                max(o.end_min for o in ops if o.request_id == j.request_id),
            )
            for j in ordered
        ),
        operations=tuple(ops),
        makespan_min=makespan,
        lower_bound_min=bound.lower_bound_min,
        lower_bound_binding_request_ids=bound.binding_request_ids,
        lower_bound_binding_resource_ids=bound.binding_resource_ids,
        gap_to_lower_bound_min=makespan - bound.lower_bound_min,
        bound_status=(
            BoundStatus.PROVABLY_OPTIMAL
            if makespan == bound.lower_bound_min
            else BoundStatus.GAP_ABOVE_LOWER_BOUND
        ),
        schedule_digest="",
    )
    return _redigest(sched)


def test_checker_is_generator_agnostic_future_comparison_hook():
    jobs = s.scheduling_jobs(s.shared_machine_requests())
    baseline = earliest_start_v1(jobs, VERSION)
    alternative = _hand_built(
        jobs, "hand_built_reference", [(ID_B, 0, 0), (ID_A, 0, 10), (ID_B, 1, 10)]
    )
    assert schedule_issues(alternative, jobs, VERSION) == []
    assert (
        alternative.schedule_input_identity != baseline.schedule_input_identity
    )  # a different rule
    comparison = {
        sc.scheduling_rule: (sc.makespan_min, sc.lower_bound_min, sc.gap_to_lower_bound_min)
        for sc in (baseline, alternative)
    }
    assert comparison == {
        "earliest_start_v1": (120, 110, 10),
        "hand_built_reference": (110, 110, 0),
    }
    invalid = _hand_built(jobs, "hand_built_reference", [(ID_B, 0, 0), (ID_A, 0, 5), (ID_B, 1, 10)])
    assert IssueCode.MACHINE_OVERLAP in _codes(invalid, jobs)
