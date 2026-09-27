"""RM14 test helpers. Every job, duration, setup rule and downtime below is a declared TEST
INPUT, not manufacturing data.

``reference_schedule`` is an independent re-implementation of the frozen RM14 rule written from the
specification (specs/milestones/RM14-sequence-dependent-changeover.md §5), never from the generator:
per job its next operation; per machine its free time and last (job, operation); a cross-job
changeover on a machine with declared rules (transition rule, else machine default); the earliest
block start >= max(job ready, machine free) whose whole [start, start + changeover + duration)
avoids downtime (a fixed-point loop over the raw intervals, not the generator's single pass);
selection by (block start, -remaining processing work for the opt-in rule, request_id). Every
candidate's changeover is evaluated at each decision; if any evaluated cross-job transition on a
machine with declared rules has no transition rule and no default, the run is refused with every
such transition of that decision.
"""

from __future__ import annotations

import rm11_support as s
from mini_prometheus.manufacturing_scheduling.model import ScheduledSetup, SetupRule
from mini_prometheus.orchestration.schedule_runner import schedule_requests
from rm11_support import FIXED_TIME

R = SetupRule
OP_MACHINE = {  # the default capability model's (RM9) assignment of each operation
    "cut_stock": "saw01",
    "face_mill": "mill01",
    "drill": "mill01",
    "pocket_mill": "mill01",
    "turn": "lathe01",
    "deburr": "bench01",
    "inspect": "cmm01",
}
MWKR = "earliest_start_v1_most_work_remaining"


def run(requests, rules=None, **kwargs):
    """schedule_requests at the fixed test time with the given setup rules."""
    return schedule_requests(requests, produced_at=FIXED_TIME, setup_rules=rules, **kwargs)


def changeovers(sched) -> list[tuple]:
    """Changeover tuples: (request_id, step, machine, prev_request_id, prev_op, curr_op, matched,
    minutes, start, end)."""
    return [setup_tuple(c) for c in sched.setups]


def setup_tuple(c: ScheduledSetup) -> tuple:
    return (
        c.request_id,
        c.step_index,
        c.resource_id,
        c.prev_request_id,
        c.prev_op,
        c.curr_op,
        str(c.matched),
        c.duration_min,
        c.start_min,
        c.end_min,
    )


def requests_of(spec: dict[str, list[tuple[str, int]]]):
    return [s.request(request_id, ops) for request_id, ops in spec.items()]


def rule_map(rules) -> dict[tuple[str, str | None, str | None], int]:
    return {(r.machine_id, r.prev_op, r.curr_op): r.duration_min for r in rules}


def missing_transitions(spec, rules) -> list[tuple[str, str, str]]:
    """Every POSSIBLE cross-job transition on a machine with declared rules that no rule covers (a
    static over-approximation; only the transitions the rule evaluates are required)."""
    declared = rule_map(rules)
    missing = set()
    for machine in {m for m, _, _ in declared}:
        if (machine, None, None) in declared:
            continue
        for first, first_ops in spec.items():
            for second, second_ops in spec.items():
                if first == second:
                    continue
                for prev_op, _ in first_ops:
                    for curr_op, _ in second_ops:
                        on_machine = OP_MACHINE[prev_op] == OP_MACHINE[curr_op] == machine
                        if on_machine and (machine, prev_op, curr_op) not in declared:
                            missing.add((machine, prev_op, curr_op))
    return sorted(missing)


def reference_schedule(spec, rules, downtime=None, mwkr=False):
    """(placements, changeovers) of the frozen RM14 rule, both in canonical order; or
    ("REFUSED", sorted undeclared (machine, prev_op, curr_op)) when the rule needs one."""
    declared = rule_map(rules)
    active = {m for m, _, _ in declared}
    blocked = downtime or {}
    ready = {r: 0 for r in spec}
    position = {r: 0 for r in spec}
    free: dict[str, int] = {}
    last: dict[str, tuple[str, str]] = {}
    placements, setups = [], []
    while any(position[r] < len(ops) for r, ops in spec.items()):
        best = None
        undeclared = set()
        for request_id in sorted(spec):
            ops = spec[request_id]
            if position[request_id] >= len(ops):
                continue
            op, duration = ops[position[request_id]]
            machine = OP_MACHINE[op]
            setup = None
            previous = last.get(machine)
            if machine in active and previous is not None and previous[0] != request_id:
                if (machine, previous[1], op) in declared:
                    setup = (*previous, "transition", declared[(machine, previous[1], op)])
                elif (machine, None, None) in declared:
                    setup = (*previous, "machine_default", declared[(machine, None, None)])
                else:
                    undeclared.add((machine, previous[1], op))
                    continue
            length = duration + (setup[3] if setup else 0)
            start = max(ready[request_id], free.get(machine, 0))
            moved = True
            while moved:  # fixed point: the whole block must avoid every downtime interval
                moved = False
                for down_start, down_end in blocked.get(machine, ()):
                    if start < down_end and down_start < start + length:
                        start, moved = down_end, True
            remaining = sum(d for _, d in ops[position[request_id] :]) if mwkr else 0
            key = (start, -remaining, request_id)
            if best is None or key < best[0]:
                best = (key, request_id, op, duration, machine, setup)
        if undeclared:
            return "REFUSED", sorted(undeclared)
        (start, _, _), request_id, op, duration, machine, setup = best
        step = position[request_id]
        if setup is not None:
            prev_request_id, prev_op, matched, minutes = setup
            record = (request_id, step, machine, prev_request_id, prev_op, op, matched, minutes)
            setups.append((*record, start, start + minutes))
            start += minutes
        placements.append((request_id, step, op, machine, start, start + duration))
        ready[request_id] = free[machine] = start + duration
        last[machine] = (request_id, op)
        position[request_id] += 1
    placements.sort(key=lambda p: (p[4], p[0], p[1]))
    setups.sort(key=lambda c: (c[8], c[0], c[1]))
    return placements, setups
