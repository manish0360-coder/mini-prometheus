"""RM13 — opt-in rule earliest_start_v1_most_work_remaining (ADR-0016).

Numbers follow the Director's RM13 test list (16 is in test_rm13_regression_corpus.py). The rule is
earliest_start_v1 except that EXACT earliest-start ties go to the job with the most remaining
processing work (candidate + later unscheduled operations, RM10 durations only), then request_id,
then step_index. Expected placements are hand-computed in the spec (§6).
"""

from __future__ import annotations

import itertools

import pytest

import rm11_support as s
from mini_prometheus.intake.request_intake import intake
from mini_prometheus.manufacturing_constraints.capability_model import default_model
from mini_prometheus.manufacturing_scheduling.checker import schedule_issues
from mini_prometheus.manufacturing_scheduling.earliest_start import (
    _Candidate,
    _decision_key,
    _Operation,
)
from mini_prometheus.manufacturing_scheduling.job_set import schedule_job_set
from mini_prometheus.manufacturing_scheduling.model import (
    SCHEDULING_RULE,
    SCHEDULING_RULE_MOST_WORK_REMAINING,
    SELECTABLE_RULES,
    JobInput,
    UnknownSchedulingRuleError,
)
from mini_prometheus.orchestration.schedule_runner import schedule_requests
from rm11_support import FIXED_TIME, ID_A, ID_B, ID_C

MW = SCHEDULING_RULE_MOST_WORK_REMAINING
LETTER = {ID_A: "A", ID_B: "B", ID_C: "C"}
MILL_OPS = ("face_mill", "drill", "pocket_mill")


def _run(requests, downtime=None, rule=MW, model=None, produced_at=FIXED_TIME):
    return schedule_requests(
        requests, capability_model=model, produced_at=produced_at, downtime=downtime, rule=rule
    ).schedule


def _placements(sched):
    return [
        (LETTER[o.request_id], o.step_index, o.resource_id, o.start_min, o.end_min)
        for o in sched.operations
    ]


def test_01_exact_start_tie_goes_to_the_job_with_most_remaining_work():
    requests = [
        s.request(ID_A, [("cut_stock", 10)]),
        s.request(ID_B, [("cut_stock", 10), ("face_mill", 100)]),
    ]
    sched = _run(requests)
    assert _placements(sched) == [
        ("B", 0, "saw01", 0, 10),
        ("A", 0, "saw01", 10, 20),
        ("B", 1, "mill01", 10, 110),
    ]
    assert sched.makespan_min == 110 and sched.scheduling_rule == MW
    baseline = _run(requests, rule=SCHEDULING_RULE)
    assert baseline.makespan_min == 120  # the RM11 worked example; the default is unchanged


def test_02_a_later_starting_candidate_is_never_chosen_over_an_earlier_one():
    # A: mill 10 (little work). B: saw 5 -> mill 100 (much more work) — B's mill op is ready at 5.
    sched = _run(
        [
            s.request(ID_A, [("face_mill", 10)]),
            s.request(ID_B, [("cut_stock", 5), ("face_mill", 100)]),
        ]
    )
    assert _placements(sched) == [
        ("A", 0, "mill01", 0, 10),
        ("B", 0, "saw01", 0, 5),
        ("B", 1, "mill01", 10, 110),
    ]


def test_03_remaining_work_includes_the_candidate_itself():
    # A: saw 30 (remaining 30) vs B: saw 10 -> deburr 15 (remaining 25): A goes first
    sched = _run(
        [s.request(ID_A, [("cut_stock", 30)]), s.request(ID_B, [("cut_stock", 10), ("deburr", 15)])]
    )
    assert _placements(sched)[:2] == [("A", 0, "saw01", 0, 30), ("B", 0, "saw01", 30, 40)]


def test_04_remaining_work_includes_every_later_unscheduled_operation():
    # A: saw 10 (10) vs B: saw 5 -> deburr 3 -> inspect 3 (11): B goes first
    sched = _run(
        [
            s.request(ID_A, [("cut_stock", 10)]),
            s.request(ID_B, [("cut_stock", 5), ("deburr", 3), ("inspect", 3)]),
        ]
    )
    assert _placements(sched) == [
        ("B", 0, "saw01", 0, 5),
        ("A", 0, "saw01", 5, 15),
        ("B", 1, "bench01", 5, 8),
        ("B", 2, "cmm01", 8, 11),
    ]


def test_05_remaining_work_excludes_downtime_and_waiting():
    # A: saw 10 -> deburr 1 (11) vs B: saw 5 -> inspect 5 (10). cmm01 is down on [500, 520): if
    # that downtime counted as work, B (10 + 20) would wrongly go first.
    sched = _run(
        [
            s.request(ID_A, [("cut_stock", 10), ("deburr", 1)]),
            s.request(ID_B, [("cut_stock", 5), ("inspect", 5)]),
        ],
        {"cmm01": [(500, 520)]},
    )
    assert sched.scheduling_rule == "earliest_start_v1_most_work_remaining_downtime"
    assert _placements(sched) == [
        ("A", 0, "saw01", 0, 10),
        ("A", 1, "bench01", 10, 11),
        ("B", 0, "saw01", 10, 15),
        ("B", 1, "cmm01", 15, 20),
    ]


def test_06_equal_remaining_work_falls_back_to_request_id_whatever_the_input_order():
    for order in ([ID_B, ID_A], [ID_A, ID_B]):
        sched = _run([s.request(rid, [("cut_stock", 10)]) for rid in order])
        assert _placements(sched) == [("A", 0, "saw01", 0, 10), ("B", 0, "saw01", 10, 20)]


def test_07_request_id_tie_falls_back_to_step_index():
    op = _Operation(0, "drill", "mill01", 5)
    later = _Candidate(0, "x", 3, "t", op, -5)
    earlier = _Candidate(0, "x", 1, "t", op, -5)
    other_job = _Candidate(0, "y", 0, "t", op, -5)
    more_work = _Candidate(0, "z", 9, "t", op, -6)
    later_start = _Candidate(1, "a", 0, "t", op, -100)
    order = sorted([later_start, other_job, later, more_work, earlier], key=_decision_key)
    assert order == [more_work, earlier, later, other_job, later_start]


def test_08_input_permutations_give_a_byte_identical_schedule():
    reference = _run(s.three_job_requests(), {"mill01": [(20, 45)]})
    for requests in itertools.permutations(s.three_job_requests()):
        assert _run(list(requests), {"mill01": [(20, 45)]}) == reference


def test_09_one_job_output_is_rm10_equivalent():
    sched = _run([s.timed_request()])
    assert [(o.start_min, o.end_min) for o in sched.operations] == s.TIMED_TIMELINE
    assert sched.makespan_min == 108 and sched.scheduling_rule == MW


def test_10_rm12_downtime_semantics_are_preserved():
    sched = _run(s.three_job_requests(), {"mill01": [(20, 45)]})
    assert sched.scheduling_rule == "earliest_start_v1_most_work_remaining_downtime"
    assert _placements(sched) == [
        ("A", 0, "saw01", 0, 10),
        ("B", 0, "saw01", 10, 15),
        ("B", 1, "lathe01", 15, 35),
        ("C", 0, "saw01", 15, 23),
        ("A", 1, "mill01", 45, 75),
        ("A", 2, "cmm01", 75, 80),
        ("C", 1, "mill01", 75, 87),
        ("B", 2, "mill01", 87, 97),
        ("C", 2, "bench01", 87, 93),
        ("B", 3, "cmm01", 97, 102),
    ]
    mill = [o for o in sched.operations if o.resource_id == "mill01"]
    assert all(o.end_min <= 20 or o.start_min >= 45 for o in mill)
    assert (sched.window_aware_lower_bound_min, sched.gap_to_lower_bound_min) == (77, 25)


def test_11_no_rerouting_to_an_idle_capable_machine():
    sched = _run(s.three_job_requests(), {"mill01": [(0, 1000)]}, model=s.twin_model())
    mill = [o for o in sched.operations if o.op in MILL_OPS]
    assert {o.resource_id for o in mill} == {"mill01"} and min(o.start_min for o in mill) >= 1000


def test_12_rule_identity_differs_only_for_the_opt_in_rule():
    default = _run(s.three_job_requests(), rule=None)
    explicit = _run(s.three_job_requests(), rule=SCHEDULING_RULE)
    opt_in = _run(s.three_job_requests())
    assert default == explicit and default.scheduling_rule == SCHEDULING_RULE
    assert opt_in.schedule_input_identity != default.schedule_input_identity
    assert opt_in.schedule_digest != default.schedule_digest
    single_default = _run([s.timed_request()], rule=None)
    single_opt_in = _run([s.timed_request()])  # identical placements, different rule identity
    assert [(o.start_min, o.end_min) for o in single_opt_in.operations] == [
        (o.start_min, o.end_min) for o in single_default.operations
    ]
    assert single_opt_in.schedule_input_identity != single_default.schedule_input_identity


def test_13_default_rule_remains_earliest_start_v1():
    assert SELECTABLE_RULES == ("earliest_start_v1", "earliest_start_v1_most_work_remaining")
    assert schedule_requests(
        s.three_job_requests(), produced_at=FIXED_TIME
    ).schedule.scheduling_rule == ("earliest_start_v1")
    inputs = [
        JobInput(r.request_id, intake(r, produced_at=FIXED_TIME)) for r in s.three_job_requests()
    ]
    assert schedule_job_set(inputs, default_model()).schedule.scheduling_rule == "earliest_start_v1"


def test_14_the_independent_checker_accepts_the_new_rules_schedules():
    for requests, downtime in (
        (s.three_job_requests(), None),
        (s.three_job_requests(), {"mill01": [(20, 45)]}),
        (s.shared_machine_requests(), {"saw01": [(0, 5)]}),
    ):
        sched = _run(requests, downtime)
        jobs = s.scheduling_jobs(requests)
        assert schedule_issues(sched, jobs, "1.0.0", downtime) == []


def test_15_repeated_execution_is_deterministic():
    first = _run(s.three_job_requests(), {"mill01": [(20, 45)]})
    again = _run(
        s.three_job_requests(), {"mill01": [(20, 45)]}, produced_at="2031-01-01T00:00:00+00:00"
    )
    assert first == again and first.schedule_digest == again.schedule_digest


@pytest.mark.parametrize("rule", ["earliest_start_v1_downtime", "earliest_start_v2", ""])
def test_unknown_rules_are_rejected_before_planning(rule):
    with pytest.raises(UnknownSchedulingRuleError, match="unknown scheduling rule"):
        schedule_requests([s.request(ID_A, [("cut_stock", None)])], rule=rule)
