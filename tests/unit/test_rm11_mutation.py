"""RM11 anti-vacuity: mutants of the scheduler, bound calculator, checker and job-set gate must
each be caught by a NAMED RM11 gate case (not by an escaping exception — a case that raises simply
counts as failed).

Each mutant is one exact textual substitution in the REAL source (the anchor must occur exactly
once), executed as an isolated module. The Director's required classes: machine no-overlap removed
(R1, C1), job precedence violated (R2), duration altered (R3), operation start shifted (R4),
operation duplicated (R5), operation omitted (R6), makespan corrupted (R7), tie-break changed (R8),
scheduler depending on argument order (R9), lower bound corrupted (R10); plus checker (C2, C3) and
job-set gate (J1-J3) mutants.
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
from mini_prometheus.manufacturing_constraints.capability_model import default_model
from mini_prometheus.manufacturing_scheduling import checker as real_checker
from mini_prometheus.manufacturing_scheduling import earliest_start as real_generator
from mini_prometheus.manufacturing_scheduling import job_set as real_job_set
from mini_prometheus.manufacturing_scheduling import lower_bound as real_bound
from mini_prometheus.manufacturing_scheduling.model import (
    IssueCode,
    JobInput,
    RefusalReason,
    ScheduleIntegrityError,
    ScheduleStatus,
    schedule_digest,
)
from rm11_support import ID_A, ID_B, ID_C
from support import FIXED_TIME

MODULES = {
    "generator": real_generator,
    "bound": real_bound,
    "checker": real_checker,
    "job_set": real_job_set,
}
SOURCES = {
    name: pathlib.Path(module.__file__).read_text(encoding="utf-8")
    for name, module in MODULES.items()
}
_START = (
    "            start = max(job_ready[job.request_id], "
    "machine_free.get(operation.resource_id, 0))\n"
)
_CHOOSE = "        chosen = min(candidates, key=_decision_key)\n"
MUTANTS = {
    "R1_machine_no_overlap_removed": (
        "generator",
        _START,
        "            start = job_ready[job.request_id]\n",
    ),
    "R2_job_precedence_violated": (
        "generator",
        _START,
        "            start = machine_free.get(operation.resource_id, 0)\n",
    ),
    "R3_duration_altered": (
        "generator",
        "(step.params or {})[DURATION_PARAM]",
        "(step.params or {})[DURATION_PARAM] + 1",
    ),
    "R4_operation_start_shifted": (
        "generator",
        "        start = chosen.start_min\n",
        "        start = chosen.start_min + 1\n",
    ),
    "R5_operation_duplicated": (
        "generator",
        "    return operations\n",
        "    return operations + operations[-1:]\n",
    ),
    "R6_operation_omitted": (
        "generator",
        "        for step in job.plan.steps\n",
        "        for step in job.plan.steps[:-1]\n",
    ),
    "R7_makespan_corrupted": (
        "generator",
        "    makespan = max(op.end_min for op in placed)\n",
        "    makespan = placed[-1].end_min\n",
    ),
    "R8_tie_break_changed": (
        "generator",
        _CHOOSE,
        "        chosen = max(candidates, key=lambda c: (-c.start_min, c.request_id, "
        "-c.step_index))\n",
    ),
    "R9_depends_on_argument_order": (
        "generator",
        _CHOOSE,
        "        chosen = min(candidates, key=lambda c: c.start_min)\n",
    ),
    "R10_lower_bound_corrupted": (
        "bound",
        "    value = max(max(job_totals.values()), max(machine_loads.values()))\n",
        "    value = max(job_totals.values())\n",
    ),
    "C1_checker_overlap_check_removed": (
        "checker",
        "            if holder is not None and op.start_min < holder.end_min:\n",
        "            if False:\n",
    ),
    "C2_checker_closed_intervals": (
        "checker",
        "op.start_min < holder.end_min",
        "op.start_min <= holder.end_min",
    ),
    "C3_checker_missing_check_removed": (
        "checker",
        "        if key not in seen:\n",
        "        if False:\n",
    ),
    "J1_manufacturable_check_removed": (
        "job_set",
        "    if verdict.status != MANUFACTURABLE:\n",
        "    if False:\n",
    ),
    "J2_duplicate_check_removed": ("job_set", "        if count > 1:\n", "        if False:\n"),
    "J3_integrity_gate_removed": ("job_set", "    if issues:\n", "    if False:\n"),
}


def _mutant(name: str) -> types.ModuleType:
    target, anchor, replacement = MUTANTS[name]
    source = SOURCES[target]
    assert source.count(anchor) == 1, f"{name}: mutation anchor must occur exactly once"
    module = types.ModuleType(f"rm11_mutant_{name}")
    sys.modules[module.__name__] = (
        module  # dataclasses resolve string annotations through sys.modules
    )
    try:
        exec(compile(source.replace(anchor, replacement), module.__name__, "exec"), module.__dict__)
    finally:
        del sys.modules[module.__name__]
    return module


def _job_inputs(requests):
    return [JobInput(r.request_id, intake(r, produced_at=FIXED_TIME)) for r in requests]


def _corrupt_generator(jobs, version):
    """A faulty generator for the gate case: one end minute off, digest re-signed."""
    sched = real_generator.earliest_start_v1(jobs, version)
    ops = list(sched.operations)
    ops[0] = dataclasses.replace(ops[0], end_min=ops[0].end_min + 1)
    bad = dataclasses.replace(sched, operations=tuple(ops))
    return dataclasses.replace(bad, schedule_digest=schedule_digest(bad))


def _case(check: Callable[[], bool]) -> bool:
    try:
        return bool(check())
    except Exception:
        return False


def _outcomes(generator, bound, checker, job_set) -> dict[str, bool]:
    version = default_model().version
    three = s.scheduling_jobs(s.three_job_requests())
    shared = s.scheduling_jobs(s.shared_machine_requests())
    independent = s.scheduling_jobs(s.independent_requests())
    (timed,) = s.scheduling_jobs([s.timed_request()])

    def gen(jobs):
        return generator.earliest_start_v1(jobs, version)

    def real_issues(sched, jobs):
        return real_checker.schedule_issues(sched, jobs, version)

    def gate_raises() -> bool:
        original = job_set.earliest_start_v1
        job_set.earliest_start_v1 = _corrupt_generator
        try:
            job_set.schedule_job_set(_job_inputs(s.three_job_requests()), default_model())
        except ScheduleIntegrityError:
            return True
        finally:
            job_set.earliest_start_v1 = original
        return False

    real_three = real_generator.earliest_start_v1(three, version)
    overlap = dataclasses.replace(
        real_three,
        operations=tuple(
            dataclasses.replace(o, start_min=12, end_min=20)
            if (o.request_id, o.step_index) == (ID_C, 0)
            else o
            for o in real_three.operations
        ),
    )
    omission = dataclasses.replace(real_three, operations=real_three.operations[:-1])
    titanium = [
        *s.three_job_requests()[:2],
        s.request(ID_C, [("cut_stock", 8), ("deburr", 6)], material="Titanium Grade 5"),
    ]
    duplicate = [s.request(ID_A, [("cut_stock", 10)]), s.request(ID_A, [("face_mill", 20)])]
    return {
        "one_job_equals_rm10": _case(
            lambda: [(o.start_min, o.end_min) for o in gen([timed]).operations] == s.TIMED_TIMELINE
            and gen([timed]).makespan_min == 108
        ),
        "shared_machine_exact": _case(
            lambda: s.placements(gen(shared))
            == [
                (ID_A, 0, "cut_stock", "saw01", 0, 10),
                (ID_B, 0, "cut_stock", "saw01", 10, 20),
                (ID_B, 1, "face_mill", "mill01", 20, 120),
            ]
        ),
        "three_job_exact": _case(lambda: s.placements(gen(three)) == s.THREE_JOB_SCHEDULE),
        "checker_clean": _case(
            lambda: all(real_issues(gen(jobs), jobs) == [] for jobs in (three, shared, independent))
        ),
        "independent_makespan": _case(lambda: gen(independent).makespan_min == 100),
        "tie_to_lower_request_id": _case(lambda: gen(shared).operations[0].request_id == ID_A),
        "argument_order_irrelevant": _case(
            lambda: gen(list(reversed(shared))) == gen(shared)
            and gen(list(reversed(three))) == gen(three)
        ),
        "lower_bound_exact": _case(
            lambda: (
                bound.lower_bound(three).lower_bound_min,
                bound.lower_bound(three).binding_resource_ids,
            )
            == (52, ("mill01",))
        ),
        "overlap_tamper_detected": _case(
            lambda: IssueCode.MACHINE_OVERLAP
            in {i.code for i in checker.schedule_issues(overlap, three, version)}
        ),
        "touching_intervals_accepted": _case(
            lambda: checker.schedule_issues(real_three, three, version) == []
        ),
        "omission_tamper_detected": _case(
            lambda: IssueCode.MISSING_OPERATION
            in {i.code for i in checker.schedule_issues(omission, three, version)}
        ),
        "non_manufacturable_refused": _case(
            lambda: (
                lambda o: o.status == ScheduleStatus.NOT_SCHEDULED
                and [r.reason for r in o.refusals] == [RefusalReason.JOB_NOT_MANUFACTURABLE]
            )(job_set.schedule_job_set(_job_inputs(titanium), default_model()))
        ),
        "duplicate_refused": _case(
            lambda: (
                lambda o: o.status == ScheduleStatus.NOT_SCHEDULED
                and [r.reason for r in o.refusals] == [RefusalReason.DUPLICATE_REQUEST_ID]
            )(job_set.schedule_job_set(_job_inputs(duplicate), default_model()))
        ),
        "integrity_gate_raises": _case(gate_raises),
    }


def _outcomes_with(name: str | None) -> dict[str, bool]:
    parts = dict(MODULES)
    if name is not None:
        parts[MUTANTS[name][0]] = _mutant(name)
    return _outcomes(parts["generator"], parts["bound"], parts["checker"], parts["job_set"])


def test_real_code_passes_every_gate_case():
    outcomes = _outcomes_with(None)
    assert all(outcomes.values()), [case for case, ok in outcomes.items() if not ok]


@pytest.mark.parametrize(
    "name,must_fail",
    [
        ("R1_machine_no_overlap_removed", "shared_machine_exact"),
        ("R1_machine_no_overlap_removed", "checker_clean"),
        ("R2_job_precedence_violated", "checker_clean"),
        ("R3_duration_altered", "checker_clean"),
        ("R4_operation_start_shifted", "one_job_equals_rm10"),
        ("R5_operation_duplicated", "checker_clean"),
        ("R6_operation_omitted", "checker_clean"),
        ("R7_makespan_corrupted", "independent_makespan"),
        ("R8_tie_break_changed", "tie_to_lower_request_id"),
        ("R9_depends_on_argument_order", "argument_order_irrelevant"),
        ("R10_lower_bound_corrupted", "lower_bound_exact"),
        ("C1_checker_overlap_check_removed", "overlap_tamper_detected"),
        ("C2_checker_closed_intervals", "touching_intervals_accepted"),
        ("C3_checker_missing_check_removed", "omission_tamper_detected"),
        ("J1_manufacturable_check_removed", "non_manufacturable_refused"),
        ("J2_duplicate_check_removed", "duplicate_refused"),
        ("J3_integrity_gate_removed", "integrity_gate_raises"),
    ],
)
def test_mutant_is_caught_by_the_named_gate_case(name, must_fail):
    assert _outcomes_with(name)[must_fail] is False
