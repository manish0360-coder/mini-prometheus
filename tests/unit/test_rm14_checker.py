"""RM14 — the independent checker under changeover (Director test Q and checker obligations 1-14).

Each tamper re-computes the digest, so the checker must find the defect itself. The checker receives
the RAW setup-rule input and re-derives, on its own, the relevant rules and every changeover each
machine's sequence requires. Expected schedules are hand-computed in test_rm14_setup.py.
"""

from __future__ import annotations

import dataclasses

import rm11_support as s
import rm14_support as t
from mini_prometheus.manufacturing_scheduling.checker import schedule_issues
from mini_prometheus.manufacturing_scheduling.earliest_start import earliest_start_v1
from mini_prometheus.manufacturing_scheduling.model import (
    MODEL_ASSUMPTIONS,
    DowntimeIssueCode,
    IssueCode,
    ScheduledSetup,
    SetupIssueCode,
    SetupMatch,
    schedule_digest,
    schedule_input_identity,
)
from mini_prometheus.manufacturing_scheduling.model import DowntimeInterval as D
from rm11_support import ID_A, ID_B, ID_C
from rm14_support import R

VERSION = "1.0.0"
SAW_THREE = {ID_A: [("cut_stock", 10)], ID_B: [("cut_stock", 10)], ID_C: [("cut_stock", 10)]}
SAW_RAW = [("saw01", None, None, 5)]
MILL_WITHIN = {ID_A: [("face_mill", 10), ("drill", 5)], ID_B: [("pocket_mill", 20)]}
MILL_PRED = {ID_A: [("face_mill", 10)], ID_B: [("cut_stock", 30), ("pocket_mill", 10)]}
TWO_MILL = {ID_A: [("face_mill", 10)], ID_B: [("pocket_mill", 20)]}
EXPLICIT_RAW = [R("mill01", "face_mill", "pocket_mill", 3), R("mill01", None, None, 9)]


def _build(spec, relevant, downtime=()):
    jobs = s.scheduling_jobs(t.requests_of(spec))
    return jobs, earliest_start_v1(jobs, VERSION, downtime=downtime, setup_rules=relevant)


def _saw():
    return _build(SAW_THREE, (R("saw01", None, None, 5),))  # B: [10,15)+[15,25); C: [25,30)+[30,40)


def _redigest(sched):
    return dataclasses.replace(sched, schedule_digest=schedule_digest(sched))


def _codes(sched, jobs, raw, downtime=None):
    return {i.code for i in schedule_issues(sched, jobs, VERSION, downtime, raw)}


def _setup(sched, request_id, step_index, **changes):
    setups = tuple(
        dataclasses.replace(c, **changes)
        if (c.request_id, c.step_index) == (request_id, step_index)
        else c
        for c in sched.setups
    )
    return dataclasses.replace(sched, setups=setups)


def _move(sched, request_id, step_index, start, end):
    ops = tuple(
        dataclasses.replace(o, start_min=start, end_min=end)
        if (o.request_id, o.step_index) == (request_id, step_index)
        else o
        for o in sched.operations
    )
    return dataclasses.replace(sched, operations=ops)


def test_valid_changeover_schedules_have_no_issues():
    cases = [
        (*_saw(), SAW_RAW, None),
        (*_build(MILL_WITHIN, (R("mill01", None, None, 7),)), [("mill01", None, None, 7)], None),
        (*_build(MILL_PRED, (R("mill01", None, None, 8),)), [("mill01", None, None, 8)], None),
        (*_build(TWO_MILL, (EXPLICIT_RAW[1], EXPLICIT_RAW[0])), EXPLICIT_RAW, None),
        (
            *_build(
                {ID_A: [("cut_stock", 10)], ID_B: [("cut_stock", 10)]},
                (R("saw01", None, None, 5),),
                (("saw01", (D(16, 20),)),),
            ),
            SAW_RAW,
            {"saw01": [(16, 20)]},
        ),
    ]
    for jobs, sched, raw, downtime in cases:
        assert sched.setups, sched
        assert schedule_issues(sched, jobs, VERSION, downtime, raw) == []


# --- times: 1-4 -----------------------------------------------------------------------------------
def test_setup_start_shifted_earlier_breaks_the_interval_arithmetic():
    jobs, sched = _saw()
    tampered = _redigest(_setup(sched, ID_B, 0, start_min=8))
    assert SetupIssueCode.SETUP_INVALID_TIME in _codes(tampered, jobs, SAW_RAW)


def test_setup_end_shifted_later_breaks_the_interval_arithmetic():
    jobs, sched = _saw()
    tampered = _redigest(_setup(sched, ID_B, 0, end_min=16))
    assert SetupIssueCode.SETUP_INVALID_TIME in _codes(tampered, jobs, SAW_RAW)


def test_negative_setup_minutes_are_invalid():
    jobs, sched = _saw()
    tampered = _redigest(_setup(sched, ID_B, 0, start_min=16, end_min=15, duration_min=-1))
    codes = _codes(tampered, jobs, SAW_RAW)
    assert {SetupIssueCode.SETUP_INVALID_TIME, SetupIssueCode.SETUP_MISMATCH} <= codes


def test_non_integer_setup_times_are_invalid():
    jobs, sched = _saw()
    tampered = _redigest(_setup(sched, ID_B, 0, start_min=10.0))
    assert SetupIssueCode.SETUP_INVALID_TIME in _codes(tampered, jobs, SAW_RAW)


def test_a_gap_between_setup_and_processing_is_rejected():
    jobs, sched = _saw()
    shifted = _setup(sched, ID_B, 0, start_min=8, end_min=13)  # whole changeover earlier
    assert SetupIssueCode.SETUP_NOT_ADJACENT in _codes(_redigest(shifted), jobs, SAW_RAW)
    later = _move(sched, ID_B, 0, 16, 26)  # processing starts one minute after the changeover
    assert SetupIssueCode.SETUP_NOT_ADJACENT in _codes(_redigest(later), jobs, SAW_RAW)


# --- occupancy, downtime, predecessor: 5, 6, 9 ----------------------------------------------------
def test_setup_overlapping_another_operation_is_rejected():
    jobs, sched = _saw()
    tampered = _move(_setup(sched, ID_C, 0, start_min=22, end_min=27), ID_C, 0, 27, 37)
    codes = _codes(_redigest(tampered), jobs, SAW_RAW)
    assert (
        SetupIssueCode.SETUP_OVERLAP in codes
    )  # C's changeover [22, 27) overlaps B's cut [15, 25)
    assert IssueCode.MACHINE_OVERLAP not in codes  # the processing intervals alone do not overlap


def test_setup_intersecting_downtime_is_rejected():
    spec = {ID_A: [("cut_stock", 10)], ID_B: [("cut_stock", 10)]}
    jobs, sched = _build(spec, (R("saw01", None, None, 5),), (("saw01", (D(16, 20),)),))
    tampered = _move(_setup(sched, ID_B, 0, start_min=15, end_min=20), ID_B, 0, 20, 30)
    codes = _codes(_redigest(tampered), jobs, SAW_RAW, {"saw01": [(16, 20)]})
    assert SetupIssueCode.SETUP_DOWNTIME_CONFLICT in codes
    assert DowntimeIssueCode.DOWNTIME_CONFLICT not in codes  # the cut [20, 30) itself is clear


def test_setup_before_the_jobs_predecessor_completes_is_rejected():
    jobs, sched = _build(MILL_PRED, (R("mill01", None, None, 8),))
    tampered = _move(_setup(sched, ID_B, 1, start_min=22, end_min=30), ID_B, 1, 30, 40)
    codes = _codes(_redigest(tampered), jobs, [("mill01", None, None, 8)])
    assert SetupIssueCode.SETUP_BEFORE_PREDECESSOR in codes  # B's cut ends at 30
    assert IssueCode.JOB_ORDER_VIOLATION not in codes  # the pocket_mill itself starts at 30


# --- which changeovers, with which minutes: 7, 8, 10-12 -------------------------------------------
def test_missing_setup_is_rejected():
    jobs, sched = _saw()
    tampered = dataclasses.replace(sched, setups=sched.setups[1:])
    assert SetupIssueCode.SETUP_MISSING in _codes(_redigest(tampered), jobs, SAW_RAW)


def test_fabricated_setups_are_rejected():
    jobs, sched = _build(MILL_WITHIN, (R("mill01", None, None, 7),))
    same_job = ScheduledSetup(
        ID_A, 1, "mill01", ID_A, "face_mill", "drill", SetupMatch.MACHINE_DEFAULT, 0, 10, 10
    )
    first_op = ScheduledSetup(
        ID_A, 0, "mill01", ID_B, "pocket_mill", "face_mill", SetupMatch.MACHINE_DEFAULT, 0, 0, 0
    )
    for fake in (same_job, first_op):
        tampered = dataclasses.replace(
            sched,
            setups=tuple(
                sorted(
                    (*sched.setups, fake), key=lambda c: (c.start_min, c.request_id, c.step_index)
                )
            ),
        )
        assert SetupIssueCode.SETUP_UNEXPECTED in _codes(
            _redigest(tampered), jobs, [("mill01", None, None, 7)]
        )


def test_setup_on_a_machine_without_declared_rules_is_rejected():
    jobs, sched = _saw()
    plain = earliest_start_v1(jobs, VERSION)
    fake = ScheduledSetup(
        ID_B, 0, "saw01", ID_A, "cut_stock", "cut_stock", SetupMatch.MACHINE_DEFAULT, 0, 10, 10
    )
    tampered = _redigest(dataclasses.replace(plain, setups=(fake,)))
    assert SetupIssueCode.SETUP_UNEXPECTED in _codes(tampered, jobs, None)


def test_wrong_minutes_machine_or_predecessor_are_rejected():
    jobs, sched = _saw()
    for changes in (
        {"duration_min": 4, "start_min": 11},  # consistent interval, wrong minutes
        {"resource_id": "mill01"},
        {"prev_request_id": ID_C},
        {"prev_op": "drill"},
        {"curr_op": "drill"},
    ):
        tampered = _redigest(_setup(sched, ID_B, 0, **changes))
        assert SetupIssueCode.SETUP_MISMATCH in _codes(tampered, jobs, SAW_RAW), changes


def test_default_applied_where_the_transition_rule_governs_is_rejected():
    jobs, sched = _build(TWO_MILL, (EXPLICIT_RAW[1], EXPLICIT_RAW[0]))
    label_only = _setup(sched, ID_B, 0, matched=SetupMatch.MACHINE_DEFAULT)
    assert SetupIssueCode.SETUP_MISMATCH in _codes(_redigest(label_only), jobs, EXPLICIT_RAW)
    as_default = _move(
        _setup(sched, ID_B, 0, matched=SetupMatch.MACHINE_DEFAULT, duration_min=9, end_min=19),
        ID_B,
        0,
        19,
        39,
    )
    assert SetupIssueCode.SETUP_MISMATCH in _codes(_redigest(as_default), jobs, EXPLICIT_RAW)


def test_a_used_transition_without_any_rule_is_unspecified():
    jobs, sched = _build(MILL_WITHIN, (R("mill01", None, None, 7),))  # drill -> pocket_mill used
    raw = [("mill01", "face_mill", "pocket_mill", 3)]
    assert SetupIssueCode.UNSPECIFIED_SETUP_TRANSITION in _codes(sched, jobs, raw)


def test_duplicate_setup_records_are_rejected():
    jobs, sched = _saw()
    tampered = _redigest(dataclasses.replace(sched, setups=(sched.setups[0], *sched.setups)))
    assert SetupIssueCode.SETUP_MISMATCH in _codes(tampered, jobs, SAW_RAW)


# --- rules, metadata, identity, ordering: 13, 14 --------------------------------------------------
def test_recorded_rules_must_be_the_relevant_canonical_input():
    jobs, sched = _saw()
    dropped = _redigest(dataclasses.replace(sched, setup_rules=()))
    assert SetupIssueCode.SETUP_RULES_MISMATCH in _codes(dropped, jobs, SAW_RAW)
    padded = (R("mill01", None, None, 1), *sched.setup_rules)  # mill01 is unused: irrelevant
    extra = _redigest(dataclasses.replace(sched, setup_rules=padded))
    assert SetupIssueCode.SETUP_RULES_MISMATCH in _codes(extra, jobs, SAW_RAW)


def test_invalid_raw_rules_are_reported():
    jobs, sched = _saw()
    for raw in ([("saw01", None, None, -5)], [("saw01", None, None)], [SAW_RAW[0], SAW_RAW[0]]):
        assert SetupIssueCode.SETUP_RULES_MISMATCH in _codes(sched, jobs, raw)


def test_a_schedule_that_ignores_declared_rules_is_rejected():
    jobs, _ = _saw()
    plain = earliest_start_v1(jobs, VERSION)  # no changeover at all
    codes = _codes(plain, jobs, SAW_RAW)
    assert {SetupIssueCode.SETUP_RULES_MISMATCH, SetupIssueCode.SETUP_MISSING} <= codes


def test_setup_metadata_and_identity_are_checked():
    jobs, sched = _saw()
    wrong_model = _redigest(dataclasses.replace(sched, model_assumptions=MODEL_ASSUMPTIONS))
    assert IssueCode.METADATA_MISMATCH in _codes(wrong_model, jobs, SAW_RAW)
    identity = schedule_input_identity(
        sched.scheduling_rule,
        sched.scheduling_rule_version,
        VERSION,
        [(j.request_id, j.plan.content_hash) for j in jobs],
    )  # computed without the setup rules
    wrong_identity = _redigest(dataclasses.replace(sched, schedule_input_identity=identity))
    assert IssueCode.METADATA_MISMATCH in _codes(wrong_identity, jobs, SAW_RAW)


def test_setups_must_be_in_canonical_order():
    jobs, sched = _saw()
    tampered = _redigest(dataclasses.replace(sched, setups=tuple(reversed(sched.setups))))
    assert IssueCode.NON_CANONICAL_ORDER in _codes(tampered, jobs, SAW_RAW)


def test_the_digest_covers_the_changeovers():
    jobs, sched = _saw()
    tampered = _setup(sched, ID_B, 0, prev_op="drill")  # digest NOT recomputed
    assert IssueCode.DIGEST_MISMATCH in _codes(tampered, jobs, SAW_RAW)
