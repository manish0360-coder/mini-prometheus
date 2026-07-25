"""RM2-M3: idempotent reuse composition + reproducibility guard.

Composes the RM1 pipeline with the RM2 read side: intake → compute reuse key → lookup → on a hit,
return the prior verified plan/verdict (writing no episode); on a miss, delegate to RM1's unchanged
``runner.run`` (plan → verify → log). On a hit the reproducibility guard (default on) recomputes the
plan and asserts its ``content_hash`` matches the stored one (verification-first — stored experience is
re-derived, never trusted blindly).

This is a NEW file: RM1's ``runner.py`` and all other RM1 modules are byte-unchanged (plan §0.6).
"""
from __future__ import annotations

from dataclasses import dataclass

from mini_prometheus._contracts import (
    ManufacturingEpisode,
    ManufacturingRequest,
    ManufacturingTask,
    ProductionPlan,
    Ref,
    Verdict,
)
from mini_prometheus._provenance import now_rfc3339
from mini_prometheus._verifier import Verifier
from mini_prometheus.experience.episode_index import EpisodeIndex, design_input_key
from mini_prometheus.experience.episode_store_reader import load
from mini_prometheus.intake.request_intake import intake
from mini_prometheus.manufacturing_constraints.capability_model import (
    ProcessCapabilityModel,
    default_model,
)
from mini_prometheus.manufacturing_planning import planner
from mini_prometheus.orchestration import runner
from mini_prometheus.orchestration.episode_store import DEFAULT_STORE


class ExperienceConsistencyError(ValueError):
    """Raised when a reused plan does not re-derive to the stored plan content_hash (drift/corruption)."""


@dataclass
class ReuseRunResult:
    status: str
    verdict: Verdict
    task: ManufacturingTask | None
    plan: ProductionPlan | None
    episode: ManufacturingEpisode | None
    reused: bool
    source_episode: Ref | None
    episode_path: str | None

    @property
    def is_error(self) -> bool:
        return self.verdict.is_error


def run_with_reuse(
    request: ManufacturingRequest,
    *,
    capability_model: ProcessCapabilityModel | None = None,
    oracle: Verifier | None = None,
    produced_at: str | None = None,
    store_path: str | None = None,
    verify_reuse: bool = True,
) -> ReuseRunResult:
    model = capability_model or default_model()
    produced_at = produced_at or now_rfc3339()
    resolved_store = store_path if store_path is not None else str(DEFAULT_STORE)

    design_input = intake(request, produced_at=produced_at)
    key = design_input_key(design_input, model.version)
    index = EpisodeIndex.build(load(resolved_store))
    hit = index.lookup(key)

    if hit is not None:
        if verify_reuse:  # reproducibility guard: re-derive the plan and confirm it matches
            _task, recomputed = planner.plan(design_input, model, produced_at=produced_at)
            if recomputed.content_hash != hit.plan.content_hash:
                raise ExperienceConsistencyError(
                    f"reuse guard: recomputed plan {recomputed.content_hash} "
                    f"!= stored {hit.plan.content_hash}"
                )
        return ReuseRunResult(
            status=hit.verdict.status,
            verdict=hit.verdict,
            task=hit.task,
            plan=hit.plan,
            episode=hit,
            reused=True,
            source_episode=Ref(id=hit.episode_id, content_hash=hit.content_hash),
            episode_path=resolved_store,
        )

    result = runner.run(
        design_input,
        capability_model=model,
        oracle=oracle,
        produced_at=produced_at,
        store_path=resolved_store,
    )
    return ReuseRunResult(
        status=result.status,
        verdict=result.verdict,
        task=result.task,
        plan=result.plan,
        episode=result.episode,
        reused=False,
        source_episode=None,
        episode_path=result.episode_path,
    )
