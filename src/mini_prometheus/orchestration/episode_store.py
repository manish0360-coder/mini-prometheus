"""RM1 order 6: ManufacturingEpisode emission (Experience-Flow data contract, Law 21).

Builds a content-hashed, provenance-complete episode and appends it as one canonical-JSON line to
an append-only JSONL store (gitignored). Persisted episodes never carry INFRA_ERROR (spec §5.3).
The Noetica lifecycle framework (retention/compression) is deferred; MP emits the content only.
"""
from __future__ import annotations

import pathlib

from mini_prometheus import _hashing as h
from mini_prometheus._contracts import (
    DesignInput,
    ManufacturingEpisode,
    ManufacturingTask,
    ProductionPlan,
    Timing,
    Verdict,
)
from mini_prometheus._provenance import make_provenance
from mini_prometheus._validate import validate

SCHEMA_VERSION = "1.0.0"
_REPO = pathlib.Path(__file__).resolve().parents[3]
DEFAULT_STORE = _REPO / "artifacts" / "episodes" / "manufacturing_episodes.jsonl"


def build_episode(
    task: ManufacturingTask,
    design_input: DesignInput,
    plan: ProductionPlan,
    verdict: Verdict,
    capability_model_version: str,
    *,
    produced_at: str,
    plan_ms: float,
    verify_ms: float,
) -> ManufacturingEpisode:
    episode = ManufacturingEpisode(
        schema_version=SCHEMA_VERSION,
        episode_id="",
        task=task,
        design_ref=task.design_input_ref,
        engineering_verification_status=design_input.engineering_verification_status,
        plan=plan,
        verdict=verdict,
        capability_model_version=capability_model_version,
        content_hash="",
        provenance=make_provenance(
            source_refs=[task.design_input_ref, plan.task_ref],
            rule_id="episode.emit",
            rule_version="1.0.0",
            produced_at=produced_at,
            capability_model_version=capability_model_version,
            component="episode-emitter",
            component_version="1.0.0",
        ),
        timing=Timing(created_at=produced_at, plan_ms=plan_ms, verify_ms=verify_ms),
    )
    episode_hash = h.content_hash(h.episode_identity(episode))
    episode.content_hash = episode_hash
    episode.episode_id = h.derive_uuid(episode_hash)
    validate("manufacturing_episode", h.to_contract_dict(episode))
    return episode


def emit(episode: ManufacturingEpisode, store_path: str | pathlib.Path | None = None) -> pathlib.Path:
    if episode.verdict.status == "INFRA_ERROR":  # invariant: never persisted (spec §5.3)
        raise ValueError("INFRA_ERROR episodes are never persisted.")
    path = pathlib.Path(store_path) if store_path is not None else DEFAULT_STORE
    path.parent.mkdir(parents=True, exist_ok=True)
    line = h.canonical_json(h.to_contract_dict(episode))
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    return path
