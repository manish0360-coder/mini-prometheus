"""RM1 orchestration: the composition root wiring the plan -> verify -> log loop.

Composes intake / Velith adapter -> deterministic planner -> manufacturability oracle -> episode
emission. INFRA_ERROR (any infrastructure fault) yields a non-grounded verdict and writes NO episode
(spec §5.3). Grounded outcomes (MANUFACTURABLE / NOT_MANUFACTURABLE / PLAN_INVALID) are logged.

MP-S1 (G2, ADR-0022): before verification the plan's shop identity must equal the model's.
A mismatch raises ``ShopIdentityMismatchError``; it is re-raised past the INFRA_ERROR handler, so
nothing is verified, logged or swallowed. The CLI gains ``--capability-model-file`` (a declared shop;
it prints a verdict trace line). Without it, every output is RM14's exactly.
"""
from __future__ import annotations

import sys
import time
from dataclasses import dataclass

from mini_prometheus._contracts import (
    DesignInput,
    EngineeringResult,
    ManufacturingEpisode,
    ManufacturingRequest,
    ManufacturingTask,
    ProducedBy,
    ProductionPlan,
    Verdict,
)
from mini_prometheus._provenance import now_rfc3339
from mini_prometheus._verifier import Verifier
from mini_prometheus.intake.request_intake import intake
from mini_prometheus.integrations.velith.adapter import from_engineering_result
from mini_prometheus.manufacturing_constraints.capability_model import (
    ProcessCapabilityModel,
    UnknownResourceError,
    constrained_model,
    default_model,
    with_unavailable_resources,
)
from mini_prometheus.manufacturing_constraints.oracle import ManufacturabilityOracle
from mini_prometheus.shop_declaration.shop_model import (
    InvalidShopModelError,
    ShopIdentityMismatchError,
    require_plan_shop_identity,
    shop_identity_line,
)
from mini_prometheus.manufacturing_planning import planner
from mini_prometheus.orchestration import episode_store
from mini_prometheus.orchestration.shop_model_file import read_shop_model, refusal_message
from mini_prometheus.orchestration.verdict_trace import trace_line, trace_run


@dataclass
class RunResult:
    status: str
    verdict: Verdict
    task: ManufacturingTask | None
    plan: ProductionPlan | None
    episode: ManufacturingEpisode | None
    episode_path: str | None

    @property
    def is_error(self) -> bool:
        return self.verdict.is_error


def run(
    design_input: DesignInput,
    *,
    capability_model: ProcessCapabilityModel | None = None,
    oracle: Verifier | None = None,
    produced_at: str | None = None,
    store_path: str | None = None,
) -> RunResult:
    model = capability_model or default_model()
    verifier: Verifier = oracle or ManufacturabilityOracle()
    produced_at = produced_at or now_rfc3339()
    try:
        t0 = time.perf_counter()
        task, plan = planner.plan(design_input, model, produced_at=produced_at)
        require_plan_shop_identity(plan, model)  # MP-S1 G2: before verification
        t1 = time.perf_counter()
        verdict = verifier.verify(plan, model)
        t2 = time.perf_counter()
    except ShopIdentityMismatchError:
        raise  # a binding violation is never an INFRA_ERROR verdict and writes nothing
    except Exception as exc:  # noqa: BLE001 - any fault becomes INFRA_ERROR (no episode)
        infra = Verdict(
            grounded=False,
            is_error=True,
            status="INFRA_ERROR",
            reason_codes=[],
            produced_by=ProducedBy(component="orchestration-runner", version="1.0.0"),
            detail=str(exc),
        )
        return RunResult("INFRA_ERROR", infra, None, None, None, None)

    episode = episode_store.build_episode(
        task, design_input, plan, verdict, model.version,
        produced_at=produced_at,
        plan_ms=(t1 - t0) * 1000.0,
        verify_ms=(t2 - t1) * 1000.0,
    )
    path = episode_store.emit(episode, store_path)
    return RunResult(verdict.status, verdict, task, plan, episode, str(path))


def run_from_request(
    request: ManufacturingRequest, *, produced_at: str | None = None, **kwargs
) -> RunResult:
    produced_at = produced_at or now_rfc3339()
    design_input = intake(request, produced_at=produced_at)
    return run(design_input, produced_at=produced_at, **kwargs)


def run_from_velith(
    result: EngineeringResult,
    manufacturing_intent: ManufacturingRequest,
    *,
    produced_at: str | None = None,
    **kwargs,
) -> RunResult:
    produced_at = produced_at or now_rfc3339()
    design_input = from_engineering_result(result, manufacturing_intent, produced_at=produced_at)
    return run(design_input, produced_at=produced_at, **kwargs)


def _main(argv: list[str] | None = None) -> int:  # pragma: no cover - thin CLI
    import argparse
    import json

    from mini_prometheus._contracts import (
        DeclaredOperation,
        ManufacturingRequest,
        ProcessOp,
        StockForm,
        Tolerances,
    )

    parser = argparse.ArgumentParser(description="RM1 plan -> verify -> log")
    parser.add_argument("request_json", help="path to a ManufacturingRequest JSON file")
    model_choice = parser.add_mutually_exclusive_group()
    model_choice.add_argument(
        "--capability-model-file",
        metavar="PATH",
        help=(
            "MP-S1: a declared ShopCapabilityModel JSON file (mutually exclusive with "
            "--capability-model). Plans carry its shop identity; a verdict trace line is printed. "
            "The declaration's evidence class is the declarer's assertion and is not independently "
            "verified. An invalid file exits 2 and nothing is run. Tolerances are read when the "
            "file declares tolerance data."
        ),
    )
    model_choice.add_argument(
        "--capability-model",
        choices=("default", "constrained"),
        default="default",
        help=(
            "default (legacy RM1 behavior): no tolerance or declared-precedence reasoning; "
            "the request's 'tolerances' field is NOT read (known limitation, RM8 spec). "
            "constrained (RM8 ECR, capability model 1.1.0): declared operation precedence + "
            "tolerance feasibility, reading 'tolerances.general_tolerance_mm'."
        ),
    )
    parser.add_argument(
        "--unavailable-resource",
        action="append",
        default=[],
        metavar="ID",
        help=(
            "RM9: declare a KNOWN resource (e.g. mill01) unavailable for this planning snapshot; "
            "repeatable. Steps are rerouted to an available capable resource, or reported "
            "RESOURCE_UNAVAILABLE. Unknown ids are rejected before planning. Omit for RM8 behavior."
        ),
    )
    args = parser.parse_args(argv)
    declared = None  # MP-S1: a loaded shop declaration, when --capability-model-file is given
    if args.capability_model_file is not None:
        try:
            declared = read_shop_model(args.capability_model_file)
        except OSError as exc:
            parser.exit(2, f"error: cannot read shop capability model: {exc}\n")
        except InvalidShopModelError as exc:
            parser.exit(2, refusal_message(exc))
    raw = json.loads(open(args.request_json, encoding="utf-8").read())
    constrained = args.capability_model == "constrained"
    # Legacy default: tolerances are not read. Only the constrained (ECR) mode carries them, and
    # (MP-S1) a declared shop that declares tolerance data.
    reads_tolerances = constrained or bool(declared and declared.capability_tolerance_mm)
    tolerances = None
    if reads_tolerances and raw.get("tolerances") is not None:
        tolerances = Tolerances(general_tolerance_mm=raw["tolerances"]["general_tolerance_mm"])
    request = ManufacturingRequest(
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
    if declared is not None:  # MP-S1: the declared shop, never a built-in fallback
        model = declared
        if args.unavailable_resource:
            try:
                model = with_unavailable_resources(declared, args.unavailable_resource)
            except UnknownResourceError as exc:
                parser.error(str(exc))
        result = run_from_request(request, capability_model=model)
        trace = trace_run(result, model)
        print(trace_line(trace, shop_identity_line(model), result.episode_path))
    elif args.unavailable_resource:
        # RM9: explicit availability snapshot on the selected capability model (validated first).
        base = constrained_model() if constrained else default_model()
        try:
            model = with_unavailable_resources(base, args.unavailable_resource)
        except UnknownResourceError as exc:
            parser.error(str(exc))
        result = run_from_request(request, capability_model=model)
    elif constrained:
        result = run_from_request(request, capability_model=constrained_model())
    else:
        result = run_from_request(request)
    if declared is None:
        print(f"{result.status} episode -> {result.episode_path}")
    # RM10: only when the request declared operation times (otherwise the output is RM9's exactly).
    episode = result.episode
    if episode is not None and episode.design_input is not None and result.plan is not None:
        if planner.timing_requested(episode.design_input):
            lead_time = planner.lead_time_min(result.plan)
            if lead_time is not None:
                print(f"lead time: {lead_time} min (single-job serialized timeline)")
            else:
                issues = planner.timeline_issues(episode.design_input, result.plan)
                print("timeline not derived: " + "; ".join(issues))
    return 1 if result.is_error else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_main(sys.argv[1:]))
