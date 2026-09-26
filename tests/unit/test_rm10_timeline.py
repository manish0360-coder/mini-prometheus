"""RM10 — single-job timeline from engineer-declared operation times (NOT a production scheduler).

Frozen rules (specs/milestones/RM10-single-job-timeline.md):
- input: DeclaredOperation.params["duration_min"], integer minutes >= 1 (no float/bool/string/conversion);
- a timeline is derived only when timing is requested, every operation has a valid duration and every
  step has an assigned machine; start_0 = 0, start_i = end_(i-1), end_i = start_i + duration_i,
  lead time = final end — serialized, exact integer arithmetic;
- otherwise NO timeline value of any kind (no default, estimate or partial timeline); the missing
  prerequisites are reported; RM9's manufacturability verdict is untouched;
- an inconsistent carried timeline -> PLAN_INVALID / PLAN_MALFORMED; versions 1.3.0 only with a timeline.
Test letters follow the Director's RM10 list.
"""
from __future__ import annotations

import copy
import dataclasses

import pytest

from mini_prometheus import _hashing as h
from mini_prometheus.intake.request_intake import intake
from mini_prometheus.manufacturing_constraints.capability_model import (
    default_model,
    with_unavailable_resources,
)
from mini_prometheus.manufacturing_constraints.oracle import (
    DURATION_PARAM,
    SCHEDULE_END_PARAM,
    SCHEDULE_LEAD_TIME_PARAM,
    SCHEDULE_START_PARAM,
    ManufacturabilityOracle,
)
from mini_prometheus.manufacturing_planning import planner

import support
from support import FIXED_TIME

TIMED = support.load_json("engineer_request_with_durations.json")      # 12, 35, 18, 18, 10, 15 -> 108
UNTIMED = support.load_json("engineer_request_machined_bracket.json")
TIMELINE_KEYS = (DURATION_PARAM, SCHEDULE_START_PARAM, SCHEDULE_END_PARAM, SCHEDULE_LEAD_TIME_PARAM)


def _raw(durations=None, ops=None, base=None):
    raw = copy.deepcopy(base or UNTIMED)
    if ops is not None:
        raw["declared_operations"] = [{"op": o} for o in ops]
    if durations is not None:
        for op, d in zip(raw["declared_operations"], durations):
            if d is not _SKIP:
                op["params"] = {DURATION_PARAM: d}
    return raw


_SKIP = object()


def _run(raw, model=None, produced_at=FIXED_TIME):
    model = model or default_model()
    design_input = intake(support.build_request(raw), produced_at=produced_at)
    _task, plan = planner.plan(design_input, model, produced_at=produced_at)
    return design_input, plan, ManufacturabilityOracle().verify(plan, model)


def _timeline(plan):
    return [(s.params.get(SCHEDULE_START_PARAM), s.params.get(SCHEDULE_END_PARAM)) for s in plan.steps]


def _no_timeline_values(plan) -> bool:
    return all(k not in (s.params or {}) for s in plan.steps for k in TIMELINE_KEYS)


# ---- A, B, C: valid timelines and exact arithmetic ----
def test_A_valid_single_step_duration():
    di, plan, verdict = _run(_raw([7], ops=["drill"]))
    assert _timeline(plan) == [(0, 7)] and planner.lead_time_min(plan) == 7
    assert verdict.status == "MANUFACTURABLE" and verdict.produced_by.version == "1.3.0"


def test_B_valid_multi_step_duration_chain():
    di, plan, verdict = _run(TIMED)
    assert _timeline(plan) == [(0, 12), (12, 47), (47, 65), (65, 83), (83, 93), (93, 108)]
    assert [s.params[DURATION_PARAM] for s in plan.steps] == [12, 35, 18, 18, 10, 15]
    assert verdict.status == "MANUFACTURABLE" and verdict.reason_codes == []


def test_C_exact_lead_time_arithmetic():
    durations = [1, 2, 3, 1000, 99999, 7]
    _di, plan, _ = _run(_raw(durations))
    assert planner.lead_time_min(plan) == sum(durations) == plan.steps[-1].params[SCHEDULE_END_PARAM]
    assert plan.steps[-1].params[SCHEDULE_LEAD_TIME_PARAM] == sum(durations)
    assert all(SCHEDULE_LEAD_TIME_PARAM not in s.params for s in plan.steps[:-1])     # final step only
    assert plan.provenance.rule_version == "1.3.0"


# ---- D-I, T: missing prerequisites -> no timeline at all, reported; verdict unchanged ----
@pytest.mark.parametrize("case,value,expected", [
    ("D_missing", _SKIP, "step 2 (drill): duration_min missing"),
    ("E_zero", 0, "step 2 (drill): duration_min invalid (0); must be an integer >= 1"),
    ("F_negative", -5, "step 2 (drill): duration_min invalid (-5); must be an integer >= 1"),
    ("G_fractional", 2.5, "step 2 (drill): duration_min invalid (2.5); must be an integer >= 1"),
    ("G_float_integral", 18.0, "step 2 (drill): duration_min invalid (18.0); must be an integer >= 1"),
    ("H_text", "18", "step 2 (drill): duration_min invalid ('18'); must be an integer >= 1"),
    ("H_bool", True, "step 2 (drill): duration_min invalid (True); must be an integer >= 1"),
])
def test_invalid_or_missing_duration_yields_no_timeline(case, value, expected):
    durations = [12, 35, value, 18, 10, 15]
    di, plan, verdict = _run(_raw(durations))
    assert _no_timeline_values(plan)                                     # T: nothing fake or partial
    assert planner.timeline_issues(di, plan) == [expected]
    assert (verdict.status, verdict.reason_codes, verdict.detail) == ("MANUFACTURABLE", [], None)
    assert verdict.produced_by.version == "1.0.0" and plan.provenance.rule_version == "1.0.0"


def test_I_unassigned_step_yields_no_timeline_and_keeps_rm9_verdict():
    di, plan, verdict = _run(TIMED, with_unavailable_resources(default_model(), ["mill01"]))
    assert _no_timeline_values(plan)
    assert planner.timeline_issues(di, plan) == [
        "step 1 (face_mill): no machine assigned", "step 2 (drill): no machine assigned",
        "step 3 (drill): no machine assigned"]
    assert (verdict.status, verdict.reason_codes) == ("NOT_MANUFACTURABLE", ["RESOURCE_UNAVAILABLE"])
    assert verdict.detail == "RESOURCE_UNAVAILABLE: mill01" and verdict.produced_by.version == "1.2.0"


def test_T_no_fake_timeline_when_several_prerequisites_are_missing():
    raw = _raw([None, 35, _SKIP, "x", 10, 15])                               # None -> invalid
    di, plan, _ = _run(raw, with_unavailable_resources(default_model(), ["cmm01"]))
    assert _no_timeline_values(plan) and planner.lead_time_min(plan) is None
    assert planner.timeline_issues(di, plan) == [
        "step 0 (cut_stock): duration_min invalid (None); must be an integer >= 1",
        "step 2 (drill): duration_min missing",
        "step 3 (drill): duration_min invalid ('x'); must be an integer >= 1",
        "step 5 (inspect): no machine assigned"]


def test_user_supplied_start_end_values_never_control_the_schedule():
    raw = copy.deepcopy(TIMED)
    raw["declared_operations"][0]["params"].update({SCHEDULE_START_PARAM: 500, SCHEDULE_END_PARAM: 9})
    _di, plan, _ = _run(raw)
    assert _timeline(plan)[0] == (0, 12)


# ---- J, K, L: tampered timelines are PLAN_INVALID / PLAN_MALFORMED ----
def _tampered(mutate):
    _di, plan, _ = _run(TIMED)
    steps = [dataclasses.replace(s, params=dict(s.params)) for s in plan.steps]
    mutate(steps)
    bad = dataclasses.replace(plan, steps=steps)
    return ManufacturabilityOracle().verify(bad, default_model())


@pytest.mark.parametrize("name,mutate", [
    ("J_start_shifted", lambda s: s[2].params.update({SCHEDULE_START_PARAM: 48})),
    ("J_first_start_not_zero", lambda s: s[0].params.update({SCHEDULE_START_PARAM: 1})),
    ("K_end_not_start_plus_duration", lambda s: s[1].params.update({SCHEDULE_END_PARAM: 46})),
    ("K_inverted_interval", lambda s: s[4].params.update({SCHEDULE_END_PARAM: 80})),
    ("L_lead_time_wrong", lambda s: s[5].params.update({SCHEDULE_LEAD_TIME_PARAM: 107})),
    ("L_lead_time_on_non_final_step", lambda s: s[3].params.update({SCHEDULE_LEAD_TIME_PARAM: 108})),
    ("length_step_missing_timeline", lambda s: [s[3].params.pop(k) for k in (DURATION_PARAM, SCHEDULE_START_PARAM,
                                                                           SCHEDULE_END_PARAM)]),
    ("non_integer_minutes", lambda s: s[1].params.update({SCHEDULE_END_PARAM: 47.0})),
    ("zero_duration", lambda s: s[0].params.update({DURATION_PARAM: 0, SCHEDULE_END_PARAM: 0})),
])
def test_tampered_timeline_is_plan_invalid(name, mutate):
    verdict = _tampered(mutate)
    assert (verdict.status, verdict.reason_codes) == ("PLAN_INVALID", ["PLAN_MALFORMED"])
    assert verdict.produced_by.version == "1.3.0"


def test_timeline_on_unassigned_step_is_plan_invalid():
    _di, plan, _ = _run(TIMED)
    bad = dataclasses.replace(plan, resource_assignments=[a for a in plan.resource_assignments if a.step_index != 4])
    verdict = ManufacturabilityOracle().verify(bad, default_model())
    assert verdict.status == "PLAN_INVALID" and "PLAN_MALFORMED" in verdict.reason_codes


def test_untampered_timeline_is_consistent():
    _di, plan, verdict = _run(TIMED)
    assert (verdict.status, verdict.reason_codes, verdict.produced_by.version) == ("MANUFACTURABLE", [], "1.3.0")


# ---- M, N, O, P: identity and determinism ----
def test_M_duration_change_changes_identity():
    a_di, a, _ = _run(TIMED)
    b_di, b, _ = _run(_raw([12, 35, 19, 18, 10, 15], base=TIMED))
    assert h.content_hash(h.design_input_identity(a_di)) != h.content_hash(h.design_input_identity(b_di))
    assert a.content_hash != b.content_hash and planner.lead_time_min(b) == 109


def test_N_irrelevant_rm9_availability_still_behaves_correctly():
    _di, normal, normal_verdict = _run(TIMED)
    _di, plan, verdict = _run(TIMED, with_unavailable_resources(default_model(), ["lathe01"]))
    assert h.to_contract_dict(plan) == h.to_contract_dict(normal) and verdict == normal_verdict
    assert planner.lead_time_min(plan) == 108


def test_O_no_duration_request_has_no_timeline_and_no_rm10_version():
    di, plan, verdict = _run(UNTIMED)
    assert not planner.timing_requested(di) and planner.timeline_issues(di, plan) == []
    assert _no_timeline_values(plan) and planner.lead_time_min(plan) is None
    assert verdict.produced_by.version == "1.0.0" and plan.provenance.rule_version == "1.0.0"


def test_P_identical_input_is_deterministic():
    _a_di, a, va = _run(TIMED)
    _b_di, b, vb = _run(TIMED, produced_at="2030-12-31T23:59:59+00:00")
    assert a.content_hash == b.content_hash and va == vb and _timeline(a) == _timeline(b)
