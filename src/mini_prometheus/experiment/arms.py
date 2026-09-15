"""RM5 C3 — the three evaluation arms (compose RM1/RM3/RM4 read-only; no new reasoning logic).

Each arm produces one RM4 ``EngineeringCritique`` for a held-out case, differing ONLY in the precedent
report handed to judgment — so the Arm3-Arm2 contrast isolates the precedent's marginal effect:

    Arm 1  Cold Start   — empty experience corpus  -> NONE report -> judge
    Arm 2  No Precedent  — full corpus available, but RM4 receives a NONE report -> judge
    Arm 3  Full System  — full corpus + the ACTUAL RM3 PrecedentReport (experience partition only) -> judge

Composition only: retrieval/ranking is RM3's ``retriever.rank`` (pure, over an in-memory experience list
for exact leakage control), report assembly is RM3's ``reasoner.reason``, and judgment is RM4's
``judgment_runner.run_judgment``. This module owns no retrieval, scoring, signal, or judgment logic and
writes nothing. Determinism: a fixed ``produced_at`` is threaded through (excluded from every identity),
so critique ``content_hash`` depends only on (episode, precedent report).

Arm1 == Arm2 by construction (both feed ``reason(query, [])``): the validity control proving judgment
depends solely on the precedent-report input, never on latent corpus state.
"""
from __future__ import annotations

from dataclasses import dataclass

from contracts.python.manufacturing.precedent_report_schema import PrecedentReport, PrecedentSignal

from mini_prometheus._contracts import DesignInput, ManufacturingEpisode
from mini_prometheus.judgment.critic_model import Assessment
from mini_prometheus.orchestration.judgment_runner import run_judgment
from mini_prometheus.precedent import reasoner, retriever

# Fixed, timing-free timestamp (matches the corpus generator); excluded from all identity views.
_FIXED_PRODUCED_AT = "2026-01-01T00:00:00+00:00"


@dataclass(frozen=True)
class ArmOutcome:
    """One arm's judgment of one held-out case (internal; not a contract)."""

    assessment: Assessment
    signal: PrecedentSignal  # the precedent signal RM4 consumed (NONE for arms 1 & 2)
    critique_content_hash: str  # RM4's reproducibility fingerprint (Arm1==Arm2 exactness check)


def none_report(query: DesignInput) -> PrecedentReport:
    """A NONE precedent report tied to ``query`` (empty ranking -> signal NONE). Arms 1 & 2."""
    return reasoner.reason(query, [], produced_at=_FIXED_PRODUCED_AT)


def real_report(query: DesignInput, experience: list[ManufacturingEpisode]) -> PrecedentReport:
    """The ACTUAL RM3 report: rank the EXPERIENCE partition only (leakage-safe), then reason. Arm 3."""
    ranked = retriever.rank(query, experience)
    return reasoner.reason(query, ranked, produced_at=_FIXED_PRODUCED_AT)


def _design(episode: ManufacturingEpisode) -> DesignInput:
    """Fail-closed access to the episode's embedded design (RM5 requires 1.1.0+ episodes)."""
    di = episode.design_input
    if di is None:
        raise ValueError(f"episode {episode.episode_id} carries no embedded design_input")
    return di


def _judge(episode: ManufacturingEpisode, report: PrecedentReport) -> ArmOutcome:
    """Run RM4 judgment for ``episode`` against ``report`` and project to the arm outcome."""
    critique = run_judgment(episode, report, produced_at=_FIXED_PRODUCED_AT)
    return ArmOutcome(
        assessment=critique.assessment,
        signal=report.signal,
        critique_content_hash=critique.content_hash,
    )


def cold_start(episode: ManufacturingEpisode) -> ArmOutcome:
    """Arm 1 — empty experience corpus -> NONE report -> judge."""
    return _judge(episode, none_report(_design(episode)))


def no_precedent(episode: ManufacturingEpisode) -> ArmOutcome:
    """Arm 2 — full corpus available (held by the runner), but RM4 receives a NONE report -> judge.

    Identical to ``cold_start`` by construction: this is the Arm1==Arm2 validity control. The full
    corpus's *availability* is a property of the harness (the runner has loaded it and Arm 3 consumes
    it); Arm 2 deliberately withholds it from judgment by passing NONE.
    """
    return _judge(episode, none_report(_design(episode)))


def full_system(episode: ManufacturingEpisode, experience: list[ManufacturingEpisode]) -> ArmOutcome:
    """Arm 3 — full corpus + the actual RM3 PrecedentReport (experience partition only) -> judge."""
    return _judge(episode, real_report(_design(episode), experience))
