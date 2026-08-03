"""RM4 Commit 2: the deterministic, versioned judgment model (Engineering Judgment domain content).

The critic model is the *content* of Engineering Judgment — it defines **what constitutes a situated
finding**: the closed taxonomy of finding families and the deterministic rule for each, plus the
deterministic summary-assessment derivation. It reasons over the internal ``EngineeringSituation``
(RM4 Commit 1) only; it performs no planning, no manufacturability verification, no retrieval, and no
persistence, and it produces no report object (assembling the advisory critique is RM4 Commit 3's job).

Finding families (first implementation — a closed taxonomy):
  * INTENT_COVERAGE      — does the proposed plan realize every operation the design declared?
  * PRECEDENT_CONSISTENCY — what does the strongly-relevant verified precedent say (consumes the RM3
                            precedent report's already-derived signal as-is; never re-retrieves/re-scores)?
  * INTERNAL_VERDICT     — surfaces the case's own recorded manufacturability verdict when adverse
                            (advisory surfacing only — never a re-verification, never a new verdict).

Determinism: findings are produced in a fixed family order with sorted reason codes and count-based,
integer-only detail; the model is versioned by ``critic_model_version`` so results are reproducible and
comparable across revisions. Every finding is **grounded** by the situation constituent that produced it
(evidence-grounding rule). No ML, embeddings, or learned weights.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from contracts.python.manufacturing.precedent_report_schema import PrecedentSignal

from mini_prometheus.judgment.engineering_situation import EngineeringSituation

CRITIC_MODEL_VERSION = "1.0.0"

# Adverse manufacturability outcomes the INTERNAL_VERDICT family surfaces (never re-verifies).
_ADVERSE_VERDICTS = frozenset({"NOT_MANUFACTURABLE", "PLAN_INVALID"})


class FindingKind(StrEnum):
    """Closed taxonomy of situated-finding families. Member change = MAJOR (contract-package rule)."""

    INTENT_COVERAGE = "INTENT_COVERAGE"
    PRECEDENT_CONSISTENCY = "PRECEDENT_CONSISTENCY"
    INTERNAL_VERDICT = "INTERNAL_VERDICT"


class FindingPolarity(StrEnum):
    """Whether a finding weighs against (cautionary) or for (supportive) the proposed plan."""

    CAUTIONARY = "CAUTIONARY"
    SUPPORTIVE = "SUPPORTIVE"


class Assessment(StrEnum):
    """The deterministic summary of a situation's findings (report-level advisory)."""

    CAUTIONARY = "CAUTIONARY"
    SUPPORTIVE = "SUPPORTIVE"
    NEUTRAL = "NEUTRAL"


@dataclass(frozen=True)
class CriticFinding:
    """One situated finding. Internal to ``judgment/`` — not a contract.

    ``constituent`` names the EngineeringSituation constituent that grounds the finding (the evidence-
    grounding rule: every finding is traceable to explicit situation evidence).
    """

    kind: FindingKind
    polarity: FindingPolarity
    constituent: str
    reason_codes: tuple[str, ...]
    detail: str


@dataclass(frozen=True)
class CriticModel:
    """A versioned judgment model. The version identifies the (fixed) finding ruleset it applies."""

    version: str


def default_model() -> CriticModel:
    """The frozen v1.0.0 critic model."""
    return CriticModel(version=CRITIC_MODEL_VERSION)


def evaluate(
    situation: EngineeringSituation, model: CriticModel | None = None
) -> tuple[CriticFinding, ...]:
    """Deterministically derive the situated findings for one engineering case.

    Pure: reads the situation, applies each finding family in a fixed order, and returns the findings
    as an immutable tuple. ``model`` selects the (versioned) ruleset; the default is the frozen v1.0.0.
    """
    _ = model or default_model()  # reserved for future versioned rulesets; v1.0.0 rules are fixed
    findings: list[CriticFinding] = []
    findings.extend(_intent_coverage(situation))
    findings.extend(_precedent_consistency(situation))
    findings.extend(_internal_verdict(situation))
    return tuple(findings)


def assess(findings: tuple[CriticFinding, ...], model: CriticModel | None = None) -> Assessment:
    """Derive the deterministic summary assessment from the findings.

    Cautionary dominates: any cautionary finding yields CAUTIONARY; otherwise a supportive finding
    yields SUPPORTIVE; an empty/neutral set yields NEUTRAL.
    """
    _ = model or default_model()
    if any(f.polarity is FindingPolarity.CAUTIONARY for f in findings):
        return Assessment.CAUTIONARY
    if any(f.polarity is FindingPolarity.SUPPORTIVE for f in findings):
        return Assessment.SUPPORTIVE
    return Assessment.NEUTRAL


# --- finding families (deterministic, pure) ---------------------------------------------------------

def _intent_coverage(situation: EngineeringSituation) -> tuple[CriticFinding, ...]:
    """Cautionary iff the plan omits an operation the design declared."""
    plan_ops = {step.op for step in situation.plan.steps}
    missing = sorted(
        {op.op.value for op in situation.design_input.declared_operations}
        - {op.value for op in plan_ops}
    )
    if not missing:
        return ()
    return (
        CriticFinding(
            kind=FindingKind.INTENT_COVERAGE,
            polarity=FindingPolarity.CAUTIONARY,
            constituent="design_input",
            reason_codes=(),
            detail=f"plan omits {len(missing)} declared operation(s): {', '.join(missing)}",
        ),
    )


def _precedent_consistency(situation: EngineeringSituation) -> tuple[CriticFinding, ...]:
    """Read the RM3 precedent report's already-derived signal (never re-retrieve or re-score)."""
    report = situation.precedent_report
    rank = report.signal_source_rank
    if rank is None:
        return ()
    source = report.precedents[rank]
    if report.signal is PrecedentSignal.CAUTIONARY:
        return (
            CriticFinding(
                kind=FindingKind.PRECEDENT_CONSISTENCY,
                polarity=FindingPolarity.CAUTIONARY,
                constituent="precedent_report",
                reason_codes=tuple(sorted(c.value for c in source.reason_codes)),
                detail=f"strongly-relevant precedent was NOT_MANUFACTURABLE (rank {source.rank})",
            ),
        )
    if report.signal is PrecedentSignal.SUPPORTING:
        return (
            CriticFinding(
                kind=FindingKind.PRECEDENT_CONSISTENCY,
                polarity=FindingPolarity.SUPPORTIVE,
                constituent="precedent_report",
                reason_codes=(),
                detail=f"strongly-relevant precedent was MANUFACTURABLE (rank {source.rank})",
            ),
        )
    return ()


def _internal_verdict(situation: EngineeringSituation) -> tuple[CriticFinding, ...]:
    """Surface the case's own recorded verdict when adverse (advisory surfacing, not a re-verdict)."""
    status = situation.verdict.status
    if status not in _ADVERSE_VERDICTS:
        return ()
    return (
        CriticFinding(
            kind=FindingKind.INTERNAL_VERDICT,
            polarity=FindingPolarity.CAUTIONARY,
            constituent="verdict",
            reason_codes=tuple(sorted(situation.verdict.reason_codes)),
            detail=f"the case's own recorded verdict is {status}",
        ),
    )
