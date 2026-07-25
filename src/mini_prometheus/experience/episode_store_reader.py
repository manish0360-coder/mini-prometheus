"""RM2-M1: read RM1's append-only episode JSONL back into verified ``ManufacturingEpisode`` objects.

Deterministic, explicit per-type reconstruction (no reflection, no new dependency). Each loaded episode's
identity is re-verified: ``content_hash(episode_identity(episode))`` must equal the stored ``content_hash``
(Law 18 / contract package §1.4). A missing store returns ``[]``. This module only reads; it never writes,
retains, prunes, or indexes (those are later milestones / Noetica's framework — Law 6).
"""
from __future__ import annotations

import json
from pathlib import Path

from mini_prometheus import _hashing as h
from mini_prometheus._contracts import (
    EngineeringVerificationStatus,
    ManufacturingEpisode,
    ManufacturingTask,
    ProcessOp,
    ProcessStep,
    ProducedBy,
    ProductIntent,
    ProductionPlan,
    Provenance,
    Ref,
    ResourceAssignment,
    Timing,
    Verdict,
)
from mini_prometheus.orchestration.episode_store import DEFAULT_STORE


class EpisodeIntegrityError(ValueError):
    """Raised when a stored episode is malformed or its content_hash does not re-verify."""


# --- explicit per-type reconstructors (only these two enum conversions exist: §0) -----------------

def _ref(d: dict) -> Ref:
    return Ref(id=d["id"], content_hash=d["content_hash"])


def _produced_by(d: dict) -> ProducedBy:
    return ProducedBy(component=d["component"], version=d["version"])


def _provenance(d: dict) -> Provenance:
    return Provenance(
        source_refs=[_ref(r) for r in d["source_refs"]],
        rule_id=d["rule_id"],
        rule_version=d["rule_version"],
        capability_model_version=d["capability_model_version"],
        produced_by=_produced_by(d["produced_by"]),
        produced_at=d["produced_at"],
    )


def _product_intent(d: dict) -> ProductIntent:
    return ProductIntent(summary=d["summary"])


def _task(d: dict) -> ManufacturingTask:
    return ManufacturingTask(
        schema_version=d["schema_version"],
        task_id=d["task_id"],
        product_intent=_product_intent(d["product_intent"]),
        design_input_ref=_ref(d["design_input_ref"]),
    )


def _step(d: dict) -> ProcessStep:
    return ProcessStep(
        index=d["index"],
        op=ProcessOp(d["op"]),  # enum conversion
        required_capability=d["required_capability"],
        inputs=list(d["inputs"]),
        provenance_ref=_ref(d["provenance_ref"]),
        params=d.get("params"),
    )


def _assignment(d: dict) -> ResourceAssignment:
    return ResourceAssignment(
        step_index=d["step_index"],
        resource_id=d["resource_id"],
        capability_id=d["capability_id"],
    )


def _plan(d: dict) -> ProductionPlan:
    return ProductionPlan(
        schema_version=d["schema_version"],
        plan_id=d["plan_id"],
        task_ref=_ref(d["task_ref"]),
        steps=[_step(s) for s in d["steps"]],
        resource_assignments=[_assignment(a) for a in d["resource_assignments"]],
        capability_model_version=d["capability_model_version"],
        content_hash=d["content_hash"],
        provenance=_provenance(d["provenance"]),
    )


def _verdict(d: dict) -> Verdict:
    return Verdict(
        grounded=d["grounded"],
        is_error=d["is_error"],
        status=d["status"],
        reason_codes=list(d["reason_codes"]),
        produced_by=_produced_by(d["produced_by"]),
        detail=d.get("detail"),
    )


def _timing(d: dict) -> Timing:
    return Timing(created_at=d["created_at"], plan_ms=d["plan_ms"], verify_ms=d["verify_ms"])


def _episode(d: dict) -> ManufacturingEpisode:
    return ManufacturingEpisode(
        schema_version=d["schema_version"],
        episode_id=d["episode_id"],
        task=_task(d["task"]),
        design_ref=_ref(d["design_ref"]),
        engineering_verification_status=EngineeringVerificationStatus(  # enum conversion
            d["engineering_verification_status"]
        ),
        plan=_plan(d["plan"]),
        verdict=_verdict(d["verdict"]),
        capability_model_version=d["capability_model_version"],
        content_hash=d["content_hash"],
        provenance=_provenance(d["provenance"]),
        timing=_timing(d["timing"]),
    )


def load(store_path: str | Path | None = None) -> list[ManufacturingEpisode]:
    """Read the JSONL episode store; reconstruct and integrity-verify each episode.

    A missing store returns ``[]``. Raises ``EpisodeIntegrityError`` on malformed JSON, a missing field,
    or a ``content_hash`` that does not re-verify.
    """
    path = Path(store_path) if store_path is not None else DEFAULT_STORE
    if not path.exists():
        return []

    episodes: list[ManufacturingEpisode] = []
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError as exc:
            raise EpisodeIntegrityError(f"line {lineno}: invalid JSON: {exc}") from exc
        try:
            episode = _episode(data)
        except (KeyError, TypeError, ValueError) as exc:
            raise EpisodeIntegrityError(f"line {lineno}: malformed episode: {exc}") from exc
        recomputed = h.content_hash(h.episode_identity(episode))
        if recomputed != data.get("content_hash"):
            raise EpisodeIntegrityError(
                f"line {lineno}: content_hash mismatch (stored={data.get('content_hash')}, recomputed={recomputed})"
            )
        episodes.append(episode)
    return episodes
