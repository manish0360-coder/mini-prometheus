"""RM4 Commit 1: the internal EngineeringSituation — the coherent engineering state of one case.

Engineering Judgment (RM4) is the **first consumer** of this primitive. ``EngineeringSituation`` is the
coherent, single-case, in-memory engineering state that Engineering Judgment reasons over. It is
assembled by **aggregation** of artifacts the prior rungs already produced — never re-derived — and it
is **strictly internal** to ``judgment/``: not a contract, not a schema, not persisted, carrying **no
external identity**, and never exposed outside this package.

Observed constituents are **contingent, not definitional**: the case's normalized design input, its
proposed production plan, its grounded manufacturability verdict, and its precedent report are present
**because Engineering Judgment — the primitive's first consumer — requires them today**. Future
constituents may be added only through evidence-driven extraction, never anticipation.

State, not behavior: ``EngineeringSituation`` performs no planning, verification, retrieval, or
reasoning. Its one invariant is **mutual referential coherence** — every constituent belongs to the same
case — enforced by matching the artifacts' existing content-hash references (no new hash is minted).
Assembly is pure and deterministic and **fails closed**: an incoherent or incomplete case raises rather
than yielding a partial, dishonest situation. It reads nothing from disk and writes nothing.
"""
from __future__ import annotations

from dataclasses import dataclass

from contracts.python.manufacturing.precedent_report_schema import PrecedentReport

from mini_prometheus._contracts import (
    DesignInput,
    ManufacturingEpisode,
    ProductionPlan,
    Verdict,
)


class SituationCoherenceError(ValueError):
    """Raised when the supplied artifacts do not form the coherent engineering state of one case."""


@dataclass(frozen=True)
class EngineeringSituation:
    """The coherent engineering state of one manufacturing case (internal to ``judgment/``).

    Holds references to the case's already-produced constituents. It has **no** ``content_hash`` and
    **no** id: the situation carries no external identity and is never persisted or exposed outside
    ``judgment/``.
    """

    design_input: DesignInput
    plan: ProductionPlan
    verdict: Verdict
    precedent_report: PrecedentReport

    @property
    def constituents(self) -> tuple[str, ...]:
        """The observed constituent set actually assembled — for milestone revelation, not identity."""
        return ("design_input", "plan", "verdict", "precedent_report")


def _precedent_report_case(precedent_report: PrecedentReport) -> str:
    """The engineering case (design content hash) a precedent report was reasoned about.

    This is the single point that knows how *today's* first consumer — the ``PrecedentReport`` — records
    the case it belongs to. Isolating it here keeps ``assemble``'s coherence invariant expressed at the
    level of the abstract engineering case rather than coupled to this consumer's field layout.
    """
    return precedent_report.query_design_input_ref.content_hash


def assemble(
    episode: ManufacturingEpisode, precedent_report: PrecedentReport
) -> EngineeringSituation:
    """Assemble the coherent EngineeringSituation for one case from already-produced artifacts.

    Read-only aggregation: the RM1 ``episode`` supplies the case's embedded design input, its proposed
    plan, and its grounded verdict; the RM3 ``precedent_report`` supplies its precedent. Coherence is
    enforced at the level of the engineering **case** — every constituent must reference the same case
    (identified by its design's content hash) — so assembly re-derives nothing, mints no identity, and
    writes nothing. Raises ``SituationCoherenceError`` on an incomplete case (no embedded design input) or
    a cross-case pairing.
    """
    design_input = episode.design_input
    if design_input is None:
        raise SituationCoherenceError(
            "episode carries no embedded design_input; cannot assemble a complete engineering situation"
        )
    # Coherence at the level of the abstract primitive: every constituent must belong to the same
    # engineering case. A case is identified by its design (its content hash); the episode is the case's
    # RM1 record, so its design_ref is the canonical case key, and every other constituent must reference
    # that same case. No new identity is minted — only existing case references are compared.
    case_key = episode.design_ref.content_hash
    precedent_case = _precedent_report_case(precedent_report)
    if precedent_case != case_key:
        raise SituationCoherenceError(
            "precedent report belongs to a different engineering case "
            f"(precedent case {precedent_case} != case {case_key})"
        )
    return EngineeringSituation(
        design_input=design_input,
        plan=episode.plan,
        verdict=episode.verdict,
        precedent_report=precedent_report,
    )
