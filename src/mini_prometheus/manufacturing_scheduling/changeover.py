"""RM14 setup-rule input: validation, canonicalization and relevance (ADR-0017).

Setup rules are immutable input to ONE scheduling run — never factory state, a tool, fixture or
material model, or a contract. Each rule declares, for a KNOWN machine, the integer minutes of a
CROSS-JOB changeover: the machine's previous operation in the run belongs to another job.

- a transition rule ``SetupRule(machine_id, prev_op, curr_op, duration_min)``: previous operation
  ``prev_op``, next operation ``curr_op`` (operation codes the machine can perform);
- a machine default ``SetupRule(machine_id, None, None, duration_min)``: every other cross-job
  transition on that machine. An explicit transition rule always beats the default.

- ``canonical_setup_rules`` validates a collection (e.g. a list) of rules — each a ``SetupRule`` or
  a 4-item sequence; known machine; both operations None or both operation codes the machine can
  perform; minutes an integer >= 0 (no bool, float or string); each (machine, prev_op, curr_op) at
  most once — and sorts them by (machine_id, default first, prev_op, curr_op). Invalid input raises
  ``InvalidSetupError``.
- ``possible_transitions`` — per machine, every ordered pair (operation of one job, operation of
  another job) of operations assigned to it: the only cross-job transitions a schedule can contain.
- ``relevant_setup_rules`` keeps only rules that can apply: transition rules whose transition is
  possible, and a machine default when some possible transition has no transition rule. Rules for
  machines used by at most one job, or for transitions that cannot occur, affect neither the
  schedule nor its identity or digest.

Refusing to invent is dynamic (``earliest_start``): on a machine with ANY declared rule, a cross-job
transition the scheduling rule actually evaluates needs its transition rule or the machine default,
otherwise the run is refused (UNSPECIFIED_SETUP_TRANSITION) — never assumed zero. A possible
transition the rule never evaluates is not required. A machine without any declared rule has no
changeover (the RM11 assumption).
"""

from __future__ import annotations

from collections.abc import Collection, Iterable, Mapping, Sequence
from typing import cast

from mini_prometheus._contracts import ProcessOp
from mini_prometheus.manufacturing_constraints.capability_model import ProcessCapabilityModel
from mini_prometheus.manufacturing_scheduling.model import (
    InvalidSetupError,
    SchedulingJob,
    SetupRule,
    SetupRules,
)

# a collection of SetupRule objects or (machine_id, prev_op, curr_op, duration_min) sequences
SetupInput = Collection[object]
_OPS = frozenset(op.value for op in ProcessOp)


def _rule_order(rule: SetupRule) -> tuple[str, bool, str, str]:
    return (rule.machine_id, rule.prev_op is not None, rule.prev_op or "", rule.curr_op or "")


def _rule(raw: object, capability_model: ProcessCapabilityModel) -> SetupRule:
    if isinstance(raw, SetupRule):
        fields: tuple[object, ...] = (raw.machine_id, raw.prev_op, raw.curr_op, raw.duration_min)
    elif isinstance(raw, str | bytes | Mapping):
        fields = ()
    else:
        try:
            fields = tuple(cast(Iterable[object], raw))
        except TypeError:
            fields = ()
    if len(fields) != 4:
        raise InvalidSetupError(
            f"setup rule {raw!r} must be (machine_id, prev_op, curr_op, duration_min)"
        )
    machine, prev_op, curr_op, minutes = fields
    if not isinstance(machine, str) or machine not in capability_model.resources:
        raise InvalidSetupError(f"setup rule {raw!r}: unknown machine id {machine!r}")
    if (prev_op is None) != (curr_op is None):
        raise InvalidSetupError(
            f"setup rule {raw!r}: prev_op and curr_op must both be operation codes, or both None "
            "for the machine default"
        )
    for op in (prev_op, curr_op):
        if op is None:
            continue
        if not isinstance(op, str) or op not in _OPS:
            raise InvalidSetupError(f"setup rule {raw!r}: unknown operation {op!r}")
        capability = capability_model.op_capability.get(ProcessOp(op))
        if capability not in capability_model.resources[machine]:
            raise InvalidSetupError(f"setup rule {raw!r}: {machine} cannot perform {op}")
    if not isinstance(minutes, int) or isinstance(minutes, bool) or minutes < 0:
        raise InvalidSetupError(
            f"setup rule {raw!r}: duration_min must be integer minutes >= 0, got {minutes!r}"
        )
    return SetupRule(machine, cast(str | None, prev_op), cast(str | None, curr_op), minutes)


def canonical_setup_rules(
    setup_rules: SetupInput | None, capability_model: ProcessCapabilityModel
) -> SetupRules:
    """Validated setup rules in canonical order (empty when none are given)."""
    if setup_rules is None:
        return ()
    # a re-iterable collection (the independent checker reads the same input again), never text
    if not isinstance(setup_rules, Collection) or isinstance(setup_rules, str | bytes | Mapping):
        raise InvalidSetupError("setup rules must be a collection (e.g. a list) of rules")
    rules = [_rule(raw, capability_model) for raw in setup_rules]
    seen: set[tuple[str, str | None, str | None]] = set()
    for rule in rules:
        key = (rule.machine_id, rule.prev_op, rule.curr_op)
        if key in seen:
            what = f"{rule.prev_op} -> {rule.curr_op}" if rule.prev_op else "default"
            raise InvalidSetupError(f"setup rule {rule.machine_id} {what} is declared twice")
        seen.add(key)
    return tuple(sorted(rules, key=_rule_order))


def possible_transitions(jobs: Sequence[SchedulingJob]) -> dict[str, set[tuple[str, str]]]:
    """Per machine, every (prev_op, curr_op) with the two operations from different jobs."""
    ops: dict[str, dict[str, set[str]]] = {}  # machine -> request_id -> operation codes
    for job in jobs:
        machine = {a.step_index: a.resource_id for a in job.plan.resource_assignments}
        for step in job.plan.steps:
            ops.setdefault(machine[step.index], {}).setdefault(job.request_id, set()).add(
                step.op.value
            )
    return {
        machine: {
            (prev_op, curr_op)
            for first, prev_ops in by_job.items()
            for second, curr_ops in by_job.items()
            if first != second
            for prev_op in prev_ops
            for curr_op in curr_ops
        }
        for machine, by_job in ops.items()
    }


def relevant_setup_rules(canonical: SetupRules, jobs: Sequence[SchedulingJob]) -> SetupRules:
    """Only the canonical rules that can apply to a possible cross-job transition of the jobs."""
    possible = possible_transitions(jobs)
    declared = {(r.machine_id, r.prev_op, r.curr_op) for r in canonical if r.prev_op is not None}
    relevant: list[SetupRule] = []
    for rule in canonical:
        pairs = possible.get(rule.machine_id, set())
        if rule.prev_op is None:
            if any((rule.machine_id, p, c) not in declared for p, c in pairs):
                relevant.append(rule)
        elif (rule.prev_op, rule.curr_op) in pairs:
            relevant.append(rule)
    return tuple(relevant)
