"""RM1 orchestration: the composition root wiring the plan -> verify -> log loop.

Composes intake / Velith adapter -> deterministic planner -> manufacturability oracle -> episode
emission. INFRA_ERROR (any infrastructure fault) yields a non-grounded verdict and writes NO episode
(spec §5.3). Grounded outcomes (MANUFACTURABLE / NOT_MANUFACTURABLE / PLAN_INVALID) are logged.
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
    default_model,
)
from mini_prometheus.manufacturing_constraints.oracle import ManufacturabilityOracle
from mini_prometheus.manufacturing_planning import planner
from mini_prometheus.orchestration import episode_store


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
        t1 = time.perf_counter()
        verdict = verifier.verify(plan, model)
        t2 = time.perf_counter()
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

    from mini_prometheus._contracts import DeclaredOperation, ManufacturingRequest, ProcessOp, StockForm

    parser = argparse.ArgumentParser(description="RM1 plan -> verify -> log")
    parser.add_argument("request_json", help="path to a ManufacturingRequest JSON file")
    args = parser.parse_args(argv)
    raw = json.loads(open(args.request_json, encoding="utf-8").read())
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
    )
    result = run_from_request(request)
    print(f"{result.status} episode -> {result.episode_path}")
    return 1 if result.is_error else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_main(sys.argv[1:]))
