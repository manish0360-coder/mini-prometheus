"""RM14 zero-diff gate (Director test P, regression requirement §27): without RELEVANT setup
rules RM14 is byte-identical to RM11/RM12/RM13.

- RM11: the frozen rm11-complete golden (read only; its digest and its probe's digest are pinned in
  test_rm12_no_downtime_zero_diff.py) is reproduced row for row with no setup rules, empty setup
  rules and setup rules only on machines no two jobs share.
- RM12: the three-job downtime schedules are unchanged by irrelevant setup rules.
- RM13: every RM13_REGRESSION_CORPUS_01 instance, under both rules, is unchanged by irrelevant setup
  rules; and zero-minute changeovers on every machine leave every placement unchanged.
"""

from __future__ import annotations

import json

import rm11_support as s
import rm12_rm11_baseline_probe as probe
import rm14_support as t
import support
from mini_prometheus.manufacturing_scheduling.model import SCHEDULING_RULE_SETUP, schedule_view
from mini_prometheus.orchestration.schedule_runner import schedule_requests
from rm14_support import OP_MACHINE, R

GOLDEN_PATH = support.FIXTURES / "rm12_rm11_baseline_golden.json"
CORPUS_PATH = support.FIXTURES / "rm13_regression_corpus_01.json"
FIRST_OP = {  # one operation each machine can perform (for an irrelevant transition rule)
    "saw01": "cut_stock",
    "mill01": "face_mill",
    "mill02": "face_mill",
    "lathe01": "turn",
    "bench01": "deburr",
    "cmm01": "inspect",
}


def _golden() -> dict:
    return json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))


def _assert_rows_equal(expected: dict, actual: dict) -> None:
    for exp, act in zip(expected["rows"], actual["rows"], strict=True):
        assert act == exp, f"{exp['case']}: differs from rm11-complete"
    assert actual == expected


def _lonely_rules(machines_by_job: dict[str, set[str]], known) -> list[R]:
    """A default and a transition rule on every known machine used by at most one job."""
    jobs_on: dict[str, set[str]] = {}
    for request_id, machines in machines_by_job.items():
        for machine in machines:
            jobs_on.setdefault(machine, set()).add(request_id)
    rules = []
    for machine in sorted(known):
        if len(jobs_on.get(machine, ())) <= 1:
            op = FIRST_OP[machine]
            rules += [R(machine, None, None, 7), R(machine, op, op, 3)]
    return rules


def test_P_no_setup_rules_is_byte_identical_to_rm11():
    for rules in (None, [], ()):
        _assert_rows_equal(
            _golden()["fingerprint"],
            probe.fingerprint(lambda c, m, r, rules=rules: {"setup_rules": rules}),
        )


def test_P_setup_rules_on_unshared_machines_are_byte_identical_to_rm11():
    rows = {row["case"]: row for row in _golden()["fingerprint"]["rows"]}
    received = []

    def irrelevant(case, model, requests):
        view = rows[case]["view"]
        machines_by_job: dict[str, set[str]] = {}
        if view is not None:  # the machines the golden schedule actually used
            for op in view["operations"]:
                machines_by_job.setdefault(op["request_id"], set()).add(op["resource_id"])
        else:  # refused rows (default model): each operation's only machine
            for request in requests:
                machines_by_job[request.request_id] = {
                    OP_MACHINE[d.op.value] for d in request.declared_operations
                }
        rules = _lonely_rules(machines_by_job, model.resources)
        received.append((case, len(rules)))
        return {"setup_rules": rules}

    _assert_rows_equal(_golden()["fingerprint"], probe.fingerprint(irrelevant))
    assert sum(n > 0 for _, n in received) == len(received)  # non-vacuous: every row received rules


def test_P_rm12_downtime_schedules_are_unchanged_by_irrelevant_rules():
    lonely = [R("lathe01", None, None, 9), R("bench01", "deburr", "deburr", 4)]  # B only / C only
    for downtime in ({"mill01": [(20, 45)]}, {"saw01": [(0, 3)], "cmm01": [(41, 50), (50, 52)]}):
        plain = t.run(s.three_job_requests(), None, downtime=downtime).schedule
        noisy = t.run(s.three_job_requests(), lonely, downtime=downtime).schedule
        assert plain.scheduling_rule == "earliest_start_v1_downtime"
        assert schedule_view(noisy) == schedule_view(plain)


def _corpus_runs(rules_for):
    """Every corpus instance under both RM13 rules with the given setup rules."""
    views = {}
    for case in json.loads(CORPUS_PATH.read_text(encoding="utf-8"))["cases"]:
        requests = [
            s.request(j["request_id"], [tuple(o) for o in j["operations"]]) for j in case["jobs"]
        ]
        machines = {
            j["request_id"]: {OP_MACHINE[op] for op, _ in j["operations"]} for j in case["jobs"]
        }
        for rule in ("earliest_start_v1", t.MWKR):
            outcome = schedule_requests(
                requests,
                produced_at=s.FIXED_TIME,
                downtime=case["downtime"],
                rule=rule,
                setup_rules=rules_for(machines),
            )
            views[(case["case"], rule)] = outcome.schedule
    return views


def test_P_rm13_corpus_is_unchanged_by_irrelevant_rules():
    known = FIRST_OP.keys() - {"mill02"}
    plain = _corpus_runs(lambda machines: None)
    noisy = _corpus_runs(lambda machines: _lonely_rules(machines, known))
    assert len(plain) == 270
    for key, sched in plain.items():
        assert schedule_view(noisy[key]) == schedule_view(sched), key


def test_P_zero_minute_changeovers_leave_every_corpus_placement_unchanged():
    zero = [R(m, None, None, 0) for m in ("saw01", "mill01", "lathe01", "bench01", "cmm01")]
    plain = _corpus_runs(lambda machines: None)
    zeroed = _corpus_runs(lambda machines: zero)
    with_changeover = 0
    for key, sched in plain.items():
        assert s.placements(zeroed[key]) == s.placements(sched), key
        assert zeroed[key].makespan_min == sched.makespan_min
        assert all(c.duration_min == 0 for c in zeroed[key].setups)
        with_changeover += bool(zeroed[key].setups)
        if zeroed[key].setups:
            assert zeroed[key].scheduling_rule.endswith("_setup")
            assert zeroed[key].schedule_input_identity != sched.schedule_input_identity
    assert with_changeover == 2 * 53  # every contended instance, under both rules, has changeovers
    assert SCHEDULING_RULE_SETUP == "earliest_start_v1_setup"
