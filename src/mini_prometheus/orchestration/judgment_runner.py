"""RM4 Commit 4: the Engineering Judgment composition entry — the thin, read-only pipeline.

Composes the already-implemented RM4 components into one deterministic call:

    (RM1 episode, RM3 precedent report)
      -> EngineeringSituation   (assemble; RM4 Commit 1 — read-only, fail-closed coherence)
      -> EngineeringCritique    (critique;  RM4 Commit 3 — pure judgment)

This is a NEW file. RM1's ``runner.py``, RM2's ``reuse_runner.py``, and RM3's ``precedent_runner.py`` are
byte-unchanged. The composition holds **no** business logic of its own — no planning, no manufacturability
verification, no retrieval, no persistence, no mutation. It **receives** the case's already-produced
artifacts (it never fetches or re-derives them) and only wires assembly + judgment, so RM4 never re-plans,
re-verifies, or re-retrieves, and never touches the RM2 read side.

Read-only and deterministic: identical ``(episode, precedent_report)`` + identical ``critic_model_version``
⇒ identical ``EngineeringCritique`` ``content_hash`` (``produced_at`` excluded from identity).
"""
from __future__ import annotations

from contracts.python.manufacturing.precedent_report_schema import PrecedentReport

from mini_prometheus._contracts import ManufacturingEpisode
from mini_prometheus.judgment.critic_model import CriticModel
from mini_prometheus.judgment.engineering_critique import EngineeringCritique, critique
from mini_prometheus.judgment.engineering_situation import assemble


def run_judgment(
    episode: ManufacturingEpisode,
    precedent_report: PrecedentReport,
    *,
    model: CriticModel | None = None,
    produced_at: str | None = None,
) -> EngineeringCritique:
    """Compose assembly + judgment into one deterministic, read-only EngineeringCritique call.

    Receives the case's already-produced RM1 ``episode`` (design / plan / verdict) and RM3
    ``precedent_report`` — never fetches or re-derives them — assembles the coherent internal
    ``EngineeringSituation`` (fail-closed on a cross-case pairing), and returns the advisory critique.
    """
    situation = assemble(episode, precedent_report)
    return critique(situation, model, produced_at=produced_at)
