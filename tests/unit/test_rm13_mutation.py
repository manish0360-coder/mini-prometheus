"""RM13 anti-vacuity: every required mutant of the opt-in rule is caught by a NAMED gate case (a
case that raises counts as failed, never as passed). One exact substitution in the REAL source each
(the anchor must occur exactly once), executed as an isolated module.

Required (Director RM13): M1 tie-break replaced by request_id; M2 candidate duration omitted; M3
later operations omitted; M4 downtime included in remaining work; M5 tie-break applied before the
earliest-start comparison; M6 remaining-work comparison reversed; M7 request_id fallback removed;
M8 default rule changed to the new rule.
"""

from __future__ import annotations

import pathlib
import sys
import types
from collections.abc import Callable

import pytest

import rm11_support as s
from mini_prometheus.intake.request_intake import intake
from mini_prometheus.manufacturing_constraints.capability_model import default_model
from mini_prometheus.manufacturing_scheduling import earliest_start as real_generator
from mini_prometheus.manufacturing_scheduling import job_set as real_job_set
from mini_prometheus.manufacturing_scheduling.model import DowntimeInterval as D
from mini_prometheus.manufacturing_scheduling.model import JobInput
from rm11_support import FIXED_TIME, ID_A, ID_B

MODULES = {"generator": real_generator, "job_set": real_job_set}
SOURCES = {n: pathlib.Path(m.__file__).read_text(encoding="utf-8") for n, m in MODULES.items()}
_PRIORITY = (
    "            priority = -sum(o.duration_min for o in remaining_ops) "
    "if most_work_remaining else 0\n"
)
_REMAINING = "            remaining_ops = ops[next_step[job.request_id] :]\n"
_KEY = (
    "    return (candidate.start_min, candidate.priority, candidate.request_id, "
    "candidate.step_index)\n"
)
MUTANTS = {
    "M1_tie_break_replaced_by_request_id": ("generator", _PRIORITY, "            priority = 0\n"),
    "M2_candidate_duration_omitted": (
        "generator",
        _REMAINING,
        "            remaining_ops = ops[next_step[job.request_id] + 1 :]\n",
    ),
    "M3_later_operations_omitted": (
        "generator",
        _REMAINING,
        "            remaining_ops = [operation]\n",
    ),
    "M4_downtime_included_in_remaining_work": (
        "generator",
        _PRIORITY,
        "            priority = -sum(o.duration_min + sum(i.end_min - i.start_min for i in "
        "blocked.get(o.resource_id, ())) for o in remaining_ops) if most_work_remaining else 0\n",
    ),
    "M5_tie_break_before_earliest_start": (
        "generator",
        _KEY,
        "    return (candidate.priority, candidate.start_min, candidate.request_id, "
        "candidate.step_index)\n",
    ),
    "M6_remaining_work_comparison_reversed": ("generator", "priority = -sum(", "priority = sum("),
    "M7_request_id_fallback_removed": (
        "generator",
        _KEY,
        "    return (candidate.start_min, candidate.priority, candidate.step_index)\n",
    ),
    "M8_default_rule_changed": (
        "job_set",
        "    rule: str = SCHEDULING_RULE,\n",
        "    rule: str = SCHEDULING_RULE_MOST_WORK_REMAINING,\n",
    ),
}


def _mutant(name: str) -> types.ModuleType:
    target, anchor, replacement = MUTANTS[name]
    source = SOURCES[target]
    assert source.count(anchor) == 1, f"{name}: mutation anchor must occur exactly once"
    module = types.ModuleType(f"rm13_mutant_{name}")
    sys.modules[module.__name__] = module  # dataclasses resolve string annotations here
    try:
        exec(compile(source.replace(anchor, replacement), module.__name__, "exec"), module.__dict__)
    finally:
        del sys.modules[module.__name__]
    return module


def _case(check: Callable[[], bool]) -> bool:
    try:
        return bool(check())
    except Exception:
        return False


def _outcomes(generator: types.ModuleType, job_set: types.ModuleType) -> dict[str, bool]:
    def first_saw(requests, downtime=()):
        jobs = s.scheduling_jobs(requests)
        sched = generator.earliest_start_v1_most_work_remaining(jobs, "1.0.0", downtime=downtime)
        saw = [o for o in sched.operations if o.resource_id == "saw01"]
        return (saw[0].request_id, saw[0].start_min, saw[0].end_min)

    def later_start_never_preferred() -> bool:
        jobs = s.scheduling_jobs(
            [
                s.request(ID_A, [("face_mill", 10)]),
                s.request(ID_B, [("cut_stock", 5), ("face_mill", 100)]),
            ]
        )
        sched = generator.earliest_start_v1_most_work_remaining(jobs, "1.0.0")
        first_mill = min(
            (o for o in sched.operations if o.resource_id == "mill01"), key=lambda o: o.start_min
        )
        return (first_mill.request_id, first_mill.start_min) == (ID_A, 0)

    def default_rule() -> bool:
        inputs = [
            JobInput(r.request_id, intake(r, produced_at=FIXED_TIME))
            for r in s.three_job_requests()
        ]
        return (
            job_set.schedule_job_set(inputs, default_model()).schedule.scheduling_rule
            == "earliest_start_v1"
        )

    return {
        "tie_uses_remaining_work": _case(
            lambda: first_saw(
                [
                    s.request(ID_A, [("cut_stock", 10)]),
                    s.request(ID_B, [("cut_stock", 10), ("face_mill", 100)]),
                ]
            )
            == (ID_B, 0, 10)
        ),
        "remaining_work_includes_candidate": _case(
            lambda: first_saw(
                [
                    s.request(ID_A, [("cut_stock", 30)]),
                    s.request(ID_B, [("cut_stock", 10), ("deburr", 15)]),
                ]
            )
            == (ID_A, 0, 30)
        ),
        "remaining_work_includes_later_ops": _case(
            lambda: first_saw(
                [
                    s.request(ID_A, [("cut_stock", 10)]),
                    s.request(ID_B, [("cut_stock", 5), ("deburr", 3), ("inspect", 3)]),
                ]
            )
            == (ID_B, 0, 5)
        ),
        "remaining_work_excludes_downtime": _case(
            lambda: first_saw(
                [
                    s.request(ID_A, [("cut_stock", 10), ("deburr", 1)]),
                    s.request(ID_B, [("cut_stock", 5), ("inspect", 5)]),
                ],
                (("cmm01", (D(500, 520),)),),
            )
            == (ID_A, 0, 10)
        ),
        "later_start_never_preferred": _case(later_start_never_preferred),
        "equal_work_falls_back_to_request_id": _case(
            lambda: first_saw(
                [s.request(ID_B, [("cut_stock", 10)]), s.request(ID_A, [("cut_stock", 10)])]
            )
            == (ID_A, 0, 10)
        ),
        "default_rule_is_earliest_start_v1": _case(default_rule),
    }


def _outcomes_with(name: str | None) -> dict[str, bool]:
    parts = dict(MODULES)
    if name is not None:
        parts[MUTANTS[name][0]] = _mutant(name)
    return _outcomes(parts["generator"], parts["job_set"])


def test_real_code_passes_every_gate_case():
    outcomes = _outcomes_with(None)
    assert all(outcomes.values()), [case for case, ok in outcomes.items() if not ok]


@pytest.mark.parametrize(
    "name,must_fail",
    [
        ("M1_tie_break_replaced_by_request_id", "tie_uses_remaining_work"),
        ("M2_candidate_duration_omitted", "remaining_work_includes_candidate"),
        ("M3_later_operations_omitted", "remaining_work_includes_later_ops"),
        ("M4_downtime_included_in_remaining_work", "remaining_work_excludes_downtime"),
        ("M5_tie_break_before_earliest_start", "later_start_never_preferred"),
        ("M6_remaining_work_comparison_reversed", "tie_uses_remaining_work"),
        ("M7_request_id_fallback_removed", "equal_work_falls_back_to_request_id"),
        ("M8_default_rule_changed", "default_rule_is_earliest_start_v1"),
    ],
)
def test_mutant_is_caught_by_the_named_gate_case(name, must_fail):
    assert _outcomes_with(name)[must_fail] is False
