"""RM12 anti-vacuity: each required downtime mutant must be caught by a NAMED gate case (a case
that raises simply counts as failed; it never counts as a pass).

Each mutant is one exact textual substitution in the REAL source (the anchor must occur exactly
once), executed as an isolated module. Required classes (Director RM12 §16): 1 downtime collision
check removed, 2 canonicalization skipped, 3 touching intervals not merged, 4 wrong boundary
semantics, 5 machine rerouting allowed, 6 append-only broken, 7 irrelevant downtime in identity,
8 relevant downtime excluded from identity, 9 window-aware bound corrupted, 10 downtime checker
removed; plus 11 canonical sorting skipped.
"""

from __future__ import annotations

import dataclasses
import pathlib
import sys
import types
from collections.abc import Callable

import pytest

import rm11_support as s
from mini_prometheus.intake.request_intake import intake
from mini_prometheus.manufacturing_scheduling import checker as real_checker
from mini_prometheus.manufacturing_scheduling import downtime as real_downtime
from mini_prometheus.manufacturing_scheduling import earliest_start as real_generator
from mini_prometheus.manufacturing_scheduling import job_set as real_job_set
from mini_prometheus.manufacturing_scheduling import lower_bound as real_bound
from mini_prometheus.manufacturing_scheduling import model as real_model
from mini_prometheus.manufacturing_scheduling.model import DowntimeInterval as D
from mini_prometheus.manufacturing_scheduling.model import (
    DowntimeIssueCode,
    JobInput,
    schedule_digest,
)
from rm11_support import ID_A
from support import FIXED_TIME

MODULES = {
    "generator": real_generator,
    "bound": real_bound,
    "checker": real_checker,
    "job_set": real_job_set,
    "downtime": real_downtime,
    "model": real_model,
}
SOURCES = {n: pathlib.Path(m.__file__).read_text(encoding="utf-8") for n, m in MODULES.items()}
_PLAN = (
    "        task, plan = planner.plan(job_input.design_input, capability_model, "
    "produced_at=produced_at)\n"
)
_REROUTE = (
    "        task, plan = planner.plan(job_input.design_input, __import__('dataclasses').replace("
    "capability_model, unavailable_resources=frozenset(canonical)), produced_at=produced_at)\n"
)
_MERGE = "            if merged and interval.start_min <= merged[-1].end_min:\n"
MUTANTS = {
    "D1_collision_check_removed": (
        "generator",
        "        if start < interval.end_min:\n",
        "        if False:\n",
    ),
    "D2_canonicalization_skipped": ("downtime", _MERGE, "            if False:\n"),
    "D3_touching_not_merged": (
        "downtime",
        _MERGE,
        "            if merged and interval.start_min < merged[-1].end_min:\n",
    ),
    "D4_wrong_boundary_semantics": (
        "generator",
        "        if start + duration <= interval.start_min:\n",
        "        if start + duration < interval.start_min:\n",
    ),
    "D5_machine_rerouting_allowed": ("job_set", _PLAN, _REROUTE),
    "D6_append_only_broken": (
        "generator",
        "        machine_free[chosen.operation.resource_id] = end\n",
        "        machine_free[chosen.operation.resource_id] = chosen.start_min\n",
    ),
    "D7_irrelevant_downtime_in_identity": (
        "downtime",
        " if machine in used\n",
        " if True\n",
    ),
    "D8_relevant_downtime_excluded_from_identity": (
        "model",
        '        view["downtime"] = downtime_view(downtime)\n',
        "        pass\n",
    ),
    "D9_window_bound_corrupted": (
        "bound",
        "        t = interval.end_min\n",
        "        t = interval.start_min\n",
    ),
    "D10_downtime_checker_removed": (
        "checker",
        "            if op.start_min < down.end_min and down.start_min < op.end_min:\n",
        "            if False:\n",
    ),
    "D11_canonical_sort_skipped": (
        "downtime",
        "        intervals = sorted(_interval(machine, raw) for raw in given)\n",
        "        intervals = [_interval(machine, raw) for raw in given]\n",
    ),
}


def _mutant(name: str) -> types.ModuleType:
    target, anchor, replacement = MUTANTS[name]
    source = SOURCES[target]
    assert source.count(anchor) == 1, f"{name}: mutation anchor must occur exactly once"
    module = types.ModuleType(f"rm12_mutant_{name}")
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


def _outcomes(parts: dict[str, types.ModuleType]) -> dict[str, bool]:
    generator, bound, checker = parts["generator"], parts["bound"], parts["checker"]
    job_set, downtime, model = parts["job_set"], parts["downtime"], parts["model"]
    version = "1.0.0"
    known = s.twin_model().resources
    three = s.scheduling_jobs(s.three_job_requests())
    twin = s.scheduling_jobs(s.three_job_requests(), s.twin_model())
    mill = (("mill01", (D(20, 45),)),)
    pairs = [(j.request_id, j.plan.content_hash) for j in three]

    def single(duration, intervals):
        (job,) = s.scheduling_jobs([s.request(ID_A, [("face_mill", duration)])])
        sched = generator.earliest_start_v1([job], version, downtime=(("mill01", intervals),))
        return (sched.operations[0].start_min, sched.operations[0].end_min)

    def clean(sched, jobs, raw):
        return real_checker.schedule_issues(sched, jobs, version, raw) == []

    def left_justified() -> bool:
        sched = generator.earliest_start_v1(three, version, downtime=mill)
        job_end: dict[str, int] = {}
        machine_end: dict[str, int] = {}
        for op in sched.operations:
            earliest = max(job_end.get(op.request_id, 0), machine_end.get(op.resource_id, 0))
            if op.resource_id == "mill01" and earliest < 45 and earliest + op.duration_min > 20:
                earliest = 45
            if op.start_min != earliest:
                return False
            job_end[op.request_id] = machine_end[op.resource_id] = op.end_min
        return True

    def tampered_conflict() -> bool:
        sched = real_generator.earliest_start_v1(three, version, downtime=mill)
        ops = tuple(
            dataclasses.replace(o, start_min=44, end_min=74)
            if (o.request_id, o.step_index) == (ID_A, 1)
            else o
            for o in sched.operations
        )
        bad = dataclasses.replace(sched, operations=ops)
        bad = dataclasses.replace(bad, schedule_digest=schedule_digest(bad))
        found = {
            i.code for i in checker.schedule_issues(bad, three, version, {"mill01": [(20, 45)]})
        }
        return DowntimeIssueCode.DOWNTIME_CONFLICT in found

    def rerouting() -> bool:
        inputs = [
            JobInput(r.request_id, intake(r, produced_at=FIXED_TIME))
            for r in s.three_job_requests()
        ]
        outcome = job_set.schedule_job_set(
            inputs, s.twin_model(), produced_at=FIXED_TIME, downtime={"mill01": [(0, 1000)]}
        )
        machines = {
            o.resource_id
            for o in outcome.schedule.operations
            if o.op in ("face_mill", "drill", "pocket_mill")
        }
        return machines == {"mill01"}

    return {
        "crossing_op_shifted": _case(lambda: single(20, (D(10, 30),)) == (30, 50)),
        "checker_clean_with_downtime": _case(
            lambda: clean(
                generator.earliest_start_v1(three, version, downtime=mill),
                three,
                {"mill01": [(20, 45)]},
            )
        ),
        "overlapping_merged": _case(
            lambda: downtime.canonical_downtime({"mill01": [(50, 100), (75, 130)]}, known)
            == {"mill01": (D(50, 130),)}
        ),
        "touching_merged": _case(
            lambda: downtime.canonical_downtime({"mill01": [(60, 120), (120, 180)]}, known)
            == {"mill01": (D(60, 180),)}
        ),
        "unsorted_input_canonical": _case(
            lambda: downtime.canonical_downtime({"mill01": [(300, 310), (10, 20)]}, known)
            == {"mill01": (D(10, 20), D(300, 310))}
        ),
        "ends_exactly_at_downtime_start": _case(lambda: single(20, (D(20, 30),)) == (0, 20)),
        "no_rerouting": _case(rerouting),
        "left_justified_append_only": _case(left_justified),
        "irrelevant_downtime_ignored": _case(
            lambda: downtime.relevant_downtime(
                {"mill01": (D(20, 45),), "mill02": (D(0, 500),)}, twin
            )
            == mill
        ),
        "relevant_downtime_changes_identity": _case(
            lambda: model.schedule_input_identity("r", "1.0.0", version, pairs, mill)
            != model.schedule_input_identity("r", "1.0.0", version, pairs, ())
        ),
        "window_bound_exact": _case(lambda: bound.available_by(52, (D(20, 45),)) == 77),
        "downtime_tamper_detected": _case(tampered_conflict),
    }


def _outcomes_with(name: str | None) -> dict[str, bool]:
    parts = dict(MODULES)
    if name is not None:
        parts[MUTANTS[name][0]] = _mutant(name)
    return _outcomes(parts)


def test_real_code_passes_every_gate_case():
    outcomes = _outcomes_with(None)
    assert all(outcomes.values()), [case for case, ok in outcomes.items() if not ok]


@pytest.mark.parametrize(
    "name,must_fail",
    [
        ("D1_collision_check_removed", "crossing_op_shifted"),
        ("D1_collision_check_removed", "checker_clean_with_downtime"),
        ("D2_canonicalization_skipped", "overlapping_merged"),
        ("D3_touching_not_merged", "touching_merged"),
        ("D4_wrong_boundary_semantics", "ends_exactly_at_downtime_start"),
        ("D5_machine_rerouting_allowed", "no_rerouting"),
        ("D6_append_only_broken", "left_justified_append_only"),
        ("D6_append_only_broken", "checker_clean_with_downtime"),
        ("D7_irrelevant_downtime_in_identity", "irrelevant_downtime_ignored"),
        ("D8_relevant_downtime_excluded_from_identity", "relevant_downtime_changes_identity"),
        ("D9_window_bound_corrupted", "window_bound_exact"),
        ("D10_downtime_checker_removed", "downtime_tamper_detected"),
        ("D11_canonical_sort_skipped", "unsorted_input_canonical"),
    ],
)
def test_mutant_is_caught_by_the_named_gate_case(name, must_fail):
    assert _outcomes_with(name)[must_fail] is False
