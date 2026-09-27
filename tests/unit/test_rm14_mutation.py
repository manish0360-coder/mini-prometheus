"""RM14 anti-vacuity: every required changeover mutant (Director §26) is caught by a NAMED gate
case (a case that raises counts as failed, never as passed). One exact substitution in the REAL
source each (the anchor must occur exactly once), executed as an isolated module; fixtures are
built with the real modules so only the unit under mutation changes.

Required: remove setup duration (S1), zero for a needed undeclared transition (S2 refusal skipped,
S3 zero in the generator), default instead of explicit (S4), precedence reversed (S5), within-job
setup (S6), setup before the predecessor completes (S7), setup crossing downtime (S8), gap between
setup and processing (S9), setup identity corrupted (S10), irrelevant setup in identity (S11),
relevant setup omitted from identity (S12); plus canonical sort skipped (S13), default never
relevant (S14) and nine checker mutants (K1-K9).
"""

from __future__ import annotations

import dataclasses
import pathlib
import sys
import types
from collections.abc import Callable

import pytest

import rm11_support as s
import rm14_support as t
from mini_prometheus.manufacturing_constraints.capability_model import default_model
from mini_prometheus.manufacturing_scheduling import changeover as real_changeover
from mini_prometheus.manufacturing_scheduling import checker as real_checker
from mini_prometheus.manufacturing_scheduling import earliest_start as real_generator
from mini_prometheus.manufacturing_scheduling import model as real_model
from mini_prometheus.manufacturing_scheduling.model import DowntimeInterval as D
from mini_prometheus.manufacturing_scheduling.model import (
    SetupIssueCode,
    UnspecifiedSetupTransitionError,
    schedule_digest,
)
from rm11_support import ID_A, ID_B, ID_C
from rm14_support import R

MODULES = {
    "generator": real_generator,
    "changeover": real_changeover,
    "model": real_model,
    "checker": real_checker,
}
SOURCES = {n: pathlib.Path(m.__file__).read_text(encoding="utf-8") for n, m in MODULES.items()}
_START = (
    "            start = max(job_ready[job.request_id], "
    "machine_free.get(operation.resource_id, 0))\n"
)
_FIT = (
    "            start = _earliest_fit(start, setup_min + operation.duration_min, "
    "machine_downtime)\n"
)
_SHIFT = "            start = setup_end\n"
MUTANTS = {
    "S1_setup_consumes_no_time": ("generator", _SHIFT, "            pass\n"),
    "S2_undeclared_transition_not_refused": (
        "generator",
        "        if undeclared:\n",
        "        if False:\n",
    ),
    "S3_generator_undeclared_as_zero": (
        "generator",
        "    if default is not None:\n"
        "        return _Setup(prev_request_id, prev_op, SetupMatch.MACHINE_DEFAULT, default)\n",
        "    return _Setup(prev_request_id, prev_op, SetupMatch.MACHINE_DEFAULT, default or 0)\n",
    ),
    "S4_default_instead_of_explicit": (
        "generator",
        "    minutes = transitions.get((prev_op, operation.op))\n",
        "    minutes = None\n",
    ),
    "S5_precedence_reversed": (
        "generator",
        "    if minutes is not None:\n",
        "    if minutes is not None and default is None:\n",
    ),
    "S6_within_job_setup_allowed": (
        "generator",
        "    if prev_request_id == request_id:\n",
        "    if False:\n",
    ),
    "S7_setup_before_predecessor": (
        "generator",
        _START,
        "            start = max(job_ready[job.request_id] - setup_min, "
        "machine_free.get(operation.resource_id, 0))\n",
    ),
    "S8_setup_crosses_downtime": (
        "generator",
        _FIT,
        "            start = _earliest_fit(start + setup_min, operation.duration_min, "
        "machine_downtime) - setup_min\n",
    ),
    "S9_gap_between_setup_and_processing": (
        "generator",
        _SHIFT,
        "            start = setup_end + 1\n",
    ),
    "S10_setup_identity_drops_minutes": (
        "model",
        "    return [dataclasses.asdict(rule) for rule in rules]\n",
        "    return [[rule.machine_id, rule.prev_op, rule.curr_op] for rule in rules]\n",
    ),
    "S11_irrelevant_rules_in_identity": (
        "changeover",
        "        elif (rule.prev_op, rule.curr_op) in pairs:\n",
        "        elif True:\n",
    ),
    "S12_relevant_rules_excluded_from_identity": (
        "model",
        '        view["setup_rules"] = setup_rules_view(setup_rules)\n',
        "        pass\n",
    ),
    "S13_canonical_sort_skipped": (
        "changeover",
        "    return tuple(sorted(rules, key=_rule_order))\n",
        "    return tuple(rules)\n",
    ),
    "S14_default_never_relevant": (
        "changeover",
        "            if any((rule.machine_id, p, c) not in declared for p, c in pairs):\n",
        "            if False:\n",
    ),
    "K1_checker_adjacency_removed": (
        "checker",
        "        if setup.end_min != op.start_min:\n",
        "        if False:\n",
    ),
    "K2_checker_missing_setup_removed": (
        "checker",
        "        if key not in recorded_setups:\n",
        "        if False:\n",
    ),
    "K3_checker_expects_same_job_setup": (
        "checker",
        "            if resource_id not in active or previous.request_id == current.request_id:\n",
        "            if resource_id not in active:\n",
    ),
    "K4_checker_setup_downtime_removed": (
        "checker",
        "            if setup.start_min < down.end_min and down.start_min < setup.end_min:\n",
        "            if False:\n",
    ),
    "K5_checker_predecessor_removed": (
        "checker",
        "        if predecessor is not None and setup.start_min < predecessor.end_min:\n",
        "        if False:\n",
    ),
    "K6_checker_setup_overlap_removed": (
        "checker",
        "                if occupied_until is not None and begin < occupied_until:\n",
        "                if False:\n",
    ),
    "K7_checker_minutes_not_compared": (
        "checker",
        "        if found != required_setups[key]:\n",
        "        if False:\n",
    ),
    "K8_checker_interval_arithmetic_removed": (
        "checker",
        "            or setup.end_min != setup.start_min + setup.duration_min\n",
        "            or False\n",
    ),
    "K9_checker_recorded_rules_unchecked": (
        "checker",
        "    if tuple(schedule.setup_rules) != relevant_setup:\n",
        "    if False:\n",
    ),
}
VERSION = "1.0.0"
SAW_THREE = {ID_A: [("cut_stock", 10)], ID_B: [("cut_stock", 10)], ID_C: [("cut_stock", 10)]}
SAW_TWO = {ID_A: [("cut_stock", 10)], ID_B: [("cut_stock", 10)]}
MILL_WITHIN = {ID_A: [("face_mill", 10), ("drill", 5)], ID_B: [("pocket_mill", 20)]}
MILL_PRED = {ID_A: [("face_mill", 10)], ID_B: [("cut_stock", 30), ("pocket_mill", 10)]}
TWO_MILL = {ID_A: [("face_mill", 10)], ID_B: [("pocket_mill", 20)]}
EXPLICIT = [R("mill01", "face_mill", "pocket_mill", 3), R("mill01", None, None, 9)]
CANONICAL = (R("mill01", None, None, 9), R("mill01", "face_mill", "pocket_mill", 3))
SAW_DOWN = (("saw01", (D(16, 20),)),)


def _mutant(name: str) -> types.ModuleType:
    target, anchor, replacement = MUTANTS[name]
    source = SOURCES[target]
    assert source.count(anchor) == 1, f"{name}: mutation anchor must occur exactly once"
    module = types.ModuleType(f"rm14_mutant_{name}")
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


def _built(spec, relevant, downtime=()):
    """A fixture schedule from the REAL generator."""
    jobs = s.scheduling_jobs(t.requests_of(spec))
    return jobs, real_generator.earliest_start_v1(
        jobs, VERSION, downtime=downtime, setup_rules=relevant
    )


def _tampered(sched, setup_key=None, op_move=None, **changes):
    if setup_key is not None:
        setups = tuple(
            dataclasses.replace(c, **changes) if (c.request_id, c.step_index) == setup_key else c
            for c in sched.setups
        )
        sched = dataclasses.replace(sched, setups=setups)
    if op_move is not None:
        (request_id, step_index), (start, end) = op_move
        ops = tuple(
            dataclasses.replace(o, start_min=start, end_min=end)
            if (o.request_id, o.step_index) == (request_id, step_index)
            else o
            for o in sched.operations
        )
        sched = dataclasses.replace(sched, operations=ops)
    return dataclasses.replace(sched, schedule_digest=schedule_digest(sched))


def _outcomes(parts: dict[str, types.ModuleType]) -> dict[str, bool]:
    generator, changeover = parts["generator"], parts["changeover"]
    model, checker = parts["model"], parts["checker"]
    two = s.scheduling_jobs(t.requests_of(TWO_MILL))
    saw_raw = [("saw01", None, None, 5)]

    def generated(spec, relevant, downtime=()):
        jobs = s.scheduling_jobs(t.requests_of(spec))
        sched = generator.earliest_start_v1(jobs, VERSION, downtime=downtime, setup_rules=relevant)
        return s.placements(sched), t.changeovers(sched)

    def never_invents() -> bool:
        try:
            generator.earliest_start_v1(
                two, VERSION, setup_rules=(R("mill01", "face_mill", "drill", 3),)
            )
        except UnspecifiedSetupTransitionError:
            return True
        return False

    def required_undeclared_refused() -> bool:
        try:
            generator.earliest_start_v1(
                two, VERSION, setup_rules=(R("mill01", "pocket_mill", "face_mill", 3),)
            )
        except UnspecifiedSetupTransitionError as missing:
            return missing.transitions == (("mill01", "face_mill", "pocket_mill"),)
        return False

    def codes(jobs, sched, raw, downtime=None):
        return {i.code for i in checker.schedule_issues(sched, jobs, VERSION, downtime, raw)}

    def accepts_valid() -> bool:
        cases = [
            (*_built(SAW_THREE, (R("saw01", None, None, 5),)), saw_raw, None),
            (
                *_built(MILL_WITHIN, (R("mill01", None, None, 7),)),
                [("mill01", None, None, 7)],
                None,
            ),
            (*_built(MILL_PRED, (R("mill01", None, None, 8),)), [("mill01", None, None, 8)], None),
            (*_built(TWO_MILL, CANONICAL), EXPLICIT, None),
            (
                *_built(SAW_TWO, (R("saw01", None, None, 5),), SAW_DOWN),
                saw_raw,
                {"saw01": [(16, 20)]},
            ),
        ]
        return all(codes(jobs, sched, raw, dt) == set() for jobs, sched, raw, dt in cases)

    def flags(code, spec, relevant, raw, downtime=(), raw_downtime=None, **tamper) -> bool:
        jobs, sched = _built(spec, relevant, downtime)
        if tamper.pop("drop_first_setup", False):
            sched = _tampered(dataclasses.replace(sched, setups=sched.setups[1:]))
        if tamper.pop("drop_rules", False):
            sched = _tampered(dataclasses.replace(sched, setup_rules=()))
        if tamper:
            sched = _tampered(sched, **tamper)
        return code in codes(jobs, sched, raw, raw_downtime)

    saw_rule = (R("saw01", None, None, 5),)
    pred_rule = (R("mill01", None, None, 8),)
    return {
        "setup_occupies_the_machine_before_its_operation": _case(
            lambda: generated(SAW_THREE, saw_rule)
            == (
                [
                    (ID_A, 0, "cut_stock", "saw01", 0, 10),
                    (ID_B, 0, "cut_stock", "saw01", 15, 25),
                    (ID_C, 0, "cut_stock", "saw01", 30, 40),
                ],
                [
                    (
                        ID_B,
                        0,
                        "saw01",
                        ID_A,
                        "cut_stock",
                        "cut_stock",
                        "machine_default",
                        5,
                        10,
                        15,
                    ),
                    (
                        ID_C,
                        0,
                        "saw01",
                        ID_B,
                        "cut_stock",
                        "cut_stock",
                        "machine_default",
                        5,
                        25,
                        30,
                    ),
                ],
            )
        ),
        "explicit_rule_beats_default": _case(
            lambda: generated(TWO_MILL, CANONICAL)[1]
            == [(ID_B, 0, "mill01", ID_A, "face_mill", "pocket_mill", "transition", 3, 10, 13)]
        ),
        "generator_never_invents_a_changeover": _case(never_invents),
        "no_changeover_inside_a_job": _case(
            lambda: generated(MILL_WITHIN, (R("mill01", None, None, 7),))[0][1]
            == (ID_A, 1, "drill", "mill01", 10, 15)
        ),
        "no_anticipatory_changeover": _case(
            lambda: generated(MILL_PRED, pred_rule)[1]
            == [(ID_B, 1, "mill01", ID_A, "face_mill", "pocket_mill", "machine_default", 8, 30, 38)]
        ),
        "block_avoids_downtime": _case(
            lambda: [c[8:] for c in generated(SAW_TWO, saw_rule, SAW_DOWN)[1]] == [(20, 25)]
        ),
        "undeclared_transition_refused": _case(required_undeclared_refused),
        "unused_transition_not_required": _case(
            lambda: generated(TWO_MILL, (EXPLICIT[0],))[1]
            == [(ID_B, 0, "mill01", ID_A, "face_mill", "pocket_mill", "transition", 3, 10, 13)]
        ),
        "only_relevant_rules": _case(
            lambda: changeover.relevant_setup_rules(
                changeover.canonical_setup_rules(
                    [
                        *EXPLICIT,
                        R("saw01", None, None, 5),
                        R("mill01", "drill", "face_mill", 2),
                        R("lathe01", "turn", "turn", 1),
                    ],
                    default_model(),
                ),
                two,
            )
            == CANONICAL
        ),
        "canonical_order": _case(
            lambda: changeover.canonical_setup_rules(EXPLICIT, default_model()) == CANONICAL
        ),
        "identity_covers_relevant_minutes": _case(
            lambda: len(
                {
                    model.schedule_input_identity(
                        "earliest_start_v1_setup", "1.0.0", VERSION, [(ID_A, "sha256:x")], (), rules
                    )
                    for rules in ((), (R("saw01", None, None, 5),), (R("saw01", None, None, 6),))
                }
            )
            == 3
        ),
        "checker_accepts_valid": _case(accepts_valid),
        "checker_adjacency": _case(
            lambda: flags(
                SetupIssueCode.SETUP_NOT_ADJACENT,
                SAW_THREE,
                saw_rule,
                saw_raw,
                op_move=((ID_B, 0), (16, 26)),
            )
        ),
        "checker_missing": _case(
            lambda: flags(
                SetupIssueCode.SETUP_MISSING, SAW_THREE, saw_rule, saw_raw, drop_first_setup=True
            )
        ),
        "checker_setup_downtime": _case(
            lambda: flags(
                SetupIssueCode.SETUP_DOWNTIME_CONFLICT,
                SAW_TWO,
                saw_rule,
                saw_raw,
                SAW_DOWN,
                {"saw01": [(16, 20)]},
                setup_key=(ID_B, 0),
                op_move=((ID_B, 0), (20, 30)),
                start_min=15,
                end_min=20,
            )
        ),
        "checker_predecessor": _case(
            lambda: flags(
                SetupIssueCode.SETUP_BEFORE_PREDECESSOR,
                MILL_PRED,
                pred_rule,
                [("mill01", None, None, 8)],
                setup_key=(ID_B, 1),
                op_move=((ID_B, 1), (30, 40)),
                start_min=22,
                end_min=30,
            )
        ),
        "checker_overlap": _case(
            lambda: flags(
                SetupIssueCode.SETUP_OVERLAP,
                SAW_THREE,
                saw_rule,
                saw_raw,
                setup_key=(ID_C, 0),
                op_move=((ID_C, 0), (27, 37)),
                start_min=22,
                end_min=27,
            )
        ),
        "checker_minutes": _case(
            lambda: flags(
                SetupIssueCode.SETUP_MISMATCH,
                SAW_THREE,
                saw_rule,
                saw_raw,
                setup_key=(ID_B, 0),
                duration_min=4,
                start_min=11,
            )
        ),
        "checker_interval_arithmetic": _case(
            lambda: flags(
                SetupIssueCode.SETUP_INVALID_TIME,
                SAW_THREE,
                saw_rule,
                saw_raw,
                setup_key=(ID_B, 0),
                start_min=8,
            )
        ),
        "checker_recorded_rules": _case(
            lambda: flags(
                SetupIssueCode.SETUP_RULES_MISMATCH, SAW_THREE, saw_rule, saw_raw, drop_rules=True
            )
        ),
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
        ("S1_setup_consumes_no_time", "setup_occupies_the_machine_before_its_operation"),
        ("S2_undeclared_transition_not_refused", "undeclared_transition_refused"),
        ("S3_generator_undeclared_as_zero", "generator_never_invents_a_changeover"),
        ("S4_default_instead_of_explicit", "explicit_rule_beats_default"),
        ("S5_precedence_reversed", "explicit_rule_beats_default"),
        ("S6_within_job_setup_allowed", "no_changeover_inside_a_job"),
        ("S7_setup_before_predecessor", "no_anticipatory_changeover"),
        ("S8_setup_crosses_downtime", "block_avoids_downtime"),
        ("S9_gap_between_setup_and_processing", "setup_occupies_the_machine_before_its_operation"),
        ("S10_setup_identity_drops_minutes", "identity_covers_relevant_minutes"),
        ("S11_irrelevant_rules_in_identity", "only_relevant_rules"),
        ("S12_relevant_rules_excluded_from_identity", "identity_covers_relevant_minutes"),
        ("S13_canonical_sort_skipped", "canonical_order"),
        ("S14_default_never_relevant", "only_relevant_rules"),
        ("K1_checker_adjacency_removed", "checker_adjacency"),
        ("K2_checker_missing_setup_removed", "checker_missing"),
        ("K3_checker_expects_same_job_setup", "checker_accepts_valid"),
        ("K4_checker_setup_downtime_removed", "checker_setup_downtime"),
        ("K5_checker_predecessor_removed", "checker_predecessor"),
        ("K6_checker_setup_overlap_removed", "checker_overlap"),
        ("K7_checker_minutes_not_compared", "checker_minutes"),
        ("K8_checker_interval_arithmetic_removed", "checker_interval_arithmetic"),
        ("K9_checker_recorded_rules_unchecked", "checker_recorded_rules"),
    ],
)
def test_mutant_is_caught_by_the_named_gate_case(name, must_fail):
    assert _outcomes_with(name)[must_fail] is False
