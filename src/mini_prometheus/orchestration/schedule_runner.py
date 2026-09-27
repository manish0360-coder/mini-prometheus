"""RM11 composition + CLI: several engineer requests -> one deterministic multi-job schedule.

``schedule_requests(requests, capability_model=...)`` normalizes each request (``intake``) and
hands the job set to ``manufacturing_scheduling.job_set``, which plans and verifies every job under
the one capability model, refuses the whole set when any prerequisite fails (all-or-nothing), and
returns a schedule only after the independent checker accepts it. The baseline rule is
``earliest_start_v1`` — NOT an optimizer — and every schedule carries a lower-bound certificate
(makespan == bound proves it optimal under the RM11 model; otherwise only the gap is stated).

Pure and read-only (Director rulings D5/D6): no episode, schedule, memory or state is written;
nothing is executed or dispatched (the plan executor is Noetica's, Handbook §6.8). ``runner.py``
(the single-job RM1-RM10 CLI) is untouched; request files are parsed exactly as it parses them, so
a job's plan here is byte-identical to its standalone plan.
"""

from __future__ import annotations

import sys
from collections.abc import Sequence
from typing import Any

from mini_prometheus._contracts import ManufacturingRequest
from mini_prometheus._provenance import now_rfc3339
from mini_prometheus.intake.request_intake import intake
from mini_prometheus.manufacturing_constraints.capability_model import (
    ProcessCapabilityModel,
    UnknownResourceError,
    constrained_model,
    default_model,
    with_unavailable_resources,
)
from mini_prometheus.manufacturing_scheduling.changeover import SetupInput, canonical_setup_rules
from mini_prometheus.manufacturing_scheduling.downtime import DowntimeInput, canonical_downtime
from mini_prometheus.manufacturing_scheduling.job_set import schedule_job_set
from mini_prometheus.manufacturing_scheduling.model import (
    SCHEDULING_RULE,
    SELECTABLE_RULES,
    BoundStatus,
    InvalidDowntimeError,
    InvalidSetupError,
    JobInput,
    ScheduledOperation,
    ScheduledSetup,
    ScheduleIntegrityError,
    ScheduleOutcome,
    ScheduleStatus,
    SetupRule,
)

_OPTIMAL = "(makespan equals the lower bound: PROVABLY OPTIMAL under the RM11 model)"
_OPTIMAL_DOWNTIME = (
    "(makespan equals the window-aware lower bound: PROVABLY OPTIMAL under the RM12 model)"
)
_OPTIMAL_SETUP = "(makespan equals the lower bound: PROVABLY OPTIMAL under the RM14 model)"
_OPTIMAL_DOWNTIME_SETUP = (
    "(makespan equals the window-aware lower bound: PROVABLY OPTIMAL under the RM14 model)"
)


def schedule_requests(
    requests: Sequence[ManufacturingRequest],
    *,
    capability_model: ProcessCapabilityModel | None = None,
    produced_at: str | None = None,
    downtime: DowntimeInput | None = None,
    rule: str | None = None,
    setup_rules: SetupInput | None = None,
) -> ScheduleOutcome:
    """RM12: ``downtime`` maps machine ids to finite [start_min, end_min) pairs for this run only;
    invalid downtime raises ``InvalidDowntimeError`` before planning. RM13: ``rule`` opts into a
    selectable rule (None = the job-set default, ``earliest_start_v1``). RM14: ``setup_rules``
    declares cross-job changeovers for this run only; invalid rules raise ``InvalidSetupError``
    before planning."""
    model = capability_model or default_model()
    produced_at = produced_at or now_rfc3339()
    jobs = [
        JobInput(request.request_id, intake(request, produced_at=produced_at))
        for request in requests
    ]
    options: dict[str, Any] = {}
    if downtime:
        options["downtime"] = downtime
    if rule is not None:
        options["rule"] = rule
    if setup_rules:
        options["setup_rules"] = setup_rules
    return schedule_job_set(jobs, model, produced_at=produced_at, **options)


def _row(
    start: object, end: object, resource: object, request_id: object, step: object, op: object
) -> str:
    return f"{start:>6} {end:>6}  {resource:<9} {request_id:<36} {step:>4}  {op}"


def _placement(op: ScheduledOperation) -> str:
    return _row(op.start_min, op.end_min, op.resource_id, op.request_id, op.step_index, op.op)


def _setup_rule(rule: SetupRule) -> str:
    what = f"{rule.prev_op} -> {rule.curr_op}" if rule.prev_op is not None else "default"
    return f"{rule.machine_id} {what} {rule.duration_min} min"


def _setup_line(setup: ScheduledSetup) -> str:
    return (
        f"changeover [{setup.start_min}, {setup.end_min}) {setup.resource_id} before "
        f"{setup.request_id} step {setup.step_index}: {setup.prev_op} ({setup.prev_request_id}) "
        f"-> {setup.curr_op}, {setup.duration_min} min ({setup.matched})"
    )


def render(outcome: ScheduleOutcome) -> list[str]:
    """The CLI report: placements, completions, makespan, lower-bound certificate, identities."""
    if outcome.status == ScheduleStatus.NOT_SCHEDULED or outcome.schedule is None:
        count = len(outcome.refusals)
        lines = [f"NOT_SCHEDULED: no schedule produced (all-or-nothing); {count} refusal(s)"]
        for refusal in outcome.refusals:
            who = f" {refusal.request_id}" if refusal.request_id else ""
            lines.append(f"refusal {refusal.reason}{who}: {refusal.detail}")
        return lines
    s = outcome.schedule
    lines = [
        f"SCHEDULED: {len(s.jobs)} jobs, {len(s.operations)} operations "
        f"(rule {s.scheduling_rule} {s.scheduling_rule_version}; {s.optimization_status}; "
        f"capability model {s.capability_model_version})",
        _row("start", "end", "resource", "request_id", "step", "op"),
    ]
    lines += [_placement(op) for op in s.operations]
    lines += [f"job {job.request_id}: completion {job.completion_min} min" for job in s.jobs]
    if s.downtime:  # RM12 lines only with relevant downtime; otherwise the RM11 report exactly
        spans = [
            f"{m} " + " ".join(f"[{i.start_min}, {i.end_min})" for i in ivs)
            for m, ivs in s.downtime
        ]
        lines.append("downtime: " + "; ".join(spans))
    if s.setup_rules:  # RM14 lines only with relevant setup rules; else the RM13 report exactly
        lines.append("setup rules: " + "; ".join(_setup_rule(r) for r in s.setup_rules))
        lines += [_setup_line(setup) for setup in s.setups]
    binding = [f"longest job {r}" for r in s.lower_bound_binding_request_ids]
    binding += [f"busiest machine {m}" for m in s.lower_bound_binding_resource_ids]
    lines.append(f"makespan: {s.makespan_min} min")
    lines.append(f"lower bound: {s.lower_bound_min} min ({'; '.join(binding)})")
    optimal = _OPTIMAL
    if s.downtime:
        machines = "; ".join(s.window_aware_lower_bound_binding_resource_ids) or "the RM11 bound"
        lines.append(
            f"window-aware lower bound: {s.window_aware_lower_bound_min} min (binding: {machines})"
        )
        optimal = _OPTIMAL_DOWNTIME
    if s.setup_rules:
        optimal = _OPTIMAL_DOWNTIME_SETUP if s.downtime else _OPTIMAL_SETUP
    gap = f"gap to lower bound: {s.gap_to_lower_bound_min} min"
    lines.append(f"{gap} {optimal}" if s.bound_status == BoundStatus.PROVABLY_OPTIMAL else gap)
    lines.append("model assumptions: " + "; ".join(s.model_assumptions))
    lines.append(f"schedule input identity: {s.schedule_input_identity}")
    lines.append(f"schedule digest: {s.schedule_digest}")
    return lines


def _request_from_json(raw: Any, constrained: bool) -> ManufacturingRequest:
    """Exactly the single-job CLI's parsing (runner.py): tolerances read only when constrained."""
    from mini_prometheus._contracts import DeclaredOperation, ProcessOp, StockForm, Tolerances

    tolerances = None
    if constrained and raw.get("tolerances") is not None:
        tolerances = Tolerances(general_tolerance_mm=raw["tolerances"]["general_tolerance_mm"])
    return ManufacturingRequest(
        schema_version=raw["schema_version"],
        request_id=raw["request_id"],
        material=raw["material"],
        material_code=raw.get("material_code"),
        stock_form=StockForm(raw["stock_form"]),
        declared_operations=[
            DeclaredOperation(op=ProcessOp(o["op"]), target=o.get("target"), params=o.get("params"))
            for o in raw["declared_operations"]
        ],
        quantity=raw["quantity"],
        tolerances=tolerances,
    )


def _downtime_from_args(values: list[str]) -> dict[str, list[tuple[int, int]]]:
    """``MACHINE:START:END`` values -> {machine: [(start, end), ...]} (integers only)."""
    downtime: dict[str, list[tuple[int, int]]] = {}
    for value in values:
        parts = value.split(":")
        if len(parts) != 3:
            raise ValueError(f"--downtime {value!r}: expected MACHINE:START_MIN:END_MIN")
        machine, start, end = parts
        try:
            interval = (int(start), int(end))
        except ValueError:
            raise ValueError(
                f"--downtime {value!r}: start and end must be integer minutes"
            ) from None
        downtime.setdefault(machine, []).append(interval)
    return downtime


def _minutes_arg(flag: str, value: str, text: str) -> int:
    try:
        return int(text)
    except ValueError:
        raise ValueError(f"{flag} {value!r}: MINUTES must be integer minutes") from None


def _setup_rules_from_args(transitions: list[str], defaults: list[str]) -> list[SetupRule]:
    """``MACHINE:PREV_OP:CURR_OP:MINUTES`` and ``MACHINE:MINUTES`` values -> setup rules."""
    rules: list[SetupRule] = []
    for value in transitions:
        parts = value.split(":")
        if len(parts) != 4:
            raise ValueError(f"--setup {value!r}: expected MACHINE:PREV_OP:CURR_OP:MINUTES")
        machine, prev_op, curr_op, minutes = parts
        rules.append(SetupRule(machine, prev_op, curr_op, _minutes_arg("--setup", value, minutes)))
    for value in defaults:
        parts = value.split(":")
        if len(parts) != 2:
            raise ValueError(f"--setup-default {value!r}: expected MACHINE:MINUTES")
        machine, minutes = parts
        rules.append(
            SetupRule(machine, None, None, _minutes_arg("--setup-default", value, minutes))
        )
    return rules


def _main(argv: list[str] | None = None) -> int:
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="RM11-RM14 multi-job schedule (earliest_start_v1, with --downtime "
        "earliest_start_v1_downtime, with relevant --setup/--setup-default a _setup suffix; "
        "NOT_OPTIMIZED; no dispatch)"
    )
    parser.add_argument(
        "request_json",
        nargs="+",
        help="ManufacturingRequest JSON files, one job each; their order is irrelevant",
    )
    parser.add_argument(
        "--capability-model",
        choices=("default", "constrained"),
        default="default",
        help="as in the single-job CLI: default (RM1) or constrained (RM8 ECR, model 1.1.0)",
    )
    parser.add_argument(
        "--unavailable-resource",
        action="append",
        default=[],
        metavar="ID",
        help="RM9: declare a KNOWN resource unavailable for this planning snapshot (repeatable; "
        "applies to every job). Unknown ids are rejected before planning.",
    )
    parser.add_argument(
        "--downtime",
        action="append",
        default=[],
        metavar="MACHINE:START:END",
        help="RM12: a KNOWN machine is down on [START, END) minutes from schedule origin 0 "
        "(integers, 0 <= START < END; repeatable). Operations on it wait; nothing is rerouted.",
    )
    parser.add_argument(
        "--rule",
        choices=SELECTABLE_RULES,
        default=SCHEDULING_RULE,
        help="RM13: scheduling rule (default earliest_start_v1). "
        "earliest_start_v1_most_work_remaining is opt-in: exact earliest-start ties go to the job "
        "with the most remaining work.",
    )
    parser.add_argument(
        "--setup",
        action="append",
        default=[],
        metavar="MACHINE:PREV_OP:CURR_OP:MINUTES",
        help="RM14: on a KNOWN machine, a cross-job changeover from PREV_OP (another job's "
        "operation) to CURR_OP takes MINUTES (integer >= 0; repeatable). On a machine with any "
        "declared changeover, a cross-job transition the schedule needs without its own rule or "
        "a --setup-default refuses the set (never assumed zero).",
    )
    parser.add_argument(
        "--setup-default",
        action="append",
        default=[],
        metavar="MACHINE:MINUTES",
        help="RM14: the machine's default cross-job changeover for transitions without their own "
        "--setup rule (repeatable, one per machine).",
    )
    args = parser.parse_args(argv)
    constrained = args.capability_model == "constrained"
    model = constrained_model() if constrained else default_model()
    if args.unavailable_resource:
        try:
            model = with_unavailable_resources(model, args.unavailable_resource)
        except UnknownResourceError as exc:
            parser.error(str(exc))
    try:
        downtime = _downtime_from_args(args.downtime)
        canonical_downtime(downtime, model.resources)
    except (ValueError, InvalidDowntimeError) as exc:
        parser.error(str(exc))
    try:
        setup_rules = _setup_rules_from_args(args.setup, args.setup_default)
        canonical_setup_rules(setup_rules, model)
    except (ValueError, InvalidSetupError) as exc:
        parser.error(str(exc))
    requests = []
    for path in args.request_json:
        with open(path, encoding="utf-8") as handle:
            requests.append(_request_from_json(json.load(handle), constrained))
    try:
        outcome = schedule_requests(
            requests,
            capability_model=model,
            downtime=downtime,
            rule=args.rule,
            setup_rules=setup_rules,
        )
    except ScheduleIntegrityError as exc:
        print(f"SCHEDULE_INTEGRITY_ERROR (no schedule returned): {exc}")
        return 1
    for line in render(outcome):
        print(line)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_main(sys.argv[1:]))
