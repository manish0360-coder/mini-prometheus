"""MP-S1 (spec §3.8, ADR-0022): a traceable form for every exposed verdict under a declared shop.

A ``Verdict`` is a consumed Noetica envelope with no plan, episode or shop field, and Mini Prometheus
may not extend it (Law 15). A bare verdict is therefore NOT traceable on its own. ``VerdictTrace`` is
the supported external form: it links the verdict to the exact shop declaration, production plan,
episode (when one exists) and evidence class, and every builder FAILS CLOSED
(``VerdictTraceError``) when those artifacts disagree. Internal, not a contract, pure, deterministic.

- ``trace_run`` covers RunResult / ReuseRunResult (fresh run, reuse hit or miss, INFRA_ERROR).
- ``trace_job`` covers a scheduling job verdict: scheduling is read-only by RM11 design, so there is
  no episode (record ``SCHEDULE_READ_ONLY``).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from contracts.python.manufacturing.production_plan_schema import CapabilityModelRef
from mini_prometheus import _hashing as h
from mini_prometheus._contracts import ProductionPlan, Ref, Verdict
from mini_prometheus.manufacturing_constraints.capability_model import ProcessCapabilityModel
from mini_prometheus.shop_declaration.shop_model import (
    NOT_VERIFIED,
    capability_model_ref_for,
)


class VerdictTraceError(ValueError):
    """The verdict, plan, episode and shop identity presented together do not agree."""


class TraceRecord(StrEnum):
    EPISODE = "EPISODE"
    SCHEDULE_READ_ONLY = "SCHEDULE_READ_ONLY"
    NONE_INFRA_ERROR = "NONE_INFRA_ERROR"


@dataclass(frozen=True)
class VerdictTrace:
    status: str
    reason_codes: tuple[str, ...]
    verdict_produced_by: tuple[str, str]
    record: TraceRecord
    plan_ref: Ref | None
    episode_ref: Ref | None
    shop_ref: CapabilityModelRef | None
    trace_hash: str


def _build(
    verdict: Verdict,
    record: TraceRecord,
    plan_ref: Ref | None,
    episode_ref: Ref | None,
    shop_ref: CapabilityModelRef | None,
) -> VerdictTrace:
    view: dict[str, Any] = {
        "status": verdict.status,
        "reason_codes": sorted(verdict.reason_codes),
        "verdict_produced_by": [verdict.produced_by.component, verdict.produced_by.version],
        "record": record.value,
        "plan_ref": h.to_contract_dict(plan_ref) if plan_ref else None,
        "episode_ref": h.to_contract_dict(episode_ref) if episode_ref else None,
        "shop_ref": h.to_contract_dict(shop_ref) if shop_ref else None,
    }
    return VerdictTrace(
        status=verdict.status,
        reason_codes=tuple(sorted(verdict.reason_codes)),
        verdict_produced_by=(verdict.produced_by.component, verdict.produced_by.version),
        record=record,
        plan_ref=plan_ref,
        episode_ref=episode_ref,
        shop_ref=shop_ref,
        trace_hash=h.content_hash(view),
    )


def _plan_ref(plan: ProductionPlan) -> Ref:
    return Ref(id=plan.plan_id, content_hash=plan.content_hash)


def trace_run(result: Any, capability_model: ProcessCapabilityModel) -> VerdictTrace:
    """Trace a ``RunResult`` or ``ReuseRunResult`` produced under ``capability_model``."""
    verdict: Verdict = result.verdict
    expected = capability_model_ref_for(capability_model)
    if verdict.is_error:
        if result.plan is not None or result.episode is not None:
            raise VerdictTraceError("an error verdict must carry no plan and no episode")
        return _build(verdict, TraceRecord.NONE_INFRA_ERROR, None, None, expected)
    plan, episode = result.plan, result.episode
    if plan is None or episode is None:
        raise VerdictTraceError("a grounded verdict must come with its plan and its episode")
    if h.to_contract_dict(episode.verdict) != h.to_contract_dict(verdict):
        raise VerdictTraceError("the episode's verdict is not the verdict being exposed")
    if episode.plan.content_hash != plan.content_hash:
        raise VerdictTraceError("the episode's plan is not the plan being exposed")
    if plan.capability_model_ref != expected:
        raise VerdictTraceError(
            f"the plan's shop identity {plan.capability_model_ref!r} is not the model's {expected!r}"
        )
    source = getattr(result, "source_episode", None)  # set only on a reuse hit
    if source is not None and (source.id, source.content_hash) != (
        episode.episode_id,
        episode.content_hash,
    ):
        raise VerdictTraceError("the reused source episode is not the episode being exposed")
    episode_ref = Ref(id=episode.episode_id, content_hash=episode.content_hash)
    return _build(verdict, TraceRecord.EPISODE, _plan_ref(plan), episode_ref, expected)


def trace_job(
    plan: ProductionPlan, verdict: Verdict, capability_model: ProcessCapabilityModel
) -> VerdictTrace:
    """Trace a scheduling job verdict (no episode: scheduling persists nothing, RM11)."""
    expected = capability_model_ref_for(capability_model)
    if plan.capability_model_ref != expected:
        raise VerdictTraceError(
            f"the plan's shop identity {plan.capability_model_ref!r} is not the model's {expected!r}"
        )
    return _build(verdict, TraceRecord.SCHEDULE_READ_ONLY, _plan_ref(plan), None, expected)


def trace_line(trace: VerdictTrace, shop_line: str, path: str | None) -> str:
    """The CLI line for a declared-shop verdict (spec §3.8)."""
    reasons = ", ".join(trace.reason_codes)
    plan = trace.plan_ref.content_hash if trace.plan_ref else "none"
    episode = trace.episode_ref.content_hash if trace.episode_ref else f"none ({trace.record})"
    where = path if path is not None else "no episode written"
    return (
        f"{trace.status} [{reasons}] plan {plan} episode {episode} {shop_line} "
        f"trace {trace.trace_hash} -> {where}"
    )


__all__ = [
    "NOT_VERIFIED",
    "TraceRecord",
    "VerdictTrace",
    "VerdictTraceError",
    "trace_job",
    "trace_line",
    "trace_run",
]
