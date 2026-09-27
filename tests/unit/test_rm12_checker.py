"""RM12 — the independent checker under downtime (Director test V and every downtime tamper class).

As in RM11, each tamper re-computes the digest, so the checker must find the defect itself. The
checker receives the RAW downtime input and re-derives the relevant canonical downtime on its own.
"""

from __future__ import annotations

import dataclasses

import pytest

import rm11_support as s
from mini_prometheus.manufacturing_scheduling.checker import schedule_issues
from mini_prometheus.manufacturing_scheduling.earliest_start import earliest_start_v1
from mini_prometheus.manufacturing_scheduling.model import (
    MODEL_ASSUMPTIONS,
    DowntimeIssueCode,
    IssueCode,
    schedule_digest,
)
from mini_prometheus.manufacturing_scheduling.model import DowntimeInterval as D
from rm11_support import ID_A

VERSION = "1.0.0"
RAW = {"mill01": [(20, 45)]}
RELEVANT = (("mill01", (D(20, 45),)),)


def _base():
    jobs = s.scheduling_jobs(s.three_job_requests())
    return jobs, earliest_start_v1(jobs, VERSION, downtime=RELEVANT)


def _redigest(sched):
    return dataclasses.replace(sched, schedule_digest=schedule_digest(sched))


def _codes(sched, jobs, downtime=RAW):
    return {i.code for i in schedule_issues(sched, jobs, VERSION, downtime)}


def _move(sched, request_id, step_index, start, end):
    ops = tuple(
        dataclasses.replace(o, start_min=start, end_min=end)
        if (o.request_id, o.step_index) == (request_id, step_index)
        else o
        for o in sched.operations
    )
    return dataclasses.replace(sched, operations=ops)


def test_valid_downtime_schedules_have_no_issues():
    jobs, sched = _base()
    assert schedule_issues(sched, jobs, VERSION, RAW) == []


def test_V_operation_intersecting_downtime_is_rejected():
    jobs, sched = _base()
    tampered = _redigest(_move(sched, ID_A, 1, 44, 74))  # mill01 [44, 74) touches [20, 45)
    assert [i.code for i in schedule_issues(tampered, jobs, VERSION, RAW)] == [
        DowntimeIssueCode.DOWNTIME_CONFLICT
    ]
    rm11 = earliest_start_v1(jobs, VERSION)  # an RM11 schedule checked against the downtime
    assert {DowntimeIssueCode.DOWNTIME_CONFLICT, DowntimeIssueCode.DOWNTIME_MISMATCH} <= _codes(
        rm11, jobs
    )


def test_half_open_boundaries_are_not_conflicts():
    jobs = s.scheduling_jobs(s.three_job_requests())
    # A1 ends exactly at the downtime start (40); B2 starts exactly at its end (45)
    edge = earliest_start_v1(jobs, VERSION, downtime=(("mill01", (D(40, 45),)),))
    assert schedule_issues(edge, jobs, VERSION, {"mill01": [(40, 45)]}) == []
    assert [(o.start_min, o.end_min) for o in edge.operations if o.resource_id == "mill01"][:2] == [
        (10, 40),
        (45, 55),
    ]


TAMPERS = [
    (
        "downtime_split_not_canonical",
        lambda sc: dataclasses.replace(sc, downtime=(("mill01", (D(20, 30), D(30, 45))),)),
        DowntimeIssueCode.DOWNTIME_MISMATCH,
    ),
    (
        "irrelevant_machine_recorded",
        lambda sc: dataclasses.replace(sc, downtime=(*sc.downtime, ("mill02", (D(0, 5),)))),
        DowntimeIssueCode.DOWNTIME_MISMATCH,
    ),
    (
        "downtime_dropped_claims_rm11",
        lambda sc: dataclasses.replace(
            sc,
            downtime=(),
            window_aware_lower_bound_min=None,
            window_aware_lower_bound_binding_resource_ids=(),
        ),
        DowntimeIssueCode.DOWNTIME_MISMATCH,
    ),
    (
        "window_bound_corrupted",
        lambda sc: dataclasses.replace(sc, window_aware_lower_bound_min=76),
        DowntimeIssueCode.WINDOW_LOWER_BOUND_MISMATCH,
    ),
    (
        "window_binding_corrupted",
        lambda sc: dataclasses.replace(sc, window_aware_lower_bound_binding_resource_ids=()),
        DowntimeIssueCode.WINDOW_LOWER_BOUND_MISMATCH,
    ),
    (
        "gap_measured_to_rm11_bound",
        lambda sc: dataclasses.replace(sc, gap_to_lower_bound_min=103 - 52),
        IssueCode.GAP_MISMATCH,
    ),
    (
        "rm11_assumptions_under_downtime",
        lambda sc: dataclasses.replace(sc, model_assumptions=MODEL_ASSUMPTIONS),
        IssueCode.METADATA_MISMATCH,
    ),
    (
        "identity_without_downtime",
        lambda sc: dataclasses.replace(
            sc,
            schedule_input_identity=earliest_start_v1(
                s.scheduling_jobs(s.three_job_requests()), VERSION
            ).schedule_input_identity,
        ),
        IssueCode.METADATA_MISMATCH,
    ),
]


@pytest.mark.parametrize("name,tamper,code", TAMPERS, ids=[t[0] for t in TAMPERS])
def test_checker_catches_every_downtime_tampering_class(name, tamper, code):
    jobs, sched = _base()
    assert code in _codes(_redigest(tamper(sched)), jobs), name


def test_every_downtime_issue_code_is_exercised():
    exercised = {code for _n, _t, code in TAMPERS} | {DowntimeIssueCode.DOWNTIME_CONFLICT}
    assert set(DowntimeIssueCode) <= exercised


def test_invalid_raw_downtime_is_reported_not_raised():
    jobs, sched = _base()
    assert DowntimeIssueCode.DOWNTIME_MISMATCH in _codes(sched, jobs, {"mill01": [(45, 20)]})
    assert DowntimeIssueCode.DOWNTIME_MISMATCH in _codes(sched, jobs, {"mill01": [5]})


def test_checker_derives_the_canonical_form_from_raw_unsorted_input_itself():
    jobs, sched = _base()
    raw = {"mill02": [(0, 9)], "mill01": [(30, 45), D(20, 25), (25, 31)]}  # split, unsorted, extra
    assert schedule_issues(sched, jobs, VERSION, raw) == []
