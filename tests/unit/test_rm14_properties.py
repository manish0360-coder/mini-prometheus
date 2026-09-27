"""RM14 property / adversarial tests (Director §25), on seeded synthetic instances.

Each instance is 2-4 jobs of 1-4 operations (default capability model), a random setup-rule set
(complete or deliberately incomplete; defaults, transition rules or both; zero minutes allowed),
optional random downtime, and either RM13 rule. For every instance:

- the set is refused exactly when the reference rule needs an undeclared cross-job transition,
  with exactly those transitions (a merely possible, never evaluated gap is not refused);
- otherwise the production schedule equals ``rm14_support.reference_schedule`` (an independent
  re-implementation from the specification) placement for placement, changeover for changeover;
- the fourteen invariants are asserted directly on the artifact, without the production checker;
- the same input gives the same artifact, and rules only on unshared machines change nothing.

These are synthetic algorithm checks, not evidence of factory performance.
"""

from __future__ import annotations

import itertools
import random

import rm11_support as s
import rm14_support as t
from mini_prometheus.manufacturing_scheduling.model import (
    RefusalReason,
    ScheduleStatus,
    schedule_view,
)
from rm14_support import OP_MACHINE, R

SEED = 20260927 + 14
INSTANCES = 400
IDS = [s.ID_A, s.ID_B, s.ID_C, "dddddddd-0000-4000-8000-000000000004"]
OPS = list(OP_MACHINE)
MACHINE_OPS = {
    m: sorted(op for op, mm in OP_MACHINE.items() if mm == m) for m in set(OP_MACHINE.values())
}


def _instance(rng: random.Random):
    spec = {
        IDS[j]: [(rng.choice(OPS), rng.randint(1, 15)) for _ in range(rng.randint(1, 4))]
        for j in range(rng.randint(2, 4))
    }
    rules = []
    for machine in sorted(MACHINE_OPS):
        style = rng.choice(["none", "default", "default+explicit", "explicit", "partial"])
        if style == "none":
            continue
        if style.startswith("default"):
            rules.append(R(machine, None, None, rng.randint(0, 12)))
        if style != "default":
            pairs = [(a, b) for a in MACHINE_OPS[machine] for b in MACHINE_OPS[machine]]
            keep = pairs if style == "explicit" else rng.sample(pairs, rng.randint(1, len(pairs)))
            rules += [R(machine, a, b, rng.randint(0, 12)) for a, b in keep]
    downtime = {}
    if rng.random() < 0.4:
        for machine in rng.sample(sorted(MACHINE_OPS), rng.randint(1, 3)):
            spans = []
            for _ in range(rng.randint(1, 3)):
                start = rng.randint(0, 80)
                spans.append((start, start + rng.randint(1, 15)))
            downtime[machine] = spans
    return spec, rules, downtime, rng.random() < 0.5


def _assert_invariants(sched, spec, rules, downtime):
    declared = t.rule_map(rules)
    ops = {(o.request_id, o.step_index): o for o in sched.operations}
    setups = {(c.request_id, c.step_index): c for c in sched.setups}
    assert len(setups) == len(sched.setups)
    block = {k: setups[k].start_min if k in setups else o.start_min for k, o in ops.items()}
    for key, c in setups.items():
        op = ops[key]
        assert c.duration_min >= 0  # 1
        assert c.end_min >= c.start_min and c.end_min - c.start_min == c.duration_min  # 2
        assert c.end_min == op.start_min and c.resource_id == op.resource_id  # 3
        if key[1] > 0:  # 6: never before the job's predecessor completes
            assert ops[(key[0], key[1] - 1)].end_min <= c.start_min
        explicit = declared.get((c.resource_id, c.prev_op, c.curr_op))  # 9, 10
        if explicit is not None:
            assert (str(c.matched), c.duration_min) == ("transition", explicit)
        else:
            assert (str(c.matched), c.duration_min) == (
                "machine_default",
                declared[(c.resource_id, None, None)],
            )
    by_machine: dict[str, list] = {}
    for key, op in ops.items():
        by_machine.setdefault(op.resource_id, []).append((block[key], op.end_min, key))
    active = {m for m, _, _ in declared}
    for machine, blocks in by_machine.items():
        blocks.sort()
        for (_, first_end, first), (second_start, _, second) in itertools.pairwise(blocks):
            assert first_end <= second_start  # 5: blocks never overlap on a machine
            needs = machine in active and first[0] != second[0]
            assert (second in setups) == needs  # 8: same job -> none; 7: first -> none (below)
            if needs:
                assert setups[second].prev_request_id == first[0]
        assert blocks[0][2] not in setups  # 7: a machine's first operation has no changeover
        for begin, end, _ in blocks:  # 4: the whole block avoids downtime
            assert all(not (begin < b and a < end) for a, b in downtime.get(machine, ()))
    assert sched.lower_bound_min <= sched.makespan_min


def test_property_rm14_against_the_reference_and_invariants():
    rng = random.Random(SEED)
    counts = {
        "refused": 0,
        "scheduled": 0,
        "scheduled_with_unused_gap": 0,
        "with_changeover": 0,
        "with_downtime": 0,
    }
    for _ in range(INSTANCES):
        spec, rules, downtime, mwkr = _instance(rng)
        kwargs = {"downtime": downtime} if downtime else {}
        if mwkr:
            kwargs["rule"] = t.MWKR
        outcome = t.run(t.requests_of(spec), rules, **kwargs)
        expected = t.reference_schedule(spec, rules, downtime, mwkr)
        if expected[0] == "REFUSED":  # 10: a needed undeclared transition is refused, never zero
            assert outcome.status == ScheduleStatus.NOT_SCHEDULED
            assert {r.reason for r in outcome.refusals} == {
                RefusalReason.UNSPECIFIED_SETUP_TRANSITION
            }
            assert [r.detail for r in outcome.refusals] == [
                f"{m}: cross-job changeover {a} -> {b} is not declared and {m} has no declared "
                "default"
                for m, a, b in expected[1]
            ]
            counts["refused"] += 1
            continue
        assert outcome.status == ScheduleStatus.SCHEDULED, outcome.refusals
        sched = outcome.schedule
        placements, setups = expected
        # an undeclared but never-needed possible transition does not refuse the set
        counts["scheduled_with_unused_gap"] += bool(t.missing_transitions(spec, rules))
        assert s.placements(sched) == placements  # 14: generator agrees with the reference
        assert t.changeovers(sched) == setups
        _assert_invariants(sched, spec, rules, downtime)
        again = t.run(t.requests_of(spec), list(reversed(rules)), **kwargs).schedule  # 12, 13
        assert schedule_view(again) == schedule_view(sched)
        counts["scheduled"] += 1
        counts["with_changeover"] += bool(sched.setups)
        counts["with_downtime"] += bool(downtime)
    assert counts["refused"] >= 30 and counts["scheduled"] >= 300, counts  # non-vacuous
    assert counts["with_changeover"] >= 100 and counts["with_downtime"] >= 50, counts
    # non-vacuous: sets the former static rule would have refused are scheduled when unneeded
    assert counts["scheduled_with_unused_gap"] >= 3, counts


def test_property_unshared_machine_rules_change_nothing():
    rng = random.Random(SEED + 1)
    compared = 0
    for _ in range(150):
        spec, _rules, downtime, mwkr = _instance(rng)
        kwargs = {"downtime": downtime} if downtime else {}
        if mwkr:
            kwargs["rule"] = t.MWKR
        jobs_on: dict[str, set[str]] = {}
        for request_id, ops in spec.items():
            for op, _ in ops:
                jobs_on.setdefault(OP_MACHINE[op], set()).add(request_id)
        lonely = [R(m, None, None, 11) for m in sorted(MACHINE_OPS) if len(jobs_on.get(m, ())) <= 1]
        if not lonely:
            continue
        plain = t.run(t.requests_of(spec), None, **kwargs).schedule  # 11: backward compatible
        noisy = t.run(t.requests_of(spec), lonely, **kwargs).schedule
        assert schedule_view(noisy) == schedule_view(plain)
        compared += 1
    assert compared >= 100
